"""Sentiment worker: consume events from Redis, score them, store in Postgres, and publish live results.

Usage:
    PYTHONPATH=src python scripts/worker_sentiment.py
"""
import json
import logging
import os
import sys
from datetime import timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mswia.db import EventRaw, SentimentScore, SessionLocal  # noqa: E402
from mswia.modeling import sentiment_service  # noqa: E402
from mswia.redis_client import (  # noqa: E402
    CHANNEL_SENTIMENT_LIVE,
    LIST_SENTIMENT_RECENT,
    QUEUE_EVENTS_PENDING,
    get_redis,
)
from mswia.schemas import CanonicalEvent  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def process_one(r, db) -> None:
    # Use BRPOP for blocking wait (more efficient than LPOP + sleep)
    # Returns (key, value) tuple
    result = r.brpop(QUEUE_EVENTS_PENDING, timeout=5)
    if not result:
        return

    _, packed = result
    try:
        data = json.loads(packed)
        ev = CanonicalEvent(**data)

        # Score
        result = sentiment_service(ev)

        # Persist EventRaw first to satisfy Foreign Key constraints
        db_raw = EventRaw(
            event_id=ev.event_id,
            source=ev.source.value,
            source_item_id=ev.source_item_id,
            author_id_hash=ev.author_id_hash,
            text=ev.text,
            language=ev.language,
            timestamp_utc=ev.timestamp_utc.replace(tzinfo=ev.timestamp_utc.tzinfo or timezone.utc),
            metadata_json=ev.metadata or {}
        )
        db.add(db_raw)
        db.flush() # ensure EventRaw is available for the FK relationship

        # Persist Score
        db_score = SentimentScore(
            event_id=result.event_id,
            label=result.label.value,
            score=result.score,
            confidence=result.confidence,
            model_version=result.model_version,
            scored_at_utc=result.scored_at_utc.replace(tzinfo=result.scored_at_utc.tzinfo or timezone.utc),
        )
        db.add(db_score)
        db.commit()

        # Publish live + cache recent
        payload = result.model_dump(mode="json")
        payload["label"] = result.label.value
        payload["scored_at_utc"] = result.scored_at_utc.isoformat()
        j = json.dumps(payload)
        r.publish(CHANNEL_SENTIMENT_LIVE, j)
        r.lpush(LIST_SENTIMENT_RECENT, j)
        r.ltrim(LIST_SENTIMENT_RECENT, 0, 999)  # keep last 1000
        
        logger.info(f"Processed sentiment for event {result.event_id}: {result.label.value}")

    except Exception as e:
        logger.error(f"Error processing event: {e}")
        db.rollback()


def main() -> None:
    r = get_redis()
    logger.info("Starting sentiment worker...")
    
    while True:
        # Create a new session per 'batch' or item to avoid long-lived connection issues
        db = SessionLocal()
        try:
            # We can process multiple items per session for efficiency, 
            # but here we'll do one for maximum isolation and reliability.
            process_one(r, db)
        except Exception as e:
            logger.error(f"Worker loop encountered unexpected error: {e}")
        finally:
            db.close()


if __name__ == "__main__":
    main()

