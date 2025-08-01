#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError

# --- Config --- #
BUCKET_NAME = 'bvr-database' 
S3_KEY      = 'uploadtest.txt'
LOCAL_FILE  = 'uploadtest.txt'

# --- 1. Create a local test file --- #
content = "bvr bucket uploading test"
with open(LOCAL_FILE, 'w') as f:
    f.write(content)
print(f"Created local file: {LOCAL_FILE}")

# --- 2. Initialize S3 client --- #
s3 = boto3.client('s3')  # will read from ~/.aws/credentials or environment variables

# --- 3. Upload file to S3 --- #
try:
    s3.upload_file(Filename=LOCAL_FILE,
                   Bucket=BUCKET_NAME,
                   Key=S3_KEY)
    print(f"✅ Uploaded successfully to s3://{BUCKET_NAME}/{S3_KEY}")
except ClientError as e:
    print(f"❌ Upload failed: {e}")
