# Spec 001 - Real-Time Multi-Source Sentiment Intelligence (PRD)

## Document Control

- Spec ID: `001`
- Version: `1.0`
- Date: `2026-03-03`
- Status: `Approved`
- Owners: Product, Data Engineering, ML Engineering

## Problem Statement

Teams need near real-time visibility into brand and product sentiment across multiple channels (YouTube, social media, reviews). Current workflows are fragmented, delayed, and cannot trigger timely action.

## MVP Goal

Deliver a production-lean app that ingests text streams from multiple sources, computes sentiment continuously, and exposes live trends with basic alerting.

## Target Users

- Product managers
- Marketing and community teams
- Customer support leads

## In Scope (MVP)

- YouTube comments ingestion (first source)
- Second source: **Reddit** (locked for Slice B)
- One review source (file/API)
- Unified text event schema and normalization pipeline
- Real-time sentiment scoring (`positive`, `neutral`, `negative`) with confidence; score in **[-1, 1]** with defined label thresholds
- **MVP API only:** `POST /analyze/text`, `GET /sentiment/summary`, `GET /stream/sentiment` (SSE)
- Live dashboard for trend and source breakdown (Slice C)
- Threshold-based alerting webhook

## Out of Scope (MVP)

- `POST /ingest`, `GET /health` (not in MVP API surface)
- Full multilingual sentiment parity
- Topic forecasting
- Complex causality inference
- Enterprise-grade role-based access control
- WebSocket (MVP stream protocol is **SSE only**)

## Success Metrics

- **P95 ingestion-to-score latency ≤ 30s** (see Measurement below).
- Pipeline availability: ≥ 99% (MVP target in controlled environment).
- **Baseline** sentiment model macro F1 on validation set: **≥ 0.70** (stretch: 0.75 with upgraded model/dataset).
- Alert precision for severe negative spikes: ≥ 0.70.

### Measurement: P95 Latency

- **t_ingest**: timestamp when an event is accepted into the canonical stream (after normalization/dedupe) and written to `data/raw` (or equivalent).
- **t_ready**: timestamp when the corresponding sentiment result is written to `data/processed` and first emitted on the SSE stream.
- **Latency** per event = `t_ready - t_ingest`. **P95** = 95th percentile over a 1-hour rolling window.

## Functional Requirements

1. System must ingest events from at least 3 source classes: video comments (YouTube), social (Reddit), reviews.
2. System must normalize all incoming events into a single canonical schema.
3. System must score sentiment per event and aggregate by configurable windows (`1m`, `5m`, `1h`).
4. **API must expose (MVP only):**
   - `POST /analyze/text` for single text inference
   - `GET /sentiment/summary` for aggregate snapshots
   - `GET /stream/sentiment` (**SSE**) for live updates
5. Dashboard must show: global sentiment trend, source-level breakdown, top recent negative items (Slice C).
6. Alert engine must trigger when rolling negative ratio exceeds threshold.

## Non-Functional Requirements

- Idempotent ingestion and deduplication
- API key and secrets via environment variables
- Structured logs for pipeline traceability
- Retry and backoff for source API failures
- Basic PII minimization (store hashed author IDs only)

## Canonical Event Contract (MVP)

```json
{
  "event_id": "string",
  "source": "youtube|reddit|reviews",
  "source_item_id": "string",
  "author_id_hash": "string",
  "text": "string",
  "language": "string",
  "timestamp_utc": "ISO-8601",
  "metadata": {}
}
```

## Sentiment Output Contract (MVP)

- **score**: real number in **[-1.0, 1.0]** (continuous). -1 = maximally negative, 0 = neutral, 1 = maximally positive.
- **Label mapping (thresholds):**
  - `negative` if `score < -0.05`
  - `positive` if `score > 0.05`
  - `neutral` if `-0.05 <= score <= 0.05`

```json
{
  "event_id": "string",
  "label": "positive|neutral|negative",
  "score": -1.0,
  "confidence": 0.0,
  "model_version": "string",
  "scored_at_utc": "ISO-8601"
}
```

## Technical Approach (MVP)

- `src/mswia/ingestion/`: source adapters (YouTube, then Reddit, reviews)
- `src/mswia/processing/`: normalization, dedupe, aggregation
- `src/mswia/modeling/`: sentiment inference service (output normalized to [-1,1] + label by thresholds)
- `src/mswia/api/main.py`: serving and **SSE** stream endpoints only for MVP
- Storage: raw events in `data/raw`, processed in `data/processed`; optional lightweight DB for dashboard

## Delivery Slices

1. **Slice A**: YouTube end-to-end (ingest → normalize → score → API + SSE)
2. **Slice B**: Reddit + reviews connector, unified aggregation
3. **Slice C**: Dashboard + alerting
4. **Slice D**: Hardening (tests, retries, observability, docs)

## Acceptance Criteria for Spec 001

1. PRD is approved; backlog tasks mapped to slices A–D.
2. Canonical contracts and MVP API surface frozen.
3. Success metrics and measurement (latency boundary, F1 baseline/stretch) documented.
4. Second source (Reddit), stream protocol (SSE), score/label thresholds, and baseline KPI frozen.

## Risks and Mitigations

- API quota/rate limits: cache and queue ingestion, add backoff.
- Data noise/spam: text cleaning and dedupe rules.
- **Model KPI:** VADER/TextBlob may not reach 0.75 macro F1 on noisy data; mitigation: 0.70 baseline acceptance, plan transformer upgrade for stretch.
- Compliance/privacy: avoid storing raw PII identifiers.

## Model Governance

- Model versions are tracked in `models/registry.yaml` (name, version, thresholds, training snapshot).
- A validation dataset in `data/validation/validation.csv` is used by `scripts/evaluate_model.py` to compute macro F1 and other metrics before promoting a new model.
- Weekly (or per-release) evaluation is recommended; if macro F1 drops below 0.70, thresholds or model choice must be revisited.
- Known limitations and potential bias (e.g., language coverage, demographic bias) must be documented in the registry notes and revisited when changing models or data sources.

## Open Questions (resolved for MVP)

1. ~~Preferred second social source~~ → **Reddit** (locked).
2. Dashboard framework: Streamlit vs Next.js — defer to Slice C.
3. Alert destinations: webhook only at launch; email optional later.
