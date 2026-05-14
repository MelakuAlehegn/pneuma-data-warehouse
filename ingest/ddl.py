"""Idempotent DDL for the raw layer of the warehouse."""

RAW_DDL = """
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.tracks (
    source_file  TEXT             NOT NULL,
    track_id     INT              NOT NULL,
    vehicle_type TEXT,
    traveled_d   DOUBLE PRECISION,
    avg_speed    DOUBLE PRECISION,
    loaded_at    TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    PRIMARY KEY (source_file, track_id)
);

CREATE TABLE IF NOT EXISTS raw.trajectory_points (
    source_file  TEXT             NOT NULL,
    track_id     INT              NOT NULL,
    frame_idx    INT              NOT NULL,
    lat          DOUBLE PRECISION,
    lon          DOUBLE PRECISION,
    speed        DOUBLE PRECISION,
    lon_acc      DOUBLE PRECISION,
    lat_acc      DOUBLE PRECISION,
    time_sec     DOUBLE PRECISION,
    loaded_at    TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    PRIMARY KEY (source_file, track_id, frame_idx)
);

CREATE INDEX IF NOT EXISTS idx_traj_track
    ON raw.trajectory_points (track_id, source_file);
"""
