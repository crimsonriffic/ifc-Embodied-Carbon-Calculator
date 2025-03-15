import json
import boto3
import os
import tempfile
import pymongo
from datetime import datetime
from bson.objectid import ObjectId
import logging
import time
import signal
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Flag to control the processing loop
running = True


def signal_handler(sig, frame):
    """Handle termination signals"""
    global running
    logger.info("Received shutdown signal, finishing current tasks...")
    running = False


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


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
                    f"ifc_versions.{ifc_version}.failure_reason": str(e),
                }
            },
        )
        raise


def process_sqs_message(db, message):
    """Process a single SQS message"""
    try:
        # Parse message
        message_body = json.loads(message["Body"])
        logger.info(f"Processing message: {message_body}")

        project_id = message_body["project_id"]
        ifc_version = message_body["ifc_version"]
        s3_path = message_body["s3_path"]

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
            QueueUrl=QUEUE_URL, ReceiptHandle=message["ReceiptHandle"]
        )

        return True

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # Don't delete the message from queue to allow for retry
        return False


def main():
    """Main function that continuously polls SQS queue"""
    logger.info("Starting EC Calculator Processor")

    # Connect to MongoDB
    db = connect_to_mongodb()

    while running:
        try:
            # Receive messages from SQS queue
            response = sqs_client.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,  # Long polling
                VisibilityTimeout=300,  # 5 minutes
            )

            # Check if any messages were received
            messages = response.get("Messages", [])

            if not messages:
                logger.info("No messages in queue, waiting...")
                continue

            # Process each message
            for message in messages:
                process_sqs_message(db, message)

        except Exception as e:
            logger.error(f"Error in main processing loop: {str(e)}")
            # Short sleep to prevent tight loops in error conditions
            time.sleep(5)

    logger.info("Processor shutting down gracefully")


if __name__ == "__main__":
    main()
