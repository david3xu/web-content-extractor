.DEFAULT_GOAL := help
.PHONY: help setup test run docker clean lint format dev fix install-hooks

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies and setup development environment
	@echo "🚀 Setting up development environment..."
	pip install poetry
	poetry install --with dev
	poetry run pre-commit install || echo "⚠️  Pre-commit installation failed, but setup continues..."
	mkdir -p output logs
	@echo "✅ Setup complete! Run 'make run' to test extraction"

test: ## Run test suite with coverage
	@echo "🧪 Running tests..."
	poetry run pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-models: ## Test enhanced models and value objects
	@echo "🧪 Testing enhanced models..."
	poetry run pytest tests/unit/test_value_objects.py tests/unit/test_enhanced_models.py -v

test-enhancements: ## Test Step 1-3 improvements
	@echo "🧪 Testing model enhancements..."
	poetry run pytest -m "models or value_objects" -v

run: ## Run extraction example
	@echo "🔍 Running extraction example..."
	./scripts/run_demo.sh

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
	poetry run python scripts/verify_setup.py

verify-improvements: format lint test-step-improvements ## Verify all improvements
	@echo "✅ All improvements verified!"

verify-enhancements: format lint test-enhancements ## Verify model improvements
	@echo "✅ Model enhancements verified!"

fix: ## Fix common setup issues
	@echo "🔧 Fixing setup issues..."
	python scripts/fix_setup.py

install-hooks: ## Install pre-commit hooks
	@echo "🔧 Installing pre-commit hooks..."
	poetry run pre-commit install
