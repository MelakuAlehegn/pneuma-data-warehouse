"""Transform DAG: rebuilds the dbt project after each successful ingest.

Triggered automatically when `ingest_pneuma` emits the `pneuma_raw` asset.
Cosmos parses the dbt project at DAG-parse time (`LoadMode.DBT_LS`) and renders
each model + test as its own Airflow task. With `TestBehavior.AFTER_ALL`, dbt
handles run+test ordering correctly (including cross-model `relationships`
tests). A failing test fails the DAG, gating downstream consumers — the
circuit-breaker the brief calls for.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

from cosmos import (
    DbtTaskGroup,
    ExecutionConfig,
    ProfileConfig,
    ProjectConfig,
    RenderConfig,
)
from cosmos.constants import LoadMode, SourceRenderingBehavior, TestBehavior

from airflow.decorators import dag, task
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
    default_args={
        "retries": 0,
        "email": [os.environ.get("ALERT_EMAIL", "admin@pneuma-dwh.local")],
        "email_on_failure": True,
    },
)
def transform_pneuma():
    dbt_tg = DbtTaskGroup(
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
            # Each source that has a `freshness:` block in sources.yml becomes
            # its own task that runs `dbt source freshness`. Wired upstream of
            # the model tasks via Cosmos's auto-graph — if raw is stale, no
            # transformation happens.
            source_rendering_behavior=SourceRenderingBehavior.WITH_TESTS_OR_FRESHNESS,
            test_behavior=TestBehavior.AFTER_ALL,
            # Elementary's package ships ~20 of its own models. Hide them from
            # the visual graph; they get refreshed in a single batched task
            # below. The on-run-end hooks still capture run metadata regardless.
            exclude=["package:elementary"],
        ),
    )

    @task
    def refresh_elementary() -> None:
        """Run dbt against just the elementary package so its run-history and
        test-results models pick up everything from the current pipeline run.

        The HTML report (via `edr report`) is intentionally NOT a DAG task —
        its internal dbt runner conflicts with site-packages permissions.
        Generate it manually when you want a snapshot:
            uv tool install elementary-data
            cd dbt/dwh
            edr report --project-name dwh --profile-target dev --profiles-dir .
        """
        subprocess.run(
            [
                DBT_EXECUTABLE,
                "build",
                "--select",
                "package:elementary",
                "--profiles-dir",
                str(DBT_PROJECT_PATH),
                "--project-dir",
                str(DBT_PROJECT_PATH),
                "--target",
                os.environ.get("DBT_TARGET", "prod"),
            ],
            check=True,
        )

    dbt_tg >> refresh_elementary()


transform_pneuma()
