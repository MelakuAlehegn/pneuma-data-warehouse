{#
    One row per observed vehicle. Joins the staging-level descriptive fields
    with the intermediate per-track aggregations. Carries a foreign key to
    dim_vehicle_type so the fact table doesn't have to.
#}

with tracks as (

    select * from {{ ref('stg_pneuma_tracks') }}

),

kinematics as (

    select * from {{ ref('int_track_kinematics') }}

),

vehicle_types as (

    select * from {{ ref('dim_vehicle_type') }}

),

joined as (

    select
        tracks.track_sk,

        -- foreign key to dim_vehicle_type
        vehicle_types.vehicle_type_sk,

        -- natural identifiers, for traceability
        tracks.source_file,
        tracks.track_id,

        -- descriptive attributes from raw
        tracks.vehicle_type,
        tracks.total_distance_m,
        tracks.avg_speed_kmh,

        -- derived attributes from int_track_kinematics
        kinematics.point_count,
        kinematics.duration_sec,
        kinematics.min_speed_kmh,
        kinematics.max_speed_kmh,
        kinematics.stopped_point_count,

        -- audit
        tracks.loaded_at

    from tracks
    left join kinematics
        on tracks.track_sk = kinematics.track_sk
    left join vehicle_types
        on tracks.vehicle_type = vehicle_types.vehicle_type_name

)

select * from joined
