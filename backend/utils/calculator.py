import ifcopenshell
from ifcopenshell.util.element import get_psets
from loguru import logger
import sys
import ifcopenshell
import ifcopenshell.geom
import numpy as np
from numpy import abs as np_abs
import os 

 # kgCO2e per kg, kg per m^3 (Gen 1)
MaterialList = {"Concrete, Cast In Situ": [0.103, 2350] , 
                "Concrete, Cast-in-Place gray": [0.103, 2350] , 
                "Concrete, C12/15": [0.097, 2350],
                "Concrete, Grade 40": [0.170, 2400], 
                "Concrete, Grade 20": [0.120,2350],
                "Concrete, Grade 25": [0.13, 2350], 
                "Concrete, Grade 20": [0.140, 2350],
                "Concrete, Grade 20": [0.140, 2350],
                "Concrete, C25/30": [0.119, 2350],
                "Concrete, General": [0.112,2350],
                "Concrete, Precast, Ordinary Portland Cement": [0.148, 2400],
                'Wood_aluminium fixed window 3-glass (SF 2010)' : 54.6, # kgCO2 per 1m^2
                'Wood_aluminium sidehung window 3-glass (SF 2010)' : 72.4,
                'M_Window-Casement-Double-Sidelight' : 86.830,
                'M_Window-Casement-Double-Sidelight' : 86.830,
                'Wooden doors T10-T25 with wooden frame' : 30.4,
                'Wooden doors T10-T25 with steel frame' : 49.4,
                'Aluminium, General': [13.100, 2700],
                'Tiles, Granite'	:[0.700,	2650],
                'Plywood':[0.910,	600],
                'Cross Laminated Timber':[-1.310,500],
                }  
MaterialsToIgnore  = ["Travertine","<Unnamed>"]
LOGGING_LEVEL = "DEBUG" 
logger.remove()  
logger.add(sys.stderr, level=LOGGING_LEVEL) 


def calculate_beams(beams):

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
                                logger.debug(f'Found NetVolume  for {beam.Name}: {quantity.VolumeValue}')
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
        if current_quantity is None:
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


    total_ec = 0
    quantities = {}
    materials = []
    current_quantity = None
    current_material = None
    rebar = None

    for column in columns:
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
            logger.debug(f"EC for {column.Name}'s rebars is {rebar_ec}")
            total_ec += rebar_ec
        
        
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

                            elif (quantity.is_a('IfcQuantityArea') and (quantity.Name == 'NetArea' or quantity.Name == 'GrossArea')) :
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
                    current_area = get_element_area(slab)
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
            print(mat_ec_data)
            print(current_volume)
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
            logger.error(f" {window.Name} Material '{current_material}' not found is not implemented yet")
            continue
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
        if hasattr(roof, "IsDecomposedBy"):
            for rel in roof.IsDecomposedBy:
                if rel.is_a("IfcRelAggregates"):
                    for slab in rel.RelatedObjects:
                        if slab.is_a("IfcSlab"):
                            #print(f"Found Slab: {slab.Name}")
                            slabs.append(slab)
        
        for slab in slabs:
            layer_thicknesses = {}
            material_layers = []
            current_area = None
            current_ec = None
            current_quantity = None
            current_material = None
            roof_ec = 0
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
                                elif quantity.is_a('IfcQuantityArea') and (quantity.Name == 'NetSideArea' or quantity.Name == 'GrossArea'):
                                    logger.debug(f'Found NetSideArea for {slab.Name}: {quantity.AreaValue}')
                                    current_area = quantity.AreaValue
                                                                    
                                # For single material
                                elif quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                    logger.debug(f'Found NetVolume for {slab.Name}: {quantity.VolumeValue / len(slabs)}')
                                    #quantities[quantity.Name] = quantity.VolumeValue
                                    current_volume = quantity.VolumeValue / len(slabs)                            

            if hasattr(slab, "HasAssociations"):
                for association in slab.HasAssociations:
                    if association.is_a("IfcRelAssociatesMaterial"):
                        material = association.RelatingMaterial
                        if material.is_a("IfcMaterial"):
                            logger.debug(f"Found material '{material.Name}', as IfcMaterial")
                            current_material = material.Name
                        elif material.is_a("IfcMaterialConstituentSet"):
                            for layer in material.MaterialConstituents:
                                print("Constituent\n")
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
                        current_area = get_element_area(slab)
                        logger.warning(f"{mat} area not found, manually calculating.")

                    ec_per_kg, density = mat_ec_data
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
                current_ec = material_ec_perkg * material_density * current_volume
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
                slab_ec = material_ec_perkg * material_density * current_quantity
                roof_ec += slab_ec

        logger.debug(f"EC for {roof.Name} is {roof_ec}")
        total_ec += roof_ec
    
    logger.debug(f"Total EC for roofs is {total_ec}")

    return total_ec



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
            print(current_material_ec)
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

# def calculate_curtainwalls(curtainwalls):

#     total_ec = 0
#     materials = []
#     current_quantity = 1
#     current_material = None

#     for curtainwall in curtainwalls:
#         curtainwalls = []
#         if hasattr(curtainwall, "IsDecomposedBy"):
#             for rel in curtainwall.IsDecomposedBy:
#                 logger.debug(rel)
#                 if rel.is_a("IfcRelAggregates"):
#                     for curtainwall in rel.RelatedObjects:
#                         if curtainwall.is_a("IfcCurtainWall"):
#                             print(f"Found curtain wall: {curtainwall.Name}")
#                             curtainwalls.append(curtainwall)
                            
#         for curtainwall in curtainwalls:
#             if hasattr(curtainwall, "IsDefinedBy"):
#                 for definition in curtainwall.IsDefinedBy:
#                     if definition.is_a('IfcRelDefinesByProperties'):
#                         property_def = definition.RelatingPropertyDefinition
#                         if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_CurtainWallQuantities':
#                             for quantity in property_def.Quantities:
#                                 logger.debug(quantity)
#                                 if quantity.is_a('IfcQuantityLength') and quantity.Name == 'Height':
#                                     logger.debug(f'Found Height for {curtainwall.Name}: {quantity.LengthValue}')
#                                     current_quantity *= (quantity.LengthValue/1000)
#                                 if quantity.is_a('IfcQuantityLength') and quantity.Name == 'Length':
#                                     logger.debug(f'Found Length for {curtainwall.Name}: {quantity.LengthValue}')
#                                     current_quantity *= (quantity.LengthValue/1000)
#                                 if quantity.is_a('IfcQuantityLength') and quantity.Name == 'Width':
#                                     logger.debug(f'Found Width for {curtainwall.Name}: {quantity.LengthValue}')
#                                     current_quantity *= (quantity.LengthValue/1000)
#                             if current_quantity is not None:
#                                 break
#             logger.debug(f"Volume for {curtainwall.Name}: {current_quantity}")
#             if hasattr(curtainwall, "HasAssociations"):
#                 for association in curtainwall.HasAssociations:
#                     if association.is_a("IfcRelAssociatesMaterial"):
#                         material = association.RelatingMaterial
#                         if material.is_a("IfcMaterial"):
#                             logger.debug(f"Found material '{material.Name}', as IfcMaterial")
#                             current_material = material.Name

#             current_material_ec = MaterialList.get(current_material, None) if current_material else None

#             if current_material_ec is None:
#                 # handle with default value?
#                 # ai?
#                 raise NotImplementedError(f"Material '{current_material}' not found is not implemented yet")
            
#             material_ec_perkg, material_density = current_material_ec
#             current_ec = material_ec_perkg  * material_density *  current_quantity 

#             logger.debug(f"EC for {curtainwall.Name} is {current_ec}")
#             total_ec += current_ec
    
#     logger.debug(f"Total EC for curtainwalls is {total_ec}")

#     return total_ec
#     pass

def calculate_members(members):
    total_ec = 0
    materials = []
    current_quantity = None
    current_material = None

    for member in members:
        if hasattr(member, "IsDefinedBy"):
            for definition in member.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_MemberBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume  for {member.Name}: {quantity.VolumeValue}')
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        if hasattr(member, "HasAssociations"):
            for association in member.HasAssociations:
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
        current_ec = material_ec_perkg * material_density * current_quantity

        logger.debug(f"EC for {member.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for members is {total_ec}")

    return total_ec          

def calculate_plates(plates):
    total_ec = 0
    materials = []
    current_quantity = None
    current_material = None

    for plate in plates:
        if hasattr(plate, "IsDefinedBy"):
            for definition in plate.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_PlateBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                logger.debug(f'Found NetVolume  for {plate.Name}: {quantity.VolumeValue}')
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        if hasattr(plate, "HasAssociations"):
            for association in plate.HasAssociations:
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
        current_ec = material_ec_perkg * material_density * current_quantity

        logger.debug(f"EC for {plate.Name} is {current_ec}")
        total_ec += current_ec
    
    logger.debug(f"Total EC for plates is {total_ec}")

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
    
    # curtainwalls = ifc_file.by_type('IfcCurtainWall')
    # logger.info(f"Total curtainwalls found {len(curtainwalls)}")
    
    members = ifc_file.by_type('IfcMember')
    logger.info(f"Total members found {len(members)}")

    plates = ifc_file.by_type('IfcPlate')
    logger.info(f"Total plates found {len(plates)}")


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
    # if curtainwalls:
    #     curtainwalls_ec = calculate_curtainwalls(curtainwalls)
    #     total_ec += curtainwalls_ec
    
    if members:
        members_ec = calculate_members(members)
        total_ec += members_ec
    
    if plates:
        plates_ec = calculate_plates(plates)
        total_ec += plates_ec
    
    
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
        # total_area += get_element_area(space)
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


    return total_ec

import os 

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
        # total_area += get_element_area(space)
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
    ifcpath = "/Users/jk/Downloads/z. Complex Models/Complex 2.ifc"
    logger.info(f"{ifcpath=}")
    calculate_embodied_carbon(ifcpath)
    calculate_gfa(ifcpath)