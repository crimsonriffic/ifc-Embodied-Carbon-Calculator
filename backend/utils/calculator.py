import ifcopenshell
from ifcopenshell.util.element import get_psets
from loguru import logger
import sys
import ifcopenshell
import ifcopenshell.geom
import numpy as np
from math import fabs
MaterialList = {"Concrete, Cast In Situ": [0.103, 2350] , 
                "Concrete, Cast-in-Place gray": [0.103, 2350] , 
                "Concrete, Grade 40": [0.170, 2400], 
                "Concrete, Grade 25": [0.13, 2350], 
                "Concrete, General": [0.112,2350], # kgCO2e per kg, kg per m^3 (Gen 1)
                'Wood_aluminium fixed window 3-glass (SF 2010)' : 54.6, # kgCO2 per 1m^2
                'Wood_aluminium sidehung window 3-glass (SF 2010)' : 72.4,
                'Wooden doors T10-T25 with wooden frame' : 30.4,
                'Wooden doors T10-T25 with steel frame' : 49.4,
                'Travertine' : [0,0],

                }  
MaterialsToIgnore  = ["Travertine"]
LOGGING_LEVEL = "DEBUG" 
logger.remove()  
logger.add(sys.stderr, level=LOGGING_LEVEL) 


def calculate_beams(beams):

    total_ec = 0
    quantities = {}
    materials = []
    current_quantity = None # in volume
    current_material = None
    for beam in beams:

        if hasattr(beam, "IsDefinedBy"):
            for definition in beam.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_BeamBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume  for {beam.Name}')
                                quantities[quantity.Name] = quantity.VolumeValue
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        # Note that it takes the first occurance of a material, subsequent materials will be ignored.
        if hasattr(beam, "HasAssociations"):
            for association in beam.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        materials.append(material.Name)
                        current_material = material.Name
                        break

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None:
            # handle with default value?
            # ai?
            raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
        
        material_ec_perkg, material_density = current_material_ec
        current_ec = material_ec_perkg * material_density * current_quantity

        logger.debug(f"EC for {beam.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for beams is {total_ec}")

    return total_ec

def calculate_columns(columns):


    total_ec = 0
    quantities = {}
    materials = []
    current_quantity = None
    current_material = None

    for column in columns:
        if hasattr(column, "IsDefinedBy"):
            for definition in column.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_ColumnBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume  for {column.Name}')
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
        current_ec = material_ec_perkg * material_density * current_quantity

        logger.debug(f"EC for {column.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for columns is {total_ec}")

    return total_ec

def calculate_slabs(slabs):

    total_ec = 0
    quantities = {}
    material_layers = []
    current_quantity = None
    current_material = None
    current_area = None
    current_ec = None

    for slab in slabs:

        layer_thicknesses = {}
        material_layers = []

        if hasattr(slab, "IsDefinedBy"):
            for definition in slab.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_SlabBaseQuantities':
                        for quantity in property_def.Quantities:
                            # For material constituent
                            if quantity.Name in MaterialList.keys(): 
                                for sub_quantity in quantity.HasQuantities:
                                    logger.debug(f'Found subquantity {sub_quantity.Name} for {quantity.Name}: {sub_quantity.LengthValue}')
                                    # logger.debug(sub_quantity.LengthValue)
                                    layer_thicknesses[quantity.Name] = sub_quantity.LengthValue

                            elif quantity.is_a('IfcQuantityArea') and quantity.Name == 'NetSideArea':
                                logger.debug(f'Found NetSideArea for {slab.Name}')
                                current_area = quantity.AreaValue

                            elif quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume  for {slab.Name}')
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
                        break
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialConstituent")
                            material_layers.append(layer.Material.Name)

        if material_layers:
            logger.debug("layered")
            # Multi-material wall
            for mat in material_layers:

                mat_ec_data = MaterialList.get(mat)
                thickness = layer_thicknesses.get(mat, None)
                if mat_ec_data is None:
                    raise NotImplementedError(f"Material '{mat}' not found in database")
                if thickness is None:
                    logger.warning(f"'{mat}' layer thickness not found, skipping EC calculation")
                    continue
                if thickness <= 0:
                    logger.warning(f"'{mat}' layer thickness <= 0, skipping EC calculation")
                    continue

                if current_area is None:
                    logger.warning(f"{mat} area not found, manually calculating.")

                ec_per_kg, density = mat_ec_data
                logger.debug(thickness)
                logger.debug(current_area)
                logger.debug(ec_per_kg)
                logger.debug(density)
                current_ec = ec_per_kg * density * (thickness/1000) * current_area
                logger.debug(f"EC for material '{mat}' in {slab.Name} is {current_ec}")
                total_ec += current_ec

        elif current_material:

            current_material_ec = MaterialList.get(current_material, None) if current_material else None

            if current_material_ec is None:
                # handle with default value?
                # ai?
                raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity
            logger.debug(f"EC for {slab.Name} is {current_ec}")
            total_ec += current_ec
        
        if current_ec is None:
            logger.warning(f"EC calculation for slab failed, attempting manual volume method")
            # Attempts to retrieve the "correct" material from material layer set. Works if able to filter down to one possible material.
            # Calculates EC using EC density * volume method.
            # Calculates volume from ifc geometry.
            
            MaterialList_filtered = [ material for material in material_layers if material not in MaterialsToIgnore]
            if len(MaterialList_filtered) != 1:
                logger.error(f"Unable to isolate to one material from material layer set. Skipping this slab {slab}") 
            if current_quantity is None:
                current_quantity = get_slab_volume(slab)
            current_material = MaterialList_filtered[0]
            logger.debug(f"Using material {current_material}")
            current_material_ec = MaterialList.get(current_material, None) if current_material else None
            if current_material_ec is None:
                # handle with default value?
                # ai?
                raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity
            logger.debug(f"EC for {slab.Name} is {current_ec}")
            total_ec += current_ec

    logger.debug(f"Total EC for slabs is {total_ec}")

    return total_ec

def calculate_windows(windows):

    total_ec = 0
    quantities = {}
    materials = []
    current_quantity = None
    current_material = None

    for window in windows:

        if hasattr(window, "IsDefinedBy"):
            for definition in window.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_windowBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume  for {window.Name}')
                                quantities[quantity.Name] = quantity.VolumeValue
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        if hasattr(window, "HasAssociations"):
            for association in window.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        materials.append(material.Name)
                        current_material = material.Name
                        break

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None:
            # handle with default value?
            # ai?
            raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
        
        material_ec_perkg, material_density = current_material_ec
        current_ec = material_ec_perkg * material_density * current_quantity

        logger.debug(f"EC for {window.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for windows is {total_ec}")

    return total_ec
def calculate_walls(walls):

    total_ec = 0
    quantities = {}
    materials = []
    current_quantity = None
    current_material = None

    for wall in walls:
        # psets = ifcopenshell.util.element.get_psets(wall)
        # print(psets)
        if hasattr(wall, "IsDefinedBy"):
            for definition in wall.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_WallBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume  for {wall.Name}')
                                quantities[quantity.Name] = quantity.VolumeValue
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        if hasattr(wall, "HasAssociations"):
            for association in wall.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        materials.append(material.Name)
                        current_material = material.Name
                        break

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None:
            # handle with default value?
            # ai?
            raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
        
        material_ec_perkg, material_density = current_material_ec
        current_ec = material_ec_perkg * material_density * current_quantity

        logger.debug(f"EC for {wall.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for walls is {total_ec}")

    return total_ec


def calculate_windows(windows):

    total_ec = 0
    quantities = {}
    materials = []
    current_quantity = None
    current_material = None

    for window in windows:

        if hasattr(window, "IsDefinedBy"):
            for definition in window.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_WindowBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityArea') and quantity.Name == 'Area':
                                logger.debug(f'Found Area for {window.Name}')
                                quantities[quantity.Name] = quantity.AreaValue
                                current_quantity = quantity.AreaValue
                                break
                        if current_quantity is not None:
                            break

        psets = get_psets(window)
        current_material = psets['Pset_WindowCommon']['Reference']

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None:
            # handle with default value?
            # ai?
            raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
        
        material_ec_per_m2 = current_material_ec
        current_ec = material_ec_per_m2 *  current_quantity 

        logger.debug(f"EC for {window.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for windows is {total_ec}")

    return total_ec

def calculate_doors(doors):

    total_ec = 0
    quantities = {}
    materials = []
    current_quantity = None
    current_material = None

    for door in doors:

        if hasattr(door, "IsDefinedBy"):
            for definition in door.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_DoorBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityArea') and quantity.Name == 'Area':
                                logger.debug(f'Found Area for {door.Name}')
                                quantities[quantity.Name] = quantity.AreaValue
                                current_quantity = quantity.AreaValue
                                break
                        if current_quantity is not None:
                            break

        psets = get_psets(door)
        current_material = psets['Pset_DoorCommon']['Reference']

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None:
            # handle with default value?
            # ai?
            raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
        
        material_ec_per_m2 = current_material_ec
        current_ec = material_ec_per_m2 *  current_quantity 

        logger.debug(f"EC for {door.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for doors is {total_ec}")

    return total_ec
    pass
                    
def calculate_element_area(element):
    area = 0
    
    # Get the area from quantities
    if hasattr(element, "IsDefinedBy"):
        for definition in element.IsDefinedBy:
            if definition.is_a('IfcRelDefinesByProperties'):
                property_def = definition.RelatingPropertyDefinition
                if property_def.is_a('IfcElementQuantity'):
                    quantity_list = [ (quantity, quantity.Name) for quantity in property_def.Quantities]
                    for i in ['NetArea','NetSideArea', 'OuterSurfaceArea', 'NetSurfaceArea']:
                        for quantity, name in quantity_list:
                            if i == name:
                                # logger.info(f"{element} has area: {quantity.AreaValue}")
                                area += quantity.AreaValue
    
    return area


def get_slab_volume( slab):
    settings = ifcopenshell.geom.settings()
    
    try:
        shape = ifcopenshell.geom.create_shape(settings, slab)
        vertices = np.array(shape.geometry.verts).reshape((-1, 3))
        faces = shape.geometry.faces
        
        volume = 0
        # Process triangulated faces
        for i in range(0, len(faces), 3):
            # Get triangle vertices
            v1 = vertices[faces[i]]
            v2 = vertices[faces[i + 1]]
            v3 = vertices[faces[i + 2]]
            
            # Calculate signed volume of tetrahedron formed by triangle and origin
            # This is based on the divergence theorem
            v321 = v3[0] * v2[1] * v1[2]
            v231 = v2[0] * v3[1] * v1[2]
            v312 = v3[0] * v1[1] * v2[2]
            v132 = v1[0] * v3[1] * v2[2]
            v213 = v2[0] * v1[1] * v3[2]
            v123 = v1[0] * v2[1] * v3[2]
            
            volume += (-v321 + v231 + v312 - v132 - v213 + v123) / 6.0
            
        return fabs(volume)  
        
    except RuntimeError as e:
        print(f"Error processing geometry: {e}")
        return None

def calculate_stairs(stairs):

    total_ec = 0
    quantities = {}
    material_layers = []

    for stair in stairs:
        current_quantity = None
        current_material = None
        current_area = None
        current_ec = None
        layer_thicknesses = {}
        material_layers = []


        if hasattr(stair, "HasAssociations"):
            for association in stair.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial

                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        material_layers.append(material.Name)
                        current_material = material.Name
                        break
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialConstituent")
                            material_layers.append(layer.Material.Name)

        if material_layers:
            logger.debug("layered")
            # Multi-material wall
            for mat in material_layers:

                mat_ec_data = MaterialList.get(mat)
                thickness = layer_thicknesses.get(mat, None)
                if mat_ec_data is None:
                    raise NotImplementedError(f"Material '{mat}' not found in database")
                if thickness is None:
                    logger.warning(f"'{mat}' layer thickness not found, skipping EC calculation")
                    continue
                if thickness <= 0:
                    logger.warning(f"'{mat}' layer thickness <= 0, skipping EC calculation")
                    continue

                if current_area is None:
                    logger.warning(f"{mat} area not found, manually calculating.")

                ec_per_kg, density = mat_ec_data
                logger.debug(thickness)
                logger.debug(current_area)
                logger.debug(ec_per_kg)
                logger.debug(density)
                current_ec = ec_per_kg * density * (thickness/1000) * current_area
                logger.debug(f"EC for material '{mat}' in {stair.Name} is {current_ec}")
                total_ec += current_ec

        elif current_material:

            current_material_ec = MaterialList.get(current_material, None) if current_material else None

            if current_material_ec is None:
                # handle with default value?
                # ai?
                raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity
            logger.debug(f"EC for {stair.Name} is {current_ec}")
            total_ec += current_ec
        
        if current_ec is None:
            logger.warning(f"EC calculation for slab failed, attempting manual volume method")
            # Attempts to retrieve the "correct" material from material layer set. Works if able to filter down to one possible material.
            # Calculates EC using EC density * volume method.
            # Calculates volume from ifc geometry.
            
            MaterialList_filtered = [ material for material in material_layers if material not in MaterialsToIgnore]
            if len(MaterialList_filtered) != 1:
                logger.error(f"Unable to isolate to one material from material layer set. Skipping this slab {stair}") 
            if current_quantity is None:
                current_quantity = get_slab_volume(stair)
            current_material = MaterialList_filtered[0]
            logger.debug(f"Using material {current_material}")
            current_material_ec = MaterialList.get(current_material, None) if current_material else None
            if current_material_ec is None:
                # handle with default value?
                # ai?
                raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity
            logger.debug(f"EC for {stair.Name} is {current_ec}")
            total_ec += current_ec

    logger.debug(f"Total EC for stairs is {total_ec}")

    return total_ec

def calculate_embodied_carbon(filepath):
    ifc_file = ifcopenshell.open(filepath)

    columns = ifc_file.by_type('IfcColumn')
    logger.info(f"Total columns found {len(columns)}")

    beams = ifc_file.by_type('IfcBeam')
    logger.info(f"Total beams found {len(beams)}")

    slabs = ifc_file.by_type('IfcSlab')
    logger.info(f"Total slabs found {len(slabs)}")

    windows = ifc_file.by_type('IfcWindow')
    logger.info(f"Total windows found {len(windows)}")

    walls = ifc_file.by_type('IfcWall')
    logger.info(f"Total walls found {len(walls)}")

    doors = ifc_file.by_type('IfcDoor')
    logger.info(f"Total doors found {len(doors)}")

    stairs = ifc_file.by_type('IfcStairFlight') 
    logger.info(f"Total stairs found {len(stairs)}")

    total_ec = 0
    if columns:
        columns_ec= calculate_columns(columns)
        total_ec += columns_ec

    if beams:
        beams_ec= calculate_beams(beams)
        total_ec += beams_ec

    if slabs:
        slabs_ec= calculate_slabs(slabs)
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

    if stairs:
        stairs_ec = calculate_stairs(stairs)
        total_ec += stairs_ec
    logger.info(f"Total EC calculated: {total_ec}")

    total_area = 0
    for elements in [walls, slabs, columns,beams]:
        for element in elements:
            area = calculate_element_area(element)
            if area:
                total_area += area


    print(total_area)
    return total_ec

import os 


if __name__ == "__main__":
    ifcpath = os.path.join(r"C:\Users\dczqd\Documents\SUTD\Capstone-calc", "IFC Test model_Stairs 1.ifc")
    logger.info(f"{ifcpath=}")
    calculate_embodied_carbon(ifcpath)
