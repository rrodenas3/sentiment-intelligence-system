# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository Purpose

This repo (`warpprojects`) holds **specs and planning documents** for a real-time sentiment intelligence system. The actual application code lives at `c:\Users\roden\projects\claude_code_cursor\agentcode`. The canonical runtime spec is `001R-spec-runtime-launch.md`; its YAML `runtime_plan` block is the single source of truth for launch commands and service configuration.

## Related Codebase Architecture

The application at `agentcode` is a multi-service real-time sentiment analysis pipeline built on **Spec 001**:

### Services (4-process local setup)
1. **Postgres 16 + Redis 7** — infrastructure via `docker compose up -d db redis`
2. **FastAPI API** (`src/mswia/api/main.py`) — REST + SSE on port 8000
3. **Sentiment worker** (`scripts/worker_sentiment.py`) — polls Redis `events:pending` queue, scores via VADER, writes to Postgres, publishes to Redis pub/sub
4. **Next.js dashboard** (`ui/`) — React 19 + Recharts + Tailwind v4 on port 3000, consumes SSE from `/stream/sentiment`

### Data Flow
```
Ingestion (YouTube/Reddit) → events:pending (Redis list)
  → worker_sentiment.py → sentiment_scores (Postgres) + sentiment:live (Redis pub/sub) + sentiment:recent (Redis list)
  → API reads from Redis (fast) with Postgres fallback
  → UI connects via SSE GET /stream/sentiment
```

### Package Structure (`src/mswia/`)
- `ingestion/` — source-specific fetchers (YouTube implemented; Reddit/reviews planned)
- `processing/` — `normalize_and_dedupe`: text cleanup + dedup by (source, item, author, text prefix)
- `modeling/` — `sentiment_service` / `score_text`: VADER-based scoring (fallback: TextBlob). Score in [-1,1], label thresholds at ±0.05
- `api/` — FastAPI app: `POST /analyze/text`, `GET /sentiment/summary`, `GET /stream/sentiment` (SSE), `POST /auth/login` (JWT)
- `schemas.py` — Pydantic contracts: `CanonicalEvent`, `SentimentOutput`, `SentimentLabel`, `SourceType`
- `db.py` — SQLAlchemy 2.0 ORM (Postgres): `events_raw`, `sentiment_scores`, `aggregates_windowed`, `users`
- `redis_client.py` — Redis keys: `events:pending`, `sentiment:live`, `sentiment:recent`
- `config.py` — env-driven config; data dirs, model version, thresholds
- `auth.py` — JWT (python-jose) + bcrypt password hashing

### Key Contracts
- Sentiment labels: `positive` (score > 0.05), `neutral` (−0.05 ≤ score ≤ 0.05), `negative` (score < −0.05)
- Model version string tracked in `SENTIMENT_MODEL_VERSION` env var (default: `vader-baseline-1.0`)
- `CanonicalEvent` is the universal ingestion schema; all sources must normalize to it
- DB schema defined in both `db/schema.sql` (canonical DDL) and `src/mswia/db.py` (ORM)

## Build & Run Commands

All backend commands run from `c:\Users\roden\projects\claude_code_cursor\agentcode` with `$env:PYTHONPATH = "src"`.

### Infrastructure
```powershell
docker compose up -d db redis
```

### API server
```powershell
$env:PYTHONPATH = "src"
python -m uvicorn mswia.api.main:app --host 127.0.0.1 --port 8000
```

### Sentiment worker
```powershell
$env:PYTHONPATH = "src"
python scripts/worker_sentiment.py
```

### YouTube ingestion worker
```powershell
$env:PYTHONPATH = "src"
python scripts/worker_ingest_youtube.py <video_id>
```

### UI (Next.js)
```powershell
# From agentcode/ui
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000"
npm run dev
```

### Lint (UI only)
```powershell
# From agentcode/ui
npm run lint
```

## Testing

Tests use **pytest** and live under `agentcode/tests/`. Run from the `agentcode` directory:

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests/ -v
```

Run a single test:
```powershell
$env:PYTHONPATH = "src"
python -m pytest tests/test_schemas.py::test_score_to_label_positive -v
```

Note: `test_api_smoke.py` uses `FastAPI.TestClient` and requires Postgres + Redis to be running for the health endpoint. The SSE stream test is skipped (blocks TestClient).

### Model Evaluation
```powershell
$env:PYTHONPATH = "src"
python scripts/evaluate_model.py
```
Expects a CSV at `data/validation/validation.csv` with columns `text,label`. Outputs macro F1 report to `reports/`.

## Environment Variables

Copy `.env.example` to `.env`. Key variables:
- `DATABASE_URL` — Postgres connection string (default: `postgresql+psycopg://postgres:postgres@localhost:5432/sentiment`)
- `REDIS_URL` — Redis connection string (default: `redis://localhost:6379/0`)
- `YOUTUBE_API_KEY` — required for YouTube ingestion workers
- `JWT_SECRET_KEY` / `JWT_ALGORITHM` — auth config
- `API_CORS_ORIGINS` — comma-separated allowed origins
- `SENTIMENT_MODEL_VERSION` — tracked in scoring output
