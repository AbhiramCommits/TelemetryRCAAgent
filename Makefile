.PHONY: setup data train eval eval-cluster test lint up down

setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"

data:
	.venv/bin/python scripts/gen_dataset.py --days 14 --faults 60 --seed 7

train:
	.venv/bin/python -m telemetry_rca.detect.train

eval:
	.venv/bin/python scripts/run_eval.py --backend local

eval-cluster:
	RCA_BACKEND=cluster .venv/bin/python scripts/run_eval.py --backend cluster

test:
	.venv/bin/pytest tests/

lint:
	.venv/bin/ruff check .

up:
	docker compose up -d

down:
	docker compose down
