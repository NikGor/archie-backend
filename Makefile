.PHONY: help install dev run db-up db-down db-reset test clean

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

db-up: ## Start PostgreSQL container
	docker-compose up -d postgres

db-down: ## Stop PostgreSQL container
	docker-compose down

db-reset: ## Reset database (stop, remove volumes, start)
	docker-compose down -v
	docker-compose up -d postgres

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
