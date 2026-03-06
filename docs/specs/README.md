# Specs (SDD)

- **001-prd-realtime-sentiment.md** — PRD with frozen MVP: 3 APIs only (`POST /analyze/text`, `GET /sentiment/summary`, `GET /stream/sentiment` SSE), Reddit as second source, score [-1,1] + label thresholds, P95 latency definition, baseline F1 ≥ 0.70 (stretch 0.75).
- **001-tasks.md** — Execution backlog by slice (A–D).

Implementation lives under `src/mswia/`. Run and test from repo root.
