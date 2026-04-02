.PHONY: help install dev test lint run docker seed migrate clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run development server with hot reload
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

run: ## Run production server
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

test: ## Run all tests
	pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

lint: ## Run linter
	ruff check src/ tests/

lint-fix: ## Run linter with auto-fix
	ruff check --fix src/ tests/

docker: ## Build and run with Docker Compose
	docker-compose up -d --build

docker-down: ## Stop Docker Compose
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f app

migrate: ## Run database migrations
	alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="description")
	alembic revision --autogenerate -m "$(msg)"

seed: ## Seed database with demo data
	python -m scripts.seed_data

clean: ## Clean up temporary files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; \
	rm -rf .pytest_cache htmlcov .coverage test.db 2>/dev/null; \
	echo "Cleaned!"

health: ## Check server health
	curl -s http://localhost:8000/health | python -m json.tool

metrics: ## View server metrics
	curl -s http://localhost:8000/metrics | python -m json.tool

docs: ## Open API documentation
	@echo "Visit http://localhost:8000/docs"
