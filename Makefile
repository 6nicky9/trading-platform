# Makefile for Trading Platform

.PHONY: help build up down logs test clean install

help:
	@echo "Trading Platform Commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make build    - Build Docker images"
	@echo "  make up       - Start services"
	@echo "  make down     - Stop services"
	@echo "  make logs     - Show logs"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up"

install:
	pip install -r requirements.txt

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	pytest tests/ -v

clean:
	docker-compose down -v
	docker system prune -f

migrate:
	alembic upgrade head

shell:
	docker-compose exec trading-app python -m IPython
