from __future__ import annotations

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from src.core.config.settings import settings


class S3Client:
    """
    MinIO-backed S3 client using environment from core.config.settings.
    Returns a public URL composed from S3_RESPONSE_ENDPOINT and object key.
    """

    def __init__(self, *, bucket: Optional[str] = None):
        endpoint = settings.S3_ACCESS_ENDPOINT
        parsed = urlparse(endpoint)
        if parsed.scheme:
            host = parsed.netloc
            secure = parsed.scheme == "https"
        else:
            host = endpoint
            secure = False

        self.client = Minio(
            host,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=secure,
        )
        self.bucket = bucket or settings.S3_BUCKET

        # Ensure bucket exists (create if missing)
        try:
            if not self.client.bucket_exists(self.bucket):
                location = settings.S3_REGION or None
                try:
                    self.client.make_bucket(self.bucket, location=location)
                except S3Error as e:
                    # Bucket may already exist (race) or location constraint mismatch
                    # Re-check existence before surfacing
                    if not self.client.bucket_exists(self.bucket):
                        raise
        except S3Error as e:
            print(f"[S3] Bucket check/create failed: {e}")

    def upload_file(self, local_path: str, remote_key: str) -> str:
        object_name = remote_key.lstrip("/")
        file_path = str(Path(local_path))
        self.client.fput_object(self.bucket, object_name, file_path)

        base = settings.S3_RESPONSE_ENDPOINT.rstrip("/")
        # Build public URL. If path-style, include bucket in path; otherwise use virtual-hosted style.
        if settings.S3_PATH_STYLE:
            return f"{base}/{self.bucket}/{object_name}"
        # Virtual-hosted style: http(s)://<bucket>.<host>/object
        parsed = urlparse(base)
        if parsed.scheme and parsed.netloc:
            host = parsed.netloc
            scheme = parsed.scheme
            return f"{scheme}://{self.bucket}.{host}/{object_name}"
        # Fallback to path-style
        return f"{base}/{self.bucket}/{object_name}"


class MockS3Client:
    def __init__(self, bucket: str = "mock-bucket"):
        self.bucket = bucket

    def upload_file(self, local_path: str, remote_key: str) -> str:
        object_name = remote_key.lstrip("/")
        print(f"[S3 MOCK] Upload {local_path} -> s3://{self.bucket}/{object_name}")
        return f"s3://{self.bucket}/{object_name}"
