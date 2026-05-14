{#
    Custom schema naming.

    Default dbt behavior is to ALWAYS prefix the model's +schema config with
    target.schema, e.g. for target.schema='dbt_dev' a marts model lands in
    `dbt_dev_analytics`. That's exactly what we want for dev and ci so each
    environment is isolated.

    In prod we don't want the prefix — the marts should live in plain
    `analytics`, `staging` lives in `staging`, etc. — so Metabase, downstream
    consumers, and Postgres grants can target stable schema names.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if target.name == 'prod' and custom_schema_name is not none -%}
        {{ custom_schema_name | trim }}
    {%- elif custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ default_schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
