"""Streaming parser for the pNEUMA CSV format.

A pNEUMA file is semicolon-delimited. The header has 10 columns. Each data row
represents ONE vehicle and has 4 fixed columns (track_id, vehicle_type,
traveled_d, avg_speed) followed by N * 6 columns — one repeating block of
(lat, lon, speed, lon_acc, lat_acc, time) per recorded frame. N varies per row,
which is why a vanilla pd.read_csv chokes on the file.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import IO

FIXED_COLS = 4
POINT_COLS = 6
DELIMITER = ";"


@dataclass(frozen=True, slots=True)
class Track:
    track_id: int
    vehicle_type: str
    traveled_d: float
    avg_speed: float


@dataclass(frozen=True, slots=True)
class TrajectoryPoint:
    track_id: int
    frame_idx: int
    lat: float
    lon: float
    speed: float
    lon_acc: float
    lat_acc: float
    time_sec: float


class PneumaParseError(ValueError):
    """Raised when a row does not match the expected pNEUMA shape."""


def _split_row(line: str) -> list[str]:
    """Split a pNEUMA row, tolerating a trailing delimiter and surrounding whitespace."""
    stripped = line.strip().rstrip(DELIMITER)
    return [field.strip() for field in stripped.split(DELIMITER)]


def parse_row(line: str) -> tuple[Track, list[TrajectoryPoint]]:
    """Parse one vehicle row into a Track header and a list of trajectory points."""
    fields = _split_row(line)
    if len(fields) < FIXED_COLS:
        raise PneumaParseError(f"Row has {len(fields)} fields, expected at least {FIXED_COLS}")

    remainder = len(fields) - FIXED_COLS
    if remainder % POINT_COLS != 0:
        raise PneumaParseError(
            f"Row has {len(fields)} fields; remainder after the {FIXED_COLS} "
            f"header columns ({remainder}) is not divisible by {POINT_COLS}"
        )

    track = Track(
        track_id=int(fields[0]),
        vehicle_type=fields[1],
        traveled_d=float(fields[2]),
        avg_speed=float(fields[3]),
    )

    points: list[TrajectoryPoint] = []
    for frame_idx, start in enumerate(range(FIXED_COLS, len(fields), POINT_COLS)):
        block = fields[start : start + POINT_COLS]
        points.append(
            TrajectoryPoint(
                track_id=track.track_id,
                frame_idx=frame_idx,
                lat=float(block[0]),
                lon=float(block[1]),
                speed=float(block[2]),
                lon_acc=float(block[3]),
                lat_acc=float(block[4]),
                time_sec=float(block[5]),
            )
        )
    return track, points


def stream_records(
    file_obj: IO[str],
) -> Iterator[tuple[Track, list[TrajectoryPoint]]]:
    """Iterate (track, [points]) tuples for every vehicle in the file.

    The first line is discarded as the column header.
    """
    header = next(file_obj, None)
    if header is None:
        return
    for line in file_obj:
        if not line.strip():
            continue
        yield parse_row(line)
