#!/usr/bin/env python3

import ifcopenshell

# From ICE database
Materials = {"Concrete, Cast In Situ": [0.090, 220]} #kgCO2e per kg, kg per m^3 (Gen 1)

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
    ifc_file = ifcopenshell.open('/Users/jk/Downloads/20241125 Wall Slab Cat 1-2.ifc')

    # Select the first wall element as an example (or choose any element type you need)
    walls = ifc_file.by_type('IfcWall')
    element = walls[0]
    materials =[]
    quantities = {}

    
    if hasattr(element, "IsDefinedBy"):
        for definition in element.IsDefinedBy:
            if definition.is_a('IfcRelDefinesByProperties'):
                property_def = definition.RelatingPropertyDefinition
                print(property_def)
                if property_def.is_a('IfcElementQuantity'):
                    if property_def.Name == 'Qto_WallBaseQuantities':
                            for quantity in property_def.Quantities:
                                if quantity.is_a('IfcQuantityLength'):
                                    quantities[quantity.Name] = quantity.LengthValue
                                elif quantity.is_a('IfcQuantityArea'):
                                    quantities[quantity.Name] = quantity.AreaValue
                                elif quantity.is_a('IfcQuantityVolume'):
                                    quantities[quantity.Name] = quantity.VolumeValue
            
    if hasattr(element, "HasAssociations"): # Material
        print("Has Associations")
        for association in element.HasAssociations: 
            print(association)
            if association.is_a("IfcRelAssociatesMaterial"):
                print("Has associateMaterial")
                material = association.RelatingMaterial
                if material.is_a("IfcMaterial"):
                    materials.append(material.Name)
                    print("IfcMaterial")
                elif material.is_a("IfcMaterialLayerSetUsage"):
                    for layer in material.ForLayerSet.MaterialLayers:
                        materials.append(layer.Material.Name)
                        print("IfcMaterialLayer")
                elif material.is_a("IfcMaterialLayerSet"):
                    print("IfcMaterialLayerSet")
                    for layer in material.MaterialLayers:
                        materials.append(layer.Material.Name)
    
    print(quantities)
    print(materials)

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
