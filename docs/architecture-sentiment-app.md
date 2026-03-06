# Sentiment Intelligence App – How It Works

This document describes how the end-to-end sentiment analysis application functions: data flow, components, and key design choices.

---

## 1. High-Level Flow

```
External sources (YouTube, etc.)
        ↓
Ingestion workers (scripts or legacy pipeline)
        ↓
PostgreSQL (events_raw) + Redis queue (events:pending)
        ↓
Sentiment worker (pops queue → VADER/TextBlob → score)
        ↓
PostgreSQL (sentiment_scores) + Redis (sentiment:live + sentiment:recent)
        ↓
FastAPI (REST + SSE)
        ↓
Next.js dashboard (summary + live stream)
```

- **Two paths into the system:** (1) **Async path:** ingestion worker → Postgres + Redis queue → sentiment worker → Postgres + Redis pub/sub → API/dashboard. (2) **Legacy path:** `run_pipeline_youtube()` in-process: fetch → normalize → score → write only to `data/processed/` (no Redis/DB, no live stream).
- **API** is stateless: it reads from Postgres and Redis and forwards the Redis live channel as SSE.

---

## 2. Data Contracts (Spec 001)

All sources normalize to a single shape.

**Canonical event (input)**  
- `event_id`, `source` (youtube | reddit | reviews), `source_item_id`, `author_id_hash`, `text`, `language`, `timestamp_utc`, `metadata`.  
- Defined in `src/mswia/schemas.py` as `CanonicalEvent`.

**Sentiment output**  
- `event_id`, `label` (positive | neutral | negative), `score` in **[-1, 1]**, `confidence`, `model_version`, `scored_at_utc`.  
- Label rules: `score < -0.05` → negative; `score > 0.05` → positive; else neutral.  
- Defined as `SentimentOutput` in `schemas.py`; thresholds in `config.py` (`SCORE_*_THRESHOLD`).

---

## 3. Component Breakdown

### 3.1 Ingestion

- **YouTube** (`src/mswia/ingestion/youtube.py`): Uses YouTube Data API v3 to fetch comment threads for a video, maps each comment to `CanonicalEvent` (hashed author id, `event_id` like `yt_{video_id}_{comment_id}`).
- **Normalization** (`src/mswia/processing/normalize.py`): Trims and collapses whitespace; deduplicates by `(source, source_item_id, author_id_hash, text)` so the same content from the same author is only processed once.

**How events enter the system**

- **Worker path:** `scripts/worker_ingest_youtube.py <video_id>` pulls comments via `fetch_youtube_comments`, does **not** run the normalizer (YouTube stream is assumed already deduped by comment id). Each event is inserted into `events_raw` and pushed to Redis list `events:pending` (JSON).
- **Legacy path:** `run_pipeline_youtube(video_id)` (in `api/main.py`) fetches comments, runs `normalize_and_dedupe`, scores in-process, and writes one JSON file per event under `data/processed/`. It does not use Postgres or Redis, so the dashboard/stream do not see these results unless you also run the sentiment worker and feed the queue some other way.

### 3.2 Queue and Sentiment Worker

- **Redis list** `events:pending`: stores serialized `CanonicalEvent` JSON. Producers: ingestion worker(s). Consumer: sentiment worker.
- **Sentiment worker** (`scripts/worker_sentiment.py`): Loop: `LPOP` one message from `events:pending`; deserialize to `CanonicalEvent`; call `sentiment_service(event)` (VADER or TextBlob); insert into `sentiment_scores`; publish JSON to channel `sentiment:live`; push same JSON to list `sentiment:recent` and trim to last 1000. If queue is empty, sleeps 0.2s.

**Sentiment model** (`src/mswia/modeling/sentiment.py`): Uses VADER if available, else TextBlob. Returns a compound/polarity score in [-1, 1] and a confidence-like value; `score_to_label()` applies the Spec 001 thresholds to get `positive` / `neutral` / `negative`.

### 3.3 Persistence

- **PostgreSQL** (schema in `db/schema.sql`, ORM in `src/mswia/db.py`):
  - `events_raw`: one row per ingested canonical event.
  - `sentiment_scores`: one row per scored event (event_id, label, score, confidence, model_version, scored_at_utc). FK to `events_raw(event_id)`.
  - `aggregates_windowed`: optional pre-aggregated counts by time window and source (not yet populated by code).
  - `users`: for JWT auth (email, hashed_password, role).

- **Redis** (`src/mswia/redis_client.py`):
  - `events:pending`: queue of events to score.
  - `sentiment:live`: pub/sub channel; each message is a `SentimentOutput` JSON (for SSE).
  - `sentiment:recent`: list of recent `SentimentOutput` JSONs (for fast summary).

### 3.4 API (FastAPI)

- **`GET /`** → redirects to **`/docs`** (Swagger).
- **`GET /health`** → returns `status` (ok | degraded | down), plus booleans for DB and Redis connectivity and app version.
- **`POST /analyze/text`** → body `{ "text": "..." }`. Runs the sentiment model in-process and returns `label`, `score`, `confidence`, `model_version`. Does not write to Postgres or Redis.
- **`POST /auth/login`** → body `{ "email", "password" }`. Validates against `users` table, returns JWT `access_token`.
- **`GET /sentiment/summary`** → reads up to `limit` items from Redis list `sentiment:recent`, parses JSON into `SentimentOutput`; if Redis is empty, falls back to Postgres `sentiment_scores` (latest by `scored_at_utc`). Returns `count`, `by_label` (positive/neutral/negative), and `recent` (last 20).
- **`GET /stream/sentiment`** → SSE stream. Subscribes to Redis channel `sentiment:live` and forwards each message as a Server-Sent Event (`data: <json>\n\n`). Blocks until the client disconnects; no events are sent until the sentiment worker publishes.

CORS is driven by `API_CORS_ORIGINS` (default `http://localhost:3000`). Prometheus metrics are exposed via `prometheus_fastapi_instrumentator` (e.g. `/metrics`).

### 3.5 Dashboard (Next.js)

- **`ui/src/app/page.tsx`**: Single dashboard page.
  - Reads `NEXT_PUBLIC_API_BASE_URL` (default `http://127.0.0.1:8000`).
  - On load: fetches `GET /sentiment/summary` for initial counts and opens `EventSource(<apiBase>/stream/sentiment)` for live updates.
  - On each SSE message: appends to a local list of recent events (max 100), updates `by_label` counts and a time-series of scores for the chart.
  - Renders: connection status (live vs connecting), total events and positive/neutral/negative percentages, an area chart of score over time, and a feed of latest events with label and score.

---

## 4. Configuration and Run Requirements

- **Environment** (see `.env.example`): `DATABASE_URL`, `REDIS_URL`, `YOUTUBE_API_KEY`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `API_CORS_ORIGINS`, `SENTIMENT_MODEL_VERSION`, optional `DATA_RAW_DIR` / `DATA_PROCESSED_DIR`.
- **For the full async path:** Postgres and Redis must be up; tables created (e.g. from `db/schema.sql` or `mswia.db.init_db()`). Start API (`uvicorn mswia.api.main:app`), sentiment worker (`python scripts/worker_sentiment.py`), and optionally ingestion worker (`python scripts/worker_ingest_youtube.py <video_id>`). Dashboard: `cd ui && npm run dev` with `NEXT_PUBLIC_API_BASE_URL` pointing at the API.
- **Legacy path:** Only needs `YOUTUBE_API_KEY`. Call `run_pipeline_youtube(video_id)` (e.g. via `scripts/run_youtube_pipeline.py`); results only on disk under `data/processed/`, not in API or dashboard.

---

## 5. Bug Fix Applied

- **`run_pipeline_youtube`** previously referenced removed in-memory lists `_sentiment_history` and `_sse_results`, and `os` was used without being imported. It is now corrected to: (1) add `import os` for CORS config, and (2) simplify the legacy pipeline to only write results to `data/processed/` (no in-memory state), so it runs correctly when Redis/Postgres are not used.

---

## 6. Summary

| Layer           | Role |
|-----------------|------|
| **Sources**     | YouTube (and future Reddit/reviews) produce raw text. |
| **Ingestion**   | Worker or legacy script turns raw data into `CanonicalEvent` and, in the worker path, stores in Postgres and pushes to Redis queue. |
| **Queue**       | Redis `events:pending` decouples ingestion from scoring. |
| **Sentiment**   | Worker pops events, runs VADER/TextBlob, writes to Postgres and publishes to Redis `sentiment:live` and `sentiment:recent`. |
| **API**         | Serves summary from Redis/Postgres and streams live events from Redis pub/sub over SSE; also provides on-demand `/analyze/text` and `/health`. |
| **Dashboard**   | Next.js app that shows summary and live stream using configurable API base URL. |

The app functions as an end-to-end sentiment intelligence pipeline: normalized events are stored, scored asynchronously via a queue, persisted, and exposed to the UI via REST and SSE, with an optional legacy path that only writes to disk.
