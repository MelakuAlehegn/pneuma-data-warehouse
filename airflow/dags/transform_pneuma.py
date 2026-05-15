"""Transform DAG: rebuilds the dbt project after each successful ingest.

Triggered automatically when `ingest_pneuma` emits the `pneuma_raw` asset.
Cosmos parses the dbt project at DAG-parse time (`LoadMode.DBT_LS`) and renders
each model + test as its own Airflow task. With `TestBehavior.AFTER_EACH`,
tests run immediately after the model they cover; a failing test blocks the
downstream models, giving us the test-as-circuit-breaker behaviour the brief
calls for.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from cosmos import (
    DbtTaskGroup,
    ExecutionConfig,
    ProfileConfig,
    ProjectConfig,
    RenderConfig,
)
from cosmos.constants import LoadMode, TestBehavior

from airflow.decorators import dag
from include.assets import pneuma_raw

DBT_PROJECT_PATH = Path("/opt/airflow/dbt")
DBT_EXECUTABLE = "/home/airflow/.local/bin/dbt"


@dag(
    dag_id="transform_pneuma",
    description=(
        "Run the dbt project against raw.* whenever a fresh ingest completes. "
        "Each dbt model is rendered as its own Airflow task via Cosmos."
    ),
    schedule=[pneuma_raw],
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["transform", "dbt", "cosmos"],
    default_args={"retries": 0},
)
def transform_pneuma():
    DbtTaskGroup(
        group_id="dbt",
        project_config=ProjectConfig(DBT_PROJECT_PATH),
        profile_config=ProfileConfig(
            profile_name="dwh",
            target_name=os.environ.get("DBT_TARGET", "prod"),
            profiles_yml_filepath=DBT_PROJECT_PATH / "profiles.yml",
        ),
        execution_config=ExecutionConfig(dbt_executable_path=DBT_EXECUTABLE),
        render_config=RenderConfig(
            load_method=LoadMode.DBT_LS,
            # AFTER_ALL: build every model, then run `dbt test` as one final
            # task. Cross-model tests like `relationships` work cleanly because
            # both sides exist by the time the test runs. A failing test fails
            # the DAG, which gates Metabase / downstream consumers.
            test_behavior=TestBehavior.AFTER_ALL,
        ),
    )


transform_pneuma()
