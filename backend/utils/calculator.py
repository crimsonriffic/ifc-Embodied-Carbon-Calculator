import ifcopenshell
from ifcopenshell.util.element import get_psets
from loguru import logger
import sys
MaterialList = {"Concrete, Cast In Situ": [0.103, 2350] , "Concrete, Cast-in-Place gray": [0.103, 2350] , "Concrete, Grade 40": [0.170, 2400], "Concrete, Grade 25": [0.13, 2350], "Concrete, General": [0.112,2350],"Concrete, Precast, Ordinary Portland Cement": [0.148,2400], # kgCO2e per kg, kg per m^3 (Gen 1)
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

def calculate_slabs(slabs):

    total_ec = 0
    quantities = {}
    materials = []
    current_quantity = None
    current_material = None

    for slab in slabs:

        if hasattr(slab, "IsDefinedBy"):
            for definition in slab.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_SlabBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
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
                        #logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                        materials.append(material.Name)
                        current_material = material.Name
                        break
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            #logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage")
                            materials.append(layer.Material.Name)
                            current_material = material.Name
                            break
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            #logger.debug(f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet")
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
                                #logger.info(f"{element} has area: {quantity.AreaValue}")
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
        slabs_ec= calculate_slabs(slabs)
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

