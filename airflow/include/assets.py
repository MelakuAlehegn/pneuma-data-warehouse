"""Asset declarations shared across DAGs.

Centralising assets here avoids drift: producer and consumer DAGs both import
the same object, so the dependency graph in the Airflow UI stays correct.
"""

from airflow.sdk import Asset

pneuma_raw = Asset(name="pneuma_raw")
"""Emitted by `ingest_pneuma` once raw.tracks and raw.trajectory_points are populated.

`transform_pneuma` listens for it to kick off the dbt build, so the transform
runs exactly as often as ingest succeeds — no cron coupling needed.
"""
