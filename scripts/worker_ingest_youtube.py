"""Ingestion worker: fetch YouTube comments and push canonical events into Postgres + Redis queue.

Usage:
    PYTHONPATH=src python scripts/worker_ingest_youtube.py <video_id>
"""
import os
import sys
from datetime import timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mswia.config import YOUTUBE_API_KEY  # noqa: E402
from mswia.db import EventRaw, SessionLocal  # noqa: E402
from mswia.ingestion.youtube import fetch_youtube_comments  # noqa: E402
from mswia.processing.normalize import normalize_and_dedupe  # noqa: E402
from mswia.redis_client import QUEUE_EVENTS_PENDING, get_redis  # noqa: E402


def main(video_id: str, max_results: int = 100) -> None:
    if not YOUTUBE_API_KEY:
        raise SystemExit("YOUTUBE_API_KEY is required")

    r = get_redis()
    db = SessionLocal()
    try:
        raw_events = fetch_youtube_comments(video_id=video_id, api_key=YOUTUBE_API_KEY, max_results=max_results)
        # Apply normalization and cross-run deduplication
        for ev in normalize_and_dedupe(raw_events):
            # Persist raw event
            db_event = EventRaw(
                event_id=ev.event_id,
                source=ev.source.value,
                source_item_id=ev.source_item_id,
                author_id_hash=ev.author_id_hash,
                text=ev.text,
                language=ev.language,
                timestamp_utc=ev.timestamp_utc.replace(tzinfo=ev.timestamp_utc.tzinfo or timezone.utc),
                metadata_json=ev.metadata,
            )
            db.merge(db_event)  # upsert on event_id
            db.commit()

            # Enqueue for scoring
            r.rpush(QUEUE_EVENTS_PENDING, ev.model_dump_json())
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: PYTHONPATH=src python scripts/worker_ingest_youtube.py <video_id>")
        raise SystemExit(1)
    main(sys.argv[1].strip())

