import requests
import os
from pathlib import Path
from datetime import datetime
import json

BASE_URL = "http://localhost:8000"


def test_get_projects(user_id: str):
    """Test the get projects endpoint with query parameters"""
    print(f"\n===Testing GET projects for user {user_id}===")

    # Using query parameter for user_id
    response = requests.get(f"{BASE_URL}/projects", params={"user_id": user_id})

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        projects = response.json()
        print("\nProjects found:")
        for project in projects:
            print(f"\nProject Name: {project['project_name']}")
            print(f"Project ID: {project['_id']}")
            print(f"Client: {project['client_name']}")
            print(f"Current Version: {project['current_version']}")

            # Print user's specific access level for this project
            user_access = project["access_control"].get(user_id, {})
            print(f"User Role: {user_access.get('role', 'No role')}")
            print(f"User Permissions: {', '.join(user_access.get('permissions', []))}")
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")


def test_upload_ifc(project_id: str, file_path: str, user_id: str):
    """Test the IFC file upload endpoint"""
    print(f"\n===Testing IFC file upload for project {project_id}===")

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
        # Using query parameter for user_id
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/upload_ifc",
            files=files,
            params={"user_id": user_id},
        )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nUpload Success:")
        print(f"Version: {result['version']}")
        print(f"Message: {result['message']}")
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")


def test_get_project_info(project_id: str):
    """Test getting project info and EC calculation"""
    print(f"\n===Testing GET project info for {project_id}===")

    response = requests.get(f"{BASE_URL}/projects/{project_id}/get_info")

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nProject Info:")
        print(f"Project ID: {project_id}")
        print(f"EC Value: {result['embodied_carbon']}")
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")


# TODO
def test_create_project(user_id: str):
    """Test creating a new project"""
    print(f"\n===Testing CREATE project===")

    project_data = {
        "project_name": "Test Project 2",
        "client_name": "Test Client",
        "user_job_role": "Test Engineer",
        "last_edited_date": "2024-01-21T00:00:00.000+00:00",
        "last_edited_user": user_id,
        "current_version": 1,
        "access_control": {
            "user789": {
                "role": "owner",
                "permissions": [
                    "read",
                    "write",
                    "execute",
                    "delete",
                    "admin",
                ],  # Example permissions
            },
            "user123": {
                "role": "viewer",
                "permissions": ["read"],  # Example permissions
            },
        },
        "edit_history": [
            {
                "timestamp": "2024-01-21T00:00:00.000+00:00",
                "user": "Mike Johnson",
                "action": "created_project",
                "description": "Project initialization",
            }
        ],
        "ifc_versions": {
            1: {
                "total_ec": 3000,
                "date_uploaded": "2024-01-21T00:00:00.000+00:00",
                "uploaded_by": user_id,
                "file_path": "s3://bucket/proj_789/v1.ifc",
            }
        },
    }

    response = requests.post(
        f"{BASE_URL}/create_project",
        json=project_data,
        params={"user_id": user_id},  # Using query parameter for user_id
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nProject Created:")
        print(f"Project ID: {result['_id']}")
        print(f"Project Name: {result['project_name']}")
        return result["_id"]  # Return the ID for use in other tests
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")
        return None


def test_get_projects(user_id: str):
    """Test the get projects endpoint with query parameters"""
    print(f"\n===Testing GET projects for user {user_id}===")

    # Using query parameter for user_id
    response = requests.get(f"{BASE_URL}/projects", params={"user_id": user_id})

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        projects = response.json()
        print("\nProjects found:")
        for project in projects:
            print(f"\nProject Name: {project['project_name']}")
            print(f"Project ID: {project['_id']}")
            print(f"Client: {project['client_name']}")
            print(f"Current Version: {project['current_version']}")

            # Print user's specific access level for this project
            user_access = project["access_control"].get(user_id, {})
            print(f"User Role: {user_access.get('role', 'No role')}")
            print(f"User Permissions: {', '.join(user_access.get('permissions', []))}")
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")


def test_upload_ifc(project_id: str, file_path: str, user_id: str):
    """Test the IFC file upload endpoint"""
    print(f"\n===Testing IFC file upload for project {project_id}===")

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
        # Using query parameter for user_id
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/upload_ifc",
            files=files,
            params={"user_id": user_id},
        )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nUpload Success:")
        print(f"Version: {result['version']}")
        print(f"Message: {result['message']}")
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")


def test_get_project_info(project_id: str):
    """Test getting project info and EC calculation"""
    print(f"\n===Testing GET project info for {project_id}===")

    response = requests.get(f"{BASE_URL}/projects/{project_id}/get_info")

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nProject Info:")
        print(f"Project ID: {project_id}")
        print(f"EC Value: {result['embodied_carbon']}")
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")


def test_create_project(user_id: str):
    """Test creating a new project"""
    print(f"\n===Testing CREATE project===")

    project_data = {
        "project_name": "Test Project 2",
        "client_name": "Test Client",
        "user_job_role": "Test Engineer",
        "last_edited_date": "2024-01-21T00:00:00.000+00:00",
        "last_edited_user": user_id,
        "current_version": 1,
        "access_control": {
            "user789": {
                "role": "owner",
                "permissions": [
                    "read",
                    "write",
                    "execute",
                    "delete",
                    "admin",
                ],  # Example permissions
            },
            "user123": {
                "role": "viewer",
                "permissions": ["read"],  # Example permissions
            },
        },
        "edit_history": [
            {
                "timestamp": "2024-01-21T00:00:00.000+00:00",
                "user": "Mike Johnson",
                "action": "created_project",
                "description": "Project initialization",
            }
        ],
        "ifc_versions": {
            "1": {
                "total_ec": 3000,
                "date_uploaded": "2024-01-21T00:00:00.000+00:00",
                "uploaded_by": user_id,
                "file_path": "s3://bucket/proj_789/v1.ifc",
            }
        },
    }

    response = requests.post(
        f"{BASE_URL}/create_project",
        json=project_data,
        params={"user_id": user_id},  # Using query parameter for user_id
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nProject Created:")
        print(f"Project ID: {result['_id']}")
        print(f"Project Name: {result['project_name']}")
        return result["_id"]  # Return the ID for use in other tests
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")
        return None


# New Material Tests


def test_get_materials(material_name=None):
    """Test the get materials endpoint"""
    print(f"\n===Testing GET materials===")

    params = {}
    if material_name:
        params["material_name"] = material_name
        print(f"Filtering by material name: {material_name}")

    response = requests.get(f"{BASE_URL}/materials", params=params)

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        materials = response.json()
        print(f"\nMaterials found: {len(materials)}")
        for material in materials:
            print(f"\nMaterial Type: {material['material_type']}")
            print(f"Specified Material: {material['specified_material']}")
            print(
                f"Embodied Carbon: {material['embodied_carbon']} {material.get('unit', '')}"
            )
            print(f"Database Source: {material['database_source']}")
            if "density" in material and material["density"] is not None:
                print(f"Density: {material['density']}")
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")
    return response.json() if response.status_code == 200 else None


def test_upload_material(user_id: str, with_density=True):
    """Test uploading a new material"""
    print(f"\n===Testing CREATE material===")

    # Generate a unique material name to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    material_data = {
        "material_type": "Test Material",
        "specified_material": f"Test Specification {timestamp}",
        "embodied_carbon": 123.45,
        "unit": "kg",
        "database_source": "Custom",
    }

    # Add density only if requested
    if with_density:
        material_data["density"] = 2000.0

    print(f"Material data: {json.dumps(material_data, indent=2)}")

    response = requests.post(
        f"{BASE_URL}/materials", json=material_data, params={"user_id": user_id}
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nMaterial Created:")
        print(f"Material ID: {result.get('_id')}")
        print(f"Material Type: {result.get('material_type')}")
        print(f"Specified Material: {result.get('specified_material')}")
        print(f"Embodied Carbon: {result.get('embodied_carbon')} {result.get('unit')}")
        if result.get("density") is not None:
            print(f"Density: {result.get('density')}")
        return result.get("_id")
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")
        return None


def test_delete_material(material_id: str, user_id: str):
    """Test deleting a material"""
    print(f"\n===Testing DELETE material {material_id}===")

    response = requests.delete(
        f"{BASE_URL}/materials/{material_id}", params={"user_id": user_id}
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nMaterial Deleted:")
        print(f"Message: {result.get('message')}")
        return True
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")
        return False


def upload_material(material_name, material_data, user_id):
    """Upload a single material or update if it exists"""
    # Check if material already exists
    response = requests.get(
        f"{BASE_URL}/materials", params={"material_name": material_name}
    )

    # Determine material type and properties
    if isinstance(material_data, list):
        # Format: [embodied_carbon, density]
        embodied_carbon = material_data[0]
        density = material_data[1]
        unit = "kg"  # For materials with density, use kg
    else:
        # Format: embodied_carbon value only
        embodied_carbon = material_data
        density = None
        unit = "m2"  # For materials without density, assume it's per m²

    # Determine material type (from name before first comma)
    material_type = material_name.split(",")[0] if "," in material_name else "General"

    # Prepare material data
    material_payload = {
        "material_type": material_type,
        "specified_material": material_name,
        "embodied_carbon": embodied_carbon,
        "unit": unit,
        "database_source": "System",
    }

    if density is not None:
        material_payload["density"] = density

    # If material exists, update it
    if response.status_code == 200 and len(response.json()) > 0:
        material_id = response.json()[0]["_id"]
        print(f"Updating existing material: {material_name}")

        # For update, we should use PUT endpoint
        update_response = requests.put(
            f"{BASE_URL}/materials/{material_id}",
            json=material_payload,
            params={"user_id": user_id},
        )

        if update_response.status_code == 200:
            print(f"✅ Successfully updated: {material_name}")
            return True
        else:
            print(f"❌ Failed to update {material_name}: {update_response.status_code}")
            print(f"Error: {update_response.json().get('detail', 'Unknown error')}")
            return False
    else:
        # Create new material
        print(f"Creating new material: {material_name}")

        create_response = requests.post(
            f"{BASE_URL}/materials", json=material_payload, params={"user_id": user_id}
        )

        if create_response.status_code == 200:
            print(f"✅ Successfully created: {material_name}")
            return True
        else:
            print(f"❌ Failed to create {material_name}: {create_response.status_code}")
            print(f"Error: {create_response.json().get('detail', 'Unknown error')}")
            return False


USER_ID = "admin_user"


def main():
    # Test user data

    print("Running API Tests...")

    ## UPLOAD ALL TO DB
    # materials_dict = {
    #     "Concrete, Cast In Situ": [0.103, 2350],
    #     "Concrete, Cast-in-Place gray": [0.103, 2350],
    #     "Concrete, C12/15": [0.097, 2350],
    #     "Concrete, Grade 40": [0.170, 2400],
    #     "Concrete, Grade 20": [0.120, 2350],
    #     "Concrete, Grade 25": [0.13, 2350],
    #     # Note: "Concrete, Grade 20" appears multiple times with different values
    #     # Using latest value for this duplicate
    #     "Concrete, C25/30": [0.119, 2350],
    #     "Concrete, General": [0.112, 2350],
    #     "Concrete, Precast, Ordinary Portland Cement": [0.148, 2400],
    #     "Wood_aluminium fixed window 3-glass (SF 2010)": 54.6,  # kgCO2 per 1m²
    #     "Wood_aluminium sidehung window 3-glass (SF 2010)": 72.4,
    #     "M_Window-Casement-Double-Sidelight": 86.830,
    #     "Wooden doors T10-T25 with wooden frame": 30.4,
    #     "Wooden doors T10-T25 with wooden frame 2": 30.4,
    #     "Wooden doors T10-T25 with steel frame": 49.4,
    #     "Aluminium, General": [13.100, 2700],
    #     "Tiles, Granite": [0.700, 2650],
    #     "Plywood": [0.910, 600],
    #     "Cross Laminated Timber": [-1.310, 500],
    #     "Primary Steel": [1.730, 7850],
    # }

    # print(f"Starting material upload/update process...")

    # success_count = 0
    # fail_count = 0

    # # Process all materials
    # for material_name, material_data in materials_dict.items():
    #     if upload_material(material_name, material_data, USER_ID):
    #         success_count += 1
    #     else:
    #         fail_count += 1

    # print(f"\nUpload complete!")
    # print(f"Successfully processed: {success_count}")
    # print(f"Failed: {fail_count}")
    # print(f"Total materials: {len(materials_dict)}")

    # # Test GET all materials
    materials = test_get_materials()

    # # If materials exist, test GET specific material
    # if materials and len(materials) > 0:
    #     material_name = materials[0]["specified_material"]
    #     test_get_materials(material_name)

    # # Test creating a material with density
    # material_id = test_upload_material(test_user, with_density=True)

    # # Test creating a material without density
    # material_id_no_density = test_upload_material(test_user, with_density=False)

    # # Test deleting a created material
    # if material_id:
    #     test_delete_material(material_id, test_user)

    # Uncomment these to test your original project endpoints
    # test_get_projects(test_user)
    # test_upload_ifc("507f1f77bcf86cd799439011", "16_Complex 1.ifc", test_user)
    # test_get_project_info("507f1f77bcf86cd799439011")
    # test_create_project(test_user)


if __name__ == "__main__":
    main()
