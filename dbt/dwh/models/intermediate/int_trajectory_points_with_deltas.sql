{# Ephemeral by layer default — dbt inlines this CTE into downstream consumers. #}

with points as (

    select * from {{ ref('stg_pneuma_trajectory_points') }}

),

with_lag as (

    -- Pull each point's predecessor (within the same track) using window functions.
    select
        *,
        lag(speed_kmh) over (
            partition by track_sk
            order by frame_idx
        ) as prev_speed_kmh,

        lag(seconds_since_start) over (
            partition by track_sk
            order by frame_idx
        ) as prev_seconds_since_start

    from points

),

with_deltas as (

    select
        *,
        seconds_since_start - prev_seconds_since_start as delta_time_sec,
        speed_kmh - prev_speed_kmh                     as delta_speed_kmh,

        case
            when speed_kmh < 1   then 'STOPPED'
            when speed_kmh < 10  then 'SLOW'
            when speed_kmh < 50  then 'NORMAL'
            else 'FAST'
        end as speed_bucket

    from with_lag

)

select * from with_deltas
