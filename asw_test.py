#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError

# —— 配置区 —— #
BUCKET_NAME = 'bvr-database'      # 替换为你的桶名
S3_KEY      = 'uploadtest.txt'        # 上传到桶中的对象名
LOCAL_FILE  = 'uploadtest.txt'        # 本地文件名

# —— 1. 生成本地测试文件 —— #
content = "bvr bucket uploading test"
with open(LOCAL_FILE, 'w') as f:
    f.write(content)
print(f"已在本地创建文件：{LOCAL_FILE}")

# —— 2. 初始化 S3 客户端 —— #
s3 = boto3.client('s3')  # 会自动读取 ~/.aws/credentials 或环境变量

# —— 3. 上传文件到 S3 —— #
try:
    s3.upload_file(Filename=LOCAL_FILE,
                   Bucket=BUCKET_NAME,
                   Key=S3_KEY)
    print(f"✅ 成功上传到 s3://{BUCKET_NAME}/{S3_KEY}")
except ClientError as e:
    print(f"❌ 上传失败：{e}")
