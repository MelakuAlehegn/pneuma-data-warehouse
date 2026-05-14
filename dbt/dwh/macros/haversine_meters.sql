{#
    Great-circle distance between two (lat, lon) points, in metres.

    Arguments are SQL expressions — usually column names, but anything that
    evaluates to a number works (literals, CASE expressions, other macros).
    The macro returns the raw SQL fragment; it is inlined wherever it is
    referenced and the warehouse evaluates it once per row.

    Earth radius is taken as 6_371_000 metres (mean). For metre-level
    precision over neighbouring frames this is more than accurate enough.

    Usage:
        select
            {{ haversine_meters('prev_latitude', 'prev_longitude', 'latitude', 'longitude') }}
                as delta_distance_m
        from ...
#}
{% macro haversine_meters(lat1, lon1, lat2, lon2) -%}
    6371000 * 2 * asin(sqrt(
        power(sin(radians({{ lat2 }} - {{ lat1 }}) / 2), 2)
        + cos(radians({{ lat1 }})) * cos(radians({{ lat2 }}))
          * power(sin(radians({{ lon2 }} - {{ lon1 }}) / 2), 2)
    ))
{%- endmacro %}
