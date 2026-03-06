# Testing Tasks — Sentiment System

## Current State
Tests live in `agentcode/tests/` and use pytest. Current coverage:
- `test_schemas.py` — unit tests for `score_to_label` threshold logic (positive, negative, neutral boundaries)
- `test_api_smoke.py` — smoke tests using FastAPI `TestClient` for `POST /analyze/text` and `GET /sentiment/summary`
- SSE stream test (`test_stream_sentiment_sse`) is skipped because it blocks the TestClient

Run all tests: `PYTHONPATH=src python -m pytest tests/ -v`

## Tasks to Complete

### Unit Tests — Modeling
- Test `score_text()` returns valid `SentimentOutput` with correct label/score/confidence ranges
- Test `sentiment_service()` correctly maps a `CanonicalEvent` to `SentimentOutput`
- Test that the VADER fallback to TextBlob works when `vaderSentiment` is not importable
- Test edge cases: empty string, very long text (50k chars), non-English text, emoji-only text

### Unit Tests — Processing
- Test `normalize_and_dedupe` strips whitespace and collapses multiple spaces
- Test deduplication: identical events by (source, item, author, text prefix) are skipped
- Test that events with empty text after normalization are dropped
- Test that naive timestamps get UTC timezone attached

### Unit Tests — Ingestion
- Test `fetch_youtube_comments` with mocked Google API responses
- Test author hashing produces consistent 32-char hex strings
- Test handling of missing fields (no `textDisplay`, no `publishedAt`, no `authorDisplayName`)
- Test pagination via `nextPageToken`

### Unit Tests — Auth
- Test `get_password_hash` and `verify_password` round-trip correctly
- Test `create_access_token` produces a valid JWT decodable with the same secret
- Test `authenticate_user` returns `None` for wrong password and wrong email
- Test `get_current_user` raises 401 for expired/invalid tokens

### Integration Tests — API Endpoints
- Test `POST /auth/login` with valid and invalid credentials (requires test DB with a seeded user)
- Test `GET /sentiment/summary` returns correct `by_label` counts after inserting known scores
- Test `POST /analyze/text` with boundary inputs: min_length=1, max_length=50,000, empty string (expect 422)
- Test the `source` query param on `/sentiment/summary` once filtering is implemented

### Integration Tests — Worker Pipeline
- Test the full flow: push a `CanonicalEvent` JSON to `events:pending` → run `process_one()` → verify `sentiment_scores` row in Postgres and `sentiment:recent` entry in Redis
- Test that `sentiment:live` pub/sub message is published with correct JSON shape
- Requires a test Postgres + Redis instance (use Docker or test fixtures)

### SSE Stream Testing
- Unblock the SSE test: use `httpx.AsyncClient` with a timeout or background task to publish a test event and verify the stream yields it
- Alternatively, test `_redis_sse_stream()` generator directly with a mocked Redis pub/sub

### Test Infrastructure
- Add a `conftest.py` with shared fixtures: test DB session, test Redis client, seeded test user
- Add a `docker-compose.test.yml` or use testcontainers for isolated Postgres + Redis
- Add pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration` so unit tests can run without infra

### Model Evaluation Tests
- Test `scripts/evaluate_model.py` with a small fixture CSV
- Verify the output JSON report has expected keys: `labels`, `per_label_f1`, `macro_f1`, `support`
- Test that missing validation CSV gracefully skips (already handled, but should be tested)
