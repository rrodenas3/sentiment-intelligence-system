---
name: sentiment-testing
description: >
  Write and maintain tests for the real-time sentiment intelligence system. Use this skill when
  working on testing tasks including: unit tests for modeling/processing/ingestion/auth modules,
  integration tests for API endpoints and the worker pipeline, SSE stream testing, test infrastructure
  setup (conftest.py, fixtures, Docker test services), model evaluation tests, or improving test
  coverage. Triggers on any pytest, test writing, test fixtures, mocking, test infrastructure,
  coverage, or QA related work in the sentiment project.
---

# Sentiment Testing Skill

## Context

Tests live in `agentcode/tests/` and use pytest. Run with `PYTHONPATH=src`.

Existing tests:
- `test_schemas.py` - Unit tests for `score_to_label` threshold logic
- `test_api_smoke.py` - Smoke tests via FastAPI `TestClient` for `/analyze/text` and `/sentiment/summary`
- SSE stream test is skipped (blocks TestClient)

Key commands:
- All tests: `python -m pytest tests/ -v`
- Single test: `python -m pytest tests/test_schemas.py::test_score_to_label_positive -v`

## Modules to Test

- `mswia.modeling.sentiment` - `score_text()`, `sentiment_service()` (VADER/TextBlob scoring)
- `mswia.processing.normalize` - `normalize_and_dedupe()` (text cleanup, dedup, timezone fix)
- `mswia.ingestion.youtube` - `fetch_youtube_comments()` (Google API, pagination, author hashing)
- `mswia.auth` - password hashing, JWT creation/decode, `authenticate_user`, `get_current_user`
- `mswia.api.main` - All endpoints including auth, analyze, summary, SSE stream
- `scripts/worker_sentiment.py` - `process_one()` (Redis -> score -> Postgres -> pub/sub)

## Test Patterns

- Use `FastAPI.TestClient` for synchronous endpoint tests
- Use `httpx.AsyncClient` for SSE stream tests (avoids blocking)
- Mock external services: Google API for YouTube, Redis pub/sub for SSE
- Integration tests need Postgres + Redis running (`docker compose up -d db redis`)
- Use pytest markers (`@pytest.mark.unit`, `@pytest.mark.integration`) to separate test tiers

## Task Reference

Read [references/tasks.md](references/tasks.md) for the complete task list before starting work.

## Workflow

1. Read `references/tasks.md` to identify the relevant test task
2. Set `$env:PYTHONPATH = "src"` before running tests
3. Ensure infra is running for integration tests: `docker compose up -d db redis`
4. Write tests following existing patterns in `test_schemas.py` and `test_api_smoke.py`
5. Run the full suite after adding tests: `python -m pytest tests/ -v`
6. Add shared fixtures to `tests/conftest.py` (create if it doesn't exist)
