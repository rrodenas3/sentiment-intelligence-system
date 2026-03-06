# Spec 001 - Execution Backlog

## Slice A - YouTube End-to-End

- [ ] Implement YouTube comment ingestion in `src/mswia/ingestion/youtube.py`.
- [ ] Add canonical event schema validator (event_id, source, source_item_id, author_id_hash, text, language, timestamp_utc, metadata).
- [ ] Build normalization + dedup pipeline in `src/mswia/processing/`.
- [ ] Implement baseline sentiment inference in `src/mswia/modeling/` (score in [-1,1], label by thresholds: negative < -0.05, positive > 0.05, else neutral).
- [ ] Extend API in `src/mswia/api/main.py`:
  - [ ] `POST /analyze/text`
  - [ ] `GET /sentiment/summary`
  - [ ] `GET /stream/sentiment` (SSE only)
- [ ] Add smoke tests for endpoints and pipeline.
- [ ] Log t_ingest / t_ready for P95 latency measurement.

## Slice B - Multi-Source Aggregation

- [ ] Add Reddit connector.
- [ ] Add reviews connector (CSV/API import).
- [ ] Unify source ingestion to canonical event stream.
- [ ] Add windowed aggregates (1m, 5m, 1h).

## Slice C - Dashboard + Alerts

- [ ] Create live dashboard (trend, source breakdown, top negative feed).
- [ ] Implement alert rule engine for negative spikes.
- [ ] Send alert payload to webhook.

## Slice D - Hardening

- [ ] Retries, timeouts, circuit-breaker for upstream APIs.
- [ ] Structured logs and tracing IDs (ingestion → inference → API).
- [ ] Model evaluation script and baseline metrics report (macro F1 ≥ 0.70 target).
- [ ] Operational runbook and deployment notes.

## Done Definition

- [ ] P95 ingestion-to-score latency (t_ready - t_ingest) ≤ 30s in test run.
- [ ] Baseline macro F1 ≥ 0.70 on validation set (stretch 0.75).
- [ ] Dashboard updates live without manual refresh (Slice C).
- [ ] Alert fires correctly on synthetic negative spike test.
