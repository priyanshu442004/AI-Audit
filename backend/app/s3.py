import os
import io
import time
import boto3
import hashlib
import pickle
from botocore.config import Config
from dotenv import load_dotenv
from app.loaders import load_file

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
AWS_BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME", "james-fixer")

CACHE_DIR = os.path.join(os.path.dirname(__file__), "../.cache_dfs")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(s3_key: str) -> str:
    key_hash = hashlib.md5(s3_key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{key_hash}.pkl")

def get_s3_client():
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ValueError("AWS credentials are not set in environment variables.")
    # Configure client timeouts to avoid infinite stalls
    config = Config(
        connect_timeout=10,
        read_timeout=30,
        retries={'max_attempts': 3}
    )
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        config=config
    )

def upload_file_to_s3(file_data: bytes, filename: str, role: str) -> dict:
    s3_client = get_s3_client()
    
    # 1. Parse the file into a DataFrame
    try:
        df = load_file(io.BytesIO(file_data), filename)
        row_count = len(df)
    except Exception as e:
        raise ValueError(f"Unable to parse file '{filename}': {e}")
    
    # 2. Upload to S3 using upload_fileobj (multithreaded/multipart transfers)
    timestamp = int(time.time() * 1000)
    # clean filename
    safe_filename = filename.replace(" ", "_")
    s3_key = f"audit-files/{role}/{timestamp}_{safe_filename}"
    
    try:
        s3_client.upload_fileobj(
            io.BytesIO(file_data),
            AWS_BUCKET_NAME,
            s3_key
        )
    except Exception as e:
        raise RuntimeError(f"S3 upload failed: {e}")
        
    # 3. Write parsed DataFrame to pickle cache immediately so we don't fetch or parse it again!
    cache_path = get_cache_path(s3_key)
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(df, f)
    except Exception as ce:
        print(f"Failed to write cache during upload for {filename}: {ce}")
        
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
