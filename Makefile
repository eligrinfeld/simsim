SHELL := /bin/bash
.PHONY: setup dev up down run-pipeline test format
setup:
	python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
dev:
	source .venv/bin/activate && pip install -r requirements-quant.txt -r requirements-llm.txt
up:
	docker compose up --build -d
down:
	docker compose down
run-pipeline:
	source .venv/bin/activate && python -m src.core.pipeline --config configs/example_equity.yaml
test:
	source .venv/bin/activate && pytest
format:
	source .venv/bin/activate && python -m pip install ruff black && ruff check . --fix && black .
