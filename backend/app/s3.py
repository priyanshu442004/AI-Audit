import os
import io
import time
import boto3
from dotenv import load_dotenv
from app.loaders import load_file

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
AWS_BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME", "james-fixer")

def get_s3_client():
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ValueError("AWS credentials are not set in environment variables.")
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

def upload_file_to_s3(file_data: bytes, filename: str, role: str) -> dict:
    s3_client = get_s3_client()
    
    # 1. Compute row count
    try:
        df = load_file(io.BytesIO(file_data), filename)
        row_count = len(df)
    except Exception as e:
        raise ValueError(f"Unable to parse file '{filename}': {e}")
    
    # 2. Upload to S3
    timestamp = int(time.time() * 1000)
    # clean filename
    safe_filename = filename.replace(" ", "_")
    s3_key = f"audit-files/{role}/{timestamp}_{safe_filename}"
    
    try:
        s3_client.put_object(
            Bucket=AWS_BUCKET_NAME,
            Key=s3_key,
            Body=file_data
        )
    except Exception as e:
        raise RuntimeError(f"S3 upload failed: {e}")
        
    s3_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
    
    return {
        "s3_key": s3_key,
        "s3_url": s3_url,
        "row_count": row_count
    }

def download_file_from_s3(s3_key: str) -> bytes:
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=AWS_BUCKET_NAME, Key=s3_key)
        return response['Body'].read()
    except Exception as e:
        raise RuntimeError(f"S3 download failed for key '{s3_key}': {e}")
