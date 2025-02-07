import ifcopenshell
from ifcopenshell.util.element import get_psets
from loguru import logger
import sys
MaterialList = {"Concrete, Cast In Situ": [0.103, 2350] , "Concrete, Cast-in-Place gray": [0.103, 2350] , "Concrete, Grade 40": [0.170, 2400], "Concrete, Grade 25": [0.13, 2350], "Concrete, General": [0.112,2350], "Concrete, Precast, Ordinary Portland Cement": [0.148, 2400],  # kgCO2e per kg, kg per m^3 (Gen 1)
                'Wood_aluminium fixed window 3-glass (SF 2010)' : 54.6, # kgCO2 per 1m^2
                'Wood_aluminium sidehung window 3-glass (SF 2010)' : 72.4,
                'Wooden doors T10-T25 with wooden frame' : 30.4,
                'Wooden doors T10-T25 with steel frame' : 49.4,
                }  

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
                                logger.debug(f'Found NetVolume  for {beam.Name}: {quantity.VolumeValue}')
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

def calculate_slabs(slabs, to_ignore=[]):

    total_ec = 0
    quantities = {}
    materials = []

    for slab in slabs:
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
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume  for {slab.Name}: {quantity.VolumeValue}')
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

        logger.debug(f"EC for {slab.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for slabs is {total_ec}")

    return total_ec
def calculate_windows(windows):

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

        logger.debug(f"EC for {window.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for windows is {total_ec}")

    return total_ec
def calculate_walls(walls):

    total_ec = 0
    #quantities = {}
    #materials = []
    
    for wall in walls:
        current_volume = None
        current_material = None
        layer_area = None
        layer_thicknesses = {}
        layer_materials = []
        
        if hasattr(wall, "IsDefinedBy"):
            for definition in wall.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_WallBaseQuantities':
                        for quantity in property_def.Quantities:
                            logger.debug(quantity)
                            # logger.debug(quantity.Name)
                            # For material constituent
                            if quantity.Name in MaterialList.keys(): 
                                for sub_quantity in quantity.HasQuantities:
                                    logger.debug(f'Found subquantity {sub_quantity.Name} for {quantity.Name}: {sub_quantity.LengthValue}')
                                    # logger.debug(sub_quantity.LengthValue)
                                    layer_thicknesses[quantity.Name] = sub_quantity.LengthValue
                            elif quantity.is_a('IfcQuantityArea') and quantity.Name == 'NetSideArea':
                                logger.debug(f'Found NetSideArea for {wall.Name}')
                                current_area = quantity.AreaValue
                                                                
                            # For single material
                            elif quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume for {wall.Name}')
                                #quantities[quantity.Name] = quantity.VolumeValue
                                current_volume = quantity.VolumeValue                            

        if hasattr(wall, "HasAssociations"):
            for association in wall.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        current_material = material.Name
                        #materials.append(material.Name)
                    # elif material.is_a("IfcMaterialLayerSetUsage"):
                    #     for layer in material.ForLayerSet.MaterialLayers:
                    #         logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                    #         materials.append(layer.Material.Name)
                    #         current_material = material.Name
                    # elif material.is_a("IfcMaterialLayerSet"):
                    #     for layer in material.MaterialLayers:
                    #         logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
                    #         materials.append(layer.Material.Name)
                    #         current_material = layer.Material.Name
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            print("Constituent\n")
                            logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialConstituent")
                            layer_materials.append(layer.Material.Name)

        if layer_materials:
            logger.debug("layered")
            # Multi-material wall
            for mat in layer_materials:
                mat_ec_data = MaterialList.get(mat)
                thickness = layer_thicknesses.get(mat, 0)

                if mat_ec_data and thickness > 0:
                    ec_per_kg, density = mat_ec_data
                    logger.debug(thickness)
                    logger.debug(current_area)
                    logger.debug(ec_per_kg)
                    logger.debug(density)
                    current_ec = ec_per_kg * density * (thickness/1000) * current_area
                    logger.debug(f"EC for material '{mat}' in {wall.Name} is {current_ec}")
                    total_ec += current_ec
                else:
                    raise NotImplementedError(f"Material '{mat}' or thickness not properly defined")
        elif current_material:
            # Single-material wall
            mat_ec_data = MaterialList.get(current_material)
            if mat_ec_data and current_volume:
                ec_per_kg, density = mat_ec_data
                current_ec = ec_per_kg * density * current_volume
                logger.debug(f"EC for {wall.Name} is {current_ec}")
                total_ec += current_ec
            else:
                raise NotImplementedError(f"Material '{current_material}' or quantity not properly defined")

        if current_ec is None:
            # handle with default value?
            # ai?
            raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
        
    logger.debug(f"Total EC for walls is {total_ec}")

    return total_ec

# TODO
# To wait for the ifc test file.
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
                                logger.info(f"{element} has area: {quantity.AreaValue}")
                                area += quantity.AreaValue
    
    return area

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

    aggregated_by = roofs[0].IsDecomposedBy
    for rel in aggregated_by:
        if rel.is_a('IfcRelAggregates'):
            print(rel)
            for part in rel.RelatedObjects:
                print(f"child : {part.is_a()}")
                if part.is_a('IfcSlab'):
                    slabs_to_ignore.append(part.id())
                    
    print(slabs_to_ignore)
    windows = ifc_file.by_type('IfcWindow')
    logger.info(f"Total windows found {len(windows)}")

    walls = ifc_file.by_type('IfcWall')
    logger.info(f"Total walls found {len(walls)}")

    # stairs = ifc_file.by_type('IfcStairFlight') # or IfcStair?
    # logger.info(f"Total stairs found {len(stairs)}")

    total_ec = 0
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
    ifcpath = "/Users/jk/Downloads/z. Complex Models/Complex 1.ifc"
    logger.info(f"{ifcpath=}")
    calculate_embodied_carbon(ifcpath)
