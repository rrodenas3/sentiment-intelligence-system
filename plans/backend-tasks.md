# Back-End Tasks — FastAPI API & Workers

## Current State
The back-end (`src/mswia/`) provides:
- FastAPI app with `POST /analyze/text`, `GET /sentiment/summary`, `GET /stream/sentiment` (SSE), `POST /auth/login`
- VADER-based sentiment scoring with TextBlob fallback
- YouTube ingestion via Google API client
- Redis for queuing (`events:pending`), pub/sub (`sentiment:live`), and caching (`sentiment:recent`)
- Postgres via SQLAlchemy 2.0 ORM with tables: `events_raw`, `sentiment_scores`, `aggregates_windowed`, `users`
- JWT authentication (python-jose + bcrypt) with `get_current_user` dependency
- Prometheus metrics via `prometheus-fastapi-instrumentator`

## Tasks to Complete

### Reddit Ingestion (Slice B)
- Implement `src/mswia/ingestion/reddit.py` producing `CanonicalEvent` with `source=SourceType.REDDIT`
- Add a `scripts/worker_ingest_reddit.py` mirroring the YouTube ingestion worker pattern
- Handle Reddit API auth (OAuth2 client credentials) and rate limiting

### Reviews Ingestion (Slice B)
- Implement `src/mswia/ingestion/reviews.py` for product review sources
- Define the input format (CSV import, API, or scrape) and normalize to `CanonicalEvent`

### Aggregates API Endpoint
- Add `GET /sentiment/aggregates` to expose the `aggregates_windowed` table
- Accept query params: `window` (1m, 5m, 1h), `source`, `start`/`end` timestamps
- Add a scheduled job or worker to populate `aggregates_windowed` from `sentiment_scores`

### Protect Endpoints with Auth
- Apply the `get_current_user` dependency to `/sentiment/summary`, `/stream/sentiment`, and `/analyze/text`
- Add a `POST /auth/register` endpoint for user creation
- Add role-based access (the `users.role` column exists but is unused)

### Alembic Migrations
- Initialize Alembic and generate an initial migration from the current `db/schema.sql` / ORM models
- The codebase currently uses `init_db()` (create_all) for local dev — migrate to Alembic for all environments
- Ensure the ORM models in `db.py` and the DDL in `db/schema.sql` stay in sync

### Sentiment Model Improvements (Slice D)
- Add support for swapping the sentiment engine (VADER → transformer-based) via config
- Track model version in `SENTIMENT_MODEL_VERSION` so results are attributable
- Use the `scripts/evaluate_model.py` flow to compare macro F1 before/after model changes
- Store evaluation reports in `reports/` with the model version in the filename

### Worker Robustness (Slice D)
- Add error handling in `worker_sentiment.py` so a single bad event doesn't crash the loop
- Add dead-letter queue for events that fail scoring repeatedly
- Add graceful shutdown (signal handling) to both workers
- Add health/liveness probes for workers (e.g., write a heartbeat key to Redis)

### `source` Filter on Summary
- The `GET /sentiment/summary` endpoint accepts a `source` param but doesn't filter by it — implement the actual filtering logic in both the Redis and Postgres code paths

### Fix `get_db` in auth.py
- `auth.py:get_db()` has a no-op `finally` block (`...`) — it should call `db.close()` or be converted to a proper generator dependency
