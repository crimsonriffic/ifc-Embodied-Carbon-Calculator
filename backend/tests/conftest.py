import boto3
import pytest
import dotenv
import os
import sys

# Load environment variables
dotenv.load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def s3_client():
    """
    Fixture that provides a real S3 client
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    )
    return s3
