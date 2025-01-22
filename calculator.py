import ifcopenshell
from ifcopenshell.util.element import get_psets
from loguru import logger
import sys
MaterialList = {"Concrete, Cast In Situ": [0.090, 220] , "Concrete, Grade 25": [0.09, 220], "Concrete, General": [0.09,220]}  # kgCO2e per kg, kg per m^3 (Gen 1)

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

def calculate_walls(walls):

    total_ec = 0
    quantities = {}
    materials = []
    current_quantity = None
    current_material = None

    for wall in walls:

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

        logger.debug(f"EC for {wall.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for walls is {total_ec}")

    return total_ec

# TODO
# To wait for the ifc test file.
def calculate_windows():
    pass

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

    logger.info(f"Total EC calculated: {total_ec}")
    return total_ec

   


if __name__ == "__main__":
    calculate_embodied_carbon("Column&Beam 1.ifc")