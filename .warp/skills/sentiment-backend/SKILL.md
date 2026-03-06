---
name: sentiment-backend
description: >
  Build and extend the FastAPI sentiment API and worker processes (src/mswia/ and scripts/ directories).
  Use this skill when working on back-end tasks for the real-time sentiment intelligence system,
  including: adding Reddit or Reviews ingestion, aggregates endpoints, auth enforcement, Alembic
  migrations, sentiment model improvements, worker robustness, bug fixes in API or workers.
  Triggers on any FastAPI, API endpoint, worker, ingestion, database, Redis, SQLAlchemy, Pydantic
  schema, or back-end related work in the sentiment project.
---

# Sentiment Back-End Skill

## Context

The back-end is a Python FastAPI application in `src/mswia/` with worker scripts in `scripts/`.
It uses Postgres 16 (SQLAlchemy 2.0), Redis 7 (queue + pub/sub + cache), and VADER for sentiment scoring.

Key modules:
- `src/mswia/api/main.py` - FastAPI app with all endpoints
- `src/mswia/schemas.py` - `CanonicalEvent`, `SentimentOutput`, `SentimentLabel`, `SourceType`
- `src/mswia/db.py` - ORM models: `EventRaw`, `SentimentScore`, `AggregateWindowed`, `User`
- `src/mswia/redis_client.py` - Redis keys: `events:pending`, `sentiment:live`, `sentiment:recent`
- `src/mswia/modeling/sentiment.py` - VADER scoring (TextBlob fallback)
- `src/mswia/ingestion/youtube.py` - YouTube comment fetcher
- `src/mswia/processing/normalize.py` - Text normalization + dedup
- `src/mswia/auth.py` - JWT + bcrypt auth
- `scripts/worker_sentiment.py` - Scoring worker (Redis -> Postgres)
- `scripts/worker_ingest_youtube.py` - YouTube ingestion worker

## Key Patterns

- All ingestion sources must produce `CanonicalEvent` (defined in `schemas.py`)
- Sentiment labels: positive (>0.05), neutral (-0.05 to 0.05), negative (<-0.05)
- Workers use `sys.path.insert` for `src/` but prefer `PYTHONPATH=src`
- DB schema lives in both `db/schema.sql` (canonical DDL) and `db.py` (ORM) - keep in sync
- Environment config via `os.environ.get()` with defaults in `config.py`

## Task Reference

Read [references/tasks.md](references/tasks.md) for the complete task list before starting work.

## Workflow

1. Read `references/tasks.md` to identify the relevant task
2. Set `$env:PYTHONPATH = "src"` before running any Python commands
3. Start infra with `docker compose up -d db redis`
4. Run the API: `python -m uvicorn mswia.api.main:app --host 127.0.0.1 --port 8000`
5. After changes, run tests: `python -m pytest tests/ -v`
6. New ingestion sources must implement an iterator yielding `CanonicalEvent`
7. New endpoints should follow existing patterns in `main.py` (Pydantic request/response models)
