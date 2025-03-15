import json
import boto3
import os
import tempfile
import pymongo
from datetime import datetime
from bson.objectid import ObjectId
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client("s3")
sqs_client = boto3.client("sqs")

# Environment variables
MONGODB_URI = os.environ["MONGODB_URI"]
MONGODB_DB = os.environ["MONGODB_DB"]
QUEUE_URL = os.environ["SQS_QUEUE_URL"]

# Import calculation modules
from utils import ec_breakdown
from utils import calculator


def extract_s3_info(s3_path):
    """Extract bucket and key from s3 path format 's3://bucket/key'"""
    path = s3_path.replace("s3://", "")
    bucket = path.split("/")[0]
    key = "/".join(path.split("/")[1:])
    return bucket, key


def connect_to_mongodb():
    """Connect to MongoDB and return database client"""
    client = pymongo.MongoClient(MONGODB_URI)
    return client[MONGODB_DB]


def create_temp_file(file_content):
    """Create a temporary file with the IFC content"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ifc")
    temp_file.write(file_content)
    temp_file.close()
    return temp_file.name


def process_ifc_file(s3_path):
    """Download and process IFC file, returning EC calculations"""
    try:
        bucket, key = extract_s3_info(s3_path)

        # Create a temporary file for download
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ifc") as tmp_file:
            temp_path = tmp_file.name

        # Download the file from S3
        s3_client.download_file(bucket, key, temp_path)

        # Calculate embodied carbon
        summary_data = ec_breakdown.overall_ec_breakdown(temp_path)
        total_ec, ec_data = calculator.calculate_embodied_carbon(
            temp_path, with_breakdown=True
        )

        # Clean up
        os.unlink(temp_path)

        return total_ec, summary_data, ec_data

    except Exception as e:
        logger.error(f"Error processing IFC file: {str(e)}")
        raise


def update_mongodb(db, project_id, ifc_version, total_ec, summary_data, ec_data):
    """Update MongoDB with EC calculation results"""
    try:
        # Insert EC breakdown data
        ec_breakdown_entry = {
            "project_id": ObjectId(project_id),
            "ifc_version": ifc_version,
            "total_ec": total_ec,
            "summary": summary_data,
            "breakdown": ec_data,
            "timestamp": datetime.now(),
        }

        ec_breakdown_result = db.ec_breakdown.insert_one(ec_breakdown_entry)
        ec_breakdown_id = ec_breakdown_result.inserted_id

        # Update project document
        db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {
                "$set": {
                    f"ifc_versions.{ifc_version}.calculation_status": "completed",
                    f"ifc_versions.{ifc_version}.total_ec": total_ec,
                    f"ifc_versions.{ifc_version}.ec_breakdown_id": ec_breakdown_id,
                }
            },
        )

        return ec_breakdown_id

    except Exception as e:
        logger.error(f"Error updating MongoDB: {str(e)}")

        # Mark calculation as failed in database
        db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {
                "$set": {
                    f"ifc_versions.{ifc_version}.calculation_status": "failed",
                }
            },
        )
        raise


def lambda_handler(event, context):
    """Main Lambda function handler"""

    # Connect to MongoDB
    db = connect_to_mongodb()

    # Process each record from SQS
    for record in event["Records"]:
        try:
            # Parse message
            message = json.loads(record["body"])
            logger.info(f"Processing message: {message}")

            project_id = message["project_id"]
            ifc_version = message["ifc_version"]
            s3_path = message["s3_path"]

            # Update status to 'processing'
            db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {
                    "$set": {
                        f"ifc_versions.{ifc_version}.calculation_status": "processing",
                    }
                },
            )

            # Calculate EC
            total_ec, summary_data, ec_data = process_ifc_file(s3_path)

            # Update MongoDB with results
            ec_breakdown_id = update_mongodb(
                db, project_id, ifc_version, total_ec, summary_data, ec_data
            )

            logger.info(
                f"Successfully processed project {project_id}, version {ifc_version}"
            )

            # Delete message from queue
            sqs_client.delete_message(
                QueueUrl=QUEUE_URL, ReceiptHandle=record["receiptHandle"]
            )

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Don't delete the message from queue to allow for retry
            # Consider implementing a dead-letter queue (DLQ) for failed messages

            # Continue processing other messages
            continue

    return {"statusCode": 200, "body": json.dumps("IFC processing completed")}
