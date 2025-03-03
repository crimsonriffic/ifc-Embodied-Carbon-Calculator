import requests
import os
from pathlib import Path
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_get_projects(user_id: str):
    """Test the get projects endpoint with query parameters"""
    print(f"\n===Testing GET projects for user {user_id}===")
    
    # Using query parameter for user_id
    response = requests.get(
        f"{BASE_URL}/projects",
        params={"user_id": user_id}
    )
    
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
            user_access = project['access_control'].get(user_id, {})
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
        
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
        # Using query parameter for user_id
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/upload_ifc",
            files=files,
            params={"user_id": user_id}
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
        "last_edited_date":"2024-01-21T00:00:00.000+00:00",
        "last_edited_user": user_id,
        "current_version": 1,
        "access_control": {
        "user789": {
            "role": "owner",
            "permissions": ["read", "write", "execute", "delete", "admin"]  # Example permissions
        },
        "user123": {
            "role": "viewer",
            "permissions": ["read"]  # Example permissions
        }
    },
        "edit_history": [
            {"timestamp": "2024-01-21T00:00:00.000+00:00",
            "user": "Mike Johnson",
            "action": "created_project",
            "description": "Project initialization"
        }
    ],
        "ifc_versions":{
        1: {
            "total_ec": 3000,
            "date_uploaded": "2024-01-21T00:00:00.000+00:00",
            "uploaded_by": user_id,
            "file_path": "s3://bucket/proj_789/v1.ifc"
        }
    },
    }
    
    response = requests.post(
        f"{BASE_URL}/create_project",
        json=project_data,
        params={"user_id": user_id}  # Using query parameter for user_id
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nProject Created:")
        print(f"Project ID: {result['_id']}")
        print(f"Project Name: {result['project_name']}")
        return result['_id']  # Return the ID for use in other tests
    else:
        print(f"Error: {response.json().get('detail', 'Unknown error')}")
        return None

def main():
    # Test user data
    test_user = "user123"  
    
    print("Running API Tests...")
    
    # test_get_projects(test_user)
    # test_get_projects("nonexistent_user")  # Should fail with 404

    test_upload_ifc("507f1f77bcf86cd799439011", "16_Complex 1.ifc", test_user)
    # test_get_project_info("507f1f77bcf86cd799439011")
    # test_create_project(test_user)
if __name__ == "__main__":
    main()