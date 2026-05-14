/*
    Vehicles on a city street should not be doing 250 km/h. If dim_track
    surfaces anything over that threshold, the source units are wrong, the
    parser is mis-aligning columns, or we have a real outlier worth
    investigating. Either way: stop the build.
*/
select
    track_sk,
    vehicle_type,
    max_speed_kmh
from {{ ref('dim_track') }}
where max_speed_kmh > 250
