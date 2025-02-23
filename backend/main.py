from fastapi import FastAPI, Form, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
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
from utils import calculator, utils, ec_breakdown
from pymongo.errors import ServerSelectionTimeoutError

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

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from your frontend
    allow_credentials=True,                  # Allow cookies and authentication headers
    allow_methods=["*"],                     # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],                     # Allow all headers (e.g., Authorization)
)


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
    typology:Optional[str] = None
    status:Optional[str] = None
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

class ProjectBreakdown(BaseModel):
    project_id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    total_ec: float
    gfa: float
    ec_breakdown:dict
    last_calculated: datetime
    version: str

class ProjectBasicInfo(BaseModel):
    project_id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    gfa: float
    typology: str
    status:str

class VersionHistory(BaseModel):
    version: str
    uploaded_by: str
    date_uploaded: datetime
    comments: str
    update_type: str
    total_ec: float

class ProjectHistoryResponse(BaseModel):
    history: List
@app.get("/test_db_connection")
async def test_db_connection():

    try:
        # List collections in the database to verify connectivity
        collections = await app.mongodb.list_collection_names()
        return {"success": True, "collections": collections}
    except ServerSelectionTimeoutError as e:
        return {"success": False, "error": str(e)}

@app.get("/projects", response_model=List[Project])
async def get_projects(user_id: str = Query(..., description="User ID to fetch projects for")):
    """Get all projects accessible by a user"""
    print("User id ",user_id)
    projects = await app.mongodb.projects.find(
        {f"access_control.{user_id}": {"$exists": True}}
    ).to_list(1000)
    #print("Projects: ", projects)
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
    user_id: str = Query(..., description="ID of the user uploading the file"),
    comments: str = Form(""),  # Default to empty string if not provided
    update_type: str = Form("")  # Default to empty string if not provided
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

        # Use temporary file for EC breakdown calculation
        with utils.temp_ifc_file(file_content) as tmp_path:
            ec_data = await ec_breakdown.overall_ec_breakdown(tmp_path)


        # Update MongoDB
        update_result = await app.mongodb.projects.update_one(
            {"_id": ObjectId(project_id)},
            {
                "$set": {
                    "current_version": int(new_version),
                    "last_edited_date": datetime.now(),
                    "last_edited_user": user_id,
                    f"ifc_versions.{new_version}": {
                        
                        "date_uploaded": datetime.now(),
                        "uploaded_by": user_id,
                        "comments":comments,
                        "update_type": update_type,
                        "file_path": f"s3://{S3_BUCKET}/{s3_path}",
                        "gfa":ec_data["gfa"],
                        "total_ec": ec_data["total_ec"], 
                        "ec_breakdown":{
                            "by_building_system":ec_data["by_building_system"],
                            "by_material":ec_data["by_material"],
                            "by_element":ec_data["by_element"],
                        }
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


# Get EC breakdown and ec value
@app.get("/projects/{project_id}/get_breakdown", response_model=ProjectBreakdown)
async def get_breakdown(project_id: str):
    project = await app.mongodb.projects.find_one({"_id": ObjectId(project_id)}) 
   
    if not project:
       raise HTTPException(status_code=404, detail="Project not found")
       
    latest_version = str(project.get("current_version"))
    ifc_data = project["ifc_versions"].get(latest_version, {})

    # file_path = project["ifc_versions"][latest_version]["file_path"].replace(f"s3://{S3_BUCKET}/", "")
   
    # Retrieve stored EC values and breakdowns
    total_ec = ifc_data.get("total_ec", 0)
    ec_breakdown = ifc_data.get("ec_breakdown", {})
    gfa = ifc_data.get("gfa", 0)
    
    print("ec breakdown is,",ec_breakdown)

    return ProjectBreakdown(
        project_id=str(project["_id"]),
        total_ec=total_ec,
        gfa = gfa,
        ec_breakdown=ec_breakdown,
        last_calculated=project.get("last_calculated", datetime.now()),
        version=latest_version
    )

@app.get("/projects/{project_id}/get_project_info", response_model=ProjectBasicInfo)
async def get_project_info(project_id:str):
    project = await app.mongodb.projects.find_one({"_id": ObjectId(project_id)}) 
   
    if not project:
       raise HTTPException(status_code=404, detail="Project not found")
    
     # Get the latest version's GFA
    latest_version = str(project.get("current_version"))
    ifc_data = project["ifc_versions"].get(latest_version, {})
    gfa = ifc_data.get("gfa", 0)

    return ProjectBasicInfo(
        _id=project["_id"],
        gfa=gfa,
        typology=project.get("typology", "Not Specified"),
        status=project.get("status", "Not Specified")
    )
# Get latest edits history (top 4 history, get the uploaded_by, date_uploaded, comments, update_type)
@app.get("/projects/{project_id}/get_history", response_model = ProjectHistoryResponse)
async def get_project_history(project_id: str):
    project = await app.mongodb.projects.find_one({"_id": ObjectId(project_id)})

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get the last 4 versions uploaded
    ifc_versions = project.get("ifc_versions", {})
    sorted_versions = sorted(ifc_versions.keys(), key=lambda v: int(v), reverse=True)[:4]

    version_history = []
    for version in sorted_versions:
        version_data = ifc_versions.get(version, {})
        version_history.append( VersionHistory(
            version=version,
            uploaded_by=version_data.get("uploaded_by", ""),
            date_uploaded=version_data.get("date_uploaded", datetime.now()),
            comments=version_data.get("comments", ""),
            update_type=version_data.get("update_type", ""),
            total_ec=version_data.get("total_ec",0.0)
        ))

    return ProjectHistoryResponse(history=version_history)
    


@app.post("/create_project", response_model=Project)
async def create_project(project: Project):
    new_project = await app.mongodb.projects.insert_one(
        project.dict(by_alias=True, exclude={"id"})
    )
    created_project = await app.mongodb.projects.find_one(
        {"_id": new_project.inserted_id}
    )
    return created_project




if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )