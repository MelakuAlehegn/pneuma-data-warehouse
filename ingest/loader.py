"""Postgres bulk loader using COPY + temp-staging upsert."""

from __future__ import annotations

import io
from collections.abc import Iterable
from dataclasses import dataclass

import psycopg2

from ingest.parser import Track, TrajectoryPoint

# Batches limit peak memory in the trajectory_points CSV buffer. 50k rows of
# eight float columns is roughly 4 MB of UTF-8 — small, but enough to amortise
# the round-trip cost of COPY.
DEFAULT_BATCH_SIZE = 50_000


@dataclass
class LoadCounts:
    tracks_loaded: int
    points_loaded: int


def _tracks_to_csv(source_file: str, tracks: Iterable[Track]) -> tuple[io.StringIO, int]:
    buf = io.StringIO()
    n = 0
    for t in tracks:
        buf.write(f"{source_file}\t{t.track_id}\t{t.vehicle_type}\t{t.traveled_d}\t{t.avg_speed}\n")
        n += 1
    buf.seek(0)
    return buf, n


def _points_chunk_to_csv(source_file: str, points: list[TrajectoryPoint]) -> io.StringIO:
    buf = io.StringIO()
    for p in points:
        buf.write(
            f"{source_file}\t{p.track_id}\t{p.frame_idx}\t"
            f"{p.lat}\t{p.lon}\t{p.speed}\t{p.lon_acc}\t{p.lat_acc}\t{p.time_sec}\n"
        )
    buf.seek(0)
    return buf


def load(
    dsn: str,
    source_file: str,
    records: Iterable[tuple[Track, list[TrajectoryPoint]]],
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> LoadCounts:
    """Stream (track, points) records into raw.tracks and raw.trajectory_points.

    Uses temp staging tables + ON CONFLICT DO NOTHING so re-running with the
    same source_file is a no-op.
    """
    tracks_accum: list[Track] = []
    points_buffer: list[TrajectoryPoint] = []
    points_loaded = 0

    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TEMP TABLE _tracks_stg (
                source_file TEXT, track_id INT, vehicle_type TEXT,
                traveled_d DOUBLE PRECISION, avg_speed DOUBLE PRECISION
            ) ON COMMIT DROP;
            CREATE TEMP TABLE _points_stg (
                source_file TEXT, track_id INT, frame_idx INT,
                lat DOUBLE PRECISION, lon DOUBLE PRECISION, speed DOUBLE PRECISION,
                lon_acc DOUBLE PRECISION, lat_acc DOUBLE PRECISION,
                time_sec DOUBLE PRECISION
            ) ON COMMIT DROP;
            """
        )

        def flush_points() -> None:
            nonlocal points_loaded
            if not points_buffer:
                return
            buf = _points_chunk_to_csv(source_file, points_buffer)
            cur.copy_expert("COPY _points_stg FROM STDIN", buf)
            points_loaded += len(points_buffer)
            points_buffer.clear()

        for track, points in records:
            tracks_accum.append(track)
            points_buffer.extend(points)
            if len(points_buffer) >= batch_size:
                flush_points()

        flush_points()

        tracks_buf, tracks_count = _tracks_to_csv(source_file, tracks_accum)
        cur.copy_expert("COPY _tracks_stg FROM STDIN", tracks_buf)

        cur.execute(
            """
            INSERT INTO raw.tracks
                (source_file, track_id, vehicle_type, traveled_d, avg_speed)
            SELECT source_file, track_id, vehicle_type, traveled_d, avg_speed
            FROM _tracks_stg
            ON CONFLICT (source_file, track_id) DO NOTHING;
            """
        )
        cur.execute(
            """
            INSERT INTO raw.trajectory_points
                (source_file, track_id, frame_idx, lat, lon, speed,
                 lon_acc, lat_acc, time_sec)
            SELECT source_file, track_id, frame_idx, lat, lon, speed,
                   lon_acc, lat_acc, time_sec
            FROM _points_stg
            ON CONFLICT (source_file, track_id, frame_idx) DO NOTHING;
            """
        )

    return LoadCounts(tracks_loaded=tracks_count, points_loaded=points_loaded)
