# Makefile for Learning Recommendation System
# Cross-platform commands (use with Make on Linux/Mac, or GNU Make on Windows)

.PHONY: help install dev-install test lint format clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make test          - Run tests with coverage"
	@echo "  make lint          - Run linters (flake8, mypy)"
	@echo "  make format        - Format code (black, isort)"
	@echo "  make docker-up     - Start Docker Compose services"
	@echo "  make docker-down   - Stop Docker Compose services"
	@echo "  make init-db       - Initialize database"
	@echo "  make sample-data   - Generate sample data"
	@echo "  make run-api       - Run API server"
	@echo "  make clean         - Clean cache files"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

lint:
	flake8 src/ scripts/ tests/ --max-line-length=100 --ignore=E203,W503
	mypy src/ --ignore-missing-imports

format:
	black src/ scripts/ tests/
	isort src/ scripts/ tests/

docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10

docker-down:
	docker-compose down

init-db:
	python scripts/init_db.py

sample-data:
	python scripts/sample_data_generator.py --users 1000 --items 500 --events 10000

run-api:
	uvicorn src.api.main:app --reload --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -f .coverage

# All-in-one setup for first-time users
setup: docker-up init-db sample-data
	@echo "✅ Setup complete! Run 'make run-api' to start the server."
