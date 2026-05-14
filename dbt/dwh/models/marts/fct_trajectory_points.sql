{{
    config(
        materialized='incremental',
        unique_key='trajectory_point_sk',
        incremental_strategy='merge',
        on_schema_change='sync_all_columns'
    )
}}

{#
    The grain: one row per recorded frame per vehicle. Several million rows
    per source file, so a full rebuild on every dbt run gets expensive fast.
    Incremental + merge means we only process rows the ingest pipeline has
    added since the last build, and re-running the same file is a no-op
    (the merge upserts by trajectory_point_sk).
#}

with points as (

    select * from {{ ref('int_trajectory_points_with_deltas') }}

    {% if is_incremental() %}
        -- On every run after the first, only process points that landed in
        -- raw after the newest one already in this table.
        where loaded_at > (select coalesce(max(loaded_at), '1900-01-01'::timestamptz) from {{ this }})
    {% endif %}

)

select
    trajectory_point_sk,
    track_sk,

    -- natural keys (kept for lineage / debugging)
    source_file,
    track_id,
    frame_idx,

    -- spatial
    latitude,
    longitude,

    -- kinematics
    speed_kmh,
    lon_acceleration_ms2,
    lat_acceleration_ms2,

    -- temporal
    seconds_since_start,

    -- derived from intermediate
    delta_time_sec,
    delta_speed_kmh,
    delta_distance_m,
    speed_bucket,

    -- audit
    loaded_at

from points
