from flask import Flask, request, render_template, jsonify
import os
from werkzeug.utils import secure_filename
import ifcopenshell

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size: 16MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Optionally, parse the IFC file with ifcopenshell
        try:
            ifc_model = ifcopenshell.open(filepath)
            # Perform any backend processing here
            return jsonify({'message': 'File uploaded successfully!', 'file': filename}), 200
        except Exception as e:
            return jsonify({'error': f'Error processing IFC file: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Please upload an .ifc file'}), 400

if __name__ == '__main__':
    app.run(debug=True)
