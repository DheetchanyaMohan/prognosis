# ML Experiment Diagnosis & Decision Support System — Backend

An agentic system that diagnoses ML training runs using deterministic
statistical tools, grounds its diagnosis in retrieved prior experiments and
curated ML knowledge, and produces a ranked, evidence-linked plan of next
experiments.

This repository currently contains the **project foundation only**: app
factory, configuration, logging, and database wiring. No business logic
(routes, tools, RAG, agent graph, training pipeline) has been implemented
yet — see the architecture doc for what comes next.

## Requirements

- Python 3.12+
- pip

## Setup

```bash
# 1. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install the project in editable mode with dev dependencies
pip install -e ".[dev]"

# 3. Copy the example environment file and adjust as needed
cp .env.example .env

# 4. Ensure the local SQLite data directory exists
mkdir -p data/db
```

Additional dependency groups (`agent`, `rag`, `ml`) are installed as later
phases are implemented, e.g. `pip install -e ".[agent,rag]"`.

## Running the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Confirm it started
correctly:

```bash
curl http://localhost:8000/health
# {"status": "ok", "environment": "development"}
```

Interactive API docs are served at `http://localhost:8000/docs`.

## Running with Docker

```bash
docker build -t ml-experiment-agent-backend .
docker run --rm -p 8000:8000 --env-file .env ml-experiment-agent-backend
```

## Running tests

```bash
pytest
```

## Project structure

```
backend/
├── app/
│   ├── main.py            # FastAPI application factory and entrypoint
│   ├── core/
│   │   ├── config.py       # Settings (pydantic-settings), env var handling
│   │   └── logging.py      # Logging configuration
│   ├── db/
│   │   ├── base.py         # SQLAlchemy declarative base
│   │   └── session.py      # Engine + session factory
│   ├── api/routes/         # HTTP route modules (empty — added later)
│   ├── agent/nodes/        # LangGraph state graph + nodes (empty — added later)
│   ├── tools/               # Deterministic analysis functions (empty — added later)
│   ├── rag/                 # Retrieval pipeline (empty — added later)
│   ├── models/               # SQLAlchemy ORM models (empty — added later)
│   └── eval/                  # Retrieval/agent evaluation harness (empty — added later)
├── tests/
├── data/db/                    # Local SQLite database file lives here
├── pyproject.toml
├── Dockerfile
├── .env.example
└── .gitignore
```

## Configuration

All configuration is environment-variable driven via `app/core/config.py`.
See `.env.example` for the full list of supported variables and their
defaults. Settings are cached per-process via `get_settings()` — import and
call that function rather than instantiating `Settings()` directly.
