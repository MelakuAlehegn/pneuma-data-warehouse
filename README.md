# pneuma-data-warehouse

A production-grade ELT data warehouse built on the **pNEUMA** open dataset — half a million vehicle trajectories captured by a swarm of drones over downtown Athens. The goal is to take raw, irregularly-shaped drone telemetry and turn it into a clean, queryable, dashboarded warehouse using a modern open-source stack.

## Architecture

```
                    ┌────────────────┐
                    │  pNEUMA CSVs   │
                    │   (Zenodo)     │
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐         ┌──────────────┐
                    │     MinIO      │◄────────│   Airflow    │
                    │ (raw landing)  │         │  (Cosmos)    │
                    └────────┬───────┘         └──────┬───────┘
                             │                        │
                             ▼                        │
                    ┌────────────────┐                │
                    │ Postgres: raw  │◄───────────────┘
                    └────────┬───────┘
                             │
                             ▼  (dbt)
              ┌──────────────────────────────┐
              │  staging → intermediate →    │
              │  analytics (star schema)     │
              └──────────────┬───────────────┘
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
              Metabase   dbt docs   Elementary
```

Full diagram and component notes live in [docs/architecture.md](docs/architecture.md).

## Tech stack

| Layer | Tool | Why |
|-------|------|-----|
| Orchestration | Apache Airflow 2.x | Industry standard, mature ecosystem |
| Transformation | dbt-core (Postgres adapter) | The analytics-engineering standard |
| Airflow ↔ dbt | astronomer-cosmos | Auto-renders dbt models as Airflow tasks |
| Warehouse | PostgreSQL 16 | Free, well-supported, ANSI-friendly |
| Raw landing | MinIO (S3-compatible) | Cloud-portable lake-style pattern |
| BI | Metabase | Modern, easy to dockerize |
| Data quality | dbt-expectations + Elementary | dbt-native tests + run observability |
| Python tooling | uv, Ruff, pytest, pre-commit | Fast, modern, low-friction |
| CI/CD | GitHub Actions | Free for public repos |

## Project layout

```
.
├── airflow/        # DAGs, plugins, shared helpers
├── dbt/dwh/        # dbt project: models, macros, tests, snapshots
├── ingest/         # Python ingest code (importable by Airflow)
├── infra/          # docker-compose, Postgres init, MinIO bootstrap
├── tests/          # pytest suite for ingest/helpers
├── docs/           # Architecture and ADRs
└── .github/        # CI workflows
```

## Quickstart

Python tooling is in place today; the Docker stack lands shortly.

```bash
make install        # uv sync + pre-commit install
make lint           # ruff check
make format         # ruff format
```

Once the stack is in:

```bash
cp .env.example .env
make up             # bring up the whole stack
make ingest         # run the ingest DAG
make dbt-run        # transform raw → analytics
make dbt-docs       # browse dbt lineage docs
```
