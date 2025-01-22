from fastapi import FastAPI, UploadFile, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uvicorn
import boto3
import os
import dotenv
from pymongo import AsyncMongoClient
from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic_core import core_schema
dotenv.load_dotenv()

# AWS Configuration
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
S3_BUCKET = os.getenv('S3_BUCKET')
AWS_REGION = os.getenv('AWS_REGION', 'ap-southeast-2')

# MongoDB Configuration
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'project_management')

app = FastAPI(title="Project Management API")

app.mongodb_client = AsyncMongoClient(MONGODB_URL)
app.mongodb = app.mongodb_client[DB_NAME]

# S3 Client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)
class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
            cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, value) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")

        return ObjectId(value)
    
class UserPermissions(BaseModel):
    role: str
    permissions: List[str]

class IFCVersion(BaseModel):
    total_ec: float
    date_uploaded: datetime
    uploaded_by: str
    file_path: str

class EditHistory(BaseModel):
    timestamp: datetime
    user: str
    action: str
    description: str

class Project(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    project_name: str
    client_name: str
    last_edited_date: datetime  
    last_edited_user: str
    user_job_role: str
    current_version: int
    access_control: Dict[str, UserPermissions]
    edit_history: List[EditHistory]
    ifc_versions: Dict[str, IFCVersion]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    user_job_role: Optional[str] = None
    access_control: Optional[Dict[str, UserPermissions]] = None

    class Config:
        arbitrary_types_allowed = True


@app.get("/projects", response_model=List[Project])
async def get_projects(user_id: str = Query(..., description="User ID to fetch projects for")):
    """Get all projects accessible by a user"""
    projects = await app.mongodb.projects.find(
        {f"access_control.{user_id}": {"$exists": True}}
    ).to_list(1000)
    
    if not projects:
        raise HTTPException(
            status_code=404,
            detail=f"No projects found for user ID: {user_id}"
        )

    for project in projects:
        project["_id"] = str(project["_id"])
    
    return projects

@app.post("/projects/{project_id}/upload_ifc", response_model=Dict)
async def upload_ifc(
    project_id: str,
    file: UploadFile,
    user_id: str = Query(..., description="ID of the user uploading the file")
):
    if not file.filename.lower().endswith('.ifc'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only IFC files are allowed."
        )

    # Verify user has upload permission
    project = await app.mongodb.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project with ID {project_id} not found"
        )
    
    user_permissions = project["access_control"].get(user_id, {}).get("permissions", [])
    if "upload" not in user_permissions:
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to upload files"
        )

    try:
        file_content = await file.read()
        new_version = str(project.get("current_version", 0) + 1)
        s3_path = f"ifc_files/{project_id}/{new_version}_{file.filename}"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_path,
            Body=file_content,
            ContentType='application/octet-stream'
        )

        # Update MongoDB
        update_result = await app.mongodb.projects.update_one(
            {"_id": ObjectId(project_id)},
            {
                "$set": {
                    "current_version": int(new_version),
                    "last_edited_date": datetime.now(),
                    "last_edited_user": user_id,
                    f"ifc_versions.{new_version}": {
                        "total_ec": 0.0, 
                        "date_uploaded": datetime.now(),
                        "uploaded_by": user_id,
                        "file_path": f"s3://{S3_BUCKET}/{s3_path}"
                    }
                },
                "$push": {
                    "edit_history": {
                        "timestamp": datetime.now(),
                        "user": user_id,
                        "action": "uploaded_ifc",
                        "description": f"Uploaded version {new_version}"
                    }
                }
            }
        )

        return {
            "success": True,
            "message": "File uploaded successfully",
            "version": new_version,
            "s3_path": f"s3://{S3_BUCKET}/{s3_path}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

# TODO
# @app.post("/projects", response_model=Project)
# async def create_project(project: Project):
#     new_project = await app.mongodb.projects.insert_one(
#         project.dict(by_alias=True, exclude={"id"})
#     )
#     created_project = await app.mongodb.projects.find_one(
#         {"_id": new_project.inserted_id}
#     )
#     return created_project

# # TODO
# @app.put("/projects/{project_id}", response_model=Project)
# async def update_project(project_id: str, project_update: Project):
#     update_result = await app.mongodb.projects.update_one(
#         {"_id": ObjectId(project_id)},
#         {"$set": project_update.dict(by_alias=True, exclude={"id"})}
#     )
    
#     if update_result.modified_count == 0:
#         raise HTTPException(
#             status_code=404,
#             detail=f"Project with ID {project_id} not found"
#         )
    
#     updated_project = await app.mongodb.projects.find_one(
#         {"_id": ObjectId(project_id)}
#     )
#     return updated_project



if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )