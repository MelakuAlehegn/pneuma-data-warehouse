"""Minimal MinIO/S3 client. Uses boto3; works with real S3 too."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import IO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


@dataclass(frozen=True)
class S3Config:
    endpoint_url: str
    access_key: str
    secret_key: str
    region: str = "us-east-1"


class S3Client:
    """Thin wrapper over boto3 with the few operations the ingest pipeline needs."""

    def __init__(self, config: S3Config) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name=config.region,
            config=Config(signature_version="s3v4"),
        )

    def object_exists(self, bucket: str, key: str) -> bool:
        try:
            self._client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as err:
            code = err.response.get("Error", {}).get("Code")
            if code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise

    def upload_file(self, local_path: Path, bucket: str, key: str) -> None:
        self._client.upload_file(str(local_path), bucket, key)

    def get_object_body(self, bucket: str, key: str) -> IO[bytes]:
        return self._client.get_object(Bucket=bucket, Key=key)["Body"]
