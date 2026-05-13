#!/bin/bash
# Bootstraps the Postgres instance with three databases (warehouse, airflow_meta,
# metabase_meta) plus dedicated roles. Runs once, on the first container start
# (when /var/lib/postgresql/data is empty).
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    -- Application roles. One role per service narrows the blast radius if
    -- credentials ever leak; each role only sees its own database/schemas.
    CREATE ROLE airflow      WITH LOGIN PASSWORD '${AIRFLOW_DB_PASSWORD}';
    CREATE ROLE warehouse    WITH LOGIN PASSWORD '${WAREHOUSE_DB_PASSWORD}';
    CREATE ROLE metabase     WITH LOGIN PASSWORD '${METABASE_DB_PASSWORD}';
    CREATE ROLE dbt_dev      WITH LOGIN PASSWORD '${DBT_DEV_PASSWORD}';
    CREATE ROLE metabase_ro  WITH LOGIN PASSWORD '${METABASE_RO_PASSWORD}';

    -- One database per service so we never tangle metadata with analytics.
    CREATE DATABASE airflow_meta  OWNER airflow;
    CREATE DATABASE metabase_meta OWNER metabase;
    CREATE DATABASE warehouse     OWNER warehouse;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "warehouse" <<-EOSQL
    -- Layered schemas. raw is loaded by the ingest pipeline; everything below
    -- staging is built by dbt and never written to by anything else.
    CREATE SCHEMA raw          AUTHORIZATION warehouse;
    CREATE SCHEMA staging      AUTHORIZATION dbt_dev;
    CREATE SCHEMA intermediate AUTHORIZATION dbt_dev;
    CREATE SCHEMA analytics    AUTHORIZATION dbt_dev;

    -- dbt reads raw (loaded by the warehouse user) and writes to the upper layers.
    GRANT USAGE ON SCHEMA raw TO dbt_dev;
    GRANT SELECT ON ALL TABLES IN SCHEMA raw TO dbt_dev;
    ALTER DEFAULT PRIVILEGES FOR ROLE warehouse IN SCHEMA raw
        GRANT SELECT ON TABLES TO dbt_dev;

    -- Metabase reads the published analytics layer only. Read-only by design.
    GRANT USAGE ON SCHEMA analytics TO metabase_ro;
    ALTER DEFAULT PRIVILEGES FOR ROLE dbt_dev IN SCHEMA analytics
        GRANT SELECT ON TABLES TO metabase_ro;
EOSQL
