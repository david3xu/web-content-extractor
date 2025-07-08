.DEFAULT_GOAL := help
.PHONY: help setup test run docker clean lint format dev

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies and setup development environment
	@echo "🚀 Setting up development environment..."
	pip install poetry
	poetry install
	poetry run pre-commit install
	mkdir -p output logs
	@echo "✅ Setup complete! Run 'make run' to test extraction"

test: ## Run test suite with coverage
	@echo "🧪 Running tests..."
	poetry run pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

run: ## Run extraction example
	@echo "🔍 Running extraction example..."
	poetry run python -c "import asyncio; from src.cli import demo; asyncio.run(demo())"

lint: ## Check code quality
	@echo "🔍 Checking code quality..."
	poetry run ruff check src/ tests/
	poetry run mypy src/

format: ## Format code
	@echo "✨ Formatting code..."
	poetry run black src/ tests/
	poetry run ruff --fix src/ tests/

docker: ## Build and run with Docker
	@echo "🐳 Building Docker container..."
	docker-compose -f docker/docker-compose.yml up --build

clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	rm -rf output/* logs/* .coverage htmlcov/ .mypy_cache/ .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

dev: ## Start development server
	@echo "🚀 Starting development server..."
	poetry run python -m src.cli serve --reload

verify: ## Verify project setup
	@echo "🔍 Verifying project setup..."
	python scripts/verify_setup.py
