# ============================================================================
# Project Makefile
# ============================================================================
# All docker compose commands run from librechat/ (where the base compose lives).
# The override file is symlinked in by bootstrap.
# ============================================================================

COMPOSE = cd librechat && docker compose
SHELL := /bin/bash

.DEFAULT_GOAL := help

# --- Bootstrap ---
.PHONY: bootstrap
bootstrap: ## Run bootstrap to generate configs from project.yaml
	./scripts/bootstrap.sh

.PHONY: bootstrap-clean
bootstrap-clean: ## Clean generated files and re-bootstrap
	./scripts/bootstrap.sh --clean

# --- Build & Run ---
.PHONY: up
up: ## Build and start all services (foreground with logs)
	$(COMPOSE) up --build

.PHONY: up-d
up-d: ## Start services in background (must be built first)
	$(COMPOSE) up -d

.PHONY: down
down: ## Stop all services (preserve volumes)
	$(COMPOSE) down

.PHONY: down-v
down-v: ## Stop all services and delete volumes (full reset)
	$(COMPOSE) down -v

.PHONY: restart
restart: ## Restart all services
	$(COMPOSE) restart

# --- Build ---
.PHONY: build
build: ## Build all images without starting
	$(COMPOSE) build

.PHONY: rebuild-api
rebuild-api: ## Rebuild LibreChat image only
	$(COMPOSE) build api && $(COMPOSE) up -d api

.PHONY: rebuild-mcp
rebuild-mcp: ## Rebuild all MCP server images
	$(COMPOSE) build $$($(COMPOSE) config --services | grep -v -E '^(api|mongodb|meilisearch|vectordb|rag_api|pipecat)')

# --- Logs ---
.PHONY: logs
logs: ## Stream logs for all services
	$(COMPOSE) logs -f

.PHONY: logs-api
logs-api: ## Stream logs for the API service only
	$(COMPOSE) logs -f api

# --- Status ---
.PHONY: ps
ps: ## Show running containers
	$(COMPOSE) ps

# --- Validation ---
.PHONY: validate
validate: ## Validate overlay targets against LibreChat submodule
	./scripts/validate-overlay.sh

# --- Prompt Sync ---
.PHONY: sync-prompt
sync-prompt: ## Sync agent system prompt to MongoDB
	@echo "TODO: Configure prompt sync for your agent ID"
	@echo "See scripts/sync-prompt.sh for the template"

# --- Deploy ---
.PHONY: deploy-railway
deploy-railway: ## Deploy to Railway (fully automated)
	./scripts/deploy-railway.sh --name "$(NAME)" --slug "$(SLUG)"

# --- Help ---
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
