# GEMINI.md — Sentiment Intelligence System (Spec & Planning)

This repository (`warpprojects`) is the **Specification and Planning Repository** for the real-time sentiment intelligence system. It serves as the "brain" for the project, defining architecture, runtime plans, and task roadmaps.

> **Note:** The actual application source code is located at:  
> `c:\Users\roden\projects\claude_code_cursor\agentcode`

## Project Overview
The system is a multi-service real-time sentiment analysis pipeline that ingests data from sources like YouTube and Reddit, processes it using VADER-based sentiment scoring, and streams live updates to a Next.js dashboard via Server-Sent Events (SSE).

### Architecture & Tech Stack
- **Backend:** FastAPI (Python 3.11+), SQLAlchemy 2.0 (Postgres), Redis (Queuing/Pub-Sub).
- **Processing:** VADER (primary), TextBlob (fallback).
- **Frontend:** Next.js (React 19), Tailwind CSS v4, Recharts.
- **Infrastructure:** Docker (Postgres 16, Redis 7).

## Building and Running
All commands for the application should be executed from the code directory:  
`c:\Users\roden\projects\claude_code_cursor\agentcode`

### Infrastructure
```powershell
docker compose up -d db redis
```

### Backend (API & Workers)
Ensure `$env:PYTHONPATH = "src"` is set before running any Python scripts.
- **API:** `python -m uvicorn mswia.api.main:app --host 127.0.0.1 --port 8000`
- **Sentiment Worker:** `python scripts/worker_sentiment.py`
- **YouTube Ingestion:** `python scripts/worker_ingest_youtube.py <video_id>`

### Frontend (Dashboard)
From `agentcode/ui`:
```powershell
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000"
npm run dev
```

### Testing
From the root of the code directory:
```powershell
$env:PYTHONPATH = "src"
python -m pytest tests/ -v
```

## Key Files (This Repo)
- **`001R-spec-runtime-launch.md`**: The **Single Source of Truth** for the local runtime environment. Contains a machine-readable YAML `runtime_plan`.
- **`AGENTS.md`**: Comprehensive architectural guidance, data flow diagrams, and command reference for AI agents.
- **`plans/`**:
    - `backend-tasks.md`: Roadmap for FastAPI, workers, and DB migrations.
    - `frontend-tasks.md`: UI features, SSE integration, and auth screens.
    - `testing-tasks.md`: Unit, integration, and model evaluation plans.

## Development Conventions
- **Canonical Schema**: All data ingestion must normalize to the `CanonicalEvent` schema (`src/mswia/schemas.py`).
- **Sentiment Labels**: `positive` (> 0.05), `neutral` (±0.05), `negative` (< -0.05).
- **Environment Variables**: Use `.env` (copy from `.env.example`). Key vars include `DATABASE_URL`, `REDIS_URL`, and `SENTIMENT_MODEL_VERSION`.
- **Model Evaluation**: Use `scripts/evaluate_model.py` to benchmark changes against `data/validation/validation.csv`.
- **Migrations**: New DB changes should be managed via Alembic (planned).
