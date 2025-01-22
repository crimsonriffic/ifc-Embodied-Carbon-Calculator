
from datetime import datetime
from bson import ObjectId
from pymongo import AsyncMongoClient
import os 
import dotenv
import asyncio
dotenv.load_dotenv()

test_data = [
    {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "project_name": "Office Building A",
        "client_name": "ABC Corp",
        "last_edited_date": datetime(2024, 1, 15),
        "last_edited_user": "John Doe",
        "user_job_role": "Architect",
        "current_version": 2,
        "access_control": {
            "user123": {
                "role": "owner",
                "permissions": ["read", "write", "upload", "share", "delete"]
            },
            "user456": {
                "role": "editor",
                "permissions": ["read", "write", "upload"]
            },
            "user789": {
                "role": "viewer",
                "permissions": ["read"]
            }
        },
        "edit_history": [
            {
                "timestamp": datetime(2024, 1, 15),
                "user": "John Doe",
                "action": "updated_ifc",
                "description": "Updated structural elements"
            }
        ],
        "ifc_versions": {
            "1": {
                "total_ec": 1200,
                "date_uploaded": datetime(2024, 1, 10),
                "uploaded_by": "John Doe",
                "file_path": "s3://bucket/proj_123/v1.ifc"
            },
            "2": {
                "total_ec": 1000,
                "date_uploaded": datetime(2024, 1, 15),
                "uploaded_by": "John Doe",
                "file_path": "s3://bucket/proj_123/v2.ifc"
            }
        }
    },
    {
        "_id": ObjectId("507f1f77bcf86cd799439012"),
        "project_name": "Shopping Mall Complex",
        "client_name": "XYZ Retail",
        "last_edited_date": datetime(2024, 1, 20),
        "last_edited_user": "Jane Smith",
        "user_job_role": "Lead Engineer",
        "current_version": 3,
        "access_control": {
            "user456": {
                "role": "owner",
                "permissions": ["read", "write", "upload", "share", "delete"]
            },
            "user123": {
                "role": "editor",
                "permissions": ["read", "write", "upload"]
            }
        },
        "edit_history": [
            {
                "timestamp": datetime(2024, 1, 18),
                "user": "Jane Smith",
                "action": "created_project",
                "description": "Initial project setup"
            },
            {
                "timestamp": datetime(2024, 1, 19),
                "user": "Jane Smith",
                "action": "uploaded_ifc",
                "description": "First IFC upload"
            },
            {
                "timestamp": datetime(2024, 1, 20),
                "user": "Jane Smith",
                "action": "updated_ifc",
                "description": "Updated foundation design"
            }
        ],
        "ifc_versions": {
            "1": {
                "total_ec": 2500,
                "date_uploaded": datetime(2024, 1, 18),
                "uploaded_by": "Jane Smith",
                "file_path": "s3://bucket/proj_456/v1.ifc"
            },
            "2": {
                "total_ec": 2200,
                "date_uploaded": datetime(2024, 1, 19),
                "uploaded_by": "Jane Smith",
                "file_path": "s3://bucket/proj_456/v2.ifc"
            },
            "3": {
                "total_ec": 1800,
                "date_uploaded": datetime(2024, 1, 20),
                "uploaded_by": "Jane Smith",
                "file_path": "s3://bucket/proj_456/v3.ifc"
            }
        }
    },
    {
        "_id": ObjectId("507f1f77bcf86cd799439013"),
        "project_name": "Residential Tower",
        "client_name": "Homes & Co",
        "last_edited_date": datetime(2024, 1, 21),
        "last_edited_user": "Mike Johnson",
        "user_job_role": "Senior Architect",
        "current_version": 1,
        "access_control": {
            "user789": {
                "role": "owner",
                "permissions": ["read", "write", "upload", "share", "delete"]
            },
            "user123": {
                "role": "viewer",
                "permissions": ["read"]
            }
        },
        "edit_history": [
            {
                "timestamp": datetime(2024, 1, 21),
                "user": "Mike Johnson",
                "action": "created_project",
                "description": "Project initialization"
            }
        ],
        "ifc_versions": {
            "1": {
                "total_ec": 3000,
                "date_uploaded": datetime(2024, 1, 21),
                "uploaded_by": "Mike Johnson",
                "file_path": "s3://bucket/proj_789/v1.ifc"
            }
        }
    },
    {
        "_id": ObjectId("507f1f77bcf86cd799439014"),
        "project_name": "Hospital Extension",
        "client_name": "Healthcare Solutions",
        "last_edited_date": datetime(2024, 1, 22),
        "last_edited_user": "Sarah Wilson",
        "user_job_role": "Project Manager",
        "current_version": 2,
        "access_control": {
            "user456": {
                "role": "owner",
                "permissions": ["read", "write", "upload", "share", "delete"]
            },
            "user789": {
                "role": "editor",
                "permissions": ["read", "write", "upload"]
            }
        },
        "edit_history": [
            {
                "timestamp": datetime(2024, 1, 21),
                "user": "Sarah Wilson",
                "action": "created_project",
                "description": "Initial setup"
            },
            {
                "timestamp": datetime(2024, 1, 22),
                "user": "Sarah Wilson",
                "action": "uploaded_ifc",
                "description": "Added emergency wing design"
            }
        ],
        "ifc_versions": {
            "1": {
                "total_ec": 4500,
                "date_uploaded": datetime(2024, 1, 21),
                "uploaded_by": "Sarah Wilson",
                "file_path": "s3://bucket/proj_101/v1.ifc"
            },
            "2": {
                "total_ec": 4200,
                "date_uploaded": datetime(2024, 1, 22),
                "uploaded_by": "Sarah Wilson",
                "file_path": "s3://bucket/proj_101/v2.ifc"
            }
        }
    }
]


async def insert_test_data(db):
    await db.projects.delete_many({})  # Clear existing data
    result = await db.projects.insert_many(test_data)
    print(f"Inserted {len(result.inserted_ids)} documents")


MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'project_management')



mongodb_client = AsyncMongoClient(MONGODB_URL)
mongodb = mongodb_client[DB_NAME]

async def main():
    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
    DB_NAME = os.getenv('DB_NAME', 'project_management')
    
    print(f"Connecting to MongoDB at {MONGODB_URL}")
    client = AsyncMongoClient(MONGODB_URL)
    db = client[DB_NAME]
    
    try:
        await insert_test_data(db)
    finally:
        await client.close()
        print("MongoDB connection closed")

async def clear_all_data():
    # Get MongoDB connection details from environment variables
    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
    DB_NAME = os.getenv('DB_NAME', 'project_management')
    
    print(f"Connecting to MongoDB at {MONGODB_URL}")
    client = AsyncMongoClient(MONGODB_URL)
    db = client[DB_NAME]
    
    try:
        # Get list of all collections
        collections = await db.list_collection_names()
        
        if not collections:
            print("No collections found in the database.")
            return
        
        print(f"Found collections: {', '.join(collections)}")
        
        # Drop each collection
        for collection in collections:
            print(f"Dropping collection: {collection}")
            await db[collection].drop()
        
        # Verify all collections are dropped
        remaining_collections = await db.list_collection_names()
        if not remaining_collections:
            print("Successfully removed all collections!")
        else:
            print(f"Warning: Some collections remain: {', '.join(remaining_collections)}")
            
    except Exception as e:
        print(f"Error during data deletion: {e}")
    finally:
        await client.close()
        print("MongoDB connection closed")

if __name__ == "__main__":
    asyncio.run(clear_all_data())
    asyncio.run(main())