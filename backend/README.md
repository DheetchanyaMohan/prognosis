# ML Experiment Diagnosis & Decision Support System — Backend

An agentic system that diagnoses ML training runs using deterministic
statistical tools, grounds its diagnosis in retrieved prior experiments and
curated ML knowledge, and produces a ranked, evidence-linked plan of next
experiments — with the entire reasoning process exposed through a single
REST endpoint.

## How the frontend invokes the LangGraph agent

The complete LangGraph diagnosis workflow (router → retrieve context →
analyze metrics → generate hypotheses → plan experiments → self-check →
finalize) is exposed as one endpoint:

POST /api/v1/runs/{run_id}/diagnose


A frontend user selects a run and clicks "Diagnose"; the frontend sends a
`POST` to this endpoint (an empty body runs the default diagnostic
question for that run, or a JSON body `{"query": "..."}` asks something
custom, e.g. naming a second run to compare against) and receives back a
single `DiagnosisResponse` containing everything the agent produced: the
router's classification, every chunk of retrieved evidence, the
deterministic diagnostics, ranked hypotheses (each with its own supporting
evidence), ranked recommendations (each with its own provenance **and an
`is_grounded` flag** — `self_check`'s own verified verdict on whether that
recommendation's evidence actually holds up, not asserted by the LLM), and
the full step-by-step execution trace. See `FRONTEND_INTEGRATION.md` for the
complete request/response contract, TypeScript interfaces, and example
payloads.

There is no separate "start" and "poll for result" flow — this is a
single request/response call. It invokes a real LLM and is meaningfully
slower than every other endpoint in this API (typically several seconds
to low tens-of-seconds); the frontend should design around an explicit
long-running loading state, not a brief spinner.

**Comparing two runs does not require the agent.** When the frontend
already knows which two runs to compare (e.g. two selected rows in a
table), `GET /api/v1/runs/{run_a_id}/compare/{run_b_id}` returns the same
deterministic config-diff and diagnostics comparison the agent computes
internally for a `compare_runs`-classified diagnosis query — but as a
fast, synchronous, LLM-free call. Reserve the diagnose endpoint's
comparison outcome for when comparison should be driven by a
natural-language question instead of a direct UI selection.

**Architecture behind this endpoint:**

FastAPI route (app/api/routes/diagnosis.py)
│ translates exceptions into HTTP status codes; no orchestration logic
▼
DiagnosisService (app/services/diagnosis_service.py)
│ the one implementation of "run the workflow and shape its output"
▼
LangGraph workflow (app/agent/graph.py)
│
▼
DiagnosisResponse (app/services/schemas.py)


`scripts/validate_agent.py` calls the exact same `DiagnosisService`
function (`run_diagnosis`) as the API route — there is only one
implementation of the diagnosis workflow in this codebase, invoked either
over HTTP or directly from a script.

This repository also exposes four read-only endpoints over experiment
and run metadata (`GET /api/v1/experiments`, `GET
/api/v1/experiments/{id}`, `GET /api/v1/runs/{id}`, `GET
/api/v1/runs/{run_a_id}/compare/{run_b_id}`) and a health check
(`GET /health`) — see `FRONTEND_INTEGRATION.md` for their full contract
too.

## Requirements

- Python 3.12+
- pip

## Setup

```bash
# 1. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install the project in editable mode with dev dependencies
pip install -e ".[dev,agent,rag,ml]"

# 3. Copy the example environment file and adjust as needed
cp .env.example .env
# set GEMINI_API_KEY (or ANTHROPIC_API_KEY + LLM_PROVIDER=anthropic)
# for the diagnosis endpoint to actually call an LLM

# 4. Ensure the local SQLite data directory exists
mkdir -p data/db

# 5. Run migrations
alembic upgrade head

# 6. Populate the knowledge base and any completed runs' summaries into Chroma
python scripts/ingest.py
```

## Running the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Confirm it started
correctly:

```bash
curl http://localhost:8000/health
```

Interactive API docs (including the diagnosis endpoint's full request/
response schema) are served at `http://localhost:8000/docs`.

Try the diagnosis endpoint directly:

```bash
curl -X POST http://localhost:8000/api/v1/runs/run_005/diagnose
```

Compare two runs deterministically, without invoking the agent:

```bash
curl http://localhost:8000/api/v1/runs/run_005/compare/run_004
```

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

backend/
├── app/
│ ├── main.py # FastAPI application factory and entrypoint
│ ├── core/ # Settings, logging
│ ├── db/ # SQLAlchemy engine/session, Alembic migrations
│ ├── models/ # SQLAlchemy ORM models
│ ├── config/ # RunConfig schema + loader/validator
│ ├── data_generation/ # Training pipeline (CIFAR-10 subset runs)
│ ├── tools/ # Deterministic analysis + agent tool layer
│ ├── rag/ # Retrieval pipeline (ingestion, embeddings, retriever)
│ ├── llm/ # Provider-independent LLM client (Anthropic, Gemini)
│ ├── agent/ # LangGraph state graph + nodes
│ ├── services/ # DiagnosisService — the one place that
│ │ invokes the LangGraph workflow
│ ├── api/routes/ # HTTP route modules (health, experiments,
│ │ runs, diagnosis)
│ └── eval/ # Retrieval evaluation harness
├── scripts/
│ ├── generate_experiment_plan.py # Generates run configs + scaffolding
│ ├── run_experiments.py # Executes training runs
│ ├── ingest.py # Populates the Chroma knowledge base
│ └── validate_agent.py # CLI wrapper around DiagnosisService
├── tests/
├── data/ # SQLite DB, experiment runs, Chroma store
├── FRONTEND_INTEGRATION.md # Full API contract for frontend development
├── pyproject.toml
├── Dockerfile
├── .env.example
└── .gitignore


## Configuration

All configuration is environment-variable driven via `app/core/config.py`.
See `.env.example` for the full list of supported variables and their
defaults. Settings are cached per-process via `get_settings()` — import and
call that function rather than instantiating `Settings()` directly.