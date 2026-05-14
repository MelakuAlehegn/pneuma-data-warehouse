{{
    config(
        materialized='view'
    )
}}

with source as (

    select * from {{ source('pneuma', 'tracks') }}

),

renamed as (

    select
        -- surrogate key — single column downstream models can join on
        {{ dbt_utils.generate_surrogate_key(['source_file', 'track_id']) }} as track_sk,

        -- natural key columns (kept for traceability)
        source_file,
        track_id,

        -- descriptive attributes
        vehicle_type,
        traveled_d as total_distance_m,
        avg_speed  as avg_speed_kmh,

        -- audit
        loaded_at

    from source

)

select * from renamed
