"""Ingest one pNEUMA CSV: local data/ → MinIO → raw.tracks + raw.trajectory_points.

The real work lives in the `ingest` package; this DAG is a thin Airflow wrapper.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag, task

from include.assets import pneuma_raw

DATA_DIR = Path("/opt/airflow/data")


@dag(
    dag_id="ingest_pneuma",
    description=(
        "Stage a pNEUMA CSV in MinIO and upsert it into raw.tracks and "
        "raw.trajectory_points. Manual trigger."
    ),
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ingest", "pneuma", "raw"],
    default_args={
        "retries": 0,
        "email": [os.environ.get("ALERT_EMAIL", "admin@pneuma-dwh.local")],
        "email_on_failure": True,
    },
)
def ingest_pneuma():
    @task
    def ingest(filename: str) -> dict:
        from ingest.pipeline import run_ingest

        return run_ingest(
            pg_dsn=os.environ["WAREHOUSE_DSN"],
            s3_endpoint=os.environ["MINIO_ENDPOINT"],
            s3_access_key=os.environ["MINIO_ROOT_USER"],
            s3_secret_key=os.environ["MINIO_ROOT_PASSWORD"],
            bucket=os.environ["MINIO_BUCKET_RAW"],
            filename=filename,
            local_data_dir=DATA_DIR,
        )

    @task(outlets=[pneuma_raw])
    def validate(counts: dict) -> None:
        """Sanity-check the load, then emit the pneuma_raw asset so the
        transform DAG picks up automatically."""
        if counts["tracks_loaded"] == 0:
            raise ValueError(f"Ingest finished with zero tracks loaded: {counts}")
        if counts["points_loaded"] == 0:
            raise ValueError(f"Ingest finished with zero trajectory points loaded: {counts}")

    filename = os.environ.get("PNEUMA_FILE", "20181101_d1_0800_0830.csv")
    validate(ingest(filename))


ingest_pneuma()
