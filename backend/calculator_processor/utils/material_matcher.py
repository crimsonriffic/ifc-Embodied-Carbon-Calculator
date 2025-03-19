import ifcopenshell
from ifcopenshell.util.element import get_psets
from loguru import logger
import sys
import ifcopenshell.geom
import numpy as np
from numpy import abs as np_abs
import os
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Setup logging
LOGGING_LEVEL = "INFO"
logger.remove()
logger.add(sys.stderr, level=LOGGING_LEVEL)

# Material data and configurations
MaterialList = {
    "Concrete, Cast In Situ": [0.103, 2350],
    "Concrete, Cast-in-Place gray": [0.103, 2350],
    "Concrete, C12/15": [0.097, 2350],
    "Concrete, Grade 40": [0.170, 2400],
    "Concrete, Grade 20": [0.120, 2350],
    "Concrete, Grade 25": [0.13, 2350],
    "Concrete, Grade 20": [0.140, 2350],
    "Concrete, Grade 20": [0.140, 2350],
    "Concrete, C25/30": [0.119, 2350],
    "Concrete, General": [0.112, 2350],
    "Concrete, Precast, Ordinary Portland Cement": [0.148, 2400],
    "Wood_aluminium fixed window 3-glass (SF 2010)": 54.6,  # kgCO2 per 1m^2
    "Wood_aluminium sidehung window 3-glass (SF 2010)": 72.4,
    "M_Window-Casement-Double-Sidelight": 86.830,
    "M_Window-Casement-Double-Sidelight": 86.830,
    "Wooden doors T10-T25 with wooden frame": 30.4,
    "Wooden doors T10-T25 with steel frame": 49.4,
    "Aluminium, General": [13.100, 2700],
    "Tiles, Granite": [0.700, 2650],
    "Plywood": [0.910, 600],
    "Cross Laminated Timber": [-1.310, 500],
}
MaterialsToIgnore = ["Travertine", "<Unnamed>", "Undefined"]

# File paths for material database
MATERIAL_CSV_PATH = "material_database.csv"
EMBEDDING_NPY_PATH = "material_embeddings.npy"

# Globals for material embedding functionality
embedding_model = None
material_embeddings = None  # Will be loaded from NPY file
material_data_df = None  # Will be loaded from CSV file

# ---------------------- Material Embedding Functions ----------------------


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
    """Load material database from CSV and NPY files if they exist"""
    global material_embeddings, material_data_df

    # Initialize with empty dataframe if nothing exists yet
    if material_data_df is None:
        try:
            if os.path.exists(MATERIAL_CSV_PATH):
                material_data_df = pd.read_csv(MATERIAL_CSV_PATH)
                logger.info(
                    f"Loaded {len(material_data_df)} material records from {MATERIAL_CSV_PATH}"
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
                logger.info(f"Created new material database (no existing file found)")
        except Exception as e:
            logger.error(f"Error loading material database CSV: {e}")
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
            if os.path.exists(EMBEDDING_NPY_PATH):
                material_embeddings = np.load(EMBEDDING_NPY_PATH)
                logger.info(
                    f"Loaded {len(material_embeddings)} material embeddings from {EMBEDDING_NPY_PATH}"
                )
            else:
                material_embeddings = np.array([])
                logger.info(f"No existing embeddings found")
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
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
    """Add a material to our CSV and embedding database"""
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

        # Save to files
        material_data_df.to_csv(MATERIAL_CSV_PATH, index=False)
        np.save(EMBEDDING_NPY_PATH, material_embeddings)

        logger.info(f"Added material '{material_name}' to database")
        return True
    except Exception as e:
        logger.error(f"Error adding material '{material_name}' to database: {e}")
        return False


def find_similar_material(element_data, min_similarity=0.7):
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


# ---------------------- Element Calculation Functions ----------------------


def calculate_beams(beams):
    """Calculate embodied carbon for beams, using material matching if needed"""
    total_ec = 0
    quantities = {}
    materials = []

    for beam in beams:
        current_quantity = None  # in volume
        current_material = None

        psets = get_psets(beam)
        rebar_set = psets.get("Rebar Set")
        if rebar_set is None:
            logger.error("Rebar set not found")
        if rebar_set:
            BL = rebar_set.get("BottomLeft")
            BM = rebar_set.get("BottomMiddle")
            BR = rebar_set.get("BottomRight")
            TL = rebar_set.get("TopLeft")
            TM = rebar_set.get("TopMiddle")
            TR = rebar_set.get("TopRight")
            if (
                BL == None
                or BM == None
                or BR == None
                or TL == None
                or TM == None
                or TR == None
            ):
                logger.error("Rebar part not found")
            BLno, BLarea = BL.split("H")
            BMno, BMarea = BM.split("H")
            BRno, BRarea = BR.split("H")
            TLno, TLarea = TL.split("H")
            TMno, TMarea = TM.split("H")
            TRno, TRarea = TR.split("H")

        dimensions = psets.get("Dimensions")
        if dimensions is None:
            logger.error("Dimensions/Diameter not found")
        if dimensions:
            lengthmm = dimensions.get("Length")
            if lengthmm is None:
                logger.error("Length not found")
            else:
                length = lengthmm / 1000

        if rebar_set:
            rebar_vol = (
                (
                    (
                        int(TLno) * 3.14 * ((int(TLarea) / 2000) ** 2)
                        + int(BLno) * 3.14 * ((int(BLarea) / 2000) ** 2)
                    )
                    * (1 / 3)
                    * length
                )
                + (
                    (
                        int(TMno) * 3.14 * ((int(TMarea) / 2000) ** 2)
                        + int(BMno) * 3.14 * ((int(BMarea) / 2000) ** 2)
                    )
                    * (1 / 3)
                    * length
                )
                + (
                    (
                        int(TRno) * 3.14 * ((int(TRarea) / 2000) ** 2)
                        + int(BRno) * 3.14 * ((int(BRarea) / 2000) ** 2)
                    )
                    * (1 / 3)
                    * length
                )
            )

        if hasattr(beam, "IsDefinedBy"):
            for definition in beam.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_BeamBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(
                                    f"Found NetVolume for {beam.Name}: {quantity.VolumeValue}"
                                )
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        # Get material information
        if hasattr(beam, "HasAssociations"):
            for association in beam.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        materials.append(material.Name)
                        current_material = material.Name
                        break

        # Check if material exists in our database
        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )

        # Store this material in our database for future reference
        if current_material and current_material not in MaterialsToIgnore:
            element_data = {
                "element_type": beam.is_a(),
                "element_name": beam.Name if hasattr(beam, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
                "has_rebar": bool(rebar_set),
            }

            # If material has EC data, include it
            if current_material_ec:
                if (
                    isinstance(current_material_ec, list)
                    and len(current_material_ec) >= 2
                ):
                    element_data["ec_per_kg"] = current_material_ec[0]
                    element_data["density"] = current_material_ec[1]
                elif isinstance(current_material_ec, (int, float)):
                    element_data["ec_per_m2"] = current_material_ec

            # Add to database
            add_material_to_database(element_data)

        if current_material_ec is None:
            # Use material matching instead of raising an error
            element_data = {
                "element_type": beam.is_a(),
                "element_name": beam.Name if hasattr(beam, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
                "has_rebar": bool(rebar_set),
            }

            # Try to find a similar material
            similar_material, similarity = find_similar_material(element_data)

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                )
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.error(
                    f"Material '{current_material}' not found and no similar material found. Skipping this beam."
                )
                continue

        if current_quantity is None:
            logger.error(f"No volume found for beam {beam.Name}. Skipping.")
            continue

        material_ec_perkg, material_density = current_material_ec

        if rebar_set == None:
            current_ec = material_ec_perkg * material_density * current_quantity
        else:
            current_ec = (
                material_ec_perkg * material_density * (current_quantity - rebar_vol)
            )
            rebar_ec = rebar_vol * 2.510 * 7850
            logger.debug(f"EC for {beam.Name}'s rebars is {rebar_ec}")
            total_ec += rebar_ec

        logger.debug(f"EC for {beam.Name} is {current_ec}")
        total_ec += current_ec

    logger.debug(f"Total EC for beams is {total_ec}")
    return total_ec


def calculate_columns(columns):
    """Calculate embodied carbon for columns, using material matching if needed"""
    total_ec = 0
    quantities = {}
    materials = []

    for column in columns:
        current_quantity = None
        current_material = None
        rebar = None

        psets = get_psets(column)
        rebar_set = psets.get("Rebar Set")
        if rebar_set is None:
            logger.error("Rebar set not found")
        if rebar_set:
            rebar = rebar_set.get("MainRebar")
            if rebar is None:
                logger.error("Rebar not found")

        dimensions = psets.get("Dimensions")
        if dimensions is None:
            logger.error("Dimensions/Diameter not found")
        if dimensions:
            heightmm = dimensions.get("Height")
            if heightmm is None:
                logger.error("Height not found")
            else:
                height = heightmm / 1000

        if rebar:
            rebar_no, area = rebar.split("H")
            rebar_vol = height * int(rebar_no) * 3.14 * ((int(area) / 2000) ** 2)

        if hasattr(column, "IsDefinedBy"):
            for definition in column.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_ColumnBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(f"Found NetVolume for {column.Name}")
                                quantities[quantity.Name] = quantity.VolumeValue
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        if hasattr(column, "HasAssociations"):
            for association in column.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        materials.append(material.Name)
                        current_material = material.Name
                        break
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage"
                            )
                            materials.append(layer.Material.Name)
                            current_material = layer.Material.Name
                            break
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet"
                            )
                            materials.append(layer.Material.Name)
                            current_material = layer.Material.Name
                            break

        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )

        # Store this material in our database for future reference
        if current_material and current_material not in MaterialsToIgnore:
            element_data = {
                "element_type": column.is_a(),
                "element_name": column.Name if hasattr(column, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
                "has_rebar": bool(rebar_set),
            }

            # If material has EC data, include it
            if current_material_ec:
                if (
                    isinstance(current_material_ec, list)
                    and len(current_material_ec) >= 2
                ):
                    element_data["ec_per_kg"] = current_material_ec[0]
                    element_data["density"] = current_material_ec[1]
                elif isinstance(current_material_ec, (int, float)):
                    element_data["ec_per_m2"] = current_material_ec

            # Add to database
            add_material_to_database(element_data)

        if current_material_ec is None:
            # Use material matching instead of raising an error
            element_data = {
                "element_type": column.is_a(),
                "element_name": column.Name if hasattr(column, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
                "has_rebar": bool(rebar_set),
            }

            # Try to find a similar material
            similar_material, similarity = find_similar_material(element_data)

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                )
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.warning(
                    f"Material '{current_material}' not found and no similar material found. Skipping this column."
                )
                continue

        if current_quantity is None:
            logger.error(f"No volume found for column {column.Name}. Skipping.")
            continue

        material_ec_perkg, material_density = current_material_ec

        if rebar == None:
            current_ec = material_ec_perkg * material_density * current_quantity
        else:
            current_ec = (
                material_ec_perkg * material_density * (current_quantity - rebar_vol)
            )
            rebar_ec = rebar_vol * 2.510 * 7850
            logger.debug(f"EC for {column.Name}'s rebars is {rebar_ec}")
            total_ec += rebar_ec

        logger.debug(f"EC for {column.Name} is {current_ec}")
        total_ec += current_ec

    logger.debug(f"Total EC for columns is {total_ec}")
    return total_ec


def calculate_slabs(slabs, to_ignore=[]):
    """Calculate embodied carbon for slabs, using material matching if needed"""
    total_ec = 0
    quantities = {}

    for slab in slabs:
        layer_thicknesses = {}
        material_layers = []
        current_area = None
        current_ec = None
        current_quantity = None
        current_material = None

        if slab.id() in to_ignore:
            logger.info(f"Skipping slab {slab.id()} as its to be ignored")
            continue

        if hasattr(slab, "IsDefinedBy"):
            for definition in slab.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_SlabBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            # For material constituent
                            if quantity.is_a("IfcPhysicalComplexQuantity"):
                                for sub_quantity in quantity.HasQuantities:
                                    logger.debug(
                                        f"Found subquantity {sub_quantity.Name} for {quantity.Name}: {sub_quantity.LengthValue}"
                                    )
                                    layer_thicknesses[quantity.Name] = (
                                        sub_quantity.LengthValue
                                    )

                            elif quantity.is_a("IfcQuantityArea") and (
                                quantity.Name == "NetArea"
                                or quantity.Name == "GrossArea"
                            ):
                                logger.debug(f"Found NetArea for {slab.Name}")
                                current_area = quantity.AreaValue

                            elif (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(
                                    f"Found NetVolume for {slab.Name}: {quantity.VolumeValue}"
                                )
                                quantities[quantity.Name] = quantity.VolumeValue
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        if hasattr(slab, "HasAssociations"):
            for association in slab.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial

                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        material_layers.append(material.Name)
                        current_material = material.Name

                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialConstituent"
                            )
                            material_layers.append(layer.Material.Name)
                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        material_layers.append(material.Name)
                        current_material = material.Name

                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage"
                            )
                            material_layers.append(layer.Material.Name)
                            current_material = layer.Material.Name

                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet"
                            )
                            material_layers.append(layer.Material.Name)
                            current_material = layer.Material.Name

        if material_layers:
            logger.debug("Processing layered slab")
            # Multi-material slab
            for mat in material_layers:
                mat_ec_data = MaterialList.get(mat)
                thickness = layer_thicknesses.get(mat, None)

                if thickness is None:
                    logger.warning(
                        f"'{mat}' layer thickness not found, skipping EC calculation"
                    )
                    continue
                if thickness <= 0:
                    logger.warning(
                        f"'{mat}' layer thickness <= 0, skipping EC calculation"
                    )
                    continue

                # Store this material in our database for future reference
                if mat and mat not in MaterialsToIgnore:
                    element_data = {
                        "element_type": slab.is_a(),
                        "element_name": slab.Name if hasattr(slab, "Name") else None,
                        "material_name": mat,
                        "material_type": "layered",
                        "volume": current_quantity,
                        "area": current_area,
                        "layer_materials": material_layers,
                        "layer_thicknesses": [thickness],
                    }

                    # If material has EC data, include it
                    if mat_ec_data:
                        if isinstance(mat_ec_data, list) and len(mat_ec_data) >= 2:
                            element_data["ec_per_kg"] = mat_ec_data[0]
                            element_data["density"] = mat_ec_data[1]
                        elif isinstance(mat_ec_data, (int, float)):
                            element_data["ec_per_m2"] = mat_ec_data

                    # Add to database
                    add_material_to_database(element_data)

                if mat_ec_data is None and mat not in MaterialsToIgnore:
                    # Try material matching
                    element_data = {
                        "element_type": slab.is_a(),
                        "element_name": slab.Name if hasattr(slab, "Name") else None,
                        "material_name": mat,
                        "material_type": "layered",
                        "volume": current_quantity,
                        "area": current_area,
                        "layer_materials": material_layers,
                        "layer_thicknesses": [thickness],
                    }

                    similar_material, similarity = find_similar_material(element_data)

                    if similar_material and similar_material in MaterialList:
                        logger.info(
                            f"Material '{mat}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                        )
                        mat = similar_material
                        mat_ec_data = MaterialList.get(mat)
                    else:
                        logger.warning(
                            f"Material '{mat}' not found and no similar material found. Skipping this layer."
                        )
                        continue

                if current_area is None:
                    current_area = get_element_area(slab)
                    logger.warning(f"{mat} area not found, manually calculating.")

                ec_per_kg, density = mat_ec_data
                logger.debug(
                    f"Layer info - thickness: {thickness}, area: {current_area}, ec_per_kg: {ec_per_kg}, density: {density}"
                )
                current_ec = ec_per_kg * density * (thickness / 1000) * current_area
                logger.debug(f"EC for material '{mat}' in {slab.Name} is {current_ec}")
                total_ec += current_ec

        elif current_material:
            # Single-material slab
            current_material_ec = (
                MaterialList.get(current_material, None) if current_material else None
            )

            if current_material_ec is None:
                # Try material matching
                element_data = {
                    "element_type": slab.is_a(),
                    "element_name": slab.Name if hasattr(slab, "Name") else None,
                    "material_name": current_material,
                    "material_type": "single",
                    "volume": current_quantity,
                    "area": current_area,
                }

                similar_material, similarity = find_similar_material(element_data)

                if similar_material and similar_material in MaterialList:
                    logger.info(
                        f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                    )
                    current_material = similar_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.warning(
                        f"Material '{current_material}' not found and no similar material found. Skipping this slab."
                    )
                    continue

            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity
            logger.debug(f"EC for {slab.Name} is {current_ec}")
            total_ec += current_ec

        if current_ec is None:
            logger.warning(
                f"EC calculation for slab failed, attempting manual volume method"
            )
            # Attempts to retrieve the "correct" material from material layer set. Works if able to filter down to one possible material.
            # Calculates EC using EC density * volume method.
            # Calculates volume from ifc geometry.

            MaterialList_filtered = [
                material
                for material in material_layers
                if material not in MaterialsToIgnore
            ]
            if len(MaterialList_filtered) > 1:
                logger.error(
                    f"Unable to isolate to one material from material layer set. Using the first material found, {MaterialList_filtered[0]} for this slab {slab}"
                )

            elif len(MaterialList_filtered) == 0:
                logger.error(f"No material found for this {slab=}")
                continue

            if current_quantity is None:
                current_quantity = get_element_volume(slab)

            current_material = MaterialList_filtered[0]
            logger.debug(f"Using material {current_material}")
            current_material_ec = (
                MaterialList.get(current_material, None) if current_material else None
            )

            if current_material_ec is None:
                # Try material matching
                element_data = {
                    "element_type": slab.is_a(),
                    "element_name": slab.Name if hasattr(slab, "Name") else None,
                    "material_name": current_material,
                    "material_type": "single",
                    "volume": current_quantity,
                }

                similar_material, similarity = find_similar_material(element_data)

                if similar_material and similar_material in MaterialList:
                    logger.info(
                        f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                    )
                    current_material = similar_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.warning(
                        f"Material '{current_material}' not found and no similar material found. Skipping this slab."
                    )
                    continue

            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity
            logger.debug(f"EC for {slab.Name} is {current_ec}")
            total_ec += current_ec

    logger.debug(f"Total EC for slabs is {total_ec}")
    return total_ec


def calculate_walls(walls):
    """Calculate embodied carbon for walls, using material matching if needed"""
    total_ec = 0

    for wall in walls:
        current_volume = None
        current_material = None
        layer_area = None
        layer_thicknesses = {}
        layer_materials = []
        current_ec = None
        current_area = None

        if hasattr(wall, "IsDefinedBy"):
            for definition in wall.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_WallBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            # For material constituent
                            if quantity.Name in MaterialList.keys():
                                for sub_quantity in quantity.HasQuantities:
                                    logger.debug(
                                        f"Found subquantity {sub_quantity.Name} for {quantity.Name}: {sub_quantity.LengthValue}"
                                    )
                                    layer_thicknesses[quantity.Name] = (
                                        sub_quantity.LengthValue
                                    )
                            elif (
                                quantity.is_a("IfcQuantityArea")
                                and quantity.Name == "NetSideArea"
                            ):
                                logger.debug(f"Found NetSideArea for {wall.Name}")
                                current_area = quantity.AreaValue

                            # For single material
                            elif (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(f"Found NetVolume for {wall.Name}")
                                current_volume = quantity.VolumeValue

        if hasattr(wall, "HasAssociations"):
            for association in wall.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        current_material = material.Name
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialConstituent"
                            )
                            layer_materials.append(layer.Material.Name)

        if layer_materials:
            logger.debug("Processing layered wall")
            # Multi-material wall
            for mat in layer_materials:
                mat_ec_data = MaterialList.get(mat)
                thickness = layer_thicknesses.get(mat, 0)

                if thickness <= 0:
                    logger.warning(
                        f"'{mat}' layer thickness <= 0, skipping EC calculation"
                    )
                    continue

                if mat_ec_data is None and mat not in MaterialsToIgnore:
                    # Try material matching
                    element_data = {
                        "element_type": wall.is_a(),
                        "element_name": wall.Name if hasattr(wall, "Name") else None,
                        "material_name": mat,
                        "material_type": "layered",
                        "volume": current_volume,
                        "area": current_area,
                        "layer_materials": layer_materials,
                        "layer_thicknesses": [thickness],
                    }

                    similar_material, similarity = find_similar_material(element_data)

                    if similar_material and similar_material in MaterialList:
                        logger.info(
                            f"Material '{mat}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                        )
                        mat = similar_material
                        mat_ec_data = MaterialList.get(mat)
                    else:
                        logger.warning(
                            f"Material '{mat}' not found and no similar material found. Skipping this layer."
                        )
                        continue

                ec_per_kg, density = mat_ec_data
                logger.debug(
                    f"Layer info - thickness: {thickness}, area: {current_area}, ec_per_kg: {ec_per_kg}, density: {density}"
                )
                current_ec = ec_per_kg * density * (thickness / 1000) * current_area
                logger.debug(f"EC for material '{mat}' in {wall.Name} is {current_ec}")
                total_ec += current_ec

        elif current_material:
            # Single-material wall
            mat_ec_data = MaterialList.get(current_material)

            if mat_ec_data is None:
                # Try material matching
                element_data = {
                    "element_type": wall.is_a(),
                    "element_name": wall.Name if hasattr(wall, "Name") else None,
                    "material_name": current_material,
                    "material_type": "single",
                    "volume": current_volume,
                }

                similar_material, similarity = find_similar_material(element_data)

                if similar_material and similar_material in MaterialList:
                    logger.info(
                        f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                    )
                    current_material = similar_material
                    mat_ec_data = MaterialList.get(current_material)
                else:
                    logger.warning(
                        f"Material '{current_material}' not found and no similar material found. Skipping this wall."
                    )
                    continue

            if current_volume is None:
                logger.error(f"No volume found for wall {wall.Name}. Skipping.")
                continue

            ec_per_kg, density = mat_ec_data
            current_ec = ec_per_kg * density * current_volume
            logger.debug(f"EC for {wall.Name} is {current_ec}")
            total_ec += current_ec

        if current_ec is None:
            # Use material matching with volume estimation
            if not layer_materials:
                logger.warning(
                    f"No material information for wall {wall.Name}. Skipping."
                )
                continue

            # Use the most common material in layers
            if layer_materials:
                current_material = max(set(layer_materials), key=layer_materials.count)

            if current_volume is None:
                current_volume = get_element_volume(wall)
                if current_volume is None:
                    logger.error(
                        f"Failed to calculate volume for wall {wall.Name}. Skipping."
                    )
                    continue

            # Try to find a similar material
            element_data = {
                "element_type": wall.is_a(),
                "element_name": wall.Name if hasattr(wall, "Name") else None,
                "material_name": current_material,
                "material_type": "single" if not layer_materials else "layered",
                "volume": current_volume,
                "layer_materials": layer_materials,
            }

            similar_material, similarity = find_similar_material(element_data)

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Using material '{similar_material}' (similarity: {similarity:.3f}) for wall {wall.Name}"
                )
                current_material = similar_material
                mat_ec_data = MaterialList.get(current_material)

                ec_per_kg, density = mat_ec_data
                current_ec = ec_per_kg * density * current_volume
                logger.debug(f"EC for {wall.Name} is {current_ec}")
                total_ec += current_ec
            else:
                logger.warning(
                    f"No suitable material found for wall {wall.Name}. Skipping."
                )
                continue

    logger.debug(f"Total EC for walls is {total_ec}")
    return total_ec


def calculate_windows(windows):
    """Calculate embodied carbon for windows, using material matching if needed"""
    total_ec = 0
    quantities = {}
    materials = []

    for window in windows:
        current_quantity = None
        current_material = None

        if hasattr(window, "IsDefinedBy"):
            for definition in window.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_WindowBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityArea")
                                and quantity.Name == "Area"
                            ):
                                logger.debug(f"Found Area for {window.Name}")
                                quantities[quantity.Name] = quantity.AreaValue
                                current_quantity = quantity.AreaValue
                                break
                        if current_quantity is not None:
                            break

        psets = get_psets(window)
        if "Pset_WindowCommon" in psets and "Reference" in psets["Pset_WindowCommon"]:
            current_material = psets["Pset_WindowCommon"]["Reference"]

        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )

        if current_material_ec is None:
            # Try material matching for windows
            element_data = {
                "element_type": window.is_a(),
                "element_name": window.Name if hasattr(window, "Name") else None,
                "material_name": current_material,
                "material_type": "reference",
                "area": current_quantity,
            }

            similar_material, similarity = find_similar_material(element_data)

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                )
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.warning(
                    f"Material '{current_material}' not found and no similar material found. Skipping this window."
                )
                continue

        if current_quantity is None:
            logger.error(f"No area found for window {window.Name}. Skipping.")
            continue

        # Window EC is per area (m²)
        if isinstance(current_material_ec, (int, float)):
            material_ec_per_m2 = current_material_ec
            current_ec = material_ec_per_m2 * current_quantity
        else:
            # Handle case where material EC is in standard [EC per kg, density] format
            material_ec_perkg, material_density = current_material_ec
            # Assume a standard thickness for windows (e.g., 25mm = 0.025m)
            standard_thickness = 0.025
            current_ec = (
                material_ec_perkg
                * material_density
                * standard_thickness
                * current_quantity
            )

        logger.debug(f"EC for {window.Name} is {current_ec}")
        total_ec += current_ec

    logger.debug(f"Total EC for windows is {total_ec}")
    return total_ec


def calculate_doors(doors):
    """Calculate embodied carbon for doors, using material matching if needed"""
    total_ec = 0
    quantities = {}
    materials = []

    for door in doors:
        current_quantity = None
        current_material = None

        if hasattr(door, "IsDefinedBy"):
            for definition in door.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_DoorBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityArea")
                                and quantity.Name == "Area"
                            ):
                                logger.debug(f"Found Area for {door.Name}")
                                quantities[quantity.Name] = quantity.AreaValue
                                current_quantity = quantity.AreaValue
                                break
                        if current_quantity is not None:
                            break

        psets = get_psets(door)
        if "Pset_DoorCommon" in psets and "Reference" in psets["Pset_DoorCommon"]:
            current_material = psets["Pset_DoorCommon"]["Reference"]

        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )

        if current_material_ec is None:
            # Try material matching for doors
            element_data = {
                "element_type": door.is_a(),
                "element_name": door.Name if hasattr(door, "Name") else None,
                "material_name": current_material,
                "material_type": "reference",
                "area": current_quantity,
            }

            similar_material, similarity = find_similar_material(element_data)

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                )
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.warning(
                    f"Material '{current_material}' not found and no similar material found. Skipping this door."
                )
                continue

        if current_quantity is None:
            logger.error(f"No area found for door {door.Name}. Skipping.")
            continue

        # Door EC is per area (m²)
        if isinstance(current_material_ec, (int, float)):
            material_ec_per_m2 = current_material_ec
            current_ec = material_ec_per_m2 * current_quantity
        else:
            # Handle case where material EC is in standard [EC per kg, density] format
            material_ec_perkg, material_density = current_material_ec
            # Assume a standard thickness for doors (e.g., 40mm = 0.04m)
            standard_thickness = 0.04
            current_ec = (
                material_ec_perkg
                * material_density
                * standard_thickness
                * current_quantity
            )

        logger.debug(f"EC for {door.Name} is {current_ec}")
        total_ec += current_ec

    logger.debug(f"Total EC for doors is {total_ec}")
    return total_ec


# ---------------------- Helper Functions ----------------------


def get_element_area(element):
    """Calculate the area of an element from its geometry"""
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
        logger.error(f"Error processing geometry: {e}")
        return None


def get_element_volume(element):
    """Calculate the volume of an element from its geometry"""
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
        logger.error(f"Error processing geometry: {e}")
        return None
