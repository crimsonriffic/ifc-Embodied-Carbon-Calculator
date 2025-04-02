import json
import boto3
import os
import tempfile
import pymongo
from datetime import datetime
from bson.objectid import ObjectId
import logging
import time
import threading
from fastapi import FastAPI, HTTPException
import uvicorn
import dotenv

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="EC Calculator Processor")

# Initialize AWS clients
s3_client = boto3.client("s3")
sqs_client = boto3.client("sqs")

# Environment variables
MONGODB_URI = os.environ.get("MONGODB_URL")
QUEUE_URL = os.environ.get("SQS_QUEUE_URL")

# Import calculation modules
from utils import calculator

# Global variables for worker state
worker_running = False
worker_thread = None
worker_last_heartbeat = datetime.now()
worker_metrics = {
    "messages_processed": 0,
    "messages_failed": 0,
    "last_error": None,
    "start_time": None,
}


def extract_s3_info(s3_path):
    """Extract bucket and key from s3 path format 's3://bucket/key'"""
    path = s3_path.replace("s3://", "")
    bucket = path.split("/")[0]
    key = "/".join(path.split("/")[1:])
    return bucket, key


def connect_to_mongodb():
    """Connect to MongoDB and return database client"""
    if not MONGODB_URI:
        logger.error("MongoDB configuration missing")
        raise ValueError("MongoDB environment variables not configured")

    # Get database name from environment variable with fallback
    db_name = os.environ.get("DB_NAME")

    client = pymongo.MongoClient(MONGODB_URI)
    return client[db_name]


def transform_ec_data(data):
    # Initialize the new structure
    summary = {"by_building_system": {}, "by_material": {}, "by_element": {}}

    # Process the ec_breakdown array
    for category in data.get("ec_breakdown", []):
        category_name = category.get("category")
        category_ec = category.get("total_ec", 0)

        # Add to by_building_system
        summary["by_building_system"][category_name] = category_ec

        # Process elements within each category
        for element in category.get("elements", []):
            element_name = element.get("element")
            element_ec = element.get("ec", 0)

            # Skip if element name is missing
            if not element_name:
                continue

            # Add to by_element
            if element_name in summary["by_element"]:
                summary["by_element"][element_name] += element_ec
            else:
                summary["by_element"][element_name] = element_ec

            # Process materials within each element
            for material in element.get("materials", []):
                material_name = material.get("material")
                material_ec = material.get("ec", 0)

                # Skip if material name is missing
                if not material_name:
                    continue

                # Add to by_material
                if material_name in summary["by_material"]:
                    summary["by_material"][material_name] += material_ec
                else:
                    summary["by_material"][material_name] = material_ec

    return {"summary": summary}


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
        print("calculating ec")
        result = calculator.calculate_embodied_carbon(temp_path, with_breakdown=True)
        if result is None:
            logger.error("calculator.calculate_embodied_carbon returned None")
            raise ValueError("Failed to calculate embodied carbon")
        total_ec, ec_data, summary_data, excel_data = result

        # summary_data = transform_ec_data(ec_data)
        # if summary_data is None:
        #     logger.error("ec_breakdown.overall_ec_breakdown returned None")
        #     raise ValueError("Failed to generate EC breakdown summary")

        print("calculating gfa")
        total_gfa = calculator.calculate_gfa(temp_path)
        if total_gfa is None:
            logger.error("calculator.calculate_gfa returned None")
            raise ValueError("Failed to calculate GFA")

        # Clean up
        os.unlink(temp_path)

        return total_ec, total_gfa, summary_data, ec_data, excel_data

    except Exception as e:
        logger.error(f"Error processing IFC file: {str(e)}")
        raise


def update_mongodb(
    db, project_id, ifc_version, total_ec, total_gfa, summary_data, ec_data, excel_data
):
    """Update MongoDB with EC calculation results"""
    try:
        # Insert EC breakdown data
        ec_breakdown_entry = {
            "project_id": ObjectId(project_id),
            "ifc_version": ifc_version,
            "total_ec": total_ec,
            "summary": summary_data,
            "breakdown": ec_data,
            "excel_data": excel_data,
            "timestamp": datetime.now(),
        }

        ec_breakdown_result = db.ec_breakdown.insert_one(ec_breakdown_entry)
        ec_breakdown_id = ec_breakdown_result.inserted_id
        logger.info(
            f"Updating MongoDB with: {total_gfa}, {total_ec}, {ec_breakdown_id}"
        )

        # Update project document
        db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {
                "$set": {
                    f"ifc_versions.{ifc_version}.calculation_status": "completed",
                    f"ifc_versions.{ifc_version}.total_ec": total_ec,
                    f"ifc_versions.{ifc_version}.gfa": total_gfa,
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
    global worker_metrics, worker_last_heartbeat

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
        total_ec, total_gfa, summary_data, ec_data, excel_data = process_ifc_file(
            s3_path
        )

        # Update MongoDB with results
        ec_breakdown_id = update_mongodb(
            db,
            project_id,
            ifc_version,
            total_ec,
            total_gfa,
            summary_data,
            ec_data,
            excel_data,
        )

        logger.info(
            f"Successfully processed project {project_id}, version {ifc_version}"
        )

        # Delete message from queue
        sqs_client.delete_message(
            QueueUrl=QUEUE_URL, ReceiptHandle=message["ReceiptHandle"]
        )

        # Update metrics
        worker_metrics["messages_processed"] += 1
        worker_last_heartbeat = datetime.now()

        return True

    except Exception as e:
        error_message = f"Error processing message: {str(e)}"
        logger.error(error_message)

        # Update metrics
        worker_metrics["messages_failed"] += 1
        worker_metrics["last_error"] = error_message
        worker_last_heartbeat = datetime.now()

        # Don't delete the message from queue to allow for retry
        return False


def poll_sqs_queue():
    """Worker function to continuously poll SQS queue"""
    global worker_running, worker_metrics, worker_last_heartbeat

    logger.info("Starting EC Calculator Processor worker thread")

    worker_metrics["start_time"] = datetime.now()

    # Connect to MongoDB
    try:
        db = connect_to_mongodb()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        worker_metrics["last_error"] = f"MongoDB connection error: {str(e)}"
        worker_running = False
        return

    # Main processing loop
    while worker_running:
        try:
            # Check if queue URL is configured
            if not QUEUE_URL:
                logger.error("SQS Queue URL not configured")
                worker_metrics["last_error"] = "SQS Queue URL not configured"
                time.sleep(30)  # Wait before retrying
                continue

            # Receive messages from SQS queue
            response = sqs_client.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,  # Long polling
                VisibilityTimeout=300,  # 5 minutes
            )

            # Update heartbeat timestamp
            worker_last_heartbeat = datetime.now()

            # Check if any messages were received
            messages = response.get("Messages", [])

            if not messages:
                logger.info("No messages in queue, waiting...")
                continue

            # Process each message
            for message in messages:
                process_sqs_message(db, message)

        except Exception as e:
            error_message = f"Error in worker thread: {str(e)}"
            logger.error(error_message)
            worker_metrics["last_error"] = error_message
            worker_last_heartbeat = datetime.now()

            # Short sleep to prevent tight loops in error conditions
            time.sleep(5)

    logger.info("Worker thread shutting down gracefully")


@app.get("/health")
async def health_check():
    """Health check endpoint for ECS"""
    global worker_running, worker_last_heartbeat, worker_metrics

    # Check if worker is running
    if not worker_running:
        raise HTTPException(status_code=503, detail="Worker thread not running")

    # Check heartbeat - ensure worker hasn't been stuck for more than 5 minutes
    heartbeat_age = (datetime.now() - worker_last_heartbeat).total_seconds()
    if heartbeat_age > 300:  # 5 minutes
        raise HTTPException(
            status_code=503,
            detail=f"Worker thread heartbeat too old ({heartbeat_age:.1f} seconds)",
        )

    # Return health status and metrics
    return {
        "status": "healthy",
        "worker_running": worker_running,
        "heartbeat_age_seconds": heartbeat_age,
        "metrics": worker_metrics,
        "queue_url": QUEUE_URL.split("/")[-1] if QUEUE_URL else "not_configured",
    }


@app.get("/metrics")
async def get_metrics():
    """Endpoint to get detailed metrics"""
    global worker_metrics, worker_last_heartbeat

    # Get queue status
    queue_stats = {}
    if QUEUE_URL:
        try:
            response = sqs_client.get_queue_attributes(
                QueueUrl=QUEUE_URL,
                AttributeNames=[
                    "ApproximateNumberOfMessages",
                    "ApproximateNumberOfMessagesNotVisible",
                ],
            )
            queue_stats = {
                "queue_name": QUEUE_URL.split("/")[-1],
                "messages_visible": int(
                    response["Attributes"]["ApproximateNumberOfMessages"]
                ),
                "messages_in_flight": int(
                    response["Attributes"]["ApproximateNumberOfMessagesNotVisible"]
                ),
            }
        except Exception as e:
            queue_stats = {"error": str(e)}

    # Calculate uptime
    uptime_seconds = 0
    if worker_metrics["start_time"]:
        uptime_seconds = (datetime.now() - worker_metrics["start_time"]).total_seconds()

    return {
        "worker_running": worker_running,
        "heartbeat_age_seconds": (
            datetime.now() - worker_last_heartbeat
        ).total_seconds(),
        "uptime_seconds": uptime_seconds,
        "queue": queue_stats,
        "metrics": worker_metrics,
    }


@app.on_event("startup")
async def startup_event():
    """Initialize worker thread when FastAPI starts"""
    global worker_running, worker_thread

    # Set worker running flag
    worker_running = True

    # Start worker thread
    worker_thread = threading.Thread(target=poll_sqs_queue)
    worker_thread.daemon = True
    worker_thread.start()

    logger.info("FastAPI application started, worker thread initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shut down worker thread when FastAPI stops"""
    global worker_running, worker_thread

    logger.info("Shutting down worker thread...")
    worker_running = False

    # Wait for thread to finish (with timeout)
    if worker_thread and worker_thread.is_alive():
        worker_thread.join(timeout=30)

    logger.info("Application shutdown complete")


if __name__ == "__main__":
    # Run FastAPI using uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
