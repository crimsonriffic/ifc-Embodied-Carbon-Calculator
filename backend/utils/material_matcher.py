import ifcopenshell
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
def extract_element_data(ifc_path):
    """
    Extract element data, separating layer information and single materials.
    For layers, store just the layer characteristics for matching.
    """
    model = ifcopenshell.open(ifc_path)
    file_name = Path(ifc_path).name
    
    single_material_data = []
    layer_data = []
    
    for element in model.by_type("IfcElement"):
        if hasattr(element, "HasAssociations"):
            for association in element.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    
                    if material.is_a("IfcMaterialLayerSet") or material.is_a("IfcMaterialLayerSetUsage"):
                        # Handle layer sets
                        layer_set = material if material.is_a("IfcMaterialLayerSet") else material.ForLayerSet
                        total_layers = len(layer_set.MaterialLayers)
                        
                        for idx, layer in enumerate(layer_set.MaterialLayers):
                            if layer.Material:
                                layer_data_entry = {
                                    'element_type': element.is_a(),
                                    'position': idx + 1,
                                    'total_layers': total_layers,
                                    'thickness': layer.LayerThickness,
                                    'material_name': layer.Material.Name
                                }
                                
                                # Create layer description for matching
                                layer_data_entry['layer_description'] = (
                                    f"ElementType:{element.is_a()} "
                                    f"Position:{idx+1}of{total_layers} "
                                    f"Thickness:{layer.LayerThickness}"
                                )
                                
                                layer_data.append(layer_data_entry)
                    
                    elif material.is_a("IfcMaterial"):
                        # Handle single materials
                        single_material_data.append({
                            'element_type': element.is_a(),
                            'material_name': material.Name
                        })
    
    return pd.DataFrame(single_material_data), pd.DataFrame(layer_data)

def save_embeddings(ifc_path, model_path='sentence-transformers/msmarco-MiniLM-L-6-v3'):
    """
    Generate and save embeddings for layer characteristics
    """
    model = SentenceTransformer(model_path)
    
    # Extract data
    _, layer_df = extract_element_data(ifc_path)
    
    if not layer_df.empty:
        # Generate embeddings for layer descriptions
        layer_embeddings = model.encode(layer_df['layer_description'].tolist())
        np.save('layer_embeddings.npy', layer_embeddings)
        
        # Save layer data
        layer_df.to_pickle('layer_data.pkl')

def find_similar_layer(element_type, position, total_layers, thickness, model):
    """
    Find similar layers based on position and thickness
    """
    # Create layer description query
    query = f"ElementType:{element_type} Position:{position}of{total_layers} Thickness:{thickness}"
    
    # Get embedding for query
    new_embedding = model.encode([query])[0]
    
    # Load saved data
    layer_embeddings = np.load('layer_embeddings.npy')
    layer_df = pd.read_pickle('layer_data.pkl')
    
    # Calculate similarities
    similarities = cosine_similarity([new_embedding], layer_embeddings)[0]
    
    # Get index of most similar layer
    most_similar_idx = np.argmax(similarities)
    
    # Return the material name and similarity score
    return (
        layer_df.iloc[most_similar_idx]['material_name'],
        similarities[most_similar_idx]
    )

def match_empty_materials(ifc_path, model):
    """
    Match materials for elements layer by layer
    """
    ifc_model = ifcopenshell.open(ifc_path)
    
    for element in ifc_model.by_type("IfcElement"):
        if hasattr(element, "HasAssociations"):
            for association in element.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    
                    if material.is_a("IfcMaterialLayerSet") or material.is_a("IfcMaterialLayerSetUsage"):
                        layer_set = material if material.is_a("IfcMaterialLayerSet") else material.ForLayerSet
                        total_layers = len(layer_set.MaterialLayers)
                        
                        print(f"\nElement ID: {element.id()}")
                        print(f"Element type: {element.is_a()}")
                        print(f"Total layers: {total_layers}")
                        
                        for idx, layer in enumerate(layer_set.MaterialLayers):
                            position = idx + 1
                            thickness = layer.LayerThickness
                            
                            material_name, similarity = find_similar_layer(
                                element.is_a(),
                                position,
                                total_layers,
                                thickness,
                                model
                            )
                            
                            print(f"\nLayer {position}:")
                            print(f"Thickness: {thickness}")
                            print(f"Suggested material: {material_name}")
                            print(f"Similarity score: {similarity:.3f}")
def suggest_materials(ifc_path, model):
    """
    Iterate through IFC elements and suggest materials based on type
    """
    ifc_model = ifcopenshell.open(ifc_path)
    
    for element in ifc_model.by_type("IfcElement"):
        print(f"\nElement ID: {element.id()}")
        print(f"Element type: {element.is_a()}")
        
        if hasattr(element, "HasAssociations"):
            for association in element.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    
                    if material.is_a("IfcMaterialLayerSet") or material.is_a("IfcMaterialLayerSetUsage"):
                        # Handle layered materials
                        layer_set = material if material.is_a("IfcMaterialLayerSet") else material.ForLayerSet
                        total_layers = len(layer_set.MaterialLayers)
                        
                        print(f"Found layered material with {total_layers} layers")
                        
                        for idx, layer in enumerate(layer_set.MaterialLayers):
                            position = idx + 1
                            thickness = layer.LayerThickness
                            
                            # Find similar layer and get material suggestion
                            material_name, similarity = find_similar_layer(
                                element.is_a(),
                                position,
                                total_layers,
                                thickness,
                                model
                            )
                            
                            print(f"\nLayer {position}:")
                            print(f"Thickness: {thickness}")
                            print(f"Suggested material: {material_name}")
                            print(f"Similarity score: {similarity:.3f}")
                    
                    else:
                        # Handle single materials (you can add logic for single material matching here)
                        print("Found single material - implement single material matching if needed")