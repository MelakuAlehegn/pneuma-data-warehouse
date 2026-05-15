SHELL := /bin/bash
.DEFAULT_GOAL := help
COMPOSE := docker compose --env-file .env -f infra/docker-compose.yml

.PHONY: help install lint format test build up down logs ps restart clean
.PHONY: ingest dbt-deps dbt-run dbt-test dbt-docs

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ---------- Local dev tooling ----------

install: ## Sync Python deps with uv and install pre-commit hooks
	uv sync
	uv run pre-commit install

lint: ## Lint code (ruff)
	uv run ruff check .

format: ## Format code (ruff)
	uv run ruff format .

test: ## Run pytest suite
	uv run pytest

# ---------- Docker stack ----------

build: ## Build custom images (Airflow with dbt + Cosmos)
	$(COMPOSE) build

up: ## Start the full stack in the background
	$(COMPOSE) up

down: ## Stop the stack (containers + networks; data volumes survive)
	$(COMPOSE) down

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

ps: ## Show running services
	$(COMPOSE) ps

restart: down up ## Restart the stack

clean: ## Remove containers, networks, AND named volumes (wipes data)
	$(COMPOSE) down -v --remove-orphans

# ---------- Pipeline shortcuts (filled in during Phases 2-4) ----------

ingest: ## Trigger the ingest DAG (alternative: run from Airflow UI)
	$(COMPOSE) exec -T airflow-scheduler airflow dags trigger ingest_pneuma

transform: ## Trigger the transform DAG manually (normally fires on the pneuma_raw asset)
	$(COMPOSE) exec -T airflow-scheduler airflow dags trigger transform_pneuma

# dbt targets run inside the airflow-scheduler container so versions match the
# image we deploy. For local dev iteration install dbt via `uv tool install
# dbt-postgres==X.Y.Z` and run `dbt` directly from dbt/dwh/.

DBT := $(COMPOSE) exec -T -w /opt/airflow/dbt airflow-scheduler dbt

dbt-debug: ## Verify dbt connectivity to the warehouse
	$(DBT) debug

dbt-deps: ## Install dbt packages declared in packages.yml
	$(DBT) deps

dbt-build: ## Run models AND tests, fail fast on errors
	$(DBT) build

dbt-run: ## Run models only
	$(DBT) run

dbt-test: ## Run tests only
	$(DBT) test

dbt-docs-generate: ## Build the dbt docs static site under dbt/dwh/target
	$(DBT) docs generate
	@echo "Generated. Serve from host with: cd dbt/dwh/target && python -m http.server 8001"
