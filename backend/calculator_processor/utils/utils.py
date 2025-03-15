import boto3
import os 
import tempfile
from contextlib import contextmanager

def get_ifc_by_filepath(s3_client: boto3.client, s3_bucket: str, s3_file_path: str):
    try:
        s3_path = s3_file_path
        response = s3_client.get_object(
            Bucket=s3_bucket,
            Key=s3_path
        )
        return response['Body'].read()
    except Exception as e:
        print(f"Error retrieving IFC file: {e}")
        return None
    

@contextmanager
def temp_ifc_file(content: bytes):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.ifc')
    try:
        tmp.write(content)
        tmp.close()
        yield tmp.name
    finally:
        os.unlink(tmp.name)