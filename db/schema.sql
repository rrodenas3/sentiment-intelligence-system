-- PostgreSQL schema for Spec 001 – events and sentiment
-- This is the canonical definition for persistence. Migrations can
-- be generated from this file or managed via Alembic.

CREATE TABLE IF NOT EXISTS events_raw (
    id              BIGSERIAL PRIMARY KEY,
    event_id        TEXT NOT NULL UNIQUE,
    source          TEXT NOT NULL, -- youtube | reddit | reviews
    source_item_id  TEXT NOT NULL,
    author_id_hash  TEXT NOT NULL,
    text            TEXT NOT NULL,
    language        TEXT NOT NULL DEFAULT 'en',
    timestamp_utc   TIMESTAMPTZ NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_raw_source_timestamp
    ON events_raw (source, timestamp_utc);


CREATE TABLE IF NOT EXISTS sentiment_scores (
    id              BIGSERIAL PRIMARY KEY,
    event_id        TEXT NOT NULL REFERENCES events_raw(event_id) ON DELETE CASCADE,
    label           TEXT NOT NULL, -- positive | neutral | negative
    score           REAL NOT NULL,
    confidence      REAL NOT NULL,
    model_version   TEXT NOT NULL,
    scored_at_utc   TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sentiment_scores_event_id
    ON sentiment_scores (event_id);

CREATE INDEX IF NOT EXISTS idx_sentiment_scores_scored_at
    ON sentiment_scores (scored_at_utc);


-- Optional precomputed aggregates for fast dashboard queries.
CREATE TABLE IF NOT EXISTS aggregates_windowed (
    bucket_start    TIMESTAMPTZ NOT NULL,
    time_window     TEXT NOT NULL, -- 1m | 5m | 1h
    source          TEXT NOT NULL,
    count_total     INTEGER NOT NULL,
    count_positive  INTEGER NOT NULL,
    count_neutral   INTEGER NOT NULL,
    count_negative  INTEGER NOT NULL,
    PRIMARY KEY (bucket_start, time_window, source)
);


CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'user',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


