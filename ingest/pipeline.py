"""Top-level ingest orchestration. Called by the Airflow DAG."""

from __future__ import annotations

import io
import logging
from dataclasses import asdict
from pathlib import Path

import psycopg2

from ingest.ddl import RAW_DDL
from ingest.loader import LoadCounts, load
from ingest.parser import stream_records
from ingest.s3 import S3Client, S3Config

log = logging.getLogger(__name__)


def ensure_raw_schema(dsn: str) -> None:
    """Create raw.tracks and raw.trajectory_points if they don't already exist."""
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(RAW_DDL)


def stage_in_minio(
    s3: S3Client,
    bucket: str,
    key: str,
    local_path: Path,
) -> None:
    """Upload local_path to s3://bucket/key if the object isn't there yet."""
    if s3.object_exists(bucket, key):
        log.info("Object already in MinIO: s3://%s/%s — skipping upload", bucket, key)
        return
    if not local_path.exists():
        raise FileNotFoundError(
            f"Neither s3://{bucket}/{key} nor local {local_path} exists. "
            "Drop a pNEUMA CSV in ./data on the host and re-trigger."
        )
    log.info("Uploading %s → s3://%s/%s", local_path, bucket, key)
    s3.upload_file(local_path, bucket, key)


def parse_and_load(
    s3: S3Client,
    bucket: str,
    key: str,
    source_file: str,
    dsn: str,
) -> LoadCounts:
    """Stream the object from MinIO, parse it, and upsert into raw.*."""
    log.info("Streaming s3://%s/%s into Postgres", bucket, key)
    body = s3.get_object_body(bucket, key)
    text_stream = io.TextIOWrapper(body, encoding="utf-8", newline="")
    return load(dsn=dsn, source_file=source_file, records=stream_records(text_stream))


def run_ingest(
    *,
    pg_dsn: str,
    s3_endpoint: str,
    s3_access_key: str,
    s3_secret_key: str,
    bucket: str,
    filename: str,
    local_data_dir: Path,
) -> dict[str, int]:
    """Full pipeline: ensure schema → stage file in MinIO → parse + load.

    The Airflow DAG calls this once per run with all the required config so
    nothing in `ingest.*` needs to know Airflow exists.
    """
    s3 = S3Client(
        S3Config(endpoint_url=s3_endpoint, access_key=s3_access_key, secret_key=s3_secret_key)
    )
    key = f"pneuma/{filename}"

    ensure_raw_schema(pg_dsn)
    stage_in_minio(s3, bucket, key, local_data_dir / filename)
    counts = parse_and_load(s3, bucket, key, filename, pg_dsn)

    log.info("Ingest finished: %s", counts)
    return asdict(counts)
