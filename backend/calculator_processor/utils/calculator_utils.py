import ifcopenshell
import numpy as np
from numpy import abs as np_abs
from ifcopenshell.util.element import get_psets
from loguru import logger
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os
import pandas as pd
from pprint import pprint
from pymongo import MongoClient
import boto3
import dotenv
import io

dotenv.load_dotenv()

S3_BUCKET_NAME = "material-matching"
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")

MONGODB_URI = os.environ.get("MONGODB_URL")
DB_NAME = os.environ.get("DB_NAME")

# Global variables
MaterialList = {}
_db_client = None
_db = None

# File paths for material database
MATERIAL_CSV_S3_PATH = f"material_database.csv"
EMBEDDING_NPY_S3_PATH = f"material_embeddings.npy"


def get_s3_client():
    """Get or create S3 client connection"""
    try:
        s3_client = boto3.client("s3", region_name=AWS_REGION)
        return s3_client
    except Exception as e:
        logger.error(f"Error creating S3 client: {e}")
        return None


def upload_to_s3(local_data, s3_path, content_type=None):
    """Upload data to S3 bucket

    Args:
        local_data: Data to upload (file path or bytes-like object)
        s3_path: Path in S3 bucket
        content_type: MIME type of the file (optional)
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False

    try:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        # If local_data is a string, assume it's a file path
        if isinstance(local_data, str) and os.path.exists(local_data):
            s3_client.upload_file(
                local_data, S3_BUCKET_NAME, s3_path, ExtraArgs=extra_args
            )
        else:
            # Assume it's a bytes-like object
            s3_client.upload_fileobj(
                local_data, S3_BUCKET_NAME, s3_path, ExtraArgs=extra_args
            )

        logger.info(f"Successfully uploaded to s3://{S3_BUCKET_NAME}/{s3_path}")
        return True
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
        return False


def download_from_s3(s3_path, local_path=None):
    """Download data from S3 bucket

    Args:
        s3_path: Path in S3 bucket
        local_path: Local path to save the file (optional)

    Returns:
        If local_path is provided: True/False for success/failure
        If local_path is not provided: BytesIO object with the data or None
    """
    s3_client = get_s3_client()
    if not s3_client:
        return None if local_path is None else False

    try:
        if local_path:
            s3_client.download_file(S3_BUCKET_NAME, s3_path, local_path)
            logger.info(f"Downloaded s3://{S3_BUCKET_NAME}/{s3_path} to {local_path}")
            return True
        else:
            # Download to memory
            buffer = io.BytesIO()
            s3_client.download_fileobj(S3_BUCKET_NAME, s3_path, buffer)
            buffer.seek(0)  # Reset the buffer position to the beginning
            logger.info(f"Downloaded s3://{S3_BUCKET_NAME}/{s3_path} to memory")
            return buffer
    except Exception as e:
        logger.error(f"Error downloading from S3: {e}")
        return None if local_path is None else False


def check_s3_file_exists(s3_path):
    """Check if a file exists in S3 bucket"""
    s3_client = get_s3_client()
    if not s3_client:
        return False

    try:
        s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=s3_path)
        return True
    except Exception:
        return False


def get_db():
    """Get or create MongoDB database connection"""
    global _db_client, _db

    if _db is None:
        if not MONGODB_URI:
            raise ValueError("MongoDB environment variables not configured")

        _db_client = MongoClient(MONGODB_URI)
        _db = _db_client[DB_NAME]

    return _db


def refresh_materials_list():
    """Refresh the materials list from MongoDB"""
    global MaterialList

    db = get_db()
    cursor = db.materials.find({})

    # Convert MongoDB results to the required dictionary format
    materials_dict = {}

    for material in cursor:
        # Extract the material name from specified_material
        material_name = material.get("specified_material")
        embodied_carbon = material.get("embodied_carbon")  # ec_per_kg
        density = material.get("density")

        if not material_name:
            continue

        # Store as [embodied_carbon, density] as per your example format
        if embodied_carbon is not None and density is not None:
            materials_dict[material_name] = [float(embodied_carbon), float(density)]
        # If it's a per m² value (e.g., for windows/doors)
        elif embodied_carbon is not None and material.get("unit") == "m2":
            materials_dict[material_name] = float(embodied_carbon)

    # Update the global variable
    MaterialList = materials_dict
    pprint(MaterialList)
    return MaterialList


MaterialsToIgnore = ["Travertine", "<Unnamed>"]


# Globals for material embedding functionality
embedding_model = None
material_embeddings = None
material_data_df = None


def get_element_area(element):
    settings = ifcopenshell.geom.settings()
    try:
        shape = ifcopenshell.geom.create_shape(settings, element)
        vertices = np.array(shape.geometry.verts).reshape((-1, 3))
        faces = np.array(shape.geometry.faces).reshape(-1, 3)

        # Get all triangle vertices at once
        v1 = vertices[faces[:, 0]]
        v2 = vertices[faces[:, 1]]
        v3 = vertices[faces[:, 2]]

        # Calculate area using cross product method
        # Area of a triangle = magnitude of cross product / 2
        cross_products = np.cross(v2 - v1, v3 - v1)
        # Calculate magnitude of cross products
        areas = np.sqrt(np.sum(cross_products**2, axis=1)) / 2.0

        # Sum all triangle areas
        total_area = np.sum(areas)
        return np.abs(total_area)

    except RuntimeError as e:
        print(f"Error processing geometry: {e}")
        return None
    return area


def get_element_volume(element):
    settings = ifcopenshell.geom.settings()

    try:
        shape = ifcopenshell.geom.create_shape(settings, element)
        vertices = np.array(shape.geometry.verts).reshape((-1, 3))
        faces = np.array(shape.geometry.faces).reshape(-1, 3)

        # Get all triangle vertices at once
        v1 = vertices[faces[:, 0]]
        v2 = vertices[faces[:, 1]]
        v3 = vertices[faces[:, 2]]

        # Calculate volume using cross product method
        # Volume = sum(v1 · (v2 × v3)) / 6
        cross_products = np.cross(v2, v3)
        dot_products = np.sum(v1 * cross_products, axis=1)
        volume = np.sum(dot_products) / 6.0

        return np_abs(volume)

    except RuntimeError as e:
        print(f"Error processing geometry: {e}")
        return None


def initialize_embedding_model():
    """Initialize the sentence transformer model for material matching"""
    global embedding_model

    if embedding_model is None:
        try:
            embedding_model = SentenceTransformer(
                "sentence-transformers/msmarco-MiniLM-L-6-v3"
            )
            logger.info("Loaded embedding model for material matching")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            embedding_model = None

    return embedding_model


def load_material_database():
    """Load material database from S3 if they exist"""
    global material_embeddings, material_data_df

    # Initialize with empty dataframe if nothing exists yet
    if material_data_df is None:
        try:
            if check_s3_file_exists(MATERIAL_CSV_S3_PATH):
                # Download CSV from S3 to memory
                csv_buffer = download_from_s3(MATERIAL_CSV_S3_PATH)
                if csv_buffer:
                    material_data_df = pd.read_csv(csv_buffer)
                    logger.info(
                        f"Loaded {len(material_data_df)} material records from S3: {MATERIAL_CSV_S3_PATH}"
                    )
            else:
                # Create an empty DataFrame with the required columns
                material_data_df = pd.DataFrame(
                    columns=[
                        "material_name",
                        "element_type",
                        "material_type",
                        "volume",
                        "area",
                        "layer_count",
                        "material_description",
                        "ec_per_kg",
                        "density",
                    ]
                )
                logger.info(
                    f"Created new material database (no existing file found in S3)"
                )
        except Exception as e:
            logger.error(f"Error loading material database CSV from S3: {e}")
            material_data_df = pd.DataFrame(
                columns=[
                    "material_name",
                    "element_type",
                    "material_type",
                    "volume",
                    "area",
                    "layer_count",
                    "material_description",
                    "ec_per_kg",
                    "density",
                ]
            )

    # Load embeddings if available
    if material_embeddings is None:
        try:
            if check_s3_file_exists(EMBEDDING_NPY_S3_PATH):
                # Download NPY from S3 to memory
                npy_buffer = download_from_s3(EMBEDDING_NPY_S3_PATH)
                if npy_buffer:
                    material_embeddings = np.load(npy_buffer)
                    logger.info(
                        f"Loaded {len(material_embeddings)} material embeddings from S3: {EMBEDDING_NPY_S3_PATH}"
                    )
            else:
                material_embeddings = np.array([])
                logger.info(f"No existing embeddings found in S3")
        except Exception as e:
            logger.error(f"Error loading embeddings from S3: {e}")
            material_embeddings = np.array([])

    return material_data_df is not None and material_embeddings is not None


def create_material_description(element_info):
    """Create a descriptive text for embedding based on element properties"""
    desc_parts = [f"ElementType:{element_info.get('element_type', 'Unknown')}"]

    # Add dimensions if available
    for key, value in element_info.items():
        if key.startswith("dimension_") and value is not None:
            dimension_name = key.replace("dimension_", "")
            desc_parts.append(f"{dimension_name.capitalize()}:{value}")

    # Add volume/area if available
    if "volume" in element_info and element_info["volume"] is not None:
        desc_parts.append(f"Volume:{element_info['volume']:.3f}")

    for area_type in ["area", "net_area", "gross_area", "net_side_area"]:
        if area_type in element_info and element_info[area_type] is not None:
            desc_parts.append(f"{area_type.capitalize()}:{element_info[area_type]:.3f}")

    # Add material properties
    if "material_type" in element_info:
        desc_parts.append(f"MaterialType:{element_info['material_type']}")

    if "material_name" in element_info and element_info["material_name"]:
        desc_parts.append(f"MaterialName:{element_info['material_name']}")

    # For layered materials, add layer info
    if (
        element_info.get("material_type") == "layered"
        and "layer_materials" in element_info
    ):
        layers = element_info.get("layer_materials", [])
        desc_parts.append(f"LayerCount:{len(layers)}")
        if layers:
            desc_parts.append(f"Layers:{','.join(layers)}")

    # For rebars, add info
    if element_info.get("has_rebar", False):
        desc_parts.append("HasRebar:true")

    return " ".join(desc_parts)


def extract_element_metadata(element, existing_data=None):
    """Extract comprehensive metadata about an element for material matching"""
    element_data = existing_data or {}

    # Basic element info
    element_data["element_id"] = element.id()
    element_data["element_type"] = element.is_a()
    element_data["element_name"] = element.Name if hasattr(element, "Name") else None

    # Get property sets
    psets = get_psets(element)

    # Extract dimensions from property sets
    dimensions = psets.get("Dimensions", {})
    for key, value in dimensions.items():
        if isinstance(value, (int, float)):
            element_data[f"dimension_{key.lower()}"] = value

    # Extract quantities
    if hasattr(element, "IsDefinedBy"):
        for definition in element.IsDefinedBy:
            if definition.is_a("IfcRelDefinesByProperties"):
                property_def = definition.RelatingPropertyDefinition
                if property_def.is_a("IfcElementQuantity"):
                    quantity_set_name = property_def.Name

                    # Different elements use different quantity sets
                    if "BaseQuantities" in quantity_set_name:
                        for quantity in property_def.Quantities:
                            # Extract volume
                            if (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                element_data["volume"] = quantity.VolumeValue

                            # Extract areas
                            elif quantity.is_a("IfcQuantityArea"):
                                area_type = quantity.Name.lower().replace("area", "")
                                element_data[f"area_{area_type}"] = quantity.AreaValue

    # Rebar information
    rebar_set = psets.get("Rebar Set")
    if rebar_set:
        element_data["has_rebar"] = True
        element_data["rebar_data"] = rebar_set
    else:
        element_data["has_rebar"] = False

    return element_data


def extract_element_materials(element, element_data=None):
    """Extract material information from an element"""
    if element_data is None:
        element_data = {}

    element_data["material_name"] = None
    element_data["material_type"] = None
    element_data["layer_materials"] = []
    element_data["layer_thicknesses"] = []

    if not hasattr(element, "HasAssociations"):
        return element_data

    for association in element.HasAssociations:
        if not association.is_a("IfcRelAssociatesMaterial"):
            continue

        material = association.RelatingMaterial

        # Handle single material
        if material.is_a("IfcMaterial"):
            element_data["material_name"] = material.Name
            element_data["material_type"] = "single"
            break

        # Handle material layer set
        elif material.is_a("IfcMaterialLayerSet") or material.is_a(
            "IfcMaterialLayerSetUsage"
        ):
            element_data["material_type"] = "layered"

            layer_set = (
                material
                if material.is_a("IfcMaterialLayerSet")
                else material.ForLayerSet
            )

            for layer in layer_set.MaterialLayers:
                if layer.Material:  # Some layers might not have a material defined
                    element_data["layer_materials"].append(layer.Material.Name)
                    element_data["layer_thicknesses"].append(layer.LayerThickness)

            # For embedding purposes, use the predominant material
            if element_data["layer_materials"]:
                element_data["material_name"] = max(
                    set(element_data["layer_materials"]),
                    key=element_data["layer_materials"].count,
                )
            break

        # Handle material constituent set
        elif material.is_a("IfcMaterialConstituentSet"):
            element_data["material_type"] = "constituent"

            for constituent in material.MaterialConstituents:
                if constituent.Material:
                    element_data["layer_materials"].append(constituent.Material.Name)

            # For embedding purposes, use the first constituent's material
            if element_data["layer_materials"]:
                element_data["material_name"] = element_data["layer_materials"][0]
            break

    # Special case for windows and doors (using Reference from Psets)
    psets = get_psets(element)
    if element.is_a() == "IfcWindow" and "Pset_WindowCommon" in psets:
        if "Reference" in psets["Pset_WindowCommon"]:
            element_data["material_name"] = psets["Pset_WindowCommon"]["Reference"]
            element_data["material_type"] = "reference"

    elif element.is_a() == "IfcDoor" and "Pset_DoorCommon" in psets:
        if "Reference" in psets["Pset_DoorCommon"]:
            element_data["material_name"] = psets["Pset_DoorCommon"]["Reference"]
            element_data["material_type"] = "reference"

    return element_data


def add_material_to_database(element_data):
    """Add a material to our S3-based CSV and embedding database"""
    global embedding_model, material_embeddings, material_data_df

    # Load the database if not loaded
    if material_data_df is None:
        load_material_database()

    # Make sure embedding model is initialized
    if not embedding_model:
        embedding_model = initialize_embedding_model()
        if not embedding_model:
            return False

    material_name = element_data.get("material_name")
    if not material_name or material_name in MaterialsToIgnore:
        return False

    # Skip if we already have this material in our database
    if material_data_df is not None and not material_data_df.empty:
        if material_name in material_data_df["material_name"].values:
            # logger.debug(f"Material '{material_name}' already in database, skipping")
            return True

    # Create description for this material
    description = create_material_description(element_data)

    try:
        # Generate embedding
        embedding = embedding_model.encode([description])[0]

        if material_name == "Undefined":
            return False
        # Create a record for the CSV
        record = {
            "material_name": material_name,
            "element_type": element_data.get("element_type", "Unknown"),
            "material_type": element_data.get("material_type", "unknown"),
            "volume": element_data.get("volume", None),
            "area": element_data.get("area", None),
            "layer_count": len(element_data.get("layer_materials", [])),
            "material_description": description,
        }

        # Add EC values if available
        if "ec_per_kg" in element_data and "density" in element_data:
            record["ec_per_kg"] = element_data["ec_per_kg"]
            record["density"] = element_data["density"]
        elif "ec_per_m2" in element_data:
            record["ec_per_m2"] = element_data["ec_per_m2"]
        elif material_name in MaterialList:
            prop = MaterialList[material_name]
            if isinstance(prop, list) and len(prop) >= 2:
                record["ec_per_kg"] = prop[0]
                record["density"] = prop[1]
            elif isinstance(prop, (int, float)):
                record["ec_per_m2"] = prop

        # Add to DataFrame
        material_data_df = pd.concat(
            [material_data_df, pd.DataFrame([record])], ignore_index=True
        )

        # Add to embeddings array
        if material_embeddings is None or len(material_embeddings) == 0:
            material_embeddings = np.array([embedding])
        else:
            material_embeddings = np.vstack([material_embeddings, embedding])

        # Save to S3
        # Save DataFrame to CSV in memory
        csv_buffer = io.BytesIO()
        material_data_df.to_csv(csv_buffer, index=False, encoding="utf-8")
        csv_buffer.seek(0)

        # Save numpy array to NPY in memory
        npy_buffer = io.BytesIO()
        np.save(npy_buffer, material_embeddings)
        npy_buffer.seek(0)

        # Upload both to S3
        csv_upload_success = upload_to_s3(csv_buffer, MATERIAL_CSV_S3_PATH, "text/csv")
        npy_upload_success = upload_to_s3(
            npy_buffer, EMBEDDING_NPY_S3_PATH, "application/octet-stream"
        )

        if csv_upload_success and npy_upload_success:
            logger.info(
                f"Added material '{material_name}' to database and uploaded to S3"
            )
            return True
        else:
            logger.error(f"Failed to upload material '{material_name}' to S3")
            return False
    except Exception as e:
        logger.error(f"Error adding material '{material_name}' to database: {e}")
        return False


def find_similar_material(element_data, min_similarity=0.5):
    """Find the most similar material in our database with element_type filtering"""
    global embedding_model, material_embeddings, material_data_df

    # Load database if not loaded
    if material_data_df is None or material_embeddings is None:
        if not load_material_database():
            logger.error("Could not load material database for similarity search")
            return None, 0

    # If database is empty, return None
    if material_data_df.empty or len(material_embeddings) == 0:
        logger.warning("Material database is empty, cannot find similar materials")
        return None, 0

    # Get the element type for filtering
    query_element_type = element_data.get("element_type", None)

    # Filter the database by element_type if specified
    if query_element_type:
        # Get indices of materials with matching element_type
        filtered_indices = material_data_df[
            material_data_df["element_type"] == query_element_type
        ].index.tolist()

        if not filtered_indices:
            logger.warning(
                f"No materials found for element type '{query_element_type}', falling back to full database"
            )
            filtered_indices = material_data_df.index.tolist()
    else:
        # If no element_type specified, use all materials
        filtered_indices = material_data_df.index.tolist()

    # Filter embeddings to only include those matching the element type
    filtered_embeddings = material_embeddings[filtered_indices]

    # Make sure embedding model is initialized
    if not embedding_model:
        embedding_model = initialize_embedding_model()
        if not embedding_model:
            return None, 0

    # Create description and generate embedding for the query
    description = create_material_description(element_data)

    try:
        query_embedding = embedding_model.encode([description])[0]

        # Calculate similarity with filtered embeddings
        similarities = cosine_similarity([query_embedding], filtered_embeddings)[0]

        # Find the most similar material
        best_local_idx = np.argmax(similarities)
        best_score = similarities[best_local_idx]

        if best_score >= min_similarity:
            # Convert local index back to global index
            best_idx = filtered_indices[best_local_idx]
            best_match = material_data_df.iloc[best_idx]["material_name"]
            logger.info(
                f"Found similar material '{best_match}' (score: {best_score:.3f}) with matching element type"
            )
            return best_match, best_score
        else:
            logger.info(
                f"No similar material found above threshold {min_similarity} (best: {best_score:.3f})"
            )
            return None, best_score

    except Exception as e:
        logger.error(f"Error finding similar material: {e}")
        return None, 0


def remove_matched_from_missing(all_missing_materials, all_matched_materials):
    """
    Remove elements that were successfully matched from the missing materials dictionary.

    Parameters:
    all_missing_materials (defaultdict): Dictionary of missing materials by element type
    all_matched_materials (defaultdict): Dictionary of matched materials by element type

    Returns:
    defaultdict: Updated missing materials dictionary with matched elements removed
    """
    from collections import defaultdict

    # Create a copy of the missing materials dictionary to avoid modifying during iteration
    cleaned_missing_materials = defaultdict(list)

    # For each element type in the missing materials dictionary
    for element_type, missing_elements in all_missing_materials.items():
        # Skip if empty list
        if not missing_elements:
            cleaned_missing_materials[element_type] = []
            continue

        # Get the list of matched element IDs for this element type
        matched_ids = []
        if element_type in all_matched_materials:
            matched_ids = [
                item["element_id"] for item in all_matched_materials[element_type]
            ]

        # For each missing element, check if its ID is in the matched list
        for missing_element in missing_elements:
            # Handle both tuple format (id, reason) and dictionary format
            if isinstance(missing_element, tuple):
                element_id = missing_element[0]
                if element_id not in matched_ids:
                    cleaned_missing_materials[element_type].append(missing_element)
            elif isinstance(missing_element, dict) and "element_id" in missing_element:
                element_id = missing_element["element_id"]
                if element_id not in matched_ids:
                    cleaned_missing_materials[element_type].append(missing_element)
            else:
                # If format doesn't match expected, keep it
                cleaned_missing_materials[element_type].append(missing_element)

    return cleaned_missing_materials


def initialize_material_database(ifc_file=None):
    """Initialize material database from existing files and add materials from IFC file"""
    # Load database from files
    success = load_material_database()

    # Initialize embedding model
    if not initialize_embedding_model():
        logger.error("Failed to initialize embedding model")
        return False

    # If an IFC file is provided, extract materials from it
    if ifc_file:
        # Only process IFC file if provided
        element_types = {
            "beams": ifc_file.by_type("IfcBeam"),
            "columns": ifc_file.by_type("IfcColumn"),
            "slabs": ifc_file.by_type("IfcSlab"),
            "walls": ifc_file.by_type("IfcWall"),
            "windows": ifc_file.by_type("IfcWindow"),
            "doors": ifc_file.by_type("IfcDoor"),
            "stairs": ifc_file.by_type("IfcStairFlight"),
            "railings": ifc_file.by_type("IfcRailing"),
            "roofs": ifc_file.by_type("IfcRoof"),
            "members": ifc_file.by_type("IfcMember"),
            "plates": ifc_file.by_type("IfcPlate"),
        }

        materials_found = 0

        for type_name, elements in element_types.items():
            logger.debug(f"Extracting materials from {len(elements)} {type_name}")

            for element in elements:
                # Extract element metadata and materials
                element_data = extract_element_metadata(element)
                element_data = extract_element_materials(element, element_data)

                # Add to database only if it has a valid material that's also in MaterialList
                material_name = element_data.get("material_name")
                if (
                    material_name
                    and material_name in MaterialList
                    and material_name not in MaterialsToIgnore
                ):
                    # Add EC values from MaterialList
                    properties = MaterialList[material_name]
                    if isinstance(properties, (int, float)):
                        element_data["ec_per_m2"] = properties
                    elif isinstance(properties, list) and len(properties) >= 2:
                        element_data["ec_per_kg"] = properties[0]
                        element_data["density"] = properties[1]

                    # Add to database with real element metadata
                    if add_material_to_database(element_data):
                        materials_found += 1

        logger.info(
            f"Found and added {materials_found} materials from IFC file to database"
        )

    logger.info(
        f"Material database initialized with {len(material_data_df) if material_data_df is not None else 0} materials"
    )
    return success


def get_substructure_elements(ifc_file_path):
    """Returns all elements associated with substructure levels (Level 0 or any Basement)."""
    model = ifcopenshell.open(ifc_file_path)

    # Find ALL target storeys
    storeys = model.by_type("IfcBuildingStorey")
    substructure_storeys = [
        s for s in storeys if s.Name == "Level 0" or "Basement" in s.Name
    ]

    if not substructure_storeys:
        logger.warning("No substructure levels (Level 0 or Basement) found.")
        return []

    # Collect elements assigned to ANY substructure storey
    elements = []
    for rel in model.by_type("IfcRelContainedInSpatialStructure"):
        if rel.RelatingStructure in substructure_storeys:
            for elem in rel.RelatedElements:
                elements.append(elem)

    substructure_names = [s.Name for s in substructure_storeys]
    logger.info(
        f"Total elements found in substructure levels {substructure_names}: {len(elements)}"
    )
    logger.info(
        f"Element types found in substructure: {set(e.is_a() for e in elements)}"
    )
    return elements
