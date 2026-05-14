/*
    delta_distance_m is computed via the haversine_meters macro, which
    returns a great-circle distance — by definition non-negative. A negative
    value would mean the macro is broken (or someone introduced an
    overflow). Catch it before consumers see it.
*/
select
    trajectory_point_sk,
    track_sk,
    delta_distance_m
from {{ ref('fct_trajectory_points') }}
where delta_distance_m < 0
