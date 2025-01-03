from flask import Flask, request, render_template, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
import subprocess
import ifcopenshell

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = './uploads'
OUTPUT_FOLDER = './static/models'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size: 16MB

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# From ICE database
MaterialList = {"Concrete, Cast In Situ": [0.090, 220]}  # kgCO2e per kg, kg per m^3 (Gen 1)


def calculate_embodied_carbon(filepath):
    ifc_file = ifcopenshell.open(filepath)

    # Initialize variables
    totalEC = 0
    slabEC = 0
    wallEC = 0

    # Calculate for walls
    walls = ifc_file.by_type('IfcWall')
    materials = []
    quantities = {}
    for element in walls:
        if hasattr(element, "IsDefinedBy"):
            for definition in element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_WallBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                quantities[quantity.Name] = quantity.VolumeValue

        if hasattr(element, "HasAssociations"):
            for association in element.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        materials.append(material.Name)
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            materials.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            materials.append(layer.Material.Name)

    for i in range(len(materials)):
        if materials[i] in MaterialList:
            wallEC += (quantities.get("NetVolume", 0) * MaterialList[materials[i]][0] * MaterialList[materials[i]][1])

    totalEC += wallEC

    # Calculate for slabs
    slabs = ifc_file.by_type('IfcSlab')
    materials = []
    quantities = {}
    for slab in slabs:
        if hasattr(slab, "IsDefinedBy"):
            for definition in slab.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_def = definition.RelatingPropertyDefinition
                    if property_def.is_a('IfcElementQuantity') and property_def.Name == 'Qto_SlabBaseQuantities':
                        for quantity in property_def.Quantities:
                            if quantity.is_a('IfcQuantityVolume') and quantity.Name == 'NetVolume':
                                quantities[quantity.Name] = quantity.VolumeValue

        if hasattr(slab, "HasAssociations"):
            for association in slab.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        materials.append(material.Name)
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        for layer in material.ForLayerSet.MaterialLayers:
                            materials.append(layer.Material.Name)
                    elif material.is_a("IfcMaterialLayerSet"):
                        for layer in material.MaterialLayers:
                            materials.append(layer.Material.Name)

    for i in range(len(materials)):
        if materials[i] in MaterialList:
            slabEC += (quantities.get("NetVolume", 0) * MaterialList[materials[i]][0] * MaterialList[materials[i]][1])

    totalEC += slabEC

    return {"slabEC": slabEC, "wallEC": wallEC, "totalEC": totalEC}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and file.filename.lower().endswith('.ifc'):
        filename = os.path.splitext(secure_filename(file.filename))[0]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}.ifc")
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{filename}.glb")
        file.save(filepath)

        try:
            # Convert IFC to GLB using IfcConvert
            subprocess.run(["IfcConvert", filepath, output_path], check=True)
            print(f"Converted {filepath} to {output_path}")

            # Calculate embodied carbon
            results = calculate_embodied_carbon(filepath)
            return jsonify({'message': 'File uploaded successfully!', 'model': f"/static/models/{filename}.glb", **results}), 200
        except subprocess.CalledProcessError as e:
            print(f"Conversion Error: {e}")
            return jsonify({'error': f'Error processing IFC file: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Error processing IFC file: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Please upload an .ifc file'}), 400


@app.route('/static/models/<path:filename>')
def serve_model(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
