"""Integration tests for the Postgres loader.

These tests need a live Postgres reachable via INTEGRATION_DSN — set that env
var to run them. Without it they auto-skip via the `integration_dsn` fixture.

Typical invocation from the project root (with the docker stack up):

    INTEGRATION_DSN=postgresql://warehouse:<pwd>@localhost:5432/warehouse \\
        uv run pytest tests/test_loader.py
"""

from __future__ import annotations

import psycopg2
import pytest

from ingest.ddl import RAW_DDL
from ingest.loader import load
from ingest.parser import stream_records

SOURCE_FILE = "test_sample_pneuma.csv"


@pytest.fixture
def fresh_raw(integration_dsn: str):
    """Reset the rows for this test's source_file. Lets the test be re-runnable."""
    with psycopg2.connect(integration_dsn) as conn, conn.cursor() as cur:
        cur.execute(RAW_DDL)
        cur.execute("DELETE FROM raw.trajectory_points WHERE source_file = %s", (SOURCE_FILE,))
        cur.execute("DELETE FROM raw.tracks WHERE source_file = %s", (SOURCE_FILE,))
    yield integration_dsn


def _row_counts(dsn: str) -> tuple[int, int]:
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM raw.tracks WHERE source_file = %s", (SOURCE_FILE,))
        tracks = cur.fetchone()[0]
        cur.execute(
            "SELECT count(*) FROM raw.trajectory_points WHERE source_file = %s",
            (SOURCE_FILE,),
        )
        points = cur.fetchone()[0]
    return tracks, points


def test_load_inserts_expected_rows(fresh_raw, sample_pneuma_path):
    dsn = fresh_raw
    with sample_pneuma_path.open() as fh:
        counts = load(dsn=dsn, source_file=SOURCE_FILE, records=stream_records(fh))

    assert counts.tracks_loaded == 3
    assert counts.points_loaded == 6
    assert _row_counts(dsn) == (3, 6)


def test_load_is_idempotent(fresh_raw, sample_pneuma_path):
    dsn = fresh_raw
    for _ in range(2):
        with sample_pneuma_path.open() as fh:
            load(dsn=dsn, source_file=SOURCE_FILE, records=stream_records(fh))

    # Same data loaded twice should produce no duplicates.
    assert _row_counts(dsn) == (3, 6)
