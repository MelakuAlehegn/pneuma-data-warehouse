SHELL := /bin/bash
.DEFAULT_GOAL := help
COMPOSE := docker compose -f infra/docker-compose.yml

.PHONY: help install lint format test up down logs ps restart clean
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

# ---------- Docker stack (filled in during Phase 1) ----------

up: ## Start the full stack
	$(COMPOSE) up -d

down: ## Stop the stack
	$(COMPOSE) down

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

ps: ## Show running services
	$(COMPOSE) ps

restart: down up ## Restart the stack

clean: ## Remove containers, volumes, and networks
	$(COMPOSE) down -v --remove-orphans

# ---------- Pipeline shortcuts (filled in during Phases 2-4) ----------

ingest: ## Trigger the ingest DAG
	@echo "Implemented in Phase 2"

dbt-deps: ## Install dbt packages
	@echo "Implemented in Phase 3"

dbt-run: ## Run dbt models
	@echo "Implemented in Phase 3"

dbt-test: ## Run dbt tests
	@echo "Implemented in Phase 3"

dbt-docs: ## Generate and serve dbt docs
	@echo "Implemented in Phase 3"
