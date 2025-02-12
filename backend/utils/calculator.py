import ifcopenshell
from ifcopenshell.util.element import get_psets
from loguru import logger
import sys
import ifcopenshell
import ifcopenshell.geom
import numpy as np
from numpy import abs as np_abs

 # kgCO2e per kg, kg per m^3 (Gen 1)
MaterialList = {"Concrete, Cast In Situ": [0.103, 2350] , 
                "Concrete, Cast-in-Place gray": [0.103, 2350] , 
                "Concrete, C12/15": [0.097, 2350],
                "Concrete, Grade 40": [0.170, 2400], 
                "Concrete, Grade 25": [0.13, 2350], 
                "Concrete, C25/30": [0.119, 2350],
                "Concrete, General": [0.112,2350],
                "Concrete, Precast, Ordinary Portland Cement": [0.148, 2400],
                'Wood_aluminium fixed window 3-glass (SF 2010)' : 54.6, # kgCO2 per 1m^2
                'Wood_aluminium sidehung window 3-glass (SF 2010)' : 72.4,
                'Wooden doors T10-T25 with wooden frame' : 30.4,
                'Wooden doors T10-T25 with steel frame' : 49.4,
                'Aluminium, General': [13.100, 2700],
                'Tiles, Granite'	:[0.700,	2650],
                'Plywood':[0.910,	600]
                }  
MaterialsToIgnore  = ["Travertine","<Unnamed>"]
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
                                    # logger.debug(sub_quantity.LengthValue)
                                    layer_thicknesses[quantity.Name] = sub_quantity.LengthValue

                            elif quantity.is_a('IfcQuantityArea') and quantity.Name == 'NetArea':
                                logger.debug(f'Found NetArea for {slab.Name}')
                                current_area = quantity.AreaValue

                            elif quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
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
                        material_layers.append(material.Name)
                        #logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        materials.append(material.Name)
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
                if thickness is None:
                    logger.warning(f"'{mat}' layer thickness not found, skipping EC calculation")
                    continue
                if thickness <= 0:
                    logger.warning(f"'{mat}' layer thickness <= 0, skipping EC calculation")
                    continue
                if mat_ec_data is None and mat not in MaterialsToIgnore:
                    raise NotImplementedError(f"Material '{mat}' not found in database")

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
                current_quantity = get_element_volume(slab)
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
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                #logger.debug(f'Found NetVolume  for {wall.Name}')
                                quantities[quantity.Name] = quantity.VolumeValue
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        if hasattr(wall, "HasAssociations"):
            for association in wall.HasAssociations:
                #
                #print(association)
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    #print(material)
                    if material.is_a("IfcMaterial"):
                        #logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        materials.append(material.Name)
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
                        break
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            #logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                            materials.append(layer.Material.Name)
                            current_material = layer.Material.Name
                            break
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            #logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
                            materials.append(layer.Material.Name)
                            current_material = layer.Material.Name
                            break

        current_material_ec = MaterialList.get(current_material, None) if current_material else None

        if current_material_ec is None:
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
                    

def calculate_roofs(roofs):

    total_ec = 0
    quantities = {}
    materials = []
    slabs = []

    for roof in roofs:
        current_ec = 0
        current_quantity = None
        current_material = None
        if hasattr(roof, "IsDecomposedBy"):
            for rel in roof.IsDecomposedBy:
                if rel.is_a("IfcRelAggregates"):
                    for slab in rel.RelatedObjects:
                        if slab.is_a("IfcSlab"):
                            #print(f"Found Slab: {slab.Name}")
                            slabs.append(slab)
        
        for slab in slabs:
            if hasattr(slab, "IsDefinedBy"):
                for definition in slab.IsDefinedBy:
                    #logger.debug(definition)
                    if definition.is_a('IfcRelDefinesByProperties'):
                        property_def = definition.RelatingPropertyDefinition
                        if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_SlabBaseQuantities':
                            for quantity in property_def.Quantities:
                                if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                    volume = quantity.VolumeValue / len(slabs)
                                    logger.debug(f'Found NetVolume  for {roof.Name}: {volume}')
                                    quantities[quantity.Name] = volume
                                    current_quantity = volume
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
            slab_ec = material_ec_perkg * material_density * current_quantity
            current_ec += slab_ec

        logger.debug(f"EC for {roof.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for roofs is {total_ec}")

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
                                ## logger.info(f"{element} has area: {quantity.AreaValue}")
                                area += quantity.AreaValue
    
    return area

## Substructure elements - Level 0 
def get_elements_on_storey(ifc_file_path, storey_name="Level 0"): 
    """ Returns all elements associated with a given storey name. """
    model = ifcopenshell.open(ifc_file_path)
    
    # Find the target storey
    storeys = model.by_type("IfcBuildingStorey")
    target_storey = next((s for s in storeys if s.Name == storey_name), None)
    
    if not target_storey:
        logger.warning(f"Storey '{storey_name}' not found.")
        return []

    # Collect elements assigned to this storey
    elements = []
    for rel in model.by_type("IfcRelContainedInSpatialStructure"):
        if rel.RelatingStructure == target_storey:
            for elem in rel.RelatedElements:
                elements.append(elem)
                elements.extend(get_nested_elements(elem))  # Get nested elements

    logger.info(f"Total elements found on {storey_name}: {len(elements)}")
    logger.info(f"Elements found in {storey_name}: {[e.is_a() for e in elements]}")
    return elements

def calculate_substructure_ec(filepath):
    ## Calcuate the embodied carbon for elements on level 0 
    elements = get_elements_on_storey(filepath, "Level 0")
    if not elements:
        logger.warning("No elements found on Level 0")
        return 0 
    total_ec = 0 
    for element in elements: 
        if element.is_a("IfcSlab"):
            total_ec += calculate_slabs([element])
        elif element.is_a("IfcWall"):
            total_ec += calculate_walls([element])
        elif element.is_a("IfcColumn"):
            total_ec += calculate_columns([element])
        elif element.is_a("IfcBeam"):
            total_ec += calculate_beams([element])
    logger.info(f"Total Embodied Carbon for Substructure (Level 0): {total_ec}")
    return total_ec
    
def calculate_superstructure_ec(filepath):
    ## Calculate the embodied carbon for elements on Level 1 and above (superstructure)
    total_ec = 0
    superstructure_slabs = set()
    model = ifcopenshell.open(filepath)
    
    storeys = model.by_type("IfcBuildingStorey")
    superstructure_levels = [s for s in storeys if s.Name != "Level 0"]

    if not superstructure_levels:
        logger.warning("No levels found above Level 0.")
        return 0

    for storey in superstructure_levels:
        elements = get_elements_on_storey(filepath, storey.Name)

        for element in elements:
            if element.is_a("IfcSlab"):
                superstructure_slabs.add(element.GlobalId)  # Track slabs
                total_ec += calculate_slabs([element])
            elif element.is_a("IfcWall"):
                total_ec += calculate_walls([element])
            elif element.is_a("IfcColumn"):
                total_ec += calculate_columns([element])
            elif element.is_a("IfcBeam"):
                total_ec += calculate_beams([element])
    
    logger.info(f"Total Embodied Carbon for Superstructure (Level 1+): {total_ec}")
    
    return total_ec

def check_slab_assignments(filepath):
    """ Checks where each slab is assigned (or unassigned) """
    model = ifcopenshell.open(filepath)
    storeys = model.by_type("IfcBuildingStorey")

    slab_storey_map = {}
    for storey in storeys:
        elements = get_elements_on_storey(filepath, storey.Name)
        for element in elements:
            if element.is_a("IfcSlab"):
                slab_storey_map[element.GlobalId] = storey.Name

    # Print all slabs and their assigned storey
    logger.info("✅ Checking slab assignments:")
    for slab in model.by_type("IfcSlab"):
        storey = slab_storey_map.get(slab.GlobalId, "❌ Unassigned")
        logger.info(f"  🏗 Slab {slab.GlobalId} -> {storey}")

def check_roof_hierarchy(filepath):
    model = ifcopenshell.open(filepath)
    for roof in model.by_type("IfcRoof"):
        logger.info(f"🏠 Roof found: {roof.Name}, ID: {roof.GlobalId}")
        for rel in model.by_type("IfcRelAggregates"):
            if rel.RelatingObject == roof:
                logger.info(f"  🔄 Aggregated elements: {[e.is_a() for e in rel.RelatedObjects]}")

## Calculating embodied carbon for all elements (successful) 

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
                if thickness is None:
                    logger.warning(f"'{mat}' layer thickness not found, skipping EC calculation")
                    continue
                if thickness <= 0:
                    logger.warning(f"'{mat}' layer thickness <= 0, skipping EC calculation")
                    continue
                if mat_ec_data is None and mat not in MaterialsToIgnore:
                    raise NotImplementedError(f"Material '{mat}' not found in database")

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
            logger.warning(f"EC calculation for stair failed, attempting manual volume method")
            # Attempts to retrieve the "correct" material from material layer set. Works if able to filter down to one possible material.
            # Calculates EC using EC density * volume method.
            # Calculates volume from ifc geometry.
            
            MaterialList_filtered = [ material for material in material_layers if material not in MaterialsToIgnore]
            if len(MaterialList_filtered) != 1:
                logger.error(f"Unable to isolate to one material from material layer set. Skipping this stair {stair}") 
            if current_quantity is None:
                current_quantity = get_element_volume(stair)
            current_material = MaterialList_filtered[0]
            logger.debug(f"Using material {current_material} with volume {current_quantity}")
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

def calculate_railings(railings):
    total_ec = 0
    material_layers = []

    for railing in railings:
        current_quantity = None
        current_material = None
        current_area = None
        current_ec = None
        layer_thicknesses = {}
        material_layers = []


        if hasattr(railing, "HasAssociations"):
            for association in railing.HasAssociations:
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

        if current_ec is None:
            # Attempts to retrieve the "correct" material from material layer set. Works if able to filter down to one possible material.
            # Calculates EC using EC density * volume method.
            # Calculates volume from ifc geometry.
            
            MaterialList_filtered = [ material for material in material_layers if material not in MaterialsToIgnore]
            if len(MaterialList_filtered) != 1:
                logger.error(f"Unable to isolate to one material from material layer set. Skipping this railing {railing}") 
            if current_quantity is None:
                current_quantity = get_element_volume(railing)
            current_material = MaterialList_filtered[0]
            logger.debug(f"Using material {current_material}")
            current_material_ec = MaterialList.get(current_material, None) if current_material else None
            if current_material_ec is None:
                # handle with default value?
                # ai?
                raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity
            logger.debug(f"EC for {railing.Name} is {current_ec}")
            total_ec += current_ec

    logger.debug(f"Total EC for railings is {total_ec}")

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

    if roofs:
        for roof in roofs:
            aggregated_by = roof.IsDecomposedBy
            for rel in aggregated_by:
                if rel.is_a('IfcRelAggregates'):
                    print(rel)
                    for part in rel.RelatedObjects:
                        print(f"child : {part.is_a()}")
                        if part.is_a('IfcSlab'):
                            slabs_to_ignore.append(part.id())
                    
    # print(slabs_to_ignore)

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
    logger.info(f"Total EC calculated: {total_ec}")


    # total_area = 0
    # for elements in [walls, slabs, columns,beams]:
    #     for element in elements:
    #         area = calculate_element_area(element)
    #         if area:
    #             total_area += area
    # print(total_area)

    total_area = 0
    for elements in [walls, slabs, columns,beams]:
        for element in elements:
            area = calculate_element_area(element)
            if area:
                total_area += area


    print("Total area calculated: ",total_area)
    return total_ec
def get_nested_elements(element):
    """ Recursively get nested elements inside an aggregated structure """
    nested_elements = []
    for rel in element.IsDecomposedBy:
        if rel.is_a("IfcRelAggregates"):
            nested_elements.extend(rel.RelatedObjects)
            for sub_element in rel.RelatedObjects:
                nested_elements.extend(get_nested_elements(sub_element))
    return nested_elements

# def calculate_embodied_carbon(filepath):
#     """ Calculates total embodied carbon for the entire model """
#     model = ifcopenshell.open(filepath)

#     total_ec = 0
#     categories = {
#         "IfcColumn": calculate_columns,
#         "IfcBeam": calculate_beams,
#         "IfcSlab": calculate_slabs,
#         "IfcWall": calculate_walls,
#         "IfcWindow": calculate_windows
#     }

#     for category, function in categories.items():
#         elements = model.by_type(category)
#         logger.info(f"Total {category} found: {len(elements)}")
#         if elements:
#             total_ec += function(elements)

#     logger.info(f"Total EC for entire model: {total_ec}")
#     return total_ec

import os 


if __name__ == "__main__":
    #ifcpath = os.path.join(r"C:\Users\dczqd\Documents\SUTD\Capstone-calc", "Window 1.ifc")
    ifcpath = os.path.join(r"C:\Users\Carina\Downloads", "Complex 1.ifc")
    logger.info(f"{ifcpath=}")
    #calculate_embodied_carbon(ifcpath)
        
    #calculate_substructure_ec(ifcpath)
    #calculate_superstructure_ec(ifcpath)
    sub_ec = calculate_substructure_ec(ifcpath)
    super_ec = calculate_superstructure_ec(ifcpath)
    #check_slab_assignments(ifcpath)
    #check_roof_hierarchy(ifcpath)
    total_ec = calculate_embodied_carbon(ifcpath)

    logger.info(f"Validation: Substructure EC + Superstructure EC = {sub_ec + super_ec}, Total EC = {total_ec}")
    
    #if abs((sub_ec + super_ec) - total_ec) > 1e-6:  # Allow small floating point differences
    #    logger.warning("Mismatch detected in EC calculations!")

