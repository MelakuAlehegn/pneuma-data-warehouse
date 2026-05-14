{{
    config(
        materialized='table'
    )
}}

{#
    Speed distribution rolled up to one row per vehicle type. The fact has
    millions of rows; this has six. Metabase reads this table directly
    instead of aggregating the fact on every dashboard hit.
#}

with points as (

    select * from {{ ref('fct_trajectory_points') }}

),

tracks as (

    select track_sk, vehicle_type_sk from {{ ref('dim_track') }}

),

vehicle_types as (

    select vehicle_type_sk, vehicle_type_name from {{ ref('dim_vehicle_type') }}

),

joined as (

    select
        vehicle_types.vehicle_type_sk,
        vehicle_types.vehicle_type_name,
        points.speed_kmh
    from points
    inner join tracks
        on points.track_sk = tracks.track_sk
    inner join vehicle_types
        on tracks.vehicle_type_sk = vehicle_types.vehicle_type_sk

)

select
    vehicle_type_sk,
    vehicle_type_name,

    count(*) as observation_count,

    avg(speed_kmh)                                                       as avg_speed_kmh,
    min(speed_kmh)                                                       as min_speed_kmh,
    max(speed_kmh)                                                       as max_speed_kmh,
    stddev(speed_kmh)                                                    as stddev_speed_kmh,

    percentile_cont(0.50) within group (order by speed_kmh)              as median_speed_kmh,
    percentile_cont(0.95) within group (order by speed_kmh)              as p95_speed_kmh

from joined
group by vehicle_type_sk, vehicle_type_name
