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

```bash
# One-time
make install                  # uv sync + pre-commit install
cp .env.example .env          # then fill in real secrets (see below)
make build                    # build the custom Airflow image (~5 min first time)

# Daily
make up                       # start the stack
make ps                       # see what's running
make logs                     # tail all logs
make down                     # stop (data survives)
make clean                    # stop AND wipe volumes
```

Generate the two required secrets:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # AIRFLOW_FERNET_KEY
openssl rand -hex 32                                                                       # AIRFLOW_JWT_SECRET
```

On Linux, set `AIRFLOW_UID` to your host user id so bind-mounted files aren't root-owned:

```bash
echo "AIRFLOW_UID=$(id -u)" >> .env
```

### Running services

| Service | URL | Login |
|---|---|---|
| Airflow UI | http://localhost:8080 | `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD` |
| Metabase | http://localhost:3000 | set on first visit |
| MinIO console | http://localhost:9001 | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| pgweb (DB explorer) | http://localhost:8081 | pre-connected as `POSTGRES_USER` |
| MailHog (alert inbox) | http://localhost:8025 | none — captures every email |
| Postgres | `localhost:5432` | per-service roles in `.env` |
