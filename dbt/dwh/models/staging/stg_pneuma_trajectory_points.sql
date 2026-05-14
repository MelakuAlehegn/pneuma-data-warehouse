{{
    config(
        materialized='view'
    )
}}

with source as (

    select * from {{ source('pneuma', 'trajectory_points') }}

),

renamed as (

    select
        -- surrogate key for this point (unique per row)
        {{ dbt_utils.generate_surrogate_key(['source_file', 'track_id', 'frame_idx']) }} as trajectory_point_sk,

        -- foreign key to stg_pneuma_tracks — same formula as that model's track_sk
        {{ dbt_utils.generate_surrogate_key(['source_file', 'track_id']) }} as track_sk,

        -- natural key columns
        source_file,
        track_id,
        frame_idx,

        -- spatial
        lat as latitude,
        lon as longitude,

        -- kinematics
        speed   as speed_kmh,
        lon_acc as lon_acceleration_ms2,
        lat_acc as lat_acceleration_ms2,

        -- time within the recording window
        time_sec as seconds_since_start,

        -- audit
        loaded_at

    from source

)

select * from renamed
