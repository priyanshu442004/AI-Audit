import os
import sys
import boto3
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Add backend directory to system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import get_connection

def clear_db():
    print("Clearing database tables...")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE s3_uploaded_files RESTART IDENTITY CASCADE;")
        conn.commit()
        cur.close()
        conn.close()
        print("Database cleared successfully.")
    except Exception as e:
        print(f"Error clearing database: {e}")

def clear_s3():
    print("Clearing audit files in S3 bucket...")
    aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    aws_region = os.environ.get("AWS_REGION", "us-east-1")
    aws_bucket = os.environ.get("AWS_BUCKET_NAME", "james-fixer")
    
    if not aws_access_key or not aws_secret_key:
        print("AWS credentials not found.")
        return
        
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )
    
    try:
        # List all objects in bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=aws_bucket, Prefix="audit-files/")
        
        delete_keys = []
        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    delete_keys.append({"Key": obj["Key"]})
                    
        if delete_keys:
            # Delete in batches of 1000
            for i in range(0, len(delete_keys), 1000):
                batch = delete_keys[i:i+1000]
                s3_client.delete_objects(
                    Bucket=aws_bucket,
                    Delete={"Objects": batch}
                )
            print(f"Successfully deleted {len(delete_keys)} objects from S3.")
        else:
            print("No objects found with prefix 'audit-files/' in S3.")
    except Exception as e:
        print(f"Error clearing S3: {e}")

if __name__ == "__main__":
    clear_db()
    clear_s3()
