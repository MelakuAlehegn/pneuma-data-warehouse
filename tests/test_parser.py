"""Unit tests for the pNEUMA parser. No external services involved."""

from __future__ import annotations

import pytest

from ingest.parser import (
    PneumaParseError,
    Track,
    TrajectoryPoint,
    parse_row,
    stream_records,
)


def test_parse_row_two_points():
    row = (
        "1; Car; 50.0; 10.0; "
        "37.97; 23.73; 5.0; 0.10; 0.00; 0.00; "
        "37.97; 23.73; 5.10; 0.10; 0.00; 0.04;"
    )
    track, points = parse_row(row)

    assert track == Track(track_id=1, vehicle_type="Car", traveled_d=50.0, avg_speed=10.0)
    assert len(points) == 2
    assert points[0] == TrajectoryPoint(
        track_id=1,
        frame_idx=0,
        lat=37.97,
        lon=23.73,
        speed=5.0,
        lon_acc=0.10,
        lat_acc=0.00,
        time_sec=0.00,
    )
    assert points[1].frame_idx == 1
    assert points[1].speed == 5.10


def test_parse_row_single_point():
    row = "2; Motorcycle; 100.0; 20.0; 37.98; 23.74; 15.0; 0.00; 0.00; 0.00;"
    track, points = parse_row(row)
    assert track.vehicle_type == "Motorcycle"
    assert len(points) == 1


def test_parse_row_rejects_bad_remainder():
    row = "1; Car; 50.0; 10.0; 37.97; 23.73; 5.0;"
    with pytest.raises(PneumaParseError):
        parse_row(row)


def test_parse_row_rejects_too_few_columns():
    with pytest.raises(PneumaParseError):
        parse_row("1; Car;")


def test_stream_records_from_fixture(sample_pneuma_path):
    with sample_pneuma_path.open() as fh:
        results = list(stream_records(fh))

    assert [t.track_id for t, _ in results] == [1, 2, 3]
    assert [len(pts) for _, pts in results] == [2, 1, 3]
    total_points = sum(len(pts) for _, pts in results)
    assert total_points == 6


def test_frame_idx_starts_at_zero_and_increments(sample_pneuma_path):
    with sample_pneuma_path.open() as fh:
        _, points = next(stream_records(fh))
    assert [p.frame_idx for p in points] == [0, 1]
