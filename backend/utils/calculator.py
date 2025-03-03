import ifcopenshell
from ifcopenshell.util.element import get_psets
from loguru import logger
import sys
import ifcopenshell
import ifcopenshell.geom
import numpy as np
import os 
from . import calculator_utils 

MaterialList = calculator_utils.MaterialList
MaterialsToIgnore = calculator_utils.MaterialsToIgnore
embedding_model = calculator_utils.embedding_model
material_embeddings = calculator_utils.material_embeddings  
material_data_df = calculator_utils.material_data_df

MATERIAL_REAPLCE = False 

def calculate_beams(beams):
    """Calculate embodied carbon for beams, using material matching if needed"""
    total_ec = 0
    quantities = {}
    materials = []
    
    for beam in beams:
        current_quantity = None # in volume
        current_material = None

        psets = get_psets(beam)
        rebar_set = psets.get('Rebar Set')
        if rebar_set is None:
            logger.error('Rebar set not found')
        if rebar_set:
            BL = rebar_set.get('BottomLeft')
            BM = rebar_set.get('BottomMiddle')
            BR = rebar_set.get('BottomRight')
            TL = rebar_set.get('TopLeft')
            TM = rebar_set.get('TopMiddle')
            TR = rebar_set.get('TopRight')
            if BL == None or BM == None or BR == None or TL == None or TM == None or TR == None:
                logger.error('Rebar part not found')
            BLno, BLarea = BL.split("H")
            BMno, BMarea = BM.split("H")
            BRno, BRarea = BR.split("H")
            TLno, TLarea = TL.split("H")
            TMno, TMarea = TM.split("H")
            TRno, TRarea = TR.split("H")
        
        dimensions = psets.get('Dimensions')
        if dimensions is None:
            logger.error('Dimensions/Diameter not found')
        if dimensions:
            lengthmm = dimensions.get('Length')
            if lengthmm is None:
                logger.error("Length not found")
            else:
                length = lengthmm / 1000
        
        if rebar_set:
            rebar_vol = ((int(TLno) * 3.14 * ((int(TLarea)/2000) ** 2) + int(BLno) * 3.14 * ((int(BLarea)/2000) ** 2)) * (1/3) * length)\
                    + ((int(TMno) * 3.14 * ((int(TMarea)/2000) ** 2) + int(BMno) * 3.14 * ((int(BMarea)/2000) ** 2)) * (1/3) * length)\
                    + ((int(TRno) * 3.14 * ((int(TRarea)/2000) ** 2) + int(BRno) * 3.14 * ((int(BRarea)/2000) ** 2)) * (1/3) * length)
        
        if hasattr(beam, "IsDefinedBy"):
            for definition in beam.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_BeamBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume for {beam.Name}: {quantity.VolumeValue}')
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
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        materials.append(material.Name)
                        current_material = material.Name
                        break

        # Check if material exists in our database
        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        # Store this material in our database for future reference
        if current_material and current_material not in MaterialsToIgnore:
            element_data = {
                'element_type': beam.is_a(),
                'element_name': beam.Name if hasattr(beam, 'Name') else None,
                'material_name': current_material,
                'material_type': 'single',
                'volume': current_quantity,
                'has_rebar': bool(rebar_set)
            }
            
            # If material has EC data, include it
            if current_material_ec:
                if isinstance(current_material_ec, list) and len(current_material_ec) >= 2:
                    element_data['ec_per_kg'] = current_material_ec[0]
                    element_data['density'] = current_material_ec[1]
                elif isinstance(current_material_ec, (int, float)):
                    element_data['ec_per_m2'] = current_material_ec
            
            # Add to database
            calculator_utils.add_material_to_database(element_data)

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Use material matching instead of raising an error
            element_data = {
                'element_type': beam.is_a(),
                'element_name': beam.Name if hasattr(beam, 'Name') else None,
                'material_name': current_material,
                'material_type': 'single',
                'volume': current_quantity,
                'has_rebar': bool(rebar_set)
            }
            
            # Try to find a similar material
            similar_material, similarity = calculator_utils.find_similar_material(element_data)
            
            if similar_material and similar_material in MaterialList:
                logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.error(f"Material '{current_material}' not found and no similar material found. Skipping this beam.")
                continue
        
        if current_quantity is None:
            logger.error(f"No volume found for beam {beam.Name}. Skipping.")
            continue
            
        material_ec_perkg, material_density = current_material_ec
        
        if rebar_set == None:
            current_ec = material_ec_perkg * material_density * current_quantity
        else:
            current_ec = material_ec_perkg * material_density * (current_quantity - rebar_vol)
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
        rebar_set = psets.get('Rebar Set')
        if rebar_set is None:
            logger.error('Rebar set not found')
        if rebar_set:
            rebar = rebar_set.get('MainRebar')
            if rebar is None:
                logger.error('Rebar not found')
        
        dimensions = psets.get('Dimensions')
        if dimensions is None:
            logger.error('Dimensions/Diameter not found')
        if dimensions:
            heightmm = dimensions.get('Height')
            if heightmm is None:
                logger.error("Height not found")
            else:
                height = heightmm / 1000
        
        if rebar:
            rebar_no, area = rebar.split("H")
            rebar_vol = height * int(rebar_no) * 3.14 * ((int(area)/2000) **2)

        if hasattr(column, "IsDefinedBy"):
            for definition in column.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_ColumnBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume for {column.Name}')
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
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        materials.append(material.Name)
                        current_material = material.Name
                        break
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                            materials.append(layer.Material.Name)
                            current_material = layer.Material.Name
                            break
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
                            materials.append(layer.Material.Name)
                            current_material = layer.Material.Name
                            break

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        # Store this material in our database for future reference
        if current_material and current_material not in MaterialsToIgnore:
            element_data = {
                'element_type': column.is_a(),
                'element_name': column.Name if hasattr(column, 'Name') else None,
                'material_name': current_material,
                'material_type': 'single',
                'volume': current_quantity,
                'has_rebar': bool(rebar_set)
            }
            
            # If material has EC data, include it
            if current_material_ec:
                if isinstance(current_material_ec, list) and len(current_material_ec) >= 2:
                    element_data['ec_per_kg'] = current_material_ec[0]
                    element_data['density'] = current_material_ec[1]
                elif isinstance(current_material_ec, (int, float)):
                    element_data['ec_per_m2'] = current_material_ec
            
            # Add to database
            calculator_utils.add_material_to_database(element_data)

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Use material matching instead of raising an error
            element_data = {
                'element_type': column.is_a(),
                'element_name': column.Name if hasattr(column, 'Name') else None,
                'material_name': current_material,
                'material_type': 'single',
                'volume': current_quantity,
                'has_rebar': bool(rebar_set)
            }
            
            # Try to find a similar material
            similar_material, similarity = calculator_utils.find_similar_material(element_data)
            
            if similar_material and similar_material in MaterialList:
                logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.warning(f"Material '{current_material}' not found and no similar material found. Skipping this column.")
                continue
        
        if current_quantity is None:
            logger.error(f"No volume found for column {column.Name}. Skipping.")
            continue
            
        material_ec_perkg, material_density = current_material_ec
        
        if rebar == None:
            current_ec = material_ec_perkg * material_density * current_quantity
        else:
            current_ec = material_ec_perkg * material_density * (current_quantity - rebar_vol)
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
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_SlabBaseQuantities':
                        for quantity in property_def.Quantities:
                            # For material constituent
                            if quantity.is_a("IfcPhysicalComplexQuantity"):
                                for sub_quantity in quantity.HasQuantities:
                                    logger.debug(f'Found subquantity {sub_quantity.Name} for {quantity.Name}: {sub_quantity.LengthValue}')
                                    layer_thicknesses[quantity.Name] = sub_quantity.LengthValue

                            elif (quantity.is_a('IfcQuantityArea') and (quantity.Name == 'NetArea' or quantity.Name == 'GrossArea')) :
                                logger.debug(f'Found NetArea for {slab.Name}: {quantity.AreaValue}')
                                current_area = quantity.AreaValue

                            elif quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume for {slab.Name}: {quantity.VolumeValue}')
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
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        material_layers.append(material.Name)
                        current_material = material.Name
                        
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialConstituent")
                            material_layers.append(layer.Material.Name)
                    if material.is_a("IfcMaterial"):
                            logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                            material_layers.append(material.Name)
                            current_material = material.Name
                            
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                            material_layers.append(layer.Material.Name)
                            current_material = layer.Material.Name
                            
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
                            material_layers.append(layer.Material.Name)
                            current_material = layer.Material.Name
                            
        if material_layers:
            logger.debug("Processing layered slab")
            # Multi-material slab
            for mat in material_layers:
                mat_ec_data = MaterialList.get(mat)
                thickness = layer_thicknesses.get(mat, None)
                
                if thickness is None:
                    logger.warning(f"'{mat}' layer thickness not found, skipping EC calculation")
                    continue
                if thickness <= 0:
                    logger.warning(f"'{mat}' layer thickness <= 0, skipping EC calculation")
                    continue
                    
                # Store this material in our database for future reference
                if mat and mat not in MaterialsToIgnore:
                    element_data = {
                        'element_type': slab.is_a(),
                        'element_name': slab.Name if hasattr(slab, 'Name') else None,
                        'material_name': mat,
                        'material_type': 'layered',
                        'volume': current_quantity,
                        'area': current_area,
                        'layer_materials': material_layers,
                        'layer_thicknesses': [thickness]
                    }
                    
                    # If material has EC data, include it
                    if mat_ec_data:
                        if isinstance(mat_ec_data, list) and len(mat_ec_data) >= 2:
                            element_data['ec_per_kg'] = mat_ec_data[0]
                            element_data['density'] = mat_ec_data[1]
                        elif isinstance(mat_ec_data, (int, float)):
                            element_data['ec_per_m2'] = mat_ec_data
                    
                    # Add to database
                    calculator_utils.add_material_to_database(element_data)
                
                if mat_ec_data is None and mat not in MaterialsToIgnore:
                    # Try material matching
                    element_data = {
                        'element_type': slab.is_a(),
                        'element_name': slab.Name if hasattr(slab, 'Name') else None,
                        'material_name': mat,
                        'material_type': 'layered',
                        'volume': current_quantity,
                        'area': current_area,
                        'layer_materials': material_layers,
                        'layer_thicknesses': [thickness]
                    }
                    
                    similar_material, similarity = calculator_utils.find_similar_material(element_data)
                    
                    if similar_material and similar_material in MaterialList:
                        logger.info(f"Material '{mat}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                        mat = similar_material
                        mat_ec_data = MaterialList.get(mat)
                    else:
                        logger.warning(f"Material '{mat}' not found and no similar material found. Skipping this layer.")
                        continue

                if current_area is None:
                    current_area = calculator_utils.get_element_area(slab)
                    logger.warning(f"{mat} area not found, manually calculating.")

                ec_per_kg, density = mat_ec_data
                logger.debug(f"Layer info - thickness: {thickness}, area: {current_area}, ec_per_kg: {ec_per_kg}, density: {density}")
                current_ec = ec_per_kg * density * (thickness/1000) * current_area
                logger.debug(f"EC for material '{mat}' in {slab.Name} is {current_ec}")
                total_ec += current_ec

        elif current_material:
            # Single-material slab
            current_material_ec = MaterialList.get(current_material, None) if current_material else None

            if current_material_ec is None and MATERIAL_REAPLCE :
                # Try material matching
                element_data = {
                    'element_type': slab.is_a(),
                    'element_name': slab.Name if hasattr(slab, 'Name') else None,
                    'material_name': current_material,
                    'material_type': 'single',
                    'volume': current_quantity,
                    'area': current_area
                }
                
                similar_material, similarity = calculator_utils.find_similar_material(element_data)
                
                if similar_material and similar_material in MaterialList:
                    logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                    current_material = similar_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.warning(f"Material '{current_material}' not found and no similar material found. Skipping this slab.")
                    continue
                    
            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity
            logger.debug(f"EC for {slab.Name} is {current_ec}")
            total_ec += current_ec
        
        if current_ec is None:
            logger.warning(f"EC calculation for slab failed, attempting manual volume method")
            # Attempts to retrieve the "correct" material from material layer set. Works if able to filter down to one possible material.
            # Calculates EC using EC density * volume method.
            # Calculates volume from ifc geometry.
            
            MaterialList_filtered = [material for material in material_layers if material not in MaterialsToIgnore]
            if len(MaterialList_filtered) > 1:
                logger.warning(f"Unable to isolate to one material from material layer set. Using the first material found, {MaterialList_filtered[0]} for this slab {slab}") 

            elif len(MaterialList_filtered) == 0 :
                logger.error(f"No material found for this {slab=}")
                continue
                
            if current_quantity is None:
                current_quantity = calculator_utils.get_element_volume(slab)
                
            current_material = MaterialList_filtered[0]
            logger.debug(f"Using material {current_material}")
            current_material_ec = MaterialList.get(current_material, None) if current_material else None
            
            if current_material_ec is None and MATERIAL_REAPLCE:
                # Try material matching
                element_data = {
                    'element_type': slab.is_a(),
                    'element_name': slab.Name if hasattr(slab, 'Name') else None,
                    'material_name': current_material,
                    'material_type': 'single',
                    'volume': current_quantity
                }
                
                similar_material, similarity = calculator_utils.find_similar_material(element_data)
                
                if similar_material and similar_material in MaterialList:
                    logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                    current_material = similar_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.warning(f"Material '{current_material}' not found and no similar material found. Skipping this slab.")
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
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_WallBaseQuantities':
                        for quantity in property_def.Quantities:
                            # For material constituent
                            if quantity.Name in MaterialList.keys(): 
                                for sub_quantity in quantity.HasQuantities:
                                    logger.debug(f'Found subquantity {sub_quantity.Name} for {quantity.Name}: {sub_quantity.LengthValue}')
                                    layer_thicknesses[quantity.Name] = sub_quantity.LengthValue
                            elif quantity.is_a('IfcQuantityArea') and quantity.Name == 'NetSideArea':
                                logger.debug(f'Found NetSideArea for {wall.Name}: {quantity.AreaValue}')
                                current_area = quantity.AreaValue
                                                                
                            # For single material
                            elif quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume for {wall.Name}: {quantity.VolumeValue}')
                                #quantities[quantity.Name] = quantity.VolumeValue
                                current_volume = quantity.VolumeValue                            

        if hasattr(wall, "HasAssociations"):
            for association in wall.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        current_material = material.Name
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialConstituent")
                            layer_materials.append(layer.Material.Name)

        if layer_materials:
            logger.debug("Processing layered wall")
            # Multi-material wall
            for mat in layer_materials:
                mat_ec_data = MaterialList.get(mat)
                thickness = layer_thicknesses.get(mat, 0)

                if thickness <= 0:
                    logger.warning(f"'{mat}' layer thickness <= 0, skipping EC calculation")
                    continue
                
                if mat_ec_data is None and mat not in MaterialsToIgnore:
                    # Try material matching
                    element_data = {
                        'element_type': wall.is_a(),
                        'element_name': wall.Name if hasattr(wall, 'Name') else None,
                        'material_name': mat,
                        'material_type': 'layered',
                        'volume': current_volume,
                        'area': current_area,
                        'layer_materials': layer_materials,
                        'layer_thicknesses': [thickness]
                    }
                    
                    similar_material, similarity = calculator_utils.find_similar_material(element_data)
                    
                    if similar_material and similar_material in MaterialList:
                        logger.info(f"Material '{mat}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                        mat = similar_material
                        mat_ec_data = MaterialList.get(mat)
                    else:
                        logger.warning(f"Material '{mat}' not found and no similar material found. Skipping this layer.")
                        continue
                
                ec_per_kg, density = mat_ec_data
                logger.debug(f"Layer info - thickness: {thickness}, area: {current_area}, ec_per_kg: {ec_per_kg}, density: {density}")
                current_ec = ec_per_kg * density * (thickness/1000) * current_area
                logger.debug(f"EC for material '{mat}' in {wall.Name} is {current_ec}")
                total_ec += current_ec
                
        elif current_material:
            # Single-material wall
            mat_ec_data = MaterialList.get(current_material)
            
            if mat_ec_data is None:
                # Try material matching
                element_data = {
                    'element_type': wall.is_a(),
                    'element_name': wall.Name if hasattr(wall, 'Name') else None,
                    'material_name': current_material,
                    'material_type': 'single',
                    'volume': current_volume
                }
                
                similar_material, similarity = calculator_utils.find_similar_material(element_data)
                
                if similar_material and similar_material in MaterialList:
                    logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                    current_material = similar_material
                    mat_ec_data = MaterialList.get(current_material)
                else:
                    logger.warning(f"Material '{current_material}' not found and no similar material found. Skipping this wall.")
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
                logger.warning(f"No material information for wall {wall.Name}. Skipping.")
                continue
                
            # Use the most common material in layers
            if layer_materials:
                current_material = max(set(layer_materials), key=layer_materials.count)
                
            if current_volume is None:
                current_volume = calculator_utils.get_element_volume(wall)
                if current_volume is None:
                    logger.error(f"Failed to calculate volume for wall {wall.Name}. Skipping.")
                    continue
            
            # Try to find a similar material
            element_data = {
                'element_type': wall.is_a(),
                'element_name': wall.Name if hasattr(wall, 'Name') else None,
                'material_name': current_material,
                'material_type': 'single' if not layer_materials else 'layered',
                'volume': current_volume,
                'layer_materials': layer_materials
            }
            
            similar_material, similarity = calculator_utils.find_similar_material(element_data)
            
            if similar_material and similar_material in MaterialList:
                logger.info(f"Using material '{similar_material}' (similarity: {similarity:.3f}) for wall {wall.Name}")
                current_material = similar_material
                mat_ec_data = MaterialList.get(current_material)
                
                ec_per_kg, density = mat_ec_data
                current_ec = ec_per_kg * density * current_volume
                logger.debug(f"EC for {wall.Name} is {current_ec}")
                total_ec += current_ec
            else:
                logger.warning(f"No suitable material found for wall {wall.Name}. Skipping.")
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
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_WindowBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityArea') and quantity.Name == 'Area':
                                logger.debug(f'Found Area for {window.Name}: {quantity.AreaValue}')
                                quantities[quantity.Name] = quantity.AreaValue
                                current_quantity = quantity.AreaValue
                                break
                        if current_quantity is not None:
                            break

        psets = get_psets(window)
        if 'Pset_WindowCommon' in psets and 'Reference' in psets['Pset_WindowCommon']:
            current_material = psets['Pset_WindowCommon']['Reference']

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Try material matching for windows
            element_data = {
                'element_type': window.is_a(),
                'element_name': window.Name if hasattr(window, 'Name') else None,
                'material_name': current_material,
                'material_type': 'reference',
                'area': current_quantity
            }
            
            similar_material, similarity = calculator_utils.find_similar_material(element_data)
            
            if similar_material and similar_material in MaterialList:
                logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.warning(f"Material '{current_material}' not found and no similar material found. Skipping this window.")
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
            current_ec = material_ec_perkg * material_density * standard_thickness * current_quantity

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
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_DoorBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityArea') and quantity.Name == 'Area':
                                logger.debug(f'Found Area for {door.Name}: {quantity.AreaValue}')
                                quantities[quantity.Name] = quantity.AreaValue
                                current_quantity = quantity.AreaValue
                                break
                        if current_quantity is not None:
                            break

        psets = get_psets(door)
        if 'Pset_DoorCommon' in psets and 'Reference' in psets['Pset_DoorCommon']:
            current_material = psets['Pset_DoorCommon']['Reference']

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Try material matching for doors
            element_data = {
                'element_type': door.is_a(),
                'element_name': door.Name if hasattr(door, 'Name') else None,
                'material_name': current_material,
                'material_type': 'reference',
                'area': current_quantity
            }
            
            similar_material, similarity = calculator_utils.find_similar_material(element_data)
            
            if similar_material and similar_material in MaterialList:
                logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.warning(f"Material '{current_material}' not found and no similar material found. Skipping this door.")
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
            current_ec = material_ec_perkg * material_density * standard_thickness * current_quantity

        logger.debug(f"EC for {door.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for doors is {total_ec}")
    return total_ec     
    
def calculate_roofs(roofs):
    """Calculate embodied carbon for roofs, using material matching if needed"""
    total_ec = 0
    quantities = {}
    materials = []

    for roof in roofs:
        slabs = []
        roof_ec = 0
        current_ec = 0
        if hasattr(roof, "IsDecomposedBy"):
            for rel in roof.IsDecomposedBy:
                if rel.is_a("IfcRelAggregates"):
                    for slab in rel.RelatedObjects:
                        if slab.is_a("IfcSlab"):
                            logger.debug(f"Found Slab: {slab.Name}")
                            slabs.append(slab)
        
        for slab in slabs:
            layer_thicknesses = {}
            material_layers = []
            current_area = None
            current_ec = None
            current_quantity = None
            current_material = None
            
            if hasattr(slab, "IsDefinedBy"):
                for definition in slab.IsDefinedBy:
                    if definition.is_a('IfcRelDefinesByProperties'):
                        property_def = definition.RelatingPropertyDefinition
                        if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_SlabBaseQuantities':
                            for quantity in property_def.Quantities:
                                # For material constituent
                                if quantity.is_a("IfcPhysicalComplexQuantity"):
                                    for sub_quantity in quantity.HasQuantities:
                                        logger.debug(f'Found subquantity {sub_quantity.Name} for {quantity.Name}: {sub_quantity.LengthValue}')
                                        layer_thicknesses[quantity.Name] = sub_quantity.LengthValue
                                elif quantity.is_a('IfcQuantityArea') and (quantity.Name == 'NetSideArea' or quantity.Name == 'GrossArea'):
                                    logger.debug(f'Found Area for {slab.Name}: {quantity.AreaValue}')
                                    current_area = quantity.AreaValue
                                                                    
                                # For single material
                                elif quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                    logger.debug(f'Found NetVolume for {slab.Name}: {quantity.VolumeValue / len(slabs)}')
                                    current_quantity = quantity.VolumeValue / len(slabs)                           

            if hasattr(slab, "HasAssociations"):
                for association in slab.HasAssociations:
                    if association.is_a("IfcRelAssociatesMaterial"):
                        material = association.RelatingMaterial
                        if material.is_a("IfcMaterial"):
                            logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                            current_material = material.Name
                        elif material.is_a("IfcMaterialConstituentSet"):
                            for layer in material.MaterialConstituents:
                                logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialConstituent")
                                material_layers.append(layer.Material.Name)
                        elif material.is_a("IfcMaterialLayerSetUsage"):
                            for layer in material.ForLayerSet.MaterialLayers:
                                logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                                material_layers.append(layer.Material.Name)
                        elif material.is_a("IfcMaterialLayerSet"):
                            for layer in material.MaterialLayers:
                                logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
                                material_layers.append(layer.Material.Name)

            if material_layers:
                logger.debug("Processing layered slab in roof")
                # Multi-material slab
                for mat in material_layers:
                    mat_ec_data = MaterialList.get(mat)
                    thickness = layer_thicknesses.get(mat, None)
                    
                    if thickness is None:
                        logger.warning(f"'{mat}' layer thickness not found, skipping EC calculation")
                        continue
                    if thickness <= 0:
                        logger.warning(f"'{mat}' layer thickness <= 0, skipping EC calculation")
                        continue
                        
                    # Store this material in our database for future reference
                    if mat and mat not in MaterialsToIgnore:
                        element_data = {
                            'element_type': slab.is_a(),
                            'element_name': slab.Name if hasattr(slab, 'Name') else None,
                            'material_name': mat,
                            'material_type': 'layered',
                            'volume': current_quantity,
                            'area': current_area,
                            'layer_materials': material_layers,
                            'layer_thicknesses': [thickness]
                        }
                        
                        # If material has EC data, include it
                        if mat_ec_data:
                            if isinstance(mat_ec_data, list) and len(mat_ec_data) >= 2:
                                element_data['ec_per_kg'] = mat_ec_data[0]
                                element_data['density'] = mat_ec_data[1]
                            elif isinstance(mat_ec_data, (int, float)):
                                element_data['ec_per_m2'] = mat_ec_data
                        
                        # Add to database
                        calculator_utils.add_material_to_database(element_data)
                    
                    if mat_ec_data is None and mat not in MaterialsToIgnore:
                        # Try material matching
                        element_data = {
                            'element_type': slab.is_a(),
                            'element_name': slab.Name if hasattr(slab, 'Name') else None,
                            'material_name': mat,
                            'material_type': 'layered',
                            'volume': current_quantity,
                            'area': current_area,
                            'layer_materials': material_layers,
                            'layer_thicknesses': [thickness]
                        }
                        
                        similar_material, similarity = calculator_utils.find_similar_material(element_data)
                        
                        if similar_material and similar_material in MaterialList:
                            logger.info(f"Material '{mat}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                            mat = similar_material
                            mat_ec_data = MaterialList.get(mat)
                        else:
                            logger.warning(f"Material '{mat}' not found and no similar material found. Skipping this layer.")
                            continue

                    if current_area is None:
                        current_area = calculator_utils.get_element_area(slab)
                        logger.warning(f"{mat} area not found, manually calculating.")

                    ec_per_kg, density = mat_ec_data
                    logger.debug(f"Layer info - thickness: {thickness}, area: {current_area}, ec_per_kg: {ec_per_kg}, density: {density}")
                    current_ec = ec_per_kg * density * (thickness/1000) * current_area
                    logger.debug(f"EC for material '{mat}' in {slab.Name} is {current_ec}")
                    roof_ec += current_ec

            elif current_material:
                # Single-material slab
                current_material_ec = MaterialList.get(current_material, None) if current_material else None

                if current_material_ec is None and MATERIAL_REAPLCE:
                    # Try material matching
                    element_data = {
                        'element_type': slab.is_a(),
                        'element_name': slab.Name if hasattr(slab, 'Name') else None,
                        'material_name': current_material,
                        'material_type': 'single',
                        'volume': current_quantity,
                        'area': current_area
                    }
                    
                    similar_material, similarity = calculator_utils.find_similar_material(element_data)
                    
                    if similar_material and similar_material in MaterialList:
                        logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                        current_material = similar_material
                        current_material_ec = MaterialList.get(current_material)
                    else:
                        logger.warning(f"Material '{current_material}' not found and no similar material found. Skipping this roof slab.")
                        continue
                        
                material_ec_perkg, material_density = current_material_ec
                current_ec = material_ec_perkg * material_density * current_quantity
                logger.debug(f"EC for {slab.Name} is {current_ec}")
                roof_ec += current_ec
            
            if current_ec is None:
                logger.warning(f"EC calculation for slab in roof failed, attempting manual volume method")
                # Attempts to retrieve the "correct" material from material layer set. Works if able to filter down to one possible material.
                # Calculates EC using EC density * volume method.
                # Calculates volume from ifc geometry.
                
                MaterialList_filtered = [material for material in material_layers if material not in MaterialsToIgnore]
                if len(MaterialList_filtered) > 1:
                    logger.error(f"Unable to isolate to one material from material layer set. Using the first material found, {MaterialList_filtered[0]} for this slab {slab}")
                elif len(MaterialList_filtered) == 0:
                    logger.error(f"No material found for this {slab=}")
                    continue
                
                if current_quantity is None:
                    current_quantity = calculator_utils.get_element_volume(slab)
                    
                current_material = MaterialList_filtered[0]
                logger.debug(f"Using material {current_material}")
                current_material_ec = MaterialList.get(current_material, None) if current_material else None
                
                if current_material_ec is None and MATERIAL_REAPLCE:
                    # Try material matching
                    element_data = {
                        'element_type': slab.is_a(),
                        'element_name': slab.Name if hasattr(slab, 'Name') else None,
                        'material_name': current_material,
                        'material_type': 'single',
                        'volume': current_quantity
                    }
                    
                    similar_material, similarity = calculator_utils.find_similar_material(element_data)
                    
                    if similar_material and similar_material in MaterialList:
                        logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                        current_material = similar_material
                        current_material_ec = MaterialList.get(current_material)
                    else:
                        logger.warning(f"Material '{current_material}' not found and no similar material found. Skipping this roof slab.")
                        continue
                
                material_ec_perkg, material_density = current_material_ec
                current_ec = material_ec_perkg * material_density * current_quantity
                logger.debug(f"EC for {slab.Name} is {current_ec}")
                roof_ec += current_ec

        logger.debug(f"EC for {roof.Name} is {roof_ec}")
        total_ec += roof_ec
    
    logger.debug(f"Total EC for roofs is {total_ec}")
    return total_ec


def calculate_stairs(stairs):
    """Calculate embodied carbon for stairs, using material matching if needed"""
    total_ec = 0
    
    for stair in stairs:
        current_quantity = None
        current_material = None
        current_area = None
        current_ec = None
        layer_thicknesses = {}
        material_layers = []

        # Get volume information
        if hasattr(stair, "IsDefinedBy"):
            for definition in stair.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_StairFlightBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume for {stair.Name}: {quantity.VolumeValue}')
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        # Get material information
        if hasattr(stair, "HasAssociations"):
            for association in stair.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial

                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        material_layers.append(material.Name)
                        current_material = material.Name
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialConstituent")
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
                            material_layers.append(layer.Material.Name)

        if material_layers:
            logger.debug("Processing layered stair")
            # Multi-material stair
            for mat in material_layers:
                mat_ec_data = MaterialList.get(mat)
                thickness = layer_thicknesses.get(mat, None)
                
                # Store this material in our database for future reference
                if mat and mat not in MaterialsToIgnore:
                    element_data = {
                        'element_type': stair.is_a(),
                        'element_name': stair.Name if hasattr(stair, 'Name') else None,
                        'material_name': mat,
                        'material_type': 'layered',
                        'volume': current_quantity,
                        'area': current_area,
                        'layer_materials': material_layers,
                        'layer_thicknesses': [thickness] if thickness else []
                    }
                    
                    # If material has EC data, include it
                    if mat_ec_data:
                        if isinstance(mat_ec_data, list) and len(mat_ec_data) >= 2:
                            element_data['ec_per_kg'] = mat_ec_data[0]
                            element_data['density'] = mat_ec_data[1]
                        elif isinstance(mat_ec_data, (int, float)):
                            element_data['ec_per_m2'] = mat_ec_data
                    
                    # Add to database
                    calculator_utils.add_material_to_database(element_data)
                
                if mat_ec_data is None and mat not in MaterialsToIgnore:
                    # Try material matching
                    element_data = {
                        'element_type': stair.is_a(),
                        'element_name': stair.Name if hasattr(stair, 'Name') else None,
                        'material_name': mat,
                        'material_type': 'layered',
                        'volume': current_quantity,
                        'area': current_area,
                        'layer_materials': material_layers,
                        'layer_thicknesses': [thickness] if thickness else []
                    }
                    
                    similar_material, similarity = calculator_utils.find_similar_material(element_data)
                    
                    if similar_material and similar_material in MaterialList:
                        logger.info(f"Material '{mat}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                        mat = similar_material
                        mat_ec_data = MaterialList.get(mat)
                    else:
                        logger.warning(f"Material '{mat}' not found and no similar material found. Skipping this layer.")
                        continue

                # If we have material but no volume, skip
                if current_quantity is None:
                    logger.warning(f"No volume found for stair {stair.Name} with material {mat}. Attempting to calculate.")
                    current_quantity = calculator_utils.get_element_volume(stair)
                    if current_quantity is None:
                        logger.error(f"Failed to calculate volume for stair {stair.Name}. Skipping.")
                        continue
                
                material_ec_perkg, material_density = mat_ec_data
                # For layered materials, divide the volume by the number of materials
                volume_per_material = current_quantity / len(material_layers)
                current_ec = material_ec_perkg * material_density * volume_per_material
                logger.debug(f"EC for material '{mat}' in {stair.Name} is {current_ec}")
                total_ec += current_ec

        elif current_material:
            # Single-material stair
            current_material_ec = MaterialList.get(current_material, None) if current_material else None

            if current_material_ec is None and MATERIAL_REAPLCE:
                # Try material matching
                element_data = {
                    'element_type': stair.is_a(),
                    'element_name': stair.Name if hasattr(stair, 'Name') else None,
                    'material_name': current_material,
                    'material_type': 'single',
                    'volume': current_quantity
                }

                similar_material, similarity = calculator_utils.find_similar_material(element_data)
                
                if similar_material and similar_material in MaterialList:
                    logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                    current_material = similar_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.warning(f"Material '{current_material}' not found and no similar material found. Skipping this stair.")
                    continue
            
            if current_quantity is None:
                logger.warning(f"No volume found for stair {stair.Name}. Attempting to calculate.")
                current_quantity = calculator_utils.get_element_volume(stair)
                if current_quantity is None:
                    logger.error(f"Failed to calculate volume for stair {stair.Name}. Skipping.")
                    continue
                
            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity
            logger.debug(f"EC for {stair.Name} is {current_ec}")
            total_ec += current_ec
        
        else:
            logger.warning(f"EC calculation for stair failed, attempting manual volume method")
            # Handle case where no material information is available
            if len(material_layers) == 0:
                logger.warning(f"No material information found for stair {stair.Name}. Using concrete as default.")
                default_material = "CONCRETE"
                if default_material in MaterialList:
                    current_material = default_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.error(f"Default material '{default_material}' not found. Skipping this stair.")
                    continue
            else:
                # Use the most common material from material layers
                MaterialList_filtered = [material for material in material_layers if material not in MaterialsToIgnore]
                if len(MaterialList_filtered) > 0:
                    current_material = max(set(MaterialList_filtered), key=MaterialList_filtered.count)
                    current_material_ec = MaterialList.get(current_material, None)
                    
                    if current_material_ec is None and MATERIAL_REAPLCE:
                        # Try material matching
                        element_data = {
                            'element_type': stair.is_a(),
                            'element_name': stair.Name if hasattr(stair, 'Name') else None,
                            'material_name': current_material,
                            'material_type': 'single',
                            'volume': current_quantity
                        }
                        
                        similar_material, similarity = calculator_utils.find_similar_material(element_data)
                        
                        if similar_material and similar_material in MaterialList:
                            logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                            current_material = similar_material
                            current_material_ec = MaterialList.get(current_material)
                        else:
                            logger.warning(f"Material '{current_material}' not found and no similar material found. Skipping this stair.")
                            continue
                else:
                    logger.error(f"No suitable material found for stair {stair.Name}. Skipping.")
                    continue
            
            if current_quantity is None:
                current_quantity = calculator_utils.get_element_volume(stair)
                if current_quantity is None:
                    logger.error(f"Failed to calculate volume for stair {stair.Name}. Skipping.")
                    continue
            
            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity
            logger.debug(f"EC for {stair.Name} is {current_ec}")
            total_ec += current_ec

    logger.debug(f"Total EC for stairs is {total_ec}")
    return total_ec

def calculate_railings(railings):
    """Calculate embodied carbon for railings, using material matching if needed"""
    total_ec = 0
    
    for railing in railings:
        current_quantity = None
        current_material = None
        current_ec = None
        material_layers = []

        # Get volume information
        if hasattr(railing, "IsDefinedBy"):
            for definition in railing.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_RailingBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume for {railing.Name}: {quantity.VolumeValue}')
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        # Get material information
        if hasattr(railing, "HasAssociations"):
            for association in railing.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        material_layers.append(material.Name)
                        current_material = material.Name
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialConstituent")
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
                            material_layers.append(layer.Material.Name)

        # Handle the material calculations
        if material_layers:
            # Filter materials to exclude ones that should be ignored
            MaterialList_filtered = [material for material in material_layers if material not in MaterialsToIgnore]
            
            if len(MaterialList_filtered) == 0:
                logger.error(f"No usable materials found for railing {railing.Name}. Skipping.")
                continue
                
            # Use the most frequent material if multiple are present
            current_material = max(set(MaterialList_filtered), key=MaterialList_filtered.count)
            logger.debug(f"Using material {current_material} for railing")
            
            current_material_ec = MaterialList.get(current_material, None)
            
            if current_material_ec is None and MATERIAL_REAPLCE:
                # Try material matching
                element_data = {
                    'element_type': railing.is_a(),
                    'element_name': railing.Name if hasattr(railing, 'Name') else None,
                    'material_name': current_material,
                    'material_type': 'single',
                    'volume': current_quantity
                }
                
                similar_material, similarity = calculator_utils.find_similar_material(element_data)
                
                if similar_material and similar_material in MaterialList:
                    logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                    current_material = similar_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    # If no similar material found but we have other materials, try the next most common
                    other_materials = [m for m in MaterialList_filtered if m != current_material]
                    if other_materials:
                        current_material = max(set(other_materials), key=other_materials.count)
                        current_material_ec = MaterialList.get(current_material)
                        if current_material_ec:
                            logger.warning(f"Using alternative material '{current_material}' for railing")
                        else:
                            logger.error(f"No suitable material found for railing {railing.Name}. Skipping.")
                            continue
                    else:
                        logger.error(f"No suitable material found for railing {railing.Name}. Skipping.")
                        continue
        else:
            logger.warning(f"No material information for railing {railing.Name}. Assuming steel.")
            # Default to steel for railings if no material is specified
            if "STEEL" in MaterialList:
                current_material = "STEEL"
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.error(f"Default steel material not found in MaterialList. Skipping this railing.")
                continue
        
        if current_quantity is None:
            current_quantity = calculator_utils.get_element_volume(railing)
            if current_quantity is None or current_quantity <= 0:
                logger.error(f"Failed to calculate positive volume for railing {railing.Name}. Skipping.")
                continue
        
        material_ec_perkg, material_density = current_material_ec
        current_ec = material_ec_perkg * material_density * current_quantity
        logger.debug(f"EC for {railing.Name} is {current_ec}, volume is {current_quantity}")
        total_ec += current_ec

    logger.debug(f"Total EC for railings is {total_ec}")
    return total_ec


def calculate_members(members):
    """Calculate embodied carbon for structural members, using material matching if needed"""
    total_ec = 0
    
    for member in members:
        current_quantity = None
        current_material = None
        material_layers = []
        
        # Get volume information
        if hasattr(member, "IsDefinedBy"):
            for definition in member.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_MemberBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume for {member.Name}: {quantity.VolumeValue}')
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        # Get material information
        if hasattr(member, "HasAssociations"):
            for association in member.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        material_layers.append(material.Name)
                        current_material = material.Name
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialConstituent")
                            material_layers.append(layer.Material.Name)

        # Store this material in our database for future reference
        if current_material and current_material not in MaterialsToIgnore:
            element_data = {
                'element_type': member.is_a(),
                'element_name': member.Name if hasattr(member, 'Name') else None,
                'material_name': current_material,
                'material_type': 'single',
                'volume': current_quantity
            }
            
            # Add to database
            calculator_utils.add_material_to_database(element_data)

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Try material matching
            if not current_material and material_layers:
                # If we have layer materials but no current material, use the most common
                material_layers_filtered = [m for m in material_layers if m not in MaterialsToIgnore]
                if material_layers_filtered:
                    current_material = max(set(material_layers_filtered), key=material_layers_filtered.count)
            
            element_data = {
                'element_type': member.is_a(),
                'element_name': member.Name if hasattr(member, 'Name') else None,
                'material_name': current_material,
                'material_type': 'single',
                'volume': current_quantity
            }
            
            similar_material, similarity = calculator_utils.find_similar_material(element_data)
            
            if similar_material and similar_material in MaterialList:
                logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                # Try with a common default if nothing else works
                if "STEEL" in MaterialList:
                    logger.warning(f"No suitable material found for member {member.Name}. Using STEEL as default.")
                    current_material = "STEEL"
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.error(f"No suitable material found for member {member.Name}. Skipping.")
                    continue
        
        if current_quantity is None:
            current_quantity = calculator_utils.get_element_volume(member)
            if current_quantity is None or current_quantity <= 0:
                logger.error(f"Failed to calculate positive volume for member {member.Name}. Skipping.")
                continue
                
        material_ec_perkg, material_density = current_material_ec
        current_ec = material_ec_perkg * material_density * current_quantity
        logger.debug(f"EC for {member.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for members is {total_ec}")
    return total_ec       
def calculate_plates(plates):
    """Calculate embodied carbon for plates, using material matching if needed"""
    total_ec = 0
    
    for plate in plates:
        current_quantity = None
        current_material = None
        current_area = None
        material_layers = []
        
        # Get volume/area information
        if hasattr(plate, "IsDefinedBy"):
            for definition in plate.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_PlateBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume for {plate.Name}: {quantity.VolumeValue}')
                                current_quantity = quantity.VolumeValue
                            elif quantity.is_a('IfcQuantityArea') and quantity.Name == 'NetArea':
                                logger.debug(f'Found NetArea for {plate.Name}: {quantity.AreaValue}')
                                current_area = quantity.AreaValue
                        if current_quantity is not None:
                            break

        # Get material information
        if hasattr(plate, "HasAssociations"):
            for association in plate.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        material_layers.append(material.Name)
                        current_material = material.Name
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                            material_layers.append(layer.Material.Name)
                            if not current_material:  # Use the first layer as the primary material
                                current_material = layer.Material.Name
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
                            material_layers.append(layer.Material.Name)
                            if not current_material:  # Use the first layer as the primary material
                                current_material = layer.Material.Name
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialConstituent")
                            material_layers.append(layer.Material.Name)
                            if not current_material:  # Use the first constituent as the primary material
                                current_material = layer.Material.Name

        # Store this material in our database for future reference
        if current_material and current_material not in MaterialsToIgnore:
            element_data = {
                'element_type': plate.is_a(),
                'element_name': plate.Name if hasattr(plate, 'Name') else None,
                'material_name': current_material,
                'material_type': 'single',
                'volume': current_quantity,
                'area': current_area
            }
            
            # Add to database
            calculator_utils.add_material_to_database(element_data)

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Try material matching
            if not current_material and material_layers:
                # If we have layer materials but no current material, use the most common
                material_layers_filtered = [m for m in material_layers if m not in MaterialsToIgnore]
                if material_layers_filtered:
                    current_material = max(set(material_layers_filtered), key=material_layers_filtered.count)
            
            element_data = {
                'element_type': plate.is_a(),
                'element_name': plate.Name if hasattr(plate, 'Name') else None,
                'material_name': current_material,
                'material_type': 'single',
                'volume': current_quantity,
                'area': current_area
            }
            
            similar_material, similarity = calculator_utils.find_similar_material(element_data)
            
            if similar_material and similar_material in MaterialList:
                logger.info(f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})")
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                # For plates, try common materials like steel or glass if no match found
                for default_material in ["STEEL", "GLASS", "ALUMINIUM"]:
                    if default_material in MaterialList:
                        logger.warning(f"No suitable material found for plate {plate.Name}. Using {default_material} as default.")
                        current_material = default_material
                        current_material_ec = MaterialList.get(current_material)
                        break
                else:
                    logger.error(f"No suitable material found for plate {plate.Name}. Skipping.")
                    continue
        
        if current_quantity is None:
            if current_area is not None:
                # Estimate volume from area if possible
                # Assume a typical thickness for plates (e.g., 10mm = 0.01m)
                estimated_thickness = 0.01  # meters
                current_quantity = current_area * estimated_thickness
                logger.warning(f"Estimating volume for plate {plate.Name} based on area: {current_quantity}")
            else:
                # Try to calculate volume directly
                current_quantity = calculator_utils.get_element_volume(plate)
                
            if current_quantity is None or current_quantity <= 0:
                logger.error(f"Failed to calculate positive volume for plate {plate.Name}. Skipping.")
                continue
                
        material_ec_perkg, material_density = current_material_ec
        current_ec = material_ec_perkg * material_density * current_quantity
        logger.debug(f"EC for {plate.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for plates is {total_ec}")

    return total_ec           

def calculate_piles(piles):


    total_ec = 0
    quantities = {}
    materials = []
    current_quantity = None
    current_material = None
    rebar = None

    for pile in piles:
        psets = get_psets(pile)
        rebar_set = psets.get('Rebar Set')
        if rebar_set is None:
            logger.error('Rebar set not found')
        if rebar_set:
            rebar = rebar_set.get('MainRebar')
            if rebar is None:
                logger.error('Rebar not found')
        
        
        dimensions = psets.get('Dimensions')
        if dimensions is None:
            logger.error('Dimensions/Diameter not found')
        if dimensions:
            lengthmm = dimensions.get('Length')
            if lengthmm is None:
                logger.error("Length not found")
            else:
                length = lengthmm / 1000
        
        if rebar:
            rebar_no, area = rebar.split("H")
            rebar_vol = length * int(rebar_no) * 3.14 * ((int(area)/2000) **2)

        if hasattr(pile, "IsDefinedBy"):
            for definition in pile.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_PileBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume  for {pile.Name}')
                                quantities[quantity.Name] = quantity.VolumeValue
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        if hasattr(pile, "HasAssociations"):
            for association in pile.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        materials.append(material.Name)
                        current_material = material.Name
                        break
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                            materials.append(layer.Material.Name)
                            current_material = material.Name
                            break
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
                            materials.append(layer.Material.Name)
                            current_material = material.Name
                            break

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None:
            # handle with default value?
            # ai?
            # raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
            print("Error, not implemented yet")
            continue
        
        material_ec_perkg, material_density = current_material_ec
        print(current_quantity)
        if rebar == None:
            current_ec = material_ec_perkg * material_density * current_quantity
            
        else:
            current_ec = material_ec_perkg * material_density * (current_quantity - rebar_vol)
            rebar_ec = rebar_vol * 2.510 * 7850
            logger.debug(f"EC for {pile.Name}'s rebars is {rebar_ec}")
            total_ec += rebar_ec
        
        
        logger.debug(f"EC for {pile.Name} is {current_ec}")
        total_ec += current_ec


    
    logger.debug(f"Total EC for piles is {total_ec}")

    return total_ec

def calculate_footings(footings):
    total_ec = 0
    quantities = {}
    materials = []
    current_quantity = None
    current_material = None
    rebar = None

    for footing in footings:
        psets = get_psets(footing)
        rebar_set = psets.get('Rebar Set')
        if rebar_set is None:
            logger.error('Rebar set not found')
        if rebar_set:
            BD = rebar_set.get('BottomDistribution')
            BM = rebar_set.get('BottomMain')
            sidebar = rebar_set.get('SideBar')
            stirrups = rebar_set.get('Stirrups')
            TD = rebar_set.get('TopDistribution')
            TM = rebar_set.get('TopMain')
            if BD == None or BM == None or sidebar == None or stirrups == None or TM == None or TD == None:
                logger.error('Rebar part not found')
                
            # Get diameter and spacing 
            BDdiameter, BDspacing = BD.split("-")
            BDdiameter = BDdiameter[1:3]
            BMdiameter, BMspacing = BM.split("-")
            BMdiameter = BMdiameter[1:3]
            sidebar_diameter, sidebar_spacing = sidebar.split("-")
            sidebar_diameter = sidebar_diameter[1:3]
            stirrups_diameter, stirrups_spacing, ignore = stirrups.split("-")
            stirrups_diameter = stirrups_diameter[1:3]
            TDdiameter, TDspacing = TD.split("-")
            TDdiameter = TDdiameter[1:3]
            TMdiameter, TMspacing = TM.split("-")
            TMdiameter = TMdiameter[1:3]

        # Get width and length 
        dimensions = psets.get('Dimensions')
        if dimensions is None:
            logger.error('Dimensions/Diameter not found')
        if dimensions:
            lengthmm = dimensions.get('Length')
            if lengthmm is None:
                logger.error("Length not found")
            else:
                length = lengthmm / 1000
            
            widthmm = dimensions.get('Width')
            if widthmm is None:
                logger.error("Width not found")
            else:
                width = widthmm / 1000
            
            heightmm = dimensions.get('Foundation Thickness')
            if heightmm is None:
                logger.error("Height not found")
            else:
                height = heightmm / 1000
        # If width is more than length, flip
        # if length and width:
        #     if length < width: 
        #         temp = length
        #         length = width
        #         width = temp  
        
        if rebar_set:
            rebar_length = length - (2 * (50/1000))
            rebar_breadth = width - (2 * (50/1000))
            rebar_height = height - (2 * (50/1000))
            # Bottom
            
            length_rebarsno = math.floor(rebar_length / (int(BDspacing)/1000)) + 1
            breadth_rebarsno = math.floor(rebar_breadth / (int(BMspacing)/1000)) + 1
            
            bottom_vol = (breadth_rebarsno * rebar_length * (3.14 * ((int(BDdiameter)/2000) ** 2 ))) + (length_rebarsno * rebar_breadth * (3.14 * ((int(BMdiameter)/2000) ** 2 )))

            # Top
            length_rebarsno = math.floor(rebar_length / (int(TDspacing)/1000)) + 1
            breadth_rebarsno = math.floor(rebar_breadth / (int(TMspacing)/1000)) + 1
            
            top_vol = (breadth_rebarsno * rebar_length * (3.14 * ((int(TDdiameter)/2000) ** 2 ))) + (length_rebarsno * rebar_breadth * (3.14 * ((int(TMdiameter)/2000) ** 2 )))
        
            # Side
            length_rebarsno = math.floor(rebar_length / (int(TDspacing)/1000)) + 1
            breadth_rebarsno = math.floor(rebar_breadth / (int(TMspacing)/1000)) + 1
            height_rebarsno = math.floor(rebar_height / (int(sidebar_spacing)/1000)) + 1
            
            #side_vol = (length * height) + (breadth * height) + (height * length) + (height * breadth)
            side_vol = (2 * (length_rebarsno * rebar_height * (3.14 * ((int(sidebar_diameter)/2000) ** 2)))) + (2 * (breadth_rebarsno * rebar_height * (3.14 * ((int(sidebar_diameter)/2000) ** 2)))) \
                    +  (2 * (height_rebarsno * rebar_length * (3.14 * ((int(sidebar_diameter)/2000) ** 2)))) + (2 * (height_rebarsno * rebar_breadth * (3.14 * ((int(sidebar_diameter)/2000) ** 2))))
            
            
            # Stirrups
            perimeter = (2*rebar_breadth) + (2*rebar_height)
            length_rebarsno = math.floor(rebar_length / (int(stirrups_spacing)/1000)) + 1
            stirrups_vol = length_rebarsno * perimeter * (3.14 * ((int(stirrups_diameter)/2000) ** 2))

            
        if hasattr(footing, "IsDefinedBy"):
            for definition in footing.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_FootingBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and (quantity.Name == 'NetVolume' or quantity.Name == 'GrossVolume'):
                                logger.debug(f'Found NetVolume  for {footing.Name}')
                                quantities[quantity.Name] = quantity.VolumeValue
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        if hasattr(footing, "HasAssociations"):
            for association in footing.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        materials.append(material.Name)
                        current_material = material.Name
                        break
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                            materials.append(layer.Material.Name)
                            current_material = material.Name
                            break
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
                            materials.append(layer.Material.Name)
                            current_material = material.Name
                            break

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None:
            # handle with default value?
            # ai?
            raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
        
        material_ec_perkg, material_density = current_material_ec
        
        if rebar_set == None:
            current_ec = material_ec_perkg * material_density * current_quantity

        else:
            rebar_vol = top_vol + bottom_vol + side_vol + stirrups_vol
            print(rebar_vol)
            current_ec = material_ec_perkg * material_density * (current_quantity - rebar_vol)
            rebar_ec = rebar_vol  * 2.510 * 7850
            logger.debug(f"EC for {footing.Name}'s rebars is {rebar_ec}")
            total_ec += rebar_ec
            
        logger.debug(f"EC for {footing.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for footings is {total_ec}")

    return total_ec



    
    logger.debug(f"Total EC for columns is {total_ec}")

    return total_ec

def calculate_embodied_carbon(filepath):
    
    
    slabs_to_ignore=[]
    
    ifc_file = ifcopenshell.open(filepath)

    columns = ifc_file.by_type('IfcColumn')
    logger.info(f"Total columns found {len(columns)}")

    beams = ifc_file.by_type('IfcBeam')
    logger.info(f"Total beams found {len(beams)}")

    slabs = ifc_file.by_type('IfcSlab')
    logger.info(f"Total slabs found {len(slabs)}")
    
    roofs = ifc_file.by_type('IfcRoof')
    logger.info(f"Total roofs found {len(roofs)}")

    windows = ifc_file.by_type('IfcWindow')
    logger.info(f"Total windows found {len(windows)}")

    walls = ifc_file.by_type('IfcWall')
    logger.info(f"Total walls found {len(walls)}")

    doors = ifc_file.by_type('IfcDoor')
    logger.info(f"Total doors found {len(doors)}")

    stairs = ifc_file.by_type('IfcStairFlight')
    logger.info(f"Total stairflights found {len(stairs)}")

    railings = ifc_file.by_type('IfcRailing')
    logger.info(f"Total railings found {len(railings)}")

    spaces = ifc_file.by_type('IfcSpace')
    logger.info(f"Total spaces found {len(spaces)}")
    
    members = ifc_file.by_type('IfcMember')
    logger.info(f"Total members found {len(members)}")

    plates = ifc_file.by_type('IfcPlate')
    logger.info(f"Total plates found {len(plates)}")
    
    piles = ifc_file.by_type('IfcPile')
    logger.info(f"Total piles found {len(piles)}")
    
    footings = ifc_file.by_type('IfcFooting')
    logger.info(f"Total footings found {len(footings)}")


    if roofs:
        for roof in roofs:
            aggregated_by = roof.IsDecomposedBy
            print(aggregated_by)
            for rel in aggregated_by:
                if rel.is_a('IfcRelAggregates'):
                    print(rel)
                    for part in rel.RelatedObjects:
                        print(f"child : {part.is_a()}")
                        if part.is_a('IfcSlab'):
                            slabs_to_ignore.append(part.id())
                    
    #print(slabs_to_ignore)

    total_ec = columns_ec = beams_ec = slabs_ec = walls_ec = windows_ec = roofs_ec = doors_ec = stairs_ec = railings_ec = members_ec = plates_ec= 0

    if columns:
        columns_ec= calculate_columns(columns)
        total_ec += columns_ec

    if beams:
        beams_ec= calculate_beams(beams)
        total_ec += beams_ec

    if slabs:
        slabs_ec= calculate_slabs(slabs, to_ignore=slabs_to_ignore)
        total_ec += slabs_ec

    if walls:
        walls_ec = calculate_walls(walls)
        total_ec += walls_ec

    if windows:
        windows_ec = calculate_windows(windows)
        total_ec += windows_ec

    if doors:
        doors_ec = calculate_doors(doors)
        total_ec += doors_ec

    # IfcStairFlight only
    if stairs:
        stairs_ec = calculate_stairs(stairs)
        total_ec += stairs_ec
    
    if railings:
        railings_ec = calculate_railings(railings)
        total_ec += railings_ec
    
    if roofs:
        roofs_ec = calculate_roofs(roofs)
        total_ec += roofs_ec
    
    if members:
        members_ec = calculate_members(members)
        total_ec += members_ec
    
    if plates:
        plates_ec = calculate_plates(plates)
        total_ec += plates_ec
    
    if plates:
        plates_ec = calculate_plates(plates)
        total_ec += plates_ec
        
    if piles:
        piles_ec = calculate_piles(piles)
        total_ec += piles_ec
        
    if footings:
        footings_ec = calculate_footings(footings)
        total_ec += footings_ec
    
    
    logger.info(f"Total EC calculated: {total_ec}")

    return total_ec

def calculate_gfa(filepath):

    ifc_file = ifcopenshell.open(filepath)
    spaces = ifc_file.by_type('IfcSpace')
    logger.info(f"Total spaces found {len(spaces)}")

    if len(spaces) == 0 :    
        logger.error("No spaces found.")
        return 0
    
    total_area = 0

    for space in spaces:
    # Get the area from quantities
        # total_area += calculator_utils.get_element_area(space)
        psets= get_psets(space)
        qto = psets.get('Qto_SpaceBaseQuantities')
        if not qto:
            logger.error(f"{space} has no pset Qto_SpaceBaseQuantities, skipping this element")
            return 0
        gfa = qto.get('GrossFloorArea')
        if not gfa:
            logger.error(f"{space} has no GFA in Qto_SpaceBaseQuantities, skipping this element")
            return 0
        total_area += gfa

    logger.info(f"Total GFA calculated: {total_area}")
    return total_area

if __name__ == "__main__":
    # Run the calculator on the specified IFC file
    ifcpath = input("Enter path to IFC file: ")
    logger.info(f"Processing file: {ifcpath}")
    
    if not os.path.exists(ifcpath):
        logger.error(f"File not found: {ifcpath}")
        sys.exit(1)
        
    total_ec = calculate_embodied_carbon(ifcpath)
    total_gfa = calculate_gfa(ifcpath)
    
    if total_gfa > 0:
        ec_per_m2 = total_ec / total_gfa
        logger.info(f"Embodied carbon per m²: {ec_per_m2} kgCO2e/m²")
    
    print(f"\nResults for {os.path.basename(ifcpath)}:")
    print(f"Total Embodied Carbon: {total_ec:.2f} kgCO2e")
    if total_gfa > 0:
        print(f"Total Gross Floor Area: {total_gfa:.2f} m²")
        print(f"Embodied Carbon per m²: {ec_per_m2:.2f} kgCO2e/m²")