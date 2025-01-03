#!/usr/bin/env python3

import ifcopenshell

# From ICE database
MaterialList = {"Concrete, Cast In Situ": [0.090, 220]} #kgCO2e per kg, kg per m^3 (Gen 1)

def get_quantities(element_quantity):
    quantities = {}
    for quantity in element_quantity.Quantities:
        if quantity.is_a('IfcQuantityLength'):
            quantities[quantity.Name] = quantity.LengthValue
        elif quantity.is_a('IfcQuantityArea'):
            quantities[quantity.Name] = quantity.AreaValue
        elif quantity.is_a('IfcQuantityVolume'):
            quantities[quantity.Name] = quantity.VolumeValue
    return quantities

if __name__ == '__main__':
    ifc_file = ifcopenshell.open('/Users/jk/Downloads/20241128 Wall Slab Cat 1 (Non-generic v3).ifc')

    # Select the first wall element as an example (or choose any element type you need)
    walls = ifc_file.by_type('IfcWall')
    slabs = ifc_file.by_type('IfcSlab')
    slab = slabs[0]
    totalEC = 0
    materials =[]
    quantities = {}

    # Wall
    for element in walls:
        if hasattr(element, "IsDefinedBy"):
            for definition in element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    #print(property_def)
                    if property_def.is_a('IfcElementQuantity'):
                        if property_def.Name == 'Qto_WallBaseQuantities':
                                for quantity in property_def.Quantities:
                                    # if quantity.is_a('IfcQuantityLength'):
                                    #     quantities[quantity.Name] = quantity.LengthValue
                                    # elif quantity.is_a('IfcQuantityArea'):
                                    #     quantities[quantity.Name] = quantity.AreaValue
                                    if quantity.is_a('IfcQuantityVolume'):
                                        #print("NetVolume")
                                        if quantity.Name == 'NetVolume':
                                            quantities[quantity.Name] = quantity.VolumeValue
                                            
                
        if hasattr(element, "HasAssociations"): # Material
            #print("Has Associations")
            for association in element.HasAssociations: 
                #print(association)
                if association.is_a("IfcRelAssociatesMaterial"):
                    #print("Has associateMaterial")
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        materials.append(material.Name)
                        #print("IfcMaterial")
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            materials.append(layer.Material.Name)
                            #print("IfcMaterialLayer")
                    elif material.is_a("IfcMaterialLayerSet"):
                        #print("IfcMaterialLayerSet")
                        for layer in material.MaterialLayers:
                            materials.append(layer.Material.Name)
        
    # print(quantities)
    # print(materials)

    wallEC = 0
    for i in range(len(materials)):
        if materials[i] in MaterialList:
            wallEC += (quantities["NetVolume"] * MaterialList[materials[i]][0] * MaterialList[materials[i]][1])
    print("Total EC for Walls is: {0}".format(wallEC))
    totalEC += wallEC
    
    materials = []
    quantities = {}
    
    # Slab    
    for slab in slabs:
        if hasattr(slab, "IsDefinedBy"):
            for definition in slab.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    #print(property_def)
                    if property_def.is_a('IfcElementQuantity'):
                        if property_def.Name == 'Qto_SlabBaseQuantities':
                                for quantity in property_def.Quantities:
                                    # if quantity.is_a('IfcQuantityLength'):
                                    #     quantities[quantity.Name] = quantity.LengthValue
                                    if quantity.is_a('IfcQuantityVolume'):
                                        if quantity.Name == "NetVolume":
                                            quantities[quantity.Name] = quantity.VolumeValue
                                    # elif quantity.is_a('IfcQuantityVolume'):
                                    #     quantities[quantity.Name] = quantity.VolumeValue
                                        
        if hasattr(slab, "HasAssociations"): # slab
            #print("Has Associations")
            for association in slab.HasAssociations: 
                #print(association)
                if association.is_a("IfcRelAssociatesMaterial"):
                    #print("Has associateMaterial")
                    material = association.RelatingMaterial
                    #print(material.is_a)
                    if material.is_a("IfcMaterial"):
                        materials.append(material.Name)
                        #print("IfcMaterial")
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            materials.append(layer.Material.Name)
                            #print("IfcMaterialLayer")
                    elif material.is_a("IfcMaterialLayerSet"):
                        #print("IfcMaterialLayerSet")
                        for layer in material.MaterialLayers:
                            materials.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            materials.append(layer.Name)
                    
    # print(quantities)
    # print(materials)
    
    slabEC = 0
    for i in range(len(materials)):
        if materials[i] in MaterialList:
            slabEC += (quantities["NetVolume"] * MaterialList[materials[i]][0] * MaterialList[materials[i]][1])
    
    print("Total EC for Slabs is: {0}".format(slabEC))
    totalEC += slabEC
    print("Total EC for all entities is: {0}".format(totalEC))


    # for definition in element.HasAssociations:
    #     if definition.is_a("IfcRelAssociates"):
    #         print(definition.RelatedObjects)
    
    # for definition in element.IsDefinedBy:
    #     print("\nDefinition:", definition)
    #     print("\nDefinition attributes:", dir(definition))
    
    # for element in walls:
        
        # Explore element.IsDefinedBy and definition structures
        # print("\nIsDefinedBy structure:", element.IsDefinedBy)
        # for definition in element.IsDefinedBy:
        #     print("\nDefinition:", definition)
        #     print("\nDefinition attributes:", dir(definition))
        #     if definition.is_a('IfcRelDefinesByProperties'):
        #         related_data = definition.RelatingPropertyDefinition
        #         print("\nrelated_data:", definition.RelatingPropertyDefinition)
        #         if related_data.is_a('IfcElementQuantity'):
        #             if related_data.Name == 'BaseQuantities':
        #                 print("\nrelated_data.Name", related_data.Name)
        #                 print("\nquantities", get_quantities(related_data))
