import os
import ifcopenshell
from ifcopenshell.util.element import get_psets
from loguru import logger
import sys
import ifcopenshell
import ifcopenshell.geom
import numpy as np
from numpy import abs as np_abs

from calculator import calculate_beams, calculate_columns, calculate_embodied_carbon, calculate_slabs, calculate_walls,calculate_roofs

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

    logger.info(f"Total elements found on {storey_name}: {len(elements)}")
    logger.info(f"Elements found in {storey_name}: {[e.is_a() for e in elements]}")
    return elements

def get_nested_elements(element):
    """ Recursively get nested elements inside an aggregated structure """
    nested_elements = []
    for rel in element.IsDecomposedBy:
        if rel.is_a("IfcRelAggregates"):
            nested_elements.extend(rel.RelatedObjects)
            for sub_element in rel.RelatedObjects:
                nested_elements.extend(get_nested_elements(sub_element))
    return nested_elements
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

        for element in elements:
            if element.is_a("IfcSlab"):
                superstructure_slabs.add(element.GlobalId)  # Track slabs
                total_ec += calculate_slabs([element],slabs_to_ignore)
            elif element.is_a("IfcWall"):
                total_ec += calculate_walls([element])
            elif element.is_a("IfcColumn"):
                total_ec += calculate_columns([element])
            elif element.is_a("IfcBeam"):
                total_ec += calculate_beams([element])
            elif element.is_a("IfcRoof"):  # ADD THIS
                total_ec += calculate_roofs([element]) 
    
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

if __name__ == "__main__":
    #ifcpath = os.path.join(r"C:\Users\dczqd\Documents\SUTD\Capstone-calc", "Window 1.ifc")
    ifcpath = os.path.join(r"C:\Users\Carina\Downloads", "Complex 1.ifc")
    logger.info(f"{ifcpath=}")
    sub_ec = calculate_substructure_ec(ifcpath)
    super_ec = calculate_superstructure_ec(ifcpath)
    
    total_ec = calculate_embodied_carbon(ifcpath)

    logger.info(f"Validation: Substructure EC + Superstructure EC = {sub_ec + super_ec}, Total EC = {total_ec}")
