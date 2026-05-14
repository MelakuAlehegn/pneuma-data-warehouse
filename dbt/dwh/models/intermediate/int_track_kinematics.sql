{{
    config(
        materialized='table'
    )
}}

{# Per-vehicle aggregations of trajectory_points. dim_track depends on this.
   Overridden to `table` because the aggregation is expensive and the result is
   small (one row per vehicle), so we want it computed once. #}

with points as (

    select * from {{ ref('stg_pneuma_trajectory_points') }}

)

select
    track_sk,

    count(*) as point_count,

    min(seconds_since_start) as first_seen_sec,
    max(seconds_since_start) as last_seen_sec,
    max(seconds_since_start) - min(seconds_since_start) as duration_sec,

    min(speed_kmh) as min_speed_kmh,
    max(speed_kmh) as max_speed_kmh,

    count(*) filter (where speed_kmh < 1) as stopped_point_count

from points

group by track_sk
