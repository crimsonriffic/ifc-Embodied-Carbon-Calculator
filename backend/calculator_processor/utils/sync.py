import pandas as pd
import numpy as np
import os

# File paths - update these to match your actual file paths
CSV_PATH = "material_database.csv"
NPY_PATH = "material_embeddings.npy"

def manually_synchronize():
    """Manually synchronize NPY embeddings with edited CSV file.
    This function preserves the exact row-to-embedding correspondence.
    """
    # 1. Load the current CSV file
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file {CSV_PATH} not found.")
        return False
        
    try:
        csv_data = pd.read_csv(CSV_PATH)
        print(f"Loaded CSV with {len(csv_data)} rows")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return False
    
    # 2. Load the current NPY file
    if not os.path.exists(NPY_PATH):
        print(f"Error: NPY file {NPY_PATH} not found.")
        return False
        
    try:
        embeddings = np.load(NPY_PATH)
        print(f"Loaded embeddings array with {len(embeddings)} embeddings")
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        return False
    
    # 3. Get indices to keep based on material names
    # You'll need to modify this section based on your specific needs
    
    # Example: Keep only rows for specific materials
    # materials_to_keep = ["Concrete, General", "Aluminium, General"]
    # indices_to_keep = csv_data[csv_data['material_name'].isin(materials_to_keep)].index.tolist()
    
    # Example: Keep specific row indices (0-based, like Python lists)
    indices_to_keep = [0, 1,2, 3,4, 5,6,7]  # Replace with the actual indices you want to keep
    
    print(f"Keeping {len(indices_to_keep)} rows/embeddings")
    
    # 4. Filter both the CSV and NPY files
    try:
        # Filter CSV
        filtered_csv = csv_data.iloc[indices_to_keep].reset_index(drop=True)
        # Filter embeddings
        filtered_embeddings = embeddings[indices_to_keep]
        
        # Save files
        filtered_csv.to_csv(CSV_PATH, index=False)
        np.save(NPY_PATH, filtered_embeddings)
        
        print(f"Successfully saved synchronized files. New record count: {len(filtered_csv)}")
        return True
    except Exception as e:
        print(f"Error during synchronization: {e}")
        return False

if __name__ == "__main__":
    manually_synchronize()