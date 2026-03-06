## Spec 001R - Runtime & Launch Plan (Reusable)

### Document Control

- Spec ID: `001R`
- Related PRD: `001-prd-realtime-sentiment.md`
- Version: `1.0`
- Date: `2026-03-03`
- Purpose: Describe how to run the **real-time sentiment system** locally in a way that other tools/agents can reuse programmatically.

---

### High-Level Overview

- **Goal**: Run the full end-to-end pipeline locally:
  - Postgres + Redis
  - FastAPI backend (API + SSE)
  - Sentiment worker
  - Next.js dashboard
- **Target OS**: Windows 10+ (PowerShell), with Docker and Python 3.11+.

---

### Machine-Readable Runtime Plan (YAML)

The following YAML block is designed to be consumed by other tools/agents to reproduce the local runtime environment.

```yaml
runtime_plan:
  id: sentiment-system-local
  version: 1.0
  prerequisites:
    - docker
    - docker-compose
    - python>=3.11
    - node>=18
  env_files:
    - .env
  services:
    db:
      type: postgres
      docker_compose_service: db
      port: 5432
      healthcheck:
        type: tcp
        host: localhost
        port: 5432
    redis:
      type: redis
      docker_compose_service: redis
      port: 6379
      healthcheck:
        type: tcp
        host: localhost
        port: 6379
    api:
      type: fastapi
      module: mswia.api.main:app
      host: 127.0.0.1
      port: 8000
      cwd: c:\\Users\\roden\\projects\\claude_code_cursor\\agentcode
      env:
        PYTHONPATH: src
        DATABASE_URL: postgresql+psycopg://postgres:postgres@localhost:5432/sentiment
        REDIS_URL: redis://localhost:6379/0
        API_CORS_ORIGINS: http://localhost:3000
      start_command: python -m uvicorn mswia.api.main:app --host 127.0.0.1 --port 8000
      healthcheck:
        type: http
        url: http://127.0.0.1:8000/health
        expected_status: 200
    worker_sentiment:
      type: python-script
      cwd: c:\\Users\\roden\\projects\\claude_code_cursor\\agentcode
      env:
        PYTHONPATH: src
        DATABASE_URL: postgresql+psycopg://postgres:postgres@localhost:5432/sentiment
        REDIS_URL: redis://localhost:6379/0
      start_command: python scripts/worker_sentiment.py
    ui:
      type: nextjs
      cwd: c:\\Users\\roden\\projects\\claude_code_cursor\\agentcode\\ui
      env:
        NEXT_PUBLIC_API_BASE_URL: http://127.0.0.1:8000
      start_command: npm run dev
      primary_port: 3000
      notes:
        - If port 3000 is busy, Next.js may choose another port automatically (e.g. 3001).
  launch_sequence:
    - step: "Start infra (db, redis)"
      command: docker compose up -d db redis
      cwd: c:\\Users\\roden\\projects\\claude_code_cursor\\agentcode
    - step: "Start API"
      service: api
    - step: "Start sentiment worker"
      service: worker_sentiment
    - step: "Start UI"
      service: ui
  smoke_tests:
    - name: api-health
      type: http
      method: GET
      url: http://127.0.0.1:8000/health
      expected_status: 200
    - name: analyze-positive-text
      type: http
      method: POST
      url: http://127.0.0.1:8000/analyze/text
      expected_status: 200
      body:
        text: "I love this product!"
    - name: sentiment-summary
      type: http
      method: GET
      url: http://127.0.0.1:8000/sentiment/summary
      expected_status: 200
```

---

### Human-Friendly Runbook (Local)

**Prereqs**

- Docker Desktop running.
- Python 3.11+ with `requirements.txt` installed.
- Node 18+ with `npm install` already run in `ui/`.
- `.env` created from `.env.example` (DB, Redis, API keys, JWT secret, etc.).

**1. Start Postgres and Redis**

From the repo root:

```powershell
cd c:\Users\roden\projects\claude_code_cursor\agentcode
docker compose up -d db redis
```

**2. Start the API**

```powershell
cd c:\Users\roden\projects\claude_code_cursor\agentcode
$env:PYTHONPATH = "src"
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/sentiment"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:API_CORS_ORIGINS = "http://localhost:3000"
python -m uvicorn mswia.api.main:app --host 127.0.0.1 --port 8000
```

**3. Start the sentiment worker**

In another terminal:

```powershell
cd c:\Users\roden\projects\claude_code_cursor\agentcode
$env:PYTHONPATH = "src"
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/sentiment"
$env:REDIS_URL = "redis://localhost:6379/0"
python scripts/worker_sentiment.py
```

**4. Start the UI**

In another terminal:

```powershell
cd c:\Users\roden\projects\claude_code_cursor\agentcode\ui
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000"
npm run dev
```

If port `3000` is already in use, Next.js may move to `3001`; in that case, open `http://localhost:3001`.

**5. Smoke test**

- Open `http://127.0.0.1:8000/health` – should return status `ok`.
- Open `http://127.0.0.1:8000/docs` – FastAPI docs.
- Call `POST /analyze/text` with a positive and negative sentence.
- Open the dashboard at `http://localhost:3000` (or `3001`) to see stats and live SSE stream.

---

### Notes for Other Tools/Agents

- Prefer using the **YAML `runtime_plan` block** for automation, and the human runbook as reference.
- If ports or paths need to change, update the YAML and treat it as the single source of truth for launch commands.

