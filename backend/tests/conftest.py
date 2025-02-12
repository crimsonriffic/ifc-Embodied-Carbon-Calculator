import boto3
import pytest
import dotenv
import os
dotenv.load_dotenv()

@pytest.fixture
def s3_client():
    """
    Fixture that provides a real S3 client
    """
    s3 = boto3.client('s3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),)
    return s3