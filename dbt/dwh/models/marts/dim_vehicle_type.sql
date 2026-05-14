{#
    Tiny conformed dimension — one row per distinct vehicle category in the data.
    Materialised as a table (the marts default) so consumers can join cheaply.
#}

with types as (

    select distinct vehicle_type
    from {{ ref('stg_pneuma_tracks') }}
    where vehicle_type is not null

)

select
    {{ dbt_utils.generate_surrogate_key(['vehicle_type']) }} as vehicle_type_sk,
    vehicle_type as vehicle_type_name

from types
