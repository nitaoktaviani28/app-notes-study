from __future__ import annotations

import tempfile
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


class S3StorageService:
    def __init__(self) -> None:
        self.client = boto3.client("s3", region_name=settings.s3_region or settings.aws_region)

    def upload_bytes(self, content: bytes, key: str, content_type: str = "application/octet-stream") -> str:
        self.client.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        return key

    def create_presigned_get_url(self, key: str, expires_seconds: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    def download_to_temp(self, key: str, suffix: str) -> str:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_path = tmp.name
        tmp.close()
        self.client.download_file(settings.s3_bucket, key, tmp_path)
        return tmp_path


s3_storage = S3StorageService()


def s3_is_enabled() -> bool:
    return settings.storage_backend.lower() == "s3" and bool(settings.s3_bucket)


def safe_create_presigned_url(key: str, expires_seconds: int = 3600) -> str | None:
    try:
        return s3_storage.create_presigned_get_url(key, expires_seconds)
    except (ClientError, BotoCoreError, Exception):
        return None


def safe_download_to_temp(key: str, suffix: str) -> str | None:
    try:
        return s3_storage.download_to_temp(key, suffix)
    except (ClientError, BotoCoreError, Exception):
        return None
