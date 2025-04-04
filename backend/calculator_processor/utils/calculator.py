import time

start_time = time.time()

import ifcopenshell
from ifcopenshell.util.element import get_psets
from loguru import logger
import sys
import ifcopenshell
import ifcopenshell.geom
import numpy as np
import os
import math

import calculator_utils
# from . import calculator_utils

MaterialList = calculator_utils.MaterialList
MaterialsToIgnore = calculator_utils.MaterialsToIgnore
material_embeddings = calculator_utils.material_embeddings
material_data_df = calculator_utils.material_data_df

MATERIAL_REAPLCE = False


def calculate_beams(beams):
    """Calculate embodied carbon for beams, using material matching if needed"""
    total_ec = 0
    beam_elements = []
    missing_materials = []
    excel_data = []

    for beam in beams:
        current_quantity = None  # in volume
        current_material = None

        psets = get_psets(beam)
        rebar_set = psets.get("Rebar Set")
        if rebar_set is None:
            logger.error("Rebar set not found")
        if rebar_set:
            BL = rebar_set.get("BottomLeft")
            BM = rebar_set.get("BottomMiddle")
            BR = rebar_set.get("BottomRight")
            TL = rebar_set.get("TopLeft")
            TM = rebar_set.get("TopMiddle")
            TR = rebar_set.get("TopRight")
            if (
                BL == None
                or BM == None
                or BR == None
                or TL == None
                or TM == None
                or TR == None
            ):
                logger.error("Rebar part not found")
            BLno, BLarea = BL.split("H")
            BMno, BMarea = BM.split("H")
            BRno, BRarea = BR.split("H")
            TLno, TLarea = TL.split("H")
            TMno, TMarea = TM.split("H")
            TRno, TRarea = TR.split("H")

        dimensions = psets.get("Dimensions")
        if dimensions is None:
            logger.error("Dimensions/Diameter not found")
        if dimensions:
            lengthmm = dimensions.get("Length")
            if lengthmm is None:
                logger.error("Length not found")
            else:
                length = lengthmm / 1000

        if rebar_set:
            rebar_vol = (
                (
                    (
                        int(TLno) * 3.14 * ((int(TLarea) / 2000) ** 2)
                        + int(BLno) * 3.14 * ((int(BLarea) / 2000) ** 2)
                    )
                    * (1 / 3)
                    * length
                )
                + (
                    (
                        int(TMno) * 3.14 * ((int(TMarea) / 2000) ** 2)
                        + int(BMno) * 3.14 * ((int(BMarea) / 2000) ** 2)
                    )
                    * (1 / 3)
                    * length
                )
                + (
                    (
                        int(TRno) * 3.14 * ((int(TRarea) / 2000) ** 2)
                        + int(BRno) * 3.14 * ((int(BRarea) / 2000) ** 2)
                    )
                    * (1 / 3)
                    * length
                )
            )

        if hasattr(beam, "IsDefinedBy"):
            for definition in beam.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_BeamBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(
                                    f"Found NetVolume for {beam.Name}: {quantity.VolumeValue}"
                                )
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        # Get material information
        if hasattr(beam, "HasAssociations"):
            for association in beam.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        current_material = material.Name
                        break

        # Check if material exists in our database
        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )
        if current_material_ec is None and current_material not in MaterialsToIgnore:
            missing_materials.append((beam.id(), current_material))

        # Store this material in our database for future reference
        if current_material and current_material not in MaterialsToIgnore:
            element_data = {
                "element_type": beam.is_a(),
                "element_name": beam.Name if hasattr(beam, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
                "has_rebar": bool(rebar_set),
            }

            # If material has EC data, include it
            if current_material_ec:
                if (
                    isinstance(current_material_ec, list)
                    and len(current_material_ec) >= 2
                ):
                    element_data["ec_per_kg"] = current_material_ec[0]
                    element_data["density"] = current_material_ec[1]
                elif isinstance(current_material_ec, (int, float)):
                    element_data["ec_per_m2"] = current_material_ec

            # Add to database
            calculator_utils.add_material_to_database(element_data)

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Use material matching instead of raising an error
            element_data = {
                "element_type": beam.is_a(),
                "element_name": beam.Name if hasattr(beam, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
                "has_rebar": bool(rebar_set),
            }

            # Try to find a similar material
            similar_material, similarity = calculator_utils.find_similar_material(
                element_data
            )

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                )
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.error(
                    f"Material '{current_material}' not found and no similar material found. Skipping this beam."
                )
                continue

        if current_quantity is None:
            logger.error(f"No volume found for beam {beam.Name}. Skipping.")
            missing_materials.append(beam.id())
            continue

        material_ec_perkg, material_density = current_material_ec
        materials_breakdown = []

        if rebar_set == None:
            concrete_ec = material_ec_perkg * material_density * current_quantity
            materials_breakdown.append(
                {
                    "material": current_material,
                    "material_mass": current_quantity * material_density,
                    "ec": concrete_ec,
                }
            )
            current_ec = concrete_ec
        else:
            concrete_ec = (
                material_ec_perkg * material_density * (current_quantity - rebar_vol)
            )
            rebar_ec = rebar_vol * 2.510 * 7850

            materials_breakdown.append(
                {
                    "material": current_material,
                    "material_mass": current_quantity,
                    "ec": concrete_ec,
                }
            )
            materials_breakdown.append(
                {"material": "Rebar", "material_mass": rebar_vol * 7850, "ec": rebar_ec}
            )

            logger.debug(f"EC for {beam.Name}'s rebars is {rebar_ec}")
            current_ec = concrete_ec + rebar_ec

        logger.debug(f"EC for {beam.Name} is {current_ec}")

        beam_elements.append(
            {"element": "Beam", "ec": current_ec, "materials": materials_breakdown}
        )
        for material_item in materials_breakdown:
            excel_data.append(
                [
                    beam.id(),  # Element ID
                    beam.is_a(),  # IFC Type
                    "Beam",  # Element Type
                    material_item["material"],  # Material
                    material_item["ec"],  # Material EC
                    material_item["material_mass"],  # Total material mass
                    "kg",
                ]
            )
        total_ec += current_ec

    logger.debug(f"Total EC for beams is {total_ec}")
    return total_ec, beam_elements, missing_materials, excel_data


def calculate_columns(columns):
    """Calculate embodied carbon for columns, using material matching if needed"""
    total_ec = 0
    quantities = {}
    materials = []
    column_elements = []
    missing_materials = []
    excel_data = []

    for column in columns:
        current_quantity = None
        current_material = None
        rebar = None
        height = None
        rebar_vol = None
        materials_breakdown = []

        psets = get_psets(column)
        rebar_set = psets.get("Rebar Set")

        if rebar_set is None:
            logger.error("Rebar set not found")
        if rebar_set:
            rebar = rebar_set.get("MainRebar")
            if rebar is None:
                logger.error("Rebar not found")

        dimensions = psets.get("Dimensions")
        if dimensions is None:
            logger.error("Dimensions/Diameter not found")
        if dimensions:
            heightmm = dimensions.get("Height")
            if heightmm is None:
                heightmm = dimensions.get("Length")
                if heightmm is None:
                    logger.error("Height not found")
                else:
                    height = heightmm / 1000
            else:
                height = heightmm / 1000

        if rebar and height:
            rebar_no, area = rebar.split("H")
            rebar_vol = height * int(rebar_no) * 3.14 * ((int(area) / 2000) ** 2)

        if hasattr(column, "IsDefinedBy"):
            for definition in column.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_ColumnBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(f"Found NetVolume for {column.Name}")
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
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        materials.append(material.Name)
                        current_material = material.Name
                        break
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage"
                            )
                            materials.append(layer.Material.Name)
                            current_material = layer.Material.Name
                            break
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet"
                            )
                            materials.append(layer.Material.Name)
                            current_material = layer.Material.Name
                            break

        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )

        if current_material_ec is None and current_material not in MaterialsToIgnore:
            logger.error(
                f"Material '{current_material}' not found and no similar material found. Skipping this column."
            )
            missing_materials.append((column.id(), current_material))
            continue

        # Store this material in our database for future reference
        if current_material and current_material not in MaterialsToIgnore:
            element_data = {
                "element_type": column.is_a(),
                "element_name": column.Name if hasattr(column, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
                "has_rebar": bool(rebar_set),
            }

            # If material has EC data, include it
            if current_material_ec:
                if (
                    isinstance(current_material_ec, list)
                    and len(current_material_ec) >= 2
                ):
                    element_data["ec_per_kg"] = current_material_ec[0]
                    element_data["density"] = current_material_ec[1]
                elif isinstance(current_material_ec, (int, float)):
                    element_data["ec_per_m2"] = current_material_ec

            # Add to database
            calculator_utils.add_material_to_database(element_data)

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Use material matching instead of raising an error
            element_data = {
                "element_type": column.is_a(),
                "element_name": column.Name if hasattr(column, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
                "has_rebar": bool(rebar_set),
            }

            # Try to find a similar material
            similar_material, similarity = calculator_utils.find_similar_material(
                element_data
            )

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                )
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.warning(
                    f"Material '{current_material}' not found and no similar material found. Skipping this column."
                )
                continue

        if current_quantity is None:
            logger.error(f"No volume found for column {column.Name}. Skipping.")
            missing_materials.append(column.id())
            continue

        material_ec_perkg, material_density = current_material_ec

        if rebar_vol == None:
            concrete_ec = material_ec_perkg * material_density * current_quantity
            materials_breakdown.append(
                {
                    "material": current_material,
                    "material_mass": material_density * current_quantity,
                    "ec": concrete_ec,
                }
            )
            current_ec = concrete_ec

        else:
            concrete_ec = (
                material_ec_perkg * material_density * (current_quantity - rebar_vol)
            )
            rebar_ec = rebar_vol * 2.510 * 7850

            materials_breakdown.append(
                {
                    "material": current_material,
                    "material_mass": material_density * (current_quantity - rebar_vol),
                    "ec": concrete_ec,
                }
            )

            materials_breakdown.append(
                {"material": "Rebar", "material_mass": rebar_vol * 7850, "ec": rebar_ec}
            )

            logger.debug(f"EC for {column.Name}'s rebars is {rebar_ec}")
            current_ec = concrete_ec + rebar_ec

        column_elements.append(
            {"element": "Column", "ec": current_ec, "materials": materials_breakdown}
        )
        for material_item in materials_breakdown:
            excel_data.append(
                [
                    column.id(),  # Element ID
                    column.is_a(),  # IFC Type
                    "Column",  # Element Type
                    material_item["material"],  # Material
                    material_item["ec"],  # Material EC
                    material_item["material_mass"],  # Total material mass
                    "kg",
                ]
            )

        logger.debug(f"EC for {column.Name} is {current_ec}")
        total_ec += current_ec

    logger.debug(f"Total EC for columns is {total_ec}")
    return total_ec, column_elements, missing_materials, excel_data


def calculate_slabs(slabs, to_ignore=[]):
    """Calculate embodied carbon for slabs, using material matching if needed"""
    total_ec = 0
    quantities = {}
    slab_elements = []
    missing_materials = []
    excel_data = []

    for slab in slabs:
        layer_thicknesses = {}
        material_layers = []
        current_area = None
        current_ec = None
        current_quantity = None
        current_material = None
        materials_breakdown = []

        if slab.id() in to_ignore:
            logger.info(f"Skipping slab {slab.id()} as its to be ignored")
            continue

        if hasattr(slab, "IsDefinedBy"):
            for definition in slab.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_SlabBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            # For material constituent
                            if quantity.is_a("IfcPhysicalComplexQuantity"):
                                for sub_quantity in quantity.HasQuantities:
                                    logger.debug(
                                        f"Found subquantity {sub_quantity.Name} for {quantity.Name}: {sub_quantity.LengthValue}"
                                    )
                                    layer_thicknesses[quantity.Name] = (
                                        sub_quantity.LengthValue
                                    )

                            elif quantity.is_a("IfcQuantityArea") and (
                                quantity.Name == "NetArea"
                                or quantity.Name == "GrossArea"
                            ):
                                logger.debug(
                                    f"Found NetArea for {slab.Name}: {quantity.AreaValue}"
                                )
                                current_area = quantity.AreaValue

                            elif (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(
                                    f"Found NetVolume for {slab.Name}: {quantity.VolumeValue}"
                                )
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
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        material_layers.append(material.Name)
                        current_material = material.Name

                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialConstituent"
                            )
                            material_layers.append(layer.Material.Name)

                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage"
                            )
                            material_layers.append(layer.Material.Name)
                            current_material = layer.Material.Name

                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet"
                            )
                            material_layers.append(layer.Material.Name)
                            current_material = layer.Material.Name

        if material_layers and len(material_layers) > 1:
            logger.debug("Processing layered slab")
            # Multi-material slab
            slab_total_ec = 0
            slab_materials = []

            for mat in material_layers:
                mat_ec_data = MaterialList.get(mat)
                thickness = layer_thicknesses.get(mat, None)

                if thickness is None:
                    logger.warning(
                        f"'{mat}' layer thickness not found, skipping EC calculation, this is on {slab=}"
                    )
                    continue
                if thickness <= 0:
                    logger.warning(
                        f"'{mat}' layer thickness <= 0, skipping EC calculation, this is on {slab=}"
                    )
                    continue

                # Store this material in our database for future reference
                if mat_ec_data and mat not in MaterialsToIgnore:
                    element_data = {
                        "element_type": slab.is_a(),
                        "element_name": slab.Name if hasattr(slab, "Name") else None,
                        "material_name": mat,
                        "material_type": "layered",
                        "volume": current_quantity,
                        "area": current_area,
                        "layer_materials": material_layers,
                        "layer_thicknesses": [thickness],
                    }

                    # If material has EC data, include it
                    if mat_ec_data:
                        if isinstance(mat_ec_data, list) and len(mat_ec_data) >= 2:
                            element_data["ec_per_kg"] = mat_ec_data[0]
                            element_data["density"] = mat_ec_data[1]
                        elif isinstance(mat_ec_data, (int, float)):
                            element_data["ec_per_m2"] = mat_ec_data

                    # Add to database
                    calculator_utils.add_material_to_database(element_data)

                if mat_ec_data is None and mat not in MaterialsToIgnore:

                    missing_materials.append((slab.id(), mat))

                    if not MATERIAL_REAPLCE:
                        logger.warning(
                            f"Material '{mat}' not found. Skipping this layer."
                        )
                        continue

                    # Try material matching
                    element_data = {
                        "element_type": slab.is_a(),
                        "element_name": slab.Name if hasattr(slab, "Name") else None,
                        "material_name": mat,
                        "material_type": "layered",
                        "volume": current_quantity,
                        "area": current_area,
                        "layer_materials": material_layers,
                        "layer_thicknesses": [thickness],
                    }

                    similar_material, similarity = (
                        calculator_utils.find_similar_material(element_data)
                    )

                    if similar_material and similar_material in MaterialList:
                        logger.info(
                            f"Material '{mat}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                        )
                        mat = similar_material
                        mat_ec_data = MaterialList.get(mat)
                    else:
                        logger.warning(
                            f"Material '{mat}' not found and no similar material found. Skipping this layer."
                        )
                        continue

                if current_area is None:
                    current_area = calculator_utils.get_element_area(slab)
                    logger.warning(f"{mat} area not found, manually calculating.")

                ec_per_kg, density = mat_ec_data
                logger.debug(
                    f"Layer info - thickness: {thickness}, area: {current_area}, ec_per_kg: {ec_per_kg}, density: {density}"
                )
                layer_ec = ec_per_kg * density * (thickness / 1000) * current_area

                if layer_ec > 0:
                    slab_materials.append(
                        {
                            "material": mat,
                            "material_mass": density
                            * (thickness / 1000)
                            * current_area,
                            "ec": layer_ec,
                        }
                    )
                    slab_total_ec += layer_ec

                logger.debug(f"EC for material '{mat}' in {slab.Name} is {current_ec}")

            if slab_total_ec > 0 and slab_materials:
                total_ec += slab_total_ec
                slab_elements.append(
                    {
                        "element": "Slab",
                        "ec": slab_total_ec,
                        "materials": slab_materials,
                    }
                )
                for material_item in slab_materials:
                    excel_data.append(
                        [
                            slab.id(),  # Element ID
                            slab.is_a(),  # IFC Type
                            "Slab",  # Element Type
                            material_item["material"],  # Material
                            material_item["ec"],  # Material EC
                            material_item["material_mass"],  # Material mass
                            "kg",
                        ]
                    )

                continue

        if current_material is None:
            logger.info("No materials found directly on slab, checking type definition")
            if hasattr(slab, "IsTypedBy"):
                for rel in slab.IsTypedBy:
                    if rel.is_a("IfcRelDefinesByType"):
                        type_obj = rel.RelatingType
                        logger.info(f"Found type definition: {type_obj.Name}")

                        # Look for materials in the type object
                        if hasattr(type_obj, "HasAssociations"):
                            for association in type_obj.HasAssociations:
                                if association.is_a("IfcRelAssociatesMaterial"):
                                    material = association.RelatingMaterial

                                    # Now check each material type as before
                                    if material.is_a("IfcMaterial"):
                                        logger.info(
                                            f"Found material '{material.Name}' in type"
                                        )
                                        current_material = material.Name

        if current_material is not None:
            # Single-material slab
            current_material_ec = (
                MaterialList.get(current_material, None) if current_material else None
            )
            if current_material_ec is None:
                logger.warning(
                    f"Material '{current_material}' not found and no similar material found. Skipping this slab."
                )
                missing_materials.append((slab.id(), current_material))
                continue

            if current_material_ec is None and MATERIAL_REAPLCE:
                # Try material matching
                element_data = {
                    "element_type": slab.is_a(),
                    "element_name": slab.Name if hasattr(slab, "Name") else None,
                    "material_name": current_material,
                    "material_type": "single",
                    "volume": current_quantity,
                    "area": current_area,
                }

                similar_material, similarity = calculator_utils.find_similar_material(
                    element_data
                )

                if similar_material and similar_material in MaterialList:
                    logger.info(
                        f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                    )
                    current_material = similar_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.error(
                        f"Material '{current_material}' not found and no similar material found. Skipping this slab."
                    )
                    continue
                
            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity

            materials_breakdown.append(
                {
                    "material": current_material,
                    "material_mass": material_density * current_quantity,
                    "ec": current_ec,
                }
            )

            slab_elements.append(
                {
                    "element": "Slab",
                    "ec": current_ec,
                    "material_mass": material_density * current_quantity,
                    "materials": materials_breakdown,
                }
            )
            for material_item in materials_breakdown:
                excel_data.append(
                    [
                        slab.id(),  # Element ID
                        slab.is_a(),  # IFC Type
                        "Slab",  # Element Type
                        material_item["material"],  # Material
                        material_item["ec"],  # Material EC
                        material_item["material_mass"],  # Material mass
                        "kg",
                    ]
                )
            logger.debug(f"EC for {slab.Name} is {current_ec}")
            total_ec += current_ec
            continue

        if current_ec is None:
            logger.warning(
                f"EC calculation for slab failed, attempting manual volume method"
            )
            # Attempts to retrieve the "correct" material from material layer set. Works if able to filter down to one possible material.
            # Calculates EC using EC density * volume method.
            # Calculates volume from ifc geometry.

            MaterialList_filtered = [
                material
                for material in material_layers
                if material not in MaterialsToIgnore
            ]
            if len(MaterialList_filtered) > 1:
                logger.warning(
                    f"Unable to isolate to one material from material layer set. Using the first material found, {MaterialList_filtered[0]} for this slab {slab}"
                )

            elif len(MaterialList_filtered) == 0:
                logger.error(f"No material found for this {slab=}")
                continue

            if current_quantity is None:
                current_quantity = calculator_utils.get_element_volume(slab)

            current_material = MaterialList_filtered[0]
            logger.debug(f"Using material {current_material}")
            current_material_ec = (
                MaterialList.get(current_material, None) if current_material else None
            )
            if current_material_ec is None:
                missing_materials.append((slab.id(), current_material))
            if current_material_ec is None and MATERIAL_REAPLCE:
                # Try material matching
                element_data = {
                    "element_type": slab.is_a(),
                    "element_name": slab.Name if hasattr(slab, "Name") else None,
                    "material_name": current_material,
                    "material_type": "single",
                    "volume": current_quantity,
                }

                similar_material, similarity = calculator_utils.find_similar_material(
                    element_data
                )

                if similar_material and similar_material in MaterialList:
                    logger.info(
                        f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                    )
                    current_material = similar_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.warning(
                        f"Material '{current_material}' not found and no similar material found. Skipping this slab."
                    )
                    continue

            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity

            materials_breakdown.append(
                {
                    "material": current_material,
                    "material_mass": material_density * current_quantity,
                    "ec": current_ec,
                }
            )
            for material_item in materials_breakdown:
                excel_data.append(
                    [
                        slab.id(),  # Element ID
                        slab.is_a(),  # IFC Type
                        "Slab",  # Element Type
                        material_item["material"],  # Material
                        material_item["ec"],  # Material EC
                        material_item["material_mass"],  # material mass
                        "kg",
                    ]
                )
            # Add this slab as an element
            slab_elements.append(
                {"element": "Slab", "ec": current_ec, "materials": materials_breakdown}
            )
            logger.debug(f"EC for {slab.Name} is {current_ec}")
            total_ec += current_ec

    logger.debug(f"Total EC for slabs is {total_ec}")
    return total_ec, slab_elements, missing_materials, excel_data


def calculate_walls(walls):
    """Calculate embodied carbon for walls, using material matching if needed"""
    total_ec = 0
    wall_elements = []
    missing_materials = []
    excel_data = []

    for wall in walls:
        current_volume = None
        current_material = None
        layer_thicknesses = {}
        layer_materials = []
        current_ec = None
        current_area = None
        materials_breakdown = []

        if hasattr(wall, "IsDefinedBy"):
            for definition in wall.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_WallBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            # For material constituent
                            if quantity.Name in MaterialList.keys():
                                for sub_quantity in quantity.HasQuantities:
                                    logger.debug(
                                        f"Found subquantity {sub_quantity.Name} for {quantity.Name}: {sub_quantity.LengthValue}"
                                    )
                                    layer_thicknesses[quantity.Name] = (
                                        sub_quantity.LengthValue
                                    )
                            elif (
                                quantity.is_a("IfcQuantityArea")
                                and quantity.Name == "NetSideArea"
                            ):
                                logger.debug(
                                    f"Found NetSideArea for {wall.Name}: {quantity.AreaValue}"
                                )
                                current_area = quantity.AreaValue

                            # For single material
                            elif (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(
                                    f"Found NetVolume for {wall.Name}: {quantity.VolumeValue}"
                                )
                                # quantities[quantity.Name] = quantity.VolumeValue
                                current_volume = quantity.VolumeValue

        if hasattr(wall, "HasAssociations"):
            for association in wall.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        current_material = material.Name
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialConstituent"
                            )
                            layer_materials.append(layer.Material.Name)

        if layer_materials:
            logger.debug("Processing layered wall")
            # Multi-material wall
            for mat in layer_materials:
                mat_ec_data = MaterialList.get(mat)
                thickness = layer_thicknesses.get(mat, 0)

                if thickness <= 0:
                    logger.warning(
                        f"'{mat}' layer thickness <= 0, skipping EC calculation"
                    )
                    continue

                if mat_ec_data is None and mat not in MaterialsToIgnore:

                    missing_materials.append((wall.id(), mat))
                    if not MATERIAL_REAPLCE:
                        logger.warning(
                            f"Material '{mat}' not found. Skipping this layer."
                        )
                        continue

                    # Try material matching
                    element_data = {
                        "element_type": wall.is_a(),
                        "element_name": wall.Name if hasattr(wall, "Name") else None,
                        "material_name": mat,
                        "material_type": "layered",
                        "volume": current_volume,
                        "area": current_area,
                        "layer_materials": layer_materials,
                        "layer_thicknesses": [thickness],
                    }

                    similar_material, similarity = (
                        calculator_utils.find_similar_material(element_data)
                    )

                    if similar_material and similar_material in MaterialList:
                        logger.info(
                            f"Material '{mat}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                        )
                        mat = similar_material
                        mat_ec_data = MaterialList.get(mat)
                    else:
                        logger.warning(
                            f"Material '{mat}' not found and no similar material found. Skipping this layer."
                        )
                        continue

                ec_per_kg, density = mat_ec_data
                logger.debug(
                    f"Layer info - thickness: {thickness}, area: {current_area}, ec_per_kg: {ec_per_kg}, density: {density}"
                )
                layer_ec = ec_per_kg * density * (thickness / 1000) * current_area

                materials_breakdown.append(
                    {
                        "material": mat,
                        "material_mass": density * (thickness / 1000) * current_area,
                        "ec": layer_ec,
                    }
                )
                logger.debug(f"EC for material '{mat}' in {wall.Name} is {layer_ec}")
                current_ec += layer_ec

            total_ec += current_ec
            wall_elements.append(
                {"element": "Wall", "ec": current_ec, "materials": materials_breakdown}
            )

            for material_item in materials_breakdown:
                excel_data.append(
                    [
                        wall.id(),  # Element ID
                        wall.is_a(),  # IFC Type
                        "Wall",  # Element Type
                        material_item["material"],  # Material
                        material_item["ec"],  # Material EC
                        material_item["material_mass"],  # material mass
                        "kg",
                    ]
                )
        elif current_material:
            # Single-material wall
            mat_ec_data = MaterialList.get(current_material)

            if mat_ec_data is None:

                missing_materials.append((wall.id(), current_material))
                if not MATERIAL_REAPLCE:
                    logger.warning(
                        f"Material '{current_material}' not found. Skipping this element)"
                    )
                    continue
                # Try material matching
                element_data = {
                    "element_type": wall.is_a(),
                    "element_name": wall.Name if hasattr(wall, "Name") else None,
                    "material_name": current_material,
                    "material_type": "single",
                    "volume": current_volume,
                }

                similar_material, similarity = calculator_utils.find_similar_material(
                    element_data
                )

                if similar_material and similar_material in MaterialList:
                    logger.info(
                        f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                    )
                    current_material = similar_material
                    mat_ec_data = MaterialList.get(current_material)
                else:
                    logger.warning(
                        f"Material '{current_material}' not found and no similar material found. Skipping this wall."
                    )
                    continue

            if current_volume is None:
                current_volume = calculator_utils.get_element_volume(wall)
                if current_volume is None:
                    logger.error(
                        f"Failed to calculate volume for wall {wall.Name}. Skipping."
                    )
                    continue

            ec_per_kg, density = mat_ec_data
            current_ec = ec_per_kg * density * current_volume

            materials_breakdown.append(
                {
                    "material": current_material,
                    "material_mass": density * current_volume,
                    "ec": current_ec,
                }
            )
            wall_elements.append(
                {"element": "Wall", "ec": current_ec, "materials": materials_breakdown}
            )
            for material_item in materials_breakdown:
                excel_data.append(
                    [
                        wall.id(),  # Element ID
                        wall.is_a(),  # IFC Type
                        "Wall",  # Element Type
                        material_item["material"],  # Material
                        material_item["ec"],  # Material EC
                        material_item["material_mass"],  # Material mass
                        "kg",
                    ]
                )

            logger.debug(f"EC for {wall.Name} is {current_ec}")
            total_ec += current_ec

        if current_ec is None:
            # Use material matching with volume estimation
            if not layer_materials:
                logger.warning(
                    f"No material information for wall {wall.Name}. Skipping."
                )
                continue

            # Use the most common material in layers
            if layer_materials:
                current_material = max(set(layer_materials), key=layer_materials.count)

            if current_volume is None:
                current_volume = calculator_utils.get_element_volume(wall)
                if current_volume is None:
                    logger.error(
                        f"Failed to calculate volume for wall {wall.Name}. Skipping."
                    )
                    continue

            # Try to find a similar material
            element_data = {
                "element_type": wall.is_a(),
                "element_name": wall.Name if hasattr(wall, "Name") else None,
                "material_name": current_material,
                "material_type": "single" if not layer_materials else "layered",
                "volume": current_volume,
                "layer_materials": layer_materials,
            }

            similar_material, similarity = calculator_utils.find_similar_material(
                element_data
            )

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Using material '{similar_material}' (similarity: {similarity:.3f}) for wall {wall.Name}"
                )
                current_material = similar_material
                mat_ec_data = MaterialList.get(current_material)

                ec_per_kg, density = mat_ec_data
                current_ec = ec_per_kg * density * current_volume

                materials_breakdown.append(
                    {
                        "material": current_material,
                        "material_mass": density * current_volume,
                        "ec": current_ec,
                    }
                )

                # Add this wall to elements
                wall_elements.append(
                    {
                        "element": "Wall",
                        "ec": current_ec,
                        "materials": materials_breakdown,
                    }
                )
                for material_item in materials_breakdown:
                    excel_data.append(
                        [
                            wall.id(),  # Element ID
                            wall.is_a(),  # IFC Type
                            "Wall",  # Element Type
                            material_item["material"],  # Material
                            material_item["ec"],  # Material EC
                            material_item["material_mass"],  # material mass
                            "kg",
                        ]
                    )

                logger.debug(f"EC for {wall.Name} is {current_ec}")
                total_ec += current_ec
            else:
                logger.warning(
                    f"No suitable material found for wall {wall.Name}. Skipping."
                )
                continue

    logger.debug(f"Total EC for walls is {total_ec}")
    return total_ec, wall_elements, missing_materials, excel_data


def calculate_windows(windows):
    """Calculate embodied carbon for windows, using material matching if needed"""
    total_ec = 0
    quantities = {}
    window_elements = []
    excel_data = []

    for window in windows:
        current_quantity = None
        current_material = None
        materials_breakdown = []
        missing_materials = []

        if hasattr(window, "IsDefinedBy"):
            for definition in window.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_WindowBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityArea")
                                and quantity.Name == "Area"
                            ):
                                logger.debug(
                                    f"Found Area for {window.Name}: {quantity.AreaValue}"
                                )
                                quantities[quantity.Name] = quantity.AreaValue
                                current_quantity = quantity.AreaValue
                                break
                        if current_quantity is not None:
                            break

        psets = get_psets(window)
        if "Pset_WindowCommon" in psets and "Reference" in psets["Pset_WindowCommon"]:
            current_material = psets["Pset_WindowCommon"]["Reference"]

        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )
        if current_material_ec is None:
            missing_materials.append((window.id(), current_material))

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Try material matching for windows
            element_data = {
                "element_type": window.is_a(),
                "element_name": window.Name if hasattr(window, "Name") else None,
                "material_name": current_material,
                "material_type": "reference",
                "area": current_quantity,
            }

            similar_material, similarity = calculator_utils.find_similar_material(
                element_data
            )

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                )
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.warning(
                    f"Material '{current_material}' not found and no similar material found. Skipping this window."
                )
                continue

        if current_quantity is None:
            logger.error(f"No area found for window {window.Name}. Skipping.")
            missing_materials.append(window.id())
            continue

        # Window EC is per area (m²)
        if isinstance(current_material_ec, (int, float)):
            material_ec_per_m2 = current_material_ec
            current_ec = material_ec_per_m2 * current_quantity
            material_quantity = current_quantity
        else:
            # Handle case where material EC is in standard [EC per kg, density] format
            material_ec_perkg, material_density = current_material_ec
            # Assume a standard thickness for windows (e.g., 25mm = 0.025m)
            standard_thickness = 0.025
            current_ec = (
                material_ec_perkg
                * material_density
                * standard_thickness
                * current_quantity
            )
            material_quantity = material_density * standard_thickness * current_quantity

        materials_breakdown.append(
            {
                "material": current_material,
                "material_mass": material_quantity,
                "ec": current_ec,
            }
        )
        window_elements.append(
            {"element": "Window", "ec": current_ec, "materials": materials_breakdown}
        )

        logger.debug(f"EC for {window.Name} is {current_ec}")
        total_ec += current_ec
        for material_item in materials_breakdown:
            excel_data.append(
                [
                    window.id(),  # Element ID
                    window.is_a(),  # IFC Type
                    "Window",  # Element Type
                    material_item["material"],  # Material
                    material_item["ec"],  # Material EC
                    material_item["material_mass"],  # Total Element EC
                    "m2",
                ]
            )

    logger.debug(f"Total EC for windows is {total_ec}")
    return total_ec, window_elements, missing_materials, excel_data


def calculate_doors(doors):
    """Calculate embodied carbon for doors, using material matching if needed"""
    total_ec = 0
    quantities = {}
    door_elements = []
    missing_materials = []
    excel_data = []

    for door in doors:
        current_quantity = None
        current_material = None
        materials_breakdown = []

        if hasattr(door, "IsDefinedBy"):
            for definition in door.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_DoorBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityArea")
                                and quantity.Name == "Area"
                            ):
                                logger.debug(
                                    f"Found Area for {door.Name}: {quantity.AreaValue}"
                                )
                                quantities[quantity.Name] = quantity.AreaValue
                                current_quantity = quantity.AreaValue
                                break
                        if current_quantity is not None:
                            break

        psets = get_psets(door)
        if "Pset_DoorCommon" in psets and "Reference" in psets["Pset_DoorCommon"]:
            current_material = psets["Pset_DoorCommon"]["Reference"]

        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )

        if current_material_ec is None:
            missing_materials.append((door.id(), current_material))

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Try material matching for doors
            element_data = {
                "element_type": door.is_a(),
                "element_name": door.Name if hasattr(door, "Name") else None,
                "material_name": current_material,
                "material_type": "reference",
                "area": current_quantity,
            }

            similar_material, similarity = calculator_utils.find_similar_material(
                element_data
            )

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                )
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.warning(
                    f"Material '{current_material}' not found and no similar material found. Skipping this door."
                )
                continue

        if current_material_ec is None:
            logger.warning(
                f"Material '{current_material}' not found. Skipping this door."
            )
            continue

        if current_quantity is None:
            logger.error(f"No area found for door {door.Name}. Skipping.")
            missing_materials.append(door.id())
            continue

        # Door EC is per area (m²)
        if isinstance(current_material_ec, (int, float)):
            material_ec_per_m2 = current_material_ec
            current_ec = material_ec_per_m2 * current_quantity
            material_quantity = current_quantity
        else:
            # Handle case where material EC is in standard [EC per kg, density] format
            material_ec_perkg, material_density = current_material_ec
            # Assume a standard thickness for doors (e.g., 40mm = 0.04m)
            standard_thickness = 0.04
            current_ec = (
                material_ec_perkg
                * material_density
                * standard_thickness
                * current_quantity
            )
            material_quantity = material_density * standard_thickness * current_quantity

        materials_breakdown.append(
            {
                "material": current_material,
                "material_mass": material_quantity,
                "ec": current_ec,
            }
        )
        door_elements.append(
            {"element": "Door", "ec": current_ec, "materials": materials_breakdown}
        )
        for material_item in materials_breakdown:
            excel_data.append(
                [
                    door.id(),  # Element ID
                    door.is_a(),  # IFC Type
                    "Door",  # Element Type
                    material_item["material"],  # Material
                    material_item["ec"],  # Material EC
                    material_item["material_mass"],  # Total Element EC
                    "m2",
                ]
            )
        logger.debug(f"EC for {door.Name} is {current_ec}")
        total_ec += current_ec

    logger.debug(f"Total EC for doors is {total_ec}")
    return total_ec, door_elements, missing_materials, excel_data


def calculate_roofs(roofs):
    """Calculate embodied carbon for roofs, using material matching if needed"""
    total_ec = 0
    roof_elements = []
    missing_materials = []
    excel_data = []

    for roof in roofs:
        slabs = []
        roof_ec = 0
        current_ec = 0
        roof_materials = []

        if hasattr(roof, "IsDecomposedBy"):
            for rel in roof.IsDecomposedBy:
                if rel.is_a("IfcRelAggregates"):
                    for slab in rel.RelatedObjects:
                        if slab.is_a("IfcSlab"):
                            logger.debug(f"Found Slab: {slab.Name}")
                            slabs.append(slab)

        for slab in slabs:
            layer_thicknesses = {}
            material_layers = []
            current_area = None
            current_ec = None
            current_quantity = None
            current_material = None
            slab_materials = []

            if hasattr(slab, "IsDefinedBy"):
                for definition in slab.IsDefinedBy:
                    if definition.is_a("IfcRelDefinesByProperties"):
                        property_def = definition.RelatingPropertyDefinition
                        if (
                            property_def.is_a("IfcElementQuantity")
                            and property_def.Name == "Qto_SlabBaseQuantities"
                        ):
                            for quantity in property_def.Quantities:
                                # For material constituent
                                if quantity.is_a("IfcPhysicalComplexQuantity"):
                                    for sub_quantity in quantity.HasQuantities:
                                        logger.debug(
                                            f"Found subquantity {sub_quantity.Name} for {quantity.Name}: {sub_quantity.LengthValue}"
                                        )
                                        layer_thicknesses[quantity.Name] = (
                                            sub_quantity.LengthValue
                                        )
                                elif quantity.is_a("IfcQuantityArea") and (
                                    quantity.Name == "NetSideArea"
                                    or quantity.Name == "GrossArea"
                                ):
                                    logger.debug(
                                        f"Found Area for {slab.Name}: {quantity.AreaValue}"
                                    )
                                    current_area = quantity.AreaValue

                                # For single material
                                elif (
                                    quantity.is_a("IfcQuantityVolume")
                                    and quantity.Name == "NetVolume"
                                ):
                                    logger.debug(
                                        f"Found NetVolume for {slab.Name}: {quantity.VolumeValue / len(slabs)}"
                                    )
                                    current_quantity = quantity.VolumeValue / len(slabs)

            if hasattr(slab, "HasAssociations"):
                for association in slab.HasAssociations:
                    if association.is_a("IfcRelAssociatesMaterial"):
                        material = association.RelatingMaterial
                        if material.is_a("IfcMaterial"):
                            logger.debug(
                                f"Found material '{material.Name}', as IfcMaterial"
                            )
                            current_material = material.Name
                        elif material.is_a("IfcMaterialConstituentSet"):
                            for layer in material.MaterialConstituents:
                                logger.debug(
                                    f"Found material '{layer.Material.Name}', as IfcMaterialConstituent"
                                )
                                material_layers.append(layer.Material.Name)
                        elif material.is_a("IfcMaterialLayerSetUsage"):
                            for layer in material.ForLayerSet.MaterialLayers:
                                logger.debug(
                                    f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage"
                                )
                                material_layers.append(layer.Material.Name)
                        elif material.is_a("IfcMaterialLayerSet"):
                            for layer in material.MaterialLayers:
                                logger.debug(
                                    f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet"
                                )
                                material_layers.append(layer.Material.Name)

            if material_layers:
                logger.debug("Processing layered slab in roof")
                # Multi-material slab
                for mat in material_layers:
                    mat_ec_data = MaterialList.get(mat)
                    thickness = layer_thicknesses.get(mat, None)

                    if thickness is None:
                        logger.warning(
                            f"'{mat}' layer thickness not found, skipping EC calculation"
                        )
                        continue
                    if thickness <= 0:
                        logger.warning(
                            f"'{mat}' layer thickness <= 0, skipping EC calculation"
                        )
                        continue

                    if not mat_ec_data:
                        missing_materials.append((roof.id(), mat))
                    # Store this material in our database for future reference
                    if mat and mat not in MaterialsToIgnore and mat_ec_data:

                        element_data = {
                            "element_type": slab.is_a(),
                            "element_name": (
                                slab.Name if hasattr(slab, "Name") else None
                            ),
                            "material_name": mat,
                            "material_type": "layered",
                            "volume": current_quantity,
                            "area": current_area,
                            "layer_materials": material_layers,
                            "layer_thicknesses": [thickness],
                        }

                        if isinstance(mat_ec_data, list) and len(mat_ec_data) >= 2:
                            element_data["ec_per_kg"] = mat_ec_data[0]
                            element_data["density"] = mat_ec_data[1]
                        elif isinstance(mat_ec_data, (int, float)):
                            element_data["ec_per_m2"] = mat_ec_data

                        # Add to database
                        calculator_utils.add_material_to_database(element_data)

                    if mat_ec_data is None and mat not in MaterialsToIgnore:
                        # Try material matching
                        element_data = {
                            "element_type": slab.is_a(),
                            "element_name": (
                                slab.Name if hasattr(slab, "Name") else None
                            ),
                            "material_name": mat,
                            "material_type": "layered",
                            "volume": current_quantity,
                            "area": current_area,
                            "layer_materials": material_layers,
                            "layer_thicknesses": [thickness],
                        }

                        similar_material, similarity = (
                            calculator_utils.find_similar_material(element_data)
                        )

                        if similar_material and similar_material in MaterialList:
                            logger.info(
                                f"Material '{mat}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                            )
                            mat = similar_material
                            mat_ec_data = MaterialList.get(mat)
                        else:
                            logger.warning(
                                f"Material '{mat}' not found and no similar material found. Skipping this layer."
                            )
                            continue

                    if current_area is None:
                        current_area = calculator_utils.get_element_area(slab)
                        logger.warning(f"{mat} area not found, manually calculating.")

                    ec_per_kg, density = mat_ec_data
                    logger.debug(
                        f"Layer info - thickness: {thickness}, area: {current_area}, ec_per_kg: {ec_per_kg}, density: {density}"
                    )
                    layer_ec = ec_per_kg * density * (thickness / 1000) * current_area

                    slab_materials.append(
                        {
                            "material": mat,
                            "material_mass": density
                            * (thickness / 1000)
                            * current_area,
                            "ec": layer_ec,
                        }
                    )

                    logger.debug(
                        f"EC for material '{mat}' in {slab.Name} is {current_ec}"
                    )
                    roof_ec += layer_ec

            elif current_material:
                # Single-material slab
                current_material_ec = (
                    MaterialList.get(current_material, None)
                    if current_material
                    else None
                )
                if current_material_ec is None:
                    missing_materials.append((roof.id(), current_material))
                if current_material_ec is None and MATERIAL_REAPLCE:
                    # Try material matching
                    element_data = {
                        "element_type": slab.is_a(),
                        "element_name": slab.Name if hasattr(slab, "Name") else None,
                        "material_name": current_material,
                        "material_type": "single",
                        "volume": current_quantity,
                        "area": current_area,
                    }

                    similar_material, similarity = (
                        calculator_utils.find_similar_material(element_data)
                    )

                    if similar_material and similar_material in MaterialList:
                        logger.info(
                            f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                        )
                        current_material = similar_material
                        current_material_ec = MaterialList.get(current_material)
                    else:
                        logger.warning(
                            f"Material '{current_material}' not found and no similar material found. Skipping this roof slab."
                        )
                        continue

                material_ec_perkg, material_density = current_material_ec
                current_ec = material_ec_perkg * material_density * current_quantity

                slab_materials.append(
                    {
                        "material": current_material,
                        "material_mass": material_density * current_quantity,
                        "ec": current_ec,
                    }
                )

                logger.debug(f"EC for {slab.Name} is {current_ec}")
                roof_ec += current_ec

            if current_ec is None:
                logger.warning(
                    f"EC calculation for slab in roof failed, attempting manual volume method"
                )
                # Attempts to retrieve the "correct" material from material layer set. Works if able to filter down to one possible material.
                # Calculates EC using EC density * volume method.
                # Calculates volume from ifc geometry.

                MaterialList_filtered = [
                    material
                    for material in material_layers
                    if material not in MaterialsToIgnore
                ]
                if len(MaterialList_filtered) > 1:
                    logger.error(
                        f"Unable to isolate to one material from material layer set. Using the first material found, {MaterialList_filtered[0]} for this slab {slab}"
                    )
                elif len(MaterialList_filtered) == 0:
                    logger.error(f"No material found for this {slab=}")
                    continue

                if current_quantity is None:
                    current_quantity = calculator_utils.get_element_volume(slab)

                current_material = MaterialList_filtered[0]
                logger.debug(f"Using material {current_material}")
                current_material_ec = (
                    MaterialList.get(current_material, None)
                    if current_material
                    else None
                )
                if not current_material_ec:
                    missing_materials.append(roof.id(), current_material)
                if current_material_ec is None and MATERIAL_REAPLCE:
                    # Try material matching
                    element_data = {
                        "element_type": slab.is_a(),
                        "element_name": slab.Name if hasattr(slab, "Name") else None,
                        "material_name": current_material,
                        "material_type": "single",
                        "volume": current_quantity,
                    }

                    similar_material, similarity = (
                        calculator_utils.find_similar_material(element_data)
                    )

                    if similar_material and similar_material in MaterialList:
                        logger.info(
                            f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                        )
                        current_material = similar_material
                        current_material_ec = MaterialList.get(current_material)
                    else:
                        logger.warning(
                            f"Material '{current_material}' not found and no similar material found. Skipping this roof slab."
                        )
                        continue

                material_ec_perkg, material_density = current_material_ec
                current_ec = material_ec_perkg * material_density * current_quantity

                slab_materials.append(
                    {
                        "material": current_material,
                        "material_mass": material_density * current_quantity,
                        "ec": current_ec,
                    }
                )

                logger.debug(f"EC for {slab.Name} is {current_ec}")
                roof_ec += current_ec

            roof_materials.extend(slab_materials)

        roof_elements.append(
            {"element": "Roof", "ec": roof_ec, "materials": roof_materials}
        )
        for material_item in roof_materials:
            excel_data.append(
                [
                    roof.id(),  # Element ID
                    roof.is_a(),  # IFC Type
                    "Roof",  # Element Type
                    material_item["material"],  # Material
                    material_item["ec"],  # Material EC
                    material_item["material_mass"],  # material mass
                    "kg",
                ]
            )
        logger.debug(f"EC for {roof.Name} is {roof_ec}")
        total_ec += roof_ec

    logger.debug(f"Total EC for roofs is {total_ec}")
    return total_ec, roof_elements, missing_materials, excel_data


def calculate_stairs(stairs):
    """Calculate embodied carbon for stairs, using material matching if needed"""
    total_ec = 0
    stair_elements = []
    missing_elements = []

    for stair in stairs:
        current_quantity = None
        current_material = None
        current_area = None
        current_ec = None
        layer_thicknesses = {}
        material_layers = []
        material_breakdown = []
        stair_total_ec = 0

        # Get volume information
        if hasattr(stair, "IsDefinedBy"):
            for definition in stair.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_StairFlightBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(
                                    f"Found NetVolume for {stair.Name}: {quantity.VolumeValue}"
                                )
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        # Get material information
        if hasattr(stair, "HasAssociations"):
            for association in stair.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial

                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        material_layers.append(material.Name)
                        current_material = material.Name
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialConstituent"
                            )
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage"
                            )
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet"
                            )
                            material_layers.append(layer.Material.Name)

        if material_layers:
            logger.debug("Processing layered stair")
            # Multi-material stair
            for mat in material_layers:
                mat_ec_data = MaterialList.get(mat)
                thickness = layer_thicknesses.get(mat, None)

                # Store this material in our database for future reference
                if mat and mat not in MaterialsToIgnore and mat in MaterialList:
                    element_data = {
                        "element_type": stair.is_a(),
                        "element_name": stair.Name if hasattr(stair, "Name") else None,
                        "material_name": mat,
                        "material_type": "layered",
                        "volume": current_quantity,
                        "area": current_area,
                        "layer_materials": material_layers,
                        "layer_thicknesses": [thickness] if thickness else [],
                    }

                    # If material has EC data, include it
                    if mat_ec_data:
                        if isinstance(mat_ec_data, list) and len(mat_ec_data) >= 2:
                            element_data["ec_per_kg"] = mat_ec_data[0]
                            element_data["density"] = mat_ec_data[1]
                        elif isinstance(mat_ec_data, (int, float)):
                            element_data["ec_per_m2"] = mat_ec_data

                    # Add to database
                    calculator_utils.add_material_to_database(element_data)

                if mat_ec_data is None and mat not in MaterialsToIgnore:
                    # Try material matching
                    missing_elements.append((stair.id(), mat))
                    if not MATERIAL_REAPLCE:
                        logger.warning(
                            f"Material '{mat}' not found. Skipping this layer."
                        )
                        continue
                    element_data = {
                        "element_type": stair.is_a(),
                        "element_name": stair.Name if hasattr(stair, "Name") else None,
                        "material_name": mat,
                        "material_type": "layered",
                        "volume": current_quantity,
                        "area": current_area,
                        "layer_materials": material_layers,
                        "layer_thicknesses": [thickness] if thickness else [],
                    }

                    similar_material, similarity = (
                        calculator_utils.find_similar_material(element_data)
                    )

                    if similar_material and similar_material in MaterialList:
                        logger.info(
                            f"Material '{mat}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                        )
                        mat = similar_material
                        mat_ec_data = MaterialList.get(mat)
                    else:
                        logger.warning(
                            f"Material '{mat}' not found and no similar material found. Skipping this layer."
                        )
                        continue

                # If we have material but no volume, skip
                if current_quantity is None:
                    logger.warning(
                        f"No volume found for stair {stair.Name} with material {mat}. Attempting to calculate."
                    )
                    current_quantity = calculator_utils.get_element_volume(stair)
                    if current_quantity is None:
                        logger.error(
                            f"Failed to calculate volume for stair {stair.Name}. Skipping."
                        )
                        missing_elements.append(stair.id())
                        continue

                material_ec_perkg, material_density = mat_ec_data
                # For layered materials, divide the volume by the number of materials
                volume_per_material = current_quantity / len(material_layers)
                layer_ec = material_ec_perkg * material_density * volume_per_material

                material_breakdown.append({"material": mat, "ec": layer_ec})

                logger.debug(f"EC for material '{mat}' in {stair.Name} is {layer_ec}")
                stair_total_ec += layer_ec

            stair_elements.append(
                {
                    "element": "Stair",
                    "ec": stair_total_ec,
                    "materials": material_breakdown,
                }
            )
            total_ec += stair_total_ec

        elif current_material:
            # Single-material stair
            current_material_ec = (
                MaterialList.get(current_material, None) if current_material else None
            )
            if current_material_ec is None:
                missing_elements.append((stair.id(), current_material))

            if current_material_ec is None and MATERIAL_REAPLCE:
                # Try material matching
                element_data = {
                    "element_type": stair.is_a(),
                    "element_name": stair.Name if hasattr(stair, "Name") else None,
                    "material_name": current_material,
                    "material_type": "single",
                    "volume": current_quantity,
                }

                similar_material, similarity = calculator_utils.find_similar_material(
                    element_data
                )

                if similar_material and similar_material in MaterialList:
                    logger.info(
                        f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                    )
                    current_material = similar_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.warning(
                        f"Material '{current_material}' not found and no similar material found. Skipping this stair."
                    )
                    continue

            if current_quantity is None:
                logger.warning(
                    f"No volume found for stair {stair.Name}. Attempting to calculate."
                )
                current_quantity = calculator_utils.get_element_volume(stair)
                if current_quantity is None:
                    logger.error(
                        f"Failed to calculate volume for stair {stair.Name}. Skipping."
                    )
                    continue

            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity

            material_breakdown.append({"material": current_material, "ec": current_ec})
            stair_elements.append(
                {"element": "Stair", "ec": current_ec, "materials": material_breakdown}
            )
            logger.debug(f"EC for {stair.Name} is {current_ec}")
            total_ec += current_ec

        else:
            logger.warning(
                f"EC calculation for stair failed, attempting manual volume method"
            )
            # Handle case where no material information is available
            if len(material_layers) == 0:
                logger.warning(
                    f"No material information found for stair {stair.Name}. Using concrete as default."
                )
                default_material = "CONCRETE"
                if default_material in MaterialList:
                    current_material = default_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.error(
                        f"Default material '{default_material}' not found. Skipping this stair."
                    )
                    continue
            else:
                # Use the most common material from material layers
                MaterialList_filtered = [
                    material
                    for material in material_layers
                    if material not in MaterialsToIgnore
                ]
                if len(MaterialList_filtered) > 0:
                    current_material = max(
                        set(MaterialList_filtered), key=MaterialList_filtered.count
                    )
                    current_material_ec = MaterialList.get(current_material, None)
                    if current_material_ec is None:
                        missing_elements.append((stairs.id(), current_material))
                    if current_material_ec is None and MATERIAL_REAPLCE:
                        # Try material matching
                        element_data = {
                            "element_type": stair.is_a(),
                            "element_name": (
                                stair.Name if hasattr(stair, "Name") else None
                            ),
                            "material_name": current_material,
                            "material_type": "single",
                            "volume": current_quantity,
                        }

                        similar_material, similarity = (
                            calculator_utils.find_similar_material(element_data)
                        )

                        if similar_material and similar_material in MaterialList:
                            logger.info(
                                f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                            )
                            current_material = similar_material
                            current_material_ec = MaterialList.get(current_material)
                        else:
                            logger.warning(
                                f"Material '{current_material}' not found and no similar material found. Skipping this stair."
                            )
                            continue
                else:
                    logger.error(
                        f"No suitable material found for stair {stair.Name}. Skipping."
                    )
                    continue

            if current_quantity is None:
                current_quantity = calculator_utils.get_element_volume(stair)
                if current_quantity is None:
                    logger.error(
                        f"Failed to calculate volume for stair {stair.Name}. Skipping."
                    )
                    missing_elements.append(stair.id())
                    continue

            material_ec_perkg, material_density = current_material_ec
            current_ec = material_ec_perkg * material_density * current_quantity

            material_breakdown.append({"material": current_material, "ec": current_ec})
            stair_elements.append(
                {"element": "Stair", "ec": current_ec, "materials": material_breakdown}
            )

            logger.debug(f"EC for {stair.Name} is {current_ec}")
            total_ec += current_ec

    logger.debug(f"Total EC for stairs is {total_ec}")
    return total_ec, stair_elements, missing_elements


def calculate_railings(railings):
    """Calculate embodied carbon for railings, using material matching if needed"""
    total_ec = 0
    railing_elements = []
    missing_materials = []

    for railing in railings:
        current_quantity = None
        current_material = None
        current_ec = None
        material_layers = []
        materials_breakdown = []

        # Get volume information
        if hasattr(railing, "IsDefinedBy"):
            for definition in railing.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_RailingBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(
                                    f"Found NetVolume for {railing.Name}: {quantity.VolumeValue}"
                                )
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        # Get material information
        if hasattr(railing, "HasAssociations"):
            for association in railing.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        material_layers.append(material.Name)
                        current_material = material.Name
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialConstituent"
                            )
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage"
                            )
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet"
                            )
                            material_layers.append(layer.Material.Name)

        # Handle the material calculations
        if material_layers:
            # Filter materials to exclude ones that should be ignored
            MaterialList_filtered = [
                material
                for material in material_layers
                if material not in MaterialsToIgnore
            ]

            if len(MaterialList_filtered) == 0:
                logger.error(
                    f"No usable materials found for railing {railing.Name}. Skipping."
                )
                continue

            # Use the most frequent material if multiple are present
            current_material = max(
                set(MaterialList_filtered), key=MaterialList_filtered.count
            )
            logger.debug(f"Using material {current_material} for railing")

            current_material_ec = MaterialList.get(current_material, None)

            if current_material_ec is None:
                missing_materials.append((railing.id(), current_material))

            if current_material_ec is None and MATERIAL_REAPLCE:
                # Try material matching
                element_data = {
                    "element_type": railing.is_a(),
                    "element_name": railing.Name if hasattr(railing, "Name") else None,
                    "material_name": current_material,
                    "material_type": "single",
                    "volume": current_quantity,
                }

                similar_material, similarity = calculator_utils.find_similar_material(
                    element_data
                )

                if similar_material and similar_material in MaterialList:
                    logger.info(
                        f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                    )
                    current_material = similar_material
                    current_material_ec = MaterialList.get(current_material)
                else:
                    # If no similar material found but we have other materials, try the next most common
                    other_materials = [
                        m for m in MaterialList_filtered if m != current_material
                    ]
                    if other_materials:
                        current_material = max(
                            set(other_materials), key=other_materials.count
                        )
                        current_material_ec = MaterialList.get(current_material)
                        if current_material_ec:
                            logger.warning(
                                f"Using alternative material '{current_material}' for railing"
                            )
                        else:
                            logger.error(
                                f"No suitable material found for railing {railing.Name}. Skipping."
                            )
                            continue
                    else:
                        logger.error(
                            f"No suitable material found for railing {railing.Name}. Skipping."
                        )
                        continue
        else:
            logger.warning(
                f"No material information for railing {railing.Name}. Assuming steel."
            )
            # Default to steel for railings if no material is specified
            if "STEEL" in MaterialList:
                current_material = "STEEL"
                current_material_ec = MaterialList.get(current_material)
            else:
                logger.error(
                    f"Default steel material not found in MaterialList. Skipping this railing."
                )
                continue

        if current_quantity is None:
            current_quantity = calculator_utils.get_element_volume(railing)
            if current_quantity is None or current_quantity <= 0:
                logger.error(
                    f"Failed to calculate positive volume for railing {railing.Name}. Skipping."
                )
                missing_materials.append(railing.id())
                continue

        material_ec_perkg, material_density = current_material_ec
        current_ec = material_ec_perkg * material_density * current_quantity

        materials_breakdown.append({"material": current_material, "ec": current_ec})

        # Add this railing as an element
        railing_elements.append(
            {"element": "Railing", "ec": current_ec, "materials": materials_breakdown}
        )

        logger.debug(
            f"EC for {railing.Name} is {current_ec}, volume is {current_quantity}"
        )
        total_ec += current_ec

    logger.debug(f"Total EC for railings is {total_ec}")
    return total_ec, railing_elements, missing_materials


def calculate_members(members):
    """Calculate embodied carbon for structural members, using material matching if needed"""
    total_ec = 0
    member_elements = []
    missing_elements = []

    for member in members:
        current_quantity = None
        current_material = None
        material_layers = []
        materials_breakdown = []

        # Get volume information
        if hasattr(member, "IsDefinedBy"):
            for definition in member.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_MemberBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(
                                    f"Found NetVolume for {member.Name}: {quantity.VolumeValue}"
                                )
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        # Get material information
        if hasattr(member, "HasAssociations"):
            for association in member.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        material_layers.append(material.Name)
                        current_material = material.Name
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage"
                            )
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet"
                            )
                            material_layers.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialConstituent"
                            )
                            material_layers.append(layer.Material.Name)

        # Store this material in our database for future reference
        if current_material and current_material not in MaterialsToIgnore:
            element_data = {
                "element_type": member.is_a(),
                "element_name": member.Name if hasattr(member, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
            }

            # Add to database
            calculator_utils.add_material_to_database(element_data)

        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )
        if current_material_ec is None:
            missing_elements.append((member.id(), current_material))

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Try material matching
            if not current_material and material_layers:
                # If we have layer materials but no current material, use the most common
                material_layers_filtered = [
                    m for m in material_layers if m not in MaterialsToIgnore
                ]
                if material_layers_filtered:
                    current_material = max(
                        set(material_layers_filtered),
                        key=material_layers_filtered.count,
                    )

            element_data = {
                "element_type": member.is_a(),
                "element_name": member.Name if hasattr(member, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
            }

            similar_material, similarity = calculator_utils.find_similar_material(
                element_data
            )

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                )
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                # Try with a common default if nothing else works
                if "STEEL" in MaterialList:
                    logger.warning(
                        f"No suitable material found for member {member.Name}. Using STEEL as default."
                    )
                    current_material = "STEEL"
                    current_material_ec = MaterialList.get(current_material)
                else:
                    logger.error(
                        f"No suitable material found for member {member.Name}. Skipping."
                    )
                    continue

        if current_quantity is None:
            current_quantity = calculator_utils.get_element_volume(member)
            if current_quantity is None or current_quantity <= 0:
                logger.error(
                    f"Failed to calculate positive volume for member {member.Name}. Skipping."
                )
                missing_elements.append(member.id())
                continue

        material_ec_perkg, material_density = current_material_ec
        current_ec = material_ec_perkg * material_density * current_quantity

        materials_breakdown.append({"material": current_material, "ec": current_ec})

        member_elements.append(
            {"element": "Member", "ec": current_ec, "materials": materials_breakdown}
        )

        logger.debug(f"EC for {member.Name} is {current_ec}")
        total_ec += current_ec

    logger.debug(f"Total EC for members is {total_ec}")
    return total_ec, member_elements, missing_elements


def calculate_plates(plates):
    """Calculate embodied carbon for plates, using material matching if needed"""
    total_ec = 0
    plate_elements = []
    missing_elements = []

    for plate in plates:
        current_quantity = None
        current_material = None
        current_area = None
        material_layers = []
        materials_breakdown = []

        # Get volume/area information
        if hasattr(plate, "IsDefinedBy"):
            for definition in plate.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_PlateBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(
                                    f"Found NetVolume for {plate.Name}: {quantity.VolumeValue}"
                                )
                                current_quantity = quantity.VolumeValue
                            elif (
                                quantity.is_a("IfcQuantityArea")
                                and quantity.Name == "NetArea"
                            ):
                                logger.debug(
                                    f"Found NetArea for {plate.Name}: {quantity.AreaValue}"
                                )
                                current_area = quantity.AreaValue
                        if current_quantity is not None:
                            break

        # Get material information
        if hasattr(plate, "HasAssociations"):
            for association in plate.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        material_layers.append(material.Name)
                        current_material = material.Name
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage"
                            )
                            material_layers.append(layer.Material.Name)
                            if (
                                not current_material
                            ):  # Use the first layer as the primary material
                                current_material = layer.Material.Name
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet"
                            )
                            material_layers.append(layer.Material.Name)
                            if (
                                not current_material
                            ):  # Use the first layer as the primary material
                                current_material = layer.Material.Name
                    elif material.is_a("IfcMaterialConstituentSet"):
                        for layer in material.MaterialConstituents:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialConstituent"
                            )
                            material_layers.append(layer.Material.Name)
                            if (
                                not current_material
                            ):  # Use the first constituent as the primary material
                                current_material = layer.Material.Name

        # Store this material in our database for future reference
        if current_material and current_material not in MaterialsToIgnore:
            element_data = {
                "element_type": plate.is_a(),
                "element_name": plate.Name if hasattr(plate, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
                "area": current_area,
            }

            # Add to database
            calculator_utils.add_material_to_database(element_data)

        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )
        if current_material_ec is None:
            missing_elements.append((plate.id(), current_material))

        if current_material_ec is None and MATERIAL_REAPLCE:
            # Try material matching
            if not current_material and material_layers:
                # If we have layer materials but no current material, use the most common
                material_layers_filtered = [
                    m for m in material_layers if m not in MaterialsToIgnore
                ]
                if material_layers_filtered:
                    current_material = max(
                        set(material_layers_filtered),
                        key=material_layers_filtered.count,
                    )

            element_data = {
                "element_type": plate.is_a(),
                "element_name": plate.Name if hasattr(plate, "Name") else None,
                "material_name": current_material,
                "material_type": "single",
                "volume": current_quantity,
                "area": current_area,
            }

            similar_material, similarity = calculator_utils.find_similar_material(
                element_data
            )

            if similar_material and similar_material in MaterialList:
                logger.info(
                    f"Material '{current_material}' not found. Using similar material '{similar_material}' (similarity: {similarity:.3f})"
                )
                current_material = similar_material
                current_material_ec = MaterialList.get(current_material)
            else:
                # For plates, try common materials like steel or glass if no match found
                for default_material in ["STEEL", "GLASS", "ALUMINIUM"]:
                    if default_material in MaterialList:
                        logger.warning(
                            f"No suitable material found for plate {plate.Name}. Using {default_material} as default."
                        )
                        current_material = default_material
                        current_material_ec = MaterialList.get(current_material)
                        break
                else:
                    logger.error(
                        f"No suitable material found for plate {plate.Name}. Skipping."
                    )
                    continue

        if current_quantity is None:
            if current_area is not None:
                # Estimate volume from area if possible
                # Assume a typical thickness for plates (e.g., 10mm = 0.01m)
                estimated_thickness = 0.01  # meters
                current_quantity = current_area * estimated_thickness
                logger.warning(
                    f"Estimating volume for plate {plate.Name} based on area: {current_quantity}"
                )
            else:
                # Try to calculate volume directly
                current_quantity = calculator_utils.get_element_volume(plate)

            if current_quantity is None or current_quantity <= 0:
                logger.error(
                    f"Failed to calculate positive volume for plate {plate.Name}. Skipping."
                )
                missing_elements.append(plate.id())
                continue

        material_ec_perkg, material_density = current_material_ec
        current_ec = material_ec_perkg * material_density * current_quantity
        materials_breakdown.append({"material": current_material, "ec": current_ec})

        plate_elements.append(
            {"element": "Plate", "ec": current_ec, "materials": materials_breakdown}
        )
        logger.debug(f"EC for {plate.Name} is {current_ec}")
        total_ec += current_ec

    logger.debug(f"Total EC for plates is {total_ec}")

    return total_ec, plate_elements, missing_elements


def calculate_piles(piles):

    total_ec = 0
    quantities = {}
    materials = []
    pile_elements = []
    missing_elements = []
    current_quantity = None
    current_material = None
    rebar = None

    for pile in piles:
        material_breakdown = []
        psets = get_psets(pile)
        rebar_set = psets.get("Rebar Set")
        if rebar_set is None:
            logger.error("Rebar set not found")
        if rebar_set:
            rebar = rebar_set.get("MainRebar")
            if rebar is None:
                logger.error("Rebar not found")

        dimensions = psets.get("Dimensions")
        if dimensions is None:
            logger.error("Dimensions/Diameter not found")
        if dimensions:
            lengthmm = dimensions.get("Length")
            if lengthmm is None:
                logger.error("Length not found")
            else:
                length = lengthmm / 1000
                logger.info(f"Length is: {length}")

        if rebar:
            rebar_no, area = rebar.split("H")
            rebar_vol = length * int(rebar_no) * 3.14 * ((int(area) / 2000) ** 2)

        if hasattr(pile, "IsDefinedBy"):
            for definition in pile.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_PileBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if (
                                quantity.is_a("IfcQuantityVolume")
                                and quantity.Name == "NetVolume"
                            ):
                                logger.debug(
                                    f"Found NetVolume  for {pile.Name}: {quantity.VolumeValue}"
                                )
                                quantities[quantity.Name] = quantity.VolumeValue
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        if hasattr(pile, "HasAssociations"):
            for association in pile.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        materials.append(material.Name)
                        current_material = material.Name
                        break
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage"
                            )
                            materials.append(layer.Material.Name)
                            current_material = material.Name
                            break
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet"
                            )
                            materials.append(layer.Material.Name)
                            current_material = material.Name
                            break

        if materials:
            logger.error("Material Layers code not implemented")
            continue

        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )

        if current_material_ec is None:
            logger.error(f"Could not find Material {current_material}")
            missing_elements.append((pile.id(), current_material))
            continue

        if current_quantity is None:
            logger.error(f"Failed to get volume for pile {pile.Name}. Skipping.")
            missing_elements.append(pile.id())
            continue
        material_ec_perkg, material_density = current_material_ec
        # print(current_quantity)
        if rebar == None:
            current_ec = material_ec_perkg * material_density * current_quantity

        else:
            current_ec = (
                material_ec_perkg * material_density * (current_quantity - rebar_vol)
            )
            rebar_ec = rebar_vol * 2.510 * 7850
            logger.debug(
                f"EC for {pile.Name}'s rebars is {rebar_ec} for volume of {rebar_vol}"
            )
            total_ec += rebar_ec

        material_breakdown.append({"material": current_material, "ec": current_ec})
        pile_elements.append(
            {"element": "Pile", "ec": current_ec, "materials": material_breakdown}
        )
        logger.debug(f"EC for {pile.Name} is {current_ec}")
        total_ec += current_ec

    logger.debug(f"Total EC for piles is {total_ec}")

    return total_ec, pile_elements, missing_elements


def calculate_footings(footings):
    total_ec = 0
    quantities = {}
    materials = []
    footing_elements = []
    missing_elements = []
    current_quantity = None
    current_material = None
    rebar = None

    for footing in footings:
        material_breakdown = []
        psets = get_psets(footing)
        rebar_set = psets.get("Rebar Set")
        if rebar_set is None:
            logger.error("Rebar set not found")
        if rebar_set:
            BD = rebar_set.get("BottomDistribution")
            BM = rebar_set.get("BottomMain")
            sidebar = rebar_set.get("SideBar")
            stirrups = rebar_set.get("Stirrups")
            TD = rebar_set.get("TopDistribution")
            TM = rebar_set.get("TopMain")
            if (
                BD == None
                or BM == None
                or sidebar == None
                or stirrups == None
                or TM == None
                or TD == None
            ):
                logger.error("Rebar part not found")

            # Get diameter and spacing
            BDdiameter, BDspacing = BD.split("-")
            BDdiameter = BDdiameter[1:3]
            BMdiameter, BMspacing = BM.split("-")
            BMdiameter = BMdiameter[1:3]
            sidebar_diameter, sidebar_spacing = sidebar.split("-")
            sidebar_diameter = sidebar_diameter[1:3]
            stirrups_diameter, stirrups_spacing, ignore = stirrups.split("-")
            stirrups_diameter = stirrups_diameter[1:3]
            TDdiameter, TDspacing = TD.split("-")
            TDdiameter = TDdiameter[1:3]
            TMdiameter, TMspacing = TM.split("-")
            TMdiameter = TMdiameter[1:3]

        # Get width and length
        dimensions = psets.get("Dimensions")
        if dimensions is None:
            logger.error("Dimensions/Diameter not found")
        if dimensions:
            lengthmm = dimensions.get("Length")
            if lengthmm is None:
                logger.error("Length not found")
            else:
                length = lengthmm / 1000

            widthmm = dimensions.get("Width")
            if widthmm is None:
                logger.error("Width not found")
            else:
                width = widthmm / 1000

            heightmm = dimensions.get("Foundation Thickness")
            if heightmm is None:
                logger.error("Height not found")
            else:
                height = heightmm / 1000
        # If width is more than length, flip
        # if length and width:
        #     if length < width:
        #         temp = length
        #         length = width
        #         width = temp

        if rebar_set:
            rebar_length = length - (2 * (50 / 1000))
            rebar_breadth = width - (2 * (50 / 1000))
            rebar_height = height - (2 * (50 / 1000))
            # Bottom

            length_rebarsno = math.floor(rebar_length / (int(BDspacing) / 1000)) + 1
            breadth_rebarsno = math.floor(rebar_breadth / (int(BMspacing) / 1000)) + 1

            bottom_vol = (
                breadth_rebarsno
                * rebar_length
                * (3.14 * ((int(BDdiameter) / 2000) ** 2))
            ) + (
                length_rebarsno
                * rebar_breadth
                * (3.14 * ((int(BMdiameter) / 2000) ** 2))
            )

            # Top
            length_rebarsno = math.floor(rebar_length / (int(TDspacing) / 1000)) + 1
            breadth_rebarsno = math.floor(rebar_breadth / (int(TMspacing) / 1000)) + 1

            top_vol = (
                breadth_rebarsno
                * rebar_length
                * (3.14 * ((int(TDdiameter) / 2000) ** 2))
            ) + (
                length_rebarsno
                * rebar_breadth
                * (3.14 * ((int(TMdiameter) / 2000) ** 2))
            )

            # Side
            length_rebarsno = math.floor(rebar_length / (int(TDspacing) / 1000)) + 1
            breadth_rebarsno = math.floor(rebar_breadth / (int(TMspacing) / 1000)) + 1
            height_rebarsno = (
                math.floor(rebar_height / (int(sidebar_spacing) / 1000)) + 1
            )

            # side_vol = (length * height) + (breadth * height) + (height * length) + (height * breadth)
            side_vol = (
                (
                    2
                    * (
                        length_rebarsno
                        * rebar_height
                        * (3.14 * ((int(sidebar_diameter) / 2000) ** 2))
                    )
                )
                + (
                    2
                    * (
                        breadth_rebarsno
                        * rebar_height
                        * (3.14 * ((int(sidebar_diameter) / 2000) ** 2))
                    )
                )
                + (
                    2
                    * (
                        height_rebarsno
                        * rebar_length
                        * (3.14 * ((int(sidebar_diameter) / 2000) ** 2))
                    )
                )
                + (
                    2
                    * (
                        height_rebarsno
                        * rebar_breadth
                        * (3.14 * ((int(sidebar_diameter) / 2000) ** 2))
                    )
                )
            )

            # Stirrups
            perimeter = (2 * rebar_breadth) + (2 * rebar_height)
            length_rebarsno = (
                math.floor(rebar_length / (int(stirrups_spacing) / 1000)) + 1
            )
            stirrups_vol = (
                length_rebarsno
                * perimeter
                * (3.14 * ((int(stirrups_diameter) / 2000) ** 2))
            )

        if hasattr(footing, "IsDefinedBy"):
            for definition in footing.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    property_def = definition.RelatingPropertyDefinition
                    if (
                        property_def.is_a("IfcElementQuantity")
                        and property_def.Name == "Qto_FootingBaseQuantities"
                    ):
                        for quantity in property_def.Quantities:
                            if quantity.is_a("IfcQuantityVolume") and (
                                quantity.Name == "NetVolume"
                                or quantity.Name == "GrossVolume"
                            ):
                                logger.debug(f"Found NetVolume  for {footing.Name}")
                                quantities[quantity.Name] = quantity.VolumeValue
                                current_quantity = quantity.VolumeValue
                                break
                        if current_quantity is not None:
                            break

        if hasattr(footing, "HasAssociations"):
            for association in footing.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        logger.debug(
                            f"Found material '{material.Name}', as IfcMaterial"
                        )
                        materials.append(material.Name)
                        current_material = material.Name
                        break
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSetUsage"
                            )
                            materials.append(layer.Material.Name)
                            current_material = material.Name
                            break
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            logger.debug(
                                f"Found material '{layer.Material.Name}', as IfcMaterialLayerSet"
                            )
                            materials.append(layer.Material.Name)
                            current_material = material.Name
                            break

        current_material_ec = (
            MaterialList.get(current_material, None) if current_material else None
        )

        if current_material_ec is None:
            logger.error(f"Could not find Material {current_material}")
            missing_elements.append((footing.id(), current_material))

        if current_quantity is None:
            logger.error(f"Failed to get volume for pile {footing.Name}. Skipping.")
            missing_elements.append(footing.id())
            continue
        material_ec_perkg, material_density = current_material_ec

        if rebar_set == None:
            current_ec = material_ec_perkg * material_density * current_quantity

        else:
            rebar_vol = top_vol + bottom_vol + side_vol + stirrups_vol
            # print(rebar_vol)
            current_ec = (
                material_ec_perkg * material_density * (current_quantity - rebar_vol)
            )
            rebar_ec = rebar_vol * 2.510 * 7850
            logger.debug(f"EC for {footing.Name}'s rebars is {rebar_ec}")
            total_ec += rebar_ec

        material_breakdown.append({"material": current_material, "ec": current_ec})
        footing_elements.append(
            {"element": "Footing", "ec": current_ec, "materials": material_breakdown}
        )
        logger.debug(f"EC for {footing.Name} is {current_ec}")
        total_ec += current_ec

    logger.debug(f"Total EC for footings is {total_ec}")

    return total_ec, footing_elements, missing_elements


def calculate_embodied_carbon(filepath, with_breakdown=False):
    global MaterialList
    MaterialList = calculator_utils.refresh_materials_list()
    slabs_to_ignore = []
    all_missing_materials = {}
    all_excel_data = []
    total_ec = columns_ec = beams_ec = slabs_ec = walls_ec = windows_ec = roofs_ec = (
        doors_ec
    ) = stairs_ec = railings_ec = members_ec = plates_ec = piles_ec = footings_ec = 0
    ec_by_elements = {}
    # Create data structure for EC breakdown
    ec_data = {
        "total_ec": 0,
        "ec_breakdown": [
            {"category": "Substructure", "total_ec": 0, "elements": []},
            {"category": "Superstructure", "total_ec": 0, "elements": []},
        ],
    }

    ifc_file = ifcopenshell.open(filepath)

    # Get elements by level
    substructure_elements = calculator_utils.get_substructure_elements(filepath)

    # Create sets for quick lookup
    substructure_ids = {elem.id() for elem in substructure_elements}

    # Get all elements from the model
    columns = ifc_file.by_type("IfcColumn")
    beams = ifc_file.by_type("IfcBeam")
    slabs = ifc_file.by_type("IfcSlab")
    walls = ifc_file.by_type("IfcWall")
    windows = ifc_file.by_type("IfcWindow")
    roofs = ifc_file.by_type("IfcRoof")
    doors = ifc_file.by_type("IfcDoor")
    stairs = ifc_file.by_type("IfcStairFlight")
    railings = ifc_file.by_type("IfcRailing")
    members = ifc_file.by_type("IfcMember")
    plates = ifc_file.by_type("IfcPlate")
    piles = ifc_file.by_type("IfcPile")
    footings = ifc_file.by_type("IfcFooting")

    # IFcstair is calculated under slabs and stairflight, this is only used to consider the stair as "considered" in the EC calculation.
    whole_stairs = ifc_file.by_type("IfcStair")
    all_elements = ifc_file.by_type("IfcBuildingElement")

    considered_elements = set()
    for element_list in [
        columns,
        beams,
        slabs,
        walls,
        windows,
        roofs,
        doors,
        stairs,
        railings,
        members,
        plates,
        piles,
        footings,
        whole_stairs,
    ]:
        considered_elements.update(element_list)

    element_type_skipped = set(all_elements) - considered_elements
    element_type_skipped = [
        (element.id(), element.is_a()) for element in element_type_skipped
    ]

    # Log element counts
    # logger.info(f"Total columns found {len(columns)}")
    # logger.info(f"Total beams found {len(beams)}")
    # logger.info(f"Total slabs found {len(slabs)}")
    # logger.info(f"Total roofs found {len(roofs)}")
    # logger.info(f"Total windows found {len(windows)}")
    # logger.info(f"Total walls found {len(walls)}")
    # logger.info(f"Total doors found {len(doors)}")
    # logger.info(f"Total stairflights found {len(stairs)}")
    # logger.info(f"Total railings found {len(railings)}")
    # logger.info(f"Total members found {len(members)}")
    # logger.info(f"Total plates found {len(plates)}")
    # logger.info(f"Total piles found {len(piles)}")
    # logger.info(f"Total footings found {len(footings)}")

    # Identify which slabs to ignore (those part of roofs)
    if roofs:
        for roof in roofs:
            if hasattr(roof, "IsDecomposedBy"):
                for rel in roof.IsDecomposedBy:
                    if rel.is_a("IfcRelAggregates"):
                        for part in rel.RelatedObjects:
                            if part.is_a("IfcSlab"):
                                slabs_to_ignore.append(part.id())

    # Split elements into substructure and superstructure based on ID
    # Columns
    if columns:
        substructure_columns = [c for c in columns if c.id() in substructure_ids]
        superstructure_columns = [c for c in columns if c.id() not in substructure_ids]
        all_missing_materials["IfcColumn"] = []
        if substructure_columns:
            sub_columns_ec, sub_columns_elements, missing_mats, columns_excel_data = (
                calculate_columns(substructure_columns)
            )
            all_excel_data.extend(columns_excel_data)
            all_missing_materials["IfcColumn"].extend(missing_mats)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_columns_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_columns_ec
            columns_ec += sub_columns_ec

        if superstructure_columns:
            (
                super_columns_ec,
                super_columns_elements,
                missing_mats,
                columns_excel_data,
            ) = calculate_columns(superstructure_columns)
            all_missing_materials["IfcColumn"].extend(missing_mats)
            all_excel_data.extend(columns_excel_data)

            ec_data["ec_breakdown"][1]["elements"].extend(super_columns_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_columns_ec
            columns_ec += super_columns_ec
        ec_by_elements["Columns"] = columns_ec
    # Beams
    if beams:
        substructure_beams = [b for b in beams if b.id() in substructure_ids]
        superstructure_beams = [b for b in beams if b.id() not in substructure_ids]
        all_missing_materials["IfcBeam"] = []

        if substructure_beams:
            sub_beams_ec, sub_beams_elements, missing_mats, beam_excel_data = (
                calculate_beams(substructure_beams)
            )
            all_missing_materials["IfcBeam"].extend(missing_mats)
            all_excel_data.extend(beam_excel_data)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_beams_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_beams_ec
            beams_ec += sub_beams_ec

        if superstructure_beams:
            super_beams_ec, super_beams_elements, missing_mats, beam_excel_data = (
                calculate_beams(superstructure_beams)
            )
            all_missing_materials["IfcBeam"].extend(missing_mats)
            all_excel_data.extend(beam_excel_data)

            ec_data["ec_breakdown"][1]["elements"].extend(super_beams_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_beams_ec
            beams_ec += super_beams_ec
        ec_by_elements["Beam"] = beams_ec

    # Slabs
    if slabs:
        valid_slabs = [s for s in slabs if s.id() not in slabs_to_ignore]
        substructure_slabs = [s for s in valid_slabs if s.id() in substructure_ids]
        superstructure_slabs = [
            s for s in valid_slabs if s.id() not in substructure_ids
        ]
        all_missing_materials["IfcSlab"] = []
        if substructure_slabs:
            sub_slabs_ec, sub_slabs_elements, missing_mats, slab_excel_data = (
                calculate_slabs(substructure_slabs)
            )
            all_missing_materials["IfcSlab"].extend(missing_mats)
            all_excel_data.extend(slab_excel_data)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_slabs_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_slabs_ec
            slabs_ec += sub_slabs_ec

        if superstructure_slabs:
            super_slabs_ec, super_slabs_elements, missing_mats, slab_excel_data = (
                calculate_slabs(superstructure_slabs)
            )
            all_missing_materials["IfcSlab"].extend(missing_mats)
            all_excel_data.extend(slab_excel_data)

            ec_data["ec_breakdown"][1]["elements"].extend(super_slabs_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_slabs_ec
            slabs_ec += super_slabs_ec
        ec_by_elements["Slabs"] = slabs_ec

    # Walls
    if walls:
        substructure_walls = [w for w in walls if w.id() in substructure_ids]
        superstructure_walls = [w for w in walls if w.id() not in substructure_ids]
        all_missing_materials["IfcWall"] = []
        if substructure_walls:
            sub_walls_ec, sub_walls_elements, missing_mats, wall_excel_data = (
                calculate_walls(substructure_walls)
            )
            all_missing_materials["IfcWall"].extend(missing_mats)
            all_excel_data.extend(wall_excel_data)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_walls_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_walls_ec
            walls_ec += sub_walls_ec

        if superstructure_walls:
            super_walls_ec, super_walls_elements, missing_mats, wall_excel_data = (
                calculate_walls(superstructure_walls)
            )
            all_missing_materials["IfcWall"].extend(missing_mats)
            all_excel_data.extend(wall_excel_data)
            ec_data["ec_breakdown"][1]["elements"].extend(super_walls_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_walls_ec
            walls_ec += super_walls_ec
        ec_by_elements["Walls"] = walls_ec

    # Windows - can be in both, so check against substructure IDs
    if windows:
        substructure_windows = [w for w in windows if w.id() in substructure_ids]
        superstructure_windows = [w for w in windows if w.id() not in substructure_ids]
        all_missing_materials["IfcWindow"] = []
        if substructure_windows:
            sub_windows_ec, sub_windows_elements, missing_mats, window_excel_data = (
                calculate_windows(substructure_windows)
            )
            all_missing_materials["IfcWindow"].extend(missing_mats)
            all_excel_data.extend(window_excel_data)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_windows_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_windows_ec
            windows_ec += sub_windows_ec

        if superstructure_windows:
            (
                super_windows_ec,
                super_windows_elements,
                missing_mats,
                window_excel_data,
            ) = calculate_windows(superstructure_windows)
            all_missing_materials["IfcWindow"].extend(missing_mats)
            all_excel_data.extend(window_excel_data)
            ec_data["ec_breakdown"][1]["elements"].extend(super_windows_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_windows_ec
            windows_ec += super_windows_ec

        total_ec += windows_ec
        ec_by_elements["Windows"] = windows_ec

    # Doors - can be in both, so check against substructure IDs
    if doors:
        substructure_doors = [d for d in doors if d.id() in substructure_ids]
        superstructure_doors = [d for d in doors if d.id() not in substructure_ids]
        all_missing_materials["IfcDoor"] = []
        if substructure_doors:
            sub_doors_ec, sub_doors_elements, missing_mats, door_excel_data = (
                calculate_doors(substructure_doors)
            )
            all_missing_materials["IfcDoor"].extend(missing_mats)
            all_excel_data.extend(door_excel_data)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_doors_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_doors_ec
            doors_ec += sub_doors_ec

        if superstructure_doors:
            super_doors_ec, super_doors_elements, missing_mats, door_excel_data = (
                calculate_doors(superstructure_doors)
            )
            all_missing_materials["IfcDoor"].extend(missing_mats)
            all_excel_data.extend(door_excel_data)

            ec_data["ec_breakdown"][1]["elements"].extend(super_doors_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_doors_ec
            doors_ec += super_doors_ec
        ec_by_elements["Doors"] = doors_ec

    # Roofs are always in superstructure
    if roofs:
        roofs_ec, roofs_elements, missing_mats, roof_excel_data = calculate_roofs(roofs)
        all_missing_materials["IfcRoof"] = missing_mats
        ec_data["ec_breakdown"][1]["elements"].extend(roofs_elements)
        all_excel_data.extend(roof_excel_data)
        ec_data["ec_breakdown"][1]["total_ec"] += roofs_ec
        total_ec += roofs_ec
        ec_by_elements["Roofs"] = roofs_ec

    # Stairs
    if stairs:
        substructure_stairs = [s for s in stairs if s.id() in substructure_ids]
        superstructure_stairs = [s for s in stairs if s.id() not in substructure_ids]
        all_missing_materials["IfcStairFlight"] = []
        if substructure_stairs:
            sub_stairs_ec, sub_stairs_elements, missing_mats = calculate_stairs(
                substructure_stairs
            )
            all_missing_materials["IfcStairFlight"].extend(missing_mats)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_stairs_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_stairs_ec
            stairs_ec += sub_stairs_ec

        if superstructure_stairs:
            super_stairs_ec, super_stairs_elements, missing_mats = calculate_stairs(
                superstructure_stairs
            )
            all_missing_materials["IfcStairFlight"].extend(missing_mats)
            ec_data["ec_breakdown"][1]["elements"].extend(super_stairs_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_stairs_ec
            stairs_ec += super_stairs_ec
        ec_by_elements["Stairs"] = stairs_ec

    # Railings
    if railings:
        substructure_railings = [r for r in railings if r.id() in substructure_ids]
        superstructure_railings = [
            r for r in railings if r.id() not in substructure_ids
        ]
        all_missing_materials["IfcRailing"] = []
        if substructure_railings:
            sub_railings_ec, sub_railings_elements, missing_mats = calculate_railings(
                substructure_railings
            )
            all_missing_materials["IfcRailing"].extend(missing_mats)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_railings_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_railings_ec
            railings_ec += sub_railings_ec

        if superstructure_railings:
            super_railings_ec, super_railings_elements, missing_mats = (
                calculate_railings(superstructure_railings)
            )
            all_missing_materials["IfcRailing"].extend(missing_mats)
            ec_data["ec_breakdown"][1]["elements"].extend(super_railings_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_railings_ec
            railings_ec += super_railings_ec
        ec_by_elements["Railings"] = railings_ec

    # Members
    if members:
        substructure_members = [m for m in members if m.id() in substructure_ids]
        superstructure_members = [m for m in members if m.id() not in substructure_ids]
        all_missing_materials["IfcMember"] = []

        if substructure_members:
            sub_members_ec, sub_members_elements, missing_mats = calculate_members(
                substructure_members
            )
            all_missing_materials["IfcMember"].extend(missing_mats)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_members_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_members_ec
            members_ec += sub_members_ec

        if superstructure_members:
            super_members_ec, super_members_elements, missing_mats = calculate_members(
                superstructure_members
            )
            all_missing_materials["IfcMember"].extend(missing_mats)
            ec_data["ec_breakdown"][1]["elements"].extend(super_members_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_members_ec
            members_ec += super_members_ec
        ec_by_elements["Members"] = members_ec

    # Plates
    if plates:
        substructure_plates = [p for p in plates if p.id() in substructure_ids]
        superstructure_plates = [p for p in plates if p.id() not in substructure_ids]
        all_missing_materials["IfcPlate"] = []

        if substructure_plates:
            sub_plates_ec, sub_plates_elements, missing_mats = calculate_plates(
                substructure_plates
            )
            all_missing_materials["IfcPlate"].extend(missing_mats)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_plates_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_plates_ec
            plates_ec += sub_plates_ec

        if superstructure_plates:
            super_plates_ec, super_plates_elements, missing_mats = calculate_plates(
                superstructure_plates
            )
            all_missing_materials["IfcPlate"].extend(missing_mats)
            ec_data["ec_breakdown"][1]["elements"].extend(super_plates_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_plates_ec
            plates_ec += super_plates_ec
        ec_by_elements["Plates"] = plates_ec

    # Piles and footings are always in substructure by definition
    if piles:
        substructure_piles = [p for p in piles if p.id() in substructure_ids]
        superstructure_piles = [p for p in piles if p.id() not in substructure_ids]
        all_missing_materials["IfcPile"] = []

        if substructure_piles:
            sub_piles_ec, sub_piles_elements, missing_mats = calculate_piles(
                substructure_piles
            )
            all_missing_materials["IfcPile"].extend(missing_mats)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_piles_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_piles_ec
            piles_ec += sub_piles_ec

        if superstructure_piles:
            super_piles_ec, super_piles_elements, missing_mats = calculate_piles(
                superstructure_piles
            )
            all_missing_materials["IfcPile"].extend(missing_mats)
            ec_data["ec_breakdown"][1]["elements"].extend(super_piles_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_piles_ec
            piles_ec += super_piles_ec
        ec_by_elements["Piles"] = piles_ec

    if footings:
        substructure_footings = [f for f in footings if f.id() in substructure_ids]
        superstructure_footings = [f for f in piles if f.id() not in substructure_ids]
        all_missing_materials["IfcFooting"] = []

        if substructure_footings:
            sub_footings_ec, sub_footings_elements, missing_mats = calculate_footings(
                substructure_footings
            )
            all_missing_materials["IfcFooting"].extend(missing_mats)
            ec_data["ec_breakdown"][0]["elements"].extend(sub_footings_elements)
            ec_data["ec_breakdown"][0]["total_ec"] += sub_footings_ec
            footings_ec += sub_footings_ec

        if superstructure_footings:
            super_footings_ec, super_footings_elements, missing_mats = (
                calculate_footings(superstructure_footings)
            )
            all_missing_materials["IfcFooting"].extend(missing_mats)
            ec_data["ec_breakdown"][1]["elements"].extend(super_footings_elements)
            ec_data["ec_breakdown"][1]["total_ec"] += super_footings_ec
            footings_ec += super_footings_ec
        ec_by_elements["Footings"] = footings_ec

    # Calculate total EC by summing individual categories
    total_ec = (
        columns_ec
        + beams_ec
        + slabs_ec
        + walls_ec
        + windows_ec
        + doors_ec
        + stairs_ec
        + railings_ec
        + roofs_ec
        + members_ec
        + plates_ec
        + piles_ec
        + footings_ec
    )
    ec_data["total_ec"] = total_ec
    logger.info(f"Total EC calculated: {total_ec}")
    logger.info(
        f"Breakdown:\n {columns_ec=}\n {beams_ec=}\n {slabs_ec=}\n\
{walls_ec=}\n {windows_ec=}\n {doors_ec=}\n {stairs_ec=} \n \
{railings_ec=}\n {roofs_ec=}\n {members_ec=}\n {plates_ec=}\n \
{piles_ec=}\n {footings_ec=}"
    )
    ec_by_building_system = {}
    ec_by_building_system["substructure_ec"] = ec_data["ec_breakdown"][0]["total_ec"]
    ec_by_building_system["superstructure_ec"] = ec_data["ec_breakdown"][1]["total_ec"]
    logger.info(
        f"Breakdown by category: Substructure EC: {ec_data['ec_breakdown'][0]['total_ec']}, Superstructure EC: {ec_data['ec_breakdown'][1]['total_ec']}"
    )
    ec_data["missing_materials"] = all_missing_materials
    logger.info(
        f"Elements with missing/unknown materials/missing volume: {all_missing_materials}"
    )
    ec_data["element_type_skipped"] = element_type_skipped
    logger.info(f"Elements skippsed: {element_type_skipped}")
    # print(ec_data)
    logger.info(f"Breakdown by elements: {ec_by_elements}")

    ec_by_materials = get_ec_by_material_category(ec_data)
    logger.info(f"Breakdown by materials: {ec_by_materials}\n")

    summary = {}
    summary["by_building_system"] = ec_by_building_system
    summary["by_material"] = ec_by_materials
    summary["by_element"] = ec_by_elements

    if with_breakdown:
        return total_ec, ec_data, summary, all_excel_data
    else:
        return total_ec


def categorize_material(material_name):
    material_name = material_name.lower()
    if "concrete" in material_name:
        return "Concrete"
    elif "window" in material_name:
        return "Window"
    elif "door" in material_name:
        return "Door"
    elif "wood" in material_name:
        return "Wood"
    elif "aluminium" in material_name:
        return "Aluminium"
    elif "granite" in material_name:
        return "Granite"
    elif "plywood" in material_name:
        return "Plywood"
    elif "steel" in material_name:
        return "Steel"
    elif "Reinforcement" in material_name:
        return "Rebar"
    else:
        return "Others"


def get_ec_by_material_category(breakdowns):
    ec_by_material = {}

    for category in breakdowns.get("ec_breakdown", []):
        for element in category.get("elements", []):
            for material in element.get("materials", []):
                material_name = material.get("material", "")
                ec = material.get("ec", 0)
                material_category = categorize_material(material_name)

                if material_category not in ec_by_material:
                    ec_by_material[material_category] = 0
                ec_by_material[material_category] += ec

    return ec_by_material


def calculate_gfa(filepath):

    ifc_file = ifcopenshell.open(filepath)
    spaces = ifc_file.by_type("IfcSpace")
    logger.info(f"Total spaces found {len(spaces)}")

    if len(spaces) == 0:
        logger.error("No spaces found.")
        return 0

    total_area = 0

    for space in spaces:
        # Get the area from quantities
        # total_area += calculator_utils.get_element_area(space)
        psets = get_psets(space)
        qto = psets.get("Qto_SpaceBaseQuantities")
        if not qto:
            logger.error(
                f"{space} has no pset Qto_SpaceBaseQuantities, skipping this element"
            )
            return 0
        gfa = qto.get("GrossFloorArea")
        if not gfa:
            logger.error(
                f"{space} has no GFA in Qto_SpaceBaseQuantities, skipping this element"
            )
            return 0
        total_area += gfa

    logger.info(f"Total GFA calculated: {total_area}")
    return total_area


if __name__ == "__main__":
    # Run the calculator on the specified IFC file
    # ifcpath = input("Enter path to IFC file: ")
    ifcpath = "/Users/jk/Downloads/z. Complex Models/Complex 4 Error Test.ifc"
    logger.info(f"Processing file: {ifcpath}")

    if not os.path.exists(ifcpath):
        logger.error(f"File not found: {ifcpath}")
        sys.exit(1)

    total_ec, ec_data, summary, excel_data = calculate_embodied_carbon(
        ifcpath, with_breakdown=True
    )
    total_gfa = calculate_gfa(ifcpath)
    print(summary)

    if total_gfa > 0:
        ec_per_m2 = total_ec / total_gfa
        logger.info(f"Embodied carbon per m²: {ec_per_m2} kgCO2e/m²")

    print(f"\nResults for {os.path.basename(ifcpath)}:")
    print(f"Totalifc Embodied Carbon: {total_ec:.2f} kgCO2e\n")
    # print(f"Breakdowns: {ec_data}")

    if total_gfa > 0:
        print(f"Total Gross Floor Area: {total_gfa} m²")
        print(f"Embodied Carbon per m²: {ec_per_m2} kgCO2e/m²")
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Execution time: {elapsed_time:.2f} seconds")
