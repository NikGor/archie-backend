.PHONY: help install dev run db-up db-down db-reset test clean db-init db-revision db-upgrade db-downgrade db-history db-current db-stamp

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies with Poetry
	poetry install

dev: ## Install development dependencies
	poetry install --with dev

run: ## Run the FastAPI server
	poetry run uvicorn main:app --host 0.0.0.0 --port 8002 --reload

services-up: ## Start all services (Backend + PostgreSQL + Redis)
	docker-compose up -d

services-build: ## Build and start all services
	docker-compose up --build -d

services-down: ## Stop all services
	docker-compose down

services-reset: ## Reset all services (stop, remove volumes, start)
	docker-compose down -v
	docker-compose up --build -d

services-logs: ## Show logs from all services
	docker-compose logs -f

network-create: ## Create shared network
	docker network create shared_network || true

network-remove: ## Remove shared network
	docker network rm shared_network || true

db-up: ## Start PostgreSQL container only
	docker-compose up -d postgres

redis-up: ## Start Redis container only
	docker-compose up -d redis

db-down: ## Stop PostgreSQL container
	docker-compose down

db-reset: ## Reset database (stop, remove volumes, start)
	docker-compose down -v
	docker-compose up -d postgres

redis-test: ## Test Redis connection and operations
	poetry run python test_redis.py

test: ## Run tests
	poetry run pytest

clean: ## Clean up build artifacts
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

format: ## Format code with black
	poetry run black .

lint: ## Run linting with ruff
	poetry run ruff check .

fix: ## Fix auto-fixable issues with ruff
	poetry run ruff check . --fix

check: ## Run both formatting and linting
	poetry run black --check .
	poetry run ruff check .

# Note: Database migrations are handled by Django
