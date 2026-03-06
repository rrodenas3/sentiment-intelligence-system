# Real-Time Sentiment Intelligence (Spec 001)

MVP: YouTube (Slice A) → Reddit + reviews (Slice B) → Dashboard + alerts (C) → Hardening (D).

## Specs

- [docs/specs/001-prd-realtime-sentiment.md](docs/specs/001-prd-realtime-sentiment.md) — PRD (frozen MVP API, Reddit, SSE, score/latency/F1).
- [docs/specs/001-tasks.md](docs/specs/001-tasks.md) — Backlog by slice.

## API (MVP only)

- `POST /analyze/text` — single text sentiment.
- `GET /sentiment/summary` — aggregate snapshot.
- `GET /stream/sentiment` — **SSE** live updates.

## Run

```bash
cd agentcode
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
set PYTHONPATH=src
uvicorn mswia.api.main:app --reload
```

- OpenAPI: http://127.0.0.1:8000/docs  
- SSE: http://127.0.0.1:8000/stream/sentiment  

Optional: set `YOUTUBE_API_KEY` for YouTube ingestion. Run the pipeline for a video:

```bash
$env:PYTHONPATH = "src"
python scripts/run_youtube_pipeline.py <video_id>
```

Example: `python scripts/run_youtube_pipeline.py dQw4w9WgXcQ`. Results go to `data/processed/` and the in-memory store (so `GET /sentiment/summary` and `GET /stream/sentiment` show them if the API is running).

## Layout

- `src/mswia/` — ingestion, processing, modeling, api
- `data/raw`, `data/processed` — raw events and sentiment outputs
