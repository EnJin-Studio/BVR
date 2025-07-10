import logging
import requests
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from botocore.config import Config

# 可选：配置 S3 客户端的重试策略
s3_config = Config(
    retries = {
        'max_attempts': 5,
        'mode': 'standard'
    }
)

def stream_video_to_s3(video_url: str, bucket: str, key: str, region: str = 'us-east-1'):
    """
    将公开 API 的视频（视频 URL）直接流式传输到 S3 桶。

    :param video_url: 公开可访问的视频文件 URL
    :param bucket:      目标 S3 桶名称
    :param key:         在桶中存储对象的键（含路径，如 'videos/my_video.mp4'）
    :param region:      AWS 区域，默认为 us-east-1
    """
    # 初始化 S3 客户端
    s3 = boto3.client('s3', region_name=region, config=s3_config)

    try:
        # 发起带流式响应的 GET 请求
        with requests.get(video_url, stream=True, timeout=30) as resp:
            resp.raise_for_status()  # 若非 200，会抛出异常

            # 直接将响应内容的底层原始流（raw）上传到 S3
            # upload_fileobj 会自动分片上传大文件
            s3.upload_fileobj(
                Fileobj=resp.raw,
                Bucket=bucket,
                Key=key,
                ExtraArgs={'ContentType': resp.headers.get('Content-Type', 'application/octet-stream')}
            )
        logging.info(f"成功将视频上传至 s3://{bucket}/{key}")

    except (requests.RequestException, BotoCoreError, ClientError) as err:
        logging.error("上传失败：%s", err)
        raise

if __name__ == "__main__":
    # 示例调用
    VIDEO_URL = "https://example.com/path/to/video.mp4"
    S3_BUCKET = "your-target-bucket"
    S3_KEY    = "uploads/video.mp4"

    stream_video_to_s3(VIDEO_URL, S3_BUCKET, S3_KEY)
