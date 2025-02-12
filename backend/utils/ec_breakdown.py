import os
import ifcopenshell
from ifcopenshell.util.element import get_psets
from loguru import logger
import sys
import ifcopenshell
import ifcopenshell.geom
import numpy as np
from numpy import abs as np_abs

from calculator import calculate_beams, calculate_columns, calculate_doors, calculate_embodied_carbon, calculate_railings, calculate_slabs, calculate_stairs, calculate_walls,calculate_roofs, calculate_windows

## EC Breakdown by building system substructure and superstructure 
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

    logger.info(f"Total elements found on {storey_name}: {len(elements)}")
    logger.info(f"Elements found in {storey_name}: {[e.is_a() for e in elements]}")
    return elements


def calculate_substructure_ec(filepath):
    ## Calcuate the embodied carbon for elements on level 0 
    elements = get_elements_on_storey(filepath, "Level 0")
    if not elements:
        logger.warning("No elements found on Level 0")
        return 0 
    substructure_ec=calculate_elements_ec(elements)
    logger.info(f"Total Embodied Carbon for Substructure (Level 0): {substructure_ec}")
    return substructure_ec
    
def calculate_superstructure_ec(filepath):
    ## Calculate the embodied carbon for elements on Level 1 and above (superstructure)
    total_ec = 0
    superstructure_slabs = set()
    slabs_to_ignore=set()
    model = ifcopenshell.open(filepath)
    
    storeys = model.by_type("IfcBuildingStorey")
    superstructure_levels = [s for s in storeys if s.Name != "Level 0"]

    if not superstructure_levels:
        logger.warning("No levels found above Level 0.")
        return 0

    # Identify slabs that belong to roofs
    roofs = model.by_type("IfcRoof")
    for roof in roofs:
        aggregated_by = roof.IsDecomposedBy
        for rel in aggregated_by:
            if rel.is_a("IfcRelAggregates"):
                for part in rel.RelatedObjects:
                    if part.is_a("IfcSlab"):
                        slabs_to_ignore.add(part.GlobalId)  # Track slabs inside roofs

    for storey in superstructure_levels:
        elements = get_elements_on_storey(filepath, storey.Name)
        superstructure_ec = calculate_elements_ec(elements,slabs_to_ignore)

    
    logger.info(f"Total Embodied Carbon for Superstructure (Level 1+): {superstructure_ec}")
    
    return superstructure_ec

## Calculate EC, given elements 
def calculate_elements_ec(elements, slabs_to_ignore=[] ,**kwargs):
   
    total_ec = 0
     # Dictionary of element types mapped to their EC calculation functions
    ec_functions = {
        "IfcColumn": calculate_columns,
        "IfcBeam": calculate_beams,
        "IfcSlab": lambda elements: calculate_slabs(elements, to_ignore=slabs_to_ignore),
        "IfcWall": calculate_walls,
        "IfcWindow": calculate_windows,
        "IfcDoor": calculate_doors,
        "IfcStairFlight": calculate_stairs,
        "IfcRailing": calculate_railings,
        "IfcRoof": calculate_roofs,
    }

    for element in elements:
        element_type = element.is_a()  # Get IFC element type
        if element_type in ec_functions:
            total_ec += ec_functions[element_type]([element], **kwargs)  # Call the correct function

    return total_ec



## EC Breakdown by materials - concrete, window, wood, aluminium, plywood, granite 
def extract_material_type(material_name):
    material_name = material_name.lower()

    if "concrete" in material_name:
        return "concrete"
    elif "window" in material_name:
        return "window"
    elif "wood" in material_name:
        return "wood"
    elif "aluminium" in material_name:
        return "aluminium"
    elif "granite" in material_name:
        return "granite"
    elif "plywood" in material_name:
        return "plywood"
    
    return None  # Ignore materials that don't match the categories


def breakdown_by_materials(filepath):
    ifc_file = ifcopenshell.open(filepath)

    # Stores elements categorized by material type
    elements_by_material = {key: [] for key in ["concrete", "window", "wood", "aluminium", "granite", "plywood"]}

    # Fetch all elements in the IFC file
    all_elements = ifc_file.by_type("IfcElement")

    for element in all_elements:
        material_sets = element.HasAssociations  # Extract materials associated with the element
        for rel in material_sets:
            if rel.is_a("IfcRelAssociatesMaterial") and rel.RelatingMaterial:
                material_name = rel.RelatingMaterial.Name  # Extract material name
                category = extract_material_type(material_name)
                if category:
                    elements_by_material[category].append(element)  # Categorize the element

    # Compute EC for each material category
    ec_breakdown = {}
    for material, elements in elements_by_material.items():
        if elements:
            ec_breakdown[material] = calculate_elements_ec(elements)
    
    return ec_breakdown

## EC Breakdown by building elements 
def breakdown_by_elements(filepath):
    slabs_to_ignore = []
    ifc_file = ifcopenshell.open(filepath)

    # Store element types dynamically
    elements = {
        "column": ifc_file.by_type("IfcColumn"),
        "beam": ifc_file.by_type("IfcBeam"),
        "slab": ifc_file.by_type("IfcSlab"),
        "wall": ifc_file.by_type("IfcWall"),
        "roof": ifc_file.by_type("IfcRoof"),
        "window": ifc_file.by_type("IfcWindow"),
        "door": ifc_file.by_type("IfcDoor"),
        "stair": ifc_file.by_type("IfcStairFlight"),
        "railing": ifc_file.by_type("IfcRailing"),
    }

    # Logging element counts
    for key, value in elements.items():
        logger.info(f"Total {key}s found: {len(value)}")

    # Identify slabs to ignore (those aggregated under roofs)
    for roof in elements["roof"]:
        for rel in roof.IsDecomposedBy:
            if rel.is_a("IfcRelAggregates"):
                for part in rel.RelatedObjects:
                    if part.is_a("IfcSlab"):
                        slabs_to_ignore.append(part.id())

    # Function mapping (instead of using `globals()`)
    calculation_functions = {
        "column": calculate_columns,
        "beam": calculate_beams,
        "slab": lambda slabs: calculate_slabs(slabs, to_ignore=slabs_to_ignore),
        "wall": calculate_walls,
        "roof": calculate_roofs,
        "window": calculate_windows,
        "door": calculate_doors,
        "stair": calculate_stairs,
        "railing": calculate_railings,
    }

    # Calculate total embodied carbon
    total_ec = 0
    breakdown = {}

    for key, elements_list in elements.items():
        if elements_list:
            func = calculation_functions.get(key)
            if func:
                ec = func(elements_list)
                total_ec += ec
                breakdown[key] = ec  # Store breakdown by element type

    logger.info(f"Total EC calculated: {total_ec}")
    
    return {
        "total_ec": total_ec,
        "by_element": breakdown  # Example output: {"beam": 500, "column": 600, "slab": 700}
    }


## Calulate total EC 
def calculate_total_ec(filepath):
    total_ec = calculate_substructure_ec(filepath)+calculate_superstructure_ec(filepath)
    return total_ec

## Debugging functions 

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

if __name__ == "__main__":
    #ifcpath = os.path.join(r"C:\Users\dczqd\Documents\SUTD\Capstone-calc", "Window 1.ifc")
    ifcpath = os.path.join(r"C:\Users\Carina\Downloads", "Complex 1.ifc")
    logger.info(f"{ifcpath=}")
    sub_ec = calculate_substructure_ec(ifcpath)
    super_ec = calculate_superstructure_ec(ifcpath)
    sum_total_ec = calculate_total_ec(ifcpath)
    total_ec = calculate_embodied_carbon(ifcpath)
    ec_by_elements = breakdown_by_elements(ifcpath)
    ec_by_materials = breakdown_by_materials(ifcpath)
    logger.info(f"Breakdown by elements = {ec_by_elements}")

    logger.info(f"Breakdown by materials = {ec_by_materials}")

    logger.info(f"Validation: Substructure EC + Superstructure EC = {sub_ec + super_ec}, Total EC = {sum_total_ec}, Total EC from calculator.py = {total_ec}")
