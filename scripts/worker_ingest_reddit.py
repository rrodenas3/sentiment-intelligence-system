"""Reddit ingestion worker: fetches comments and pushes to events:pending queue (Spec 001).

Usage:
    PYTHONPATH=src python scripts/worker_ingest_reddit.py <subreddit> [limit]
"""
import json
import logging
import os
import sys
import time
from datetime import timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mswia.config import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
)
from mswia.db import EventRaw, SessionLocal
from mswia.ingestion.reddit import fetch_reddit_comments
from mswia.processing.normalize import normalize_and_dedupe
from mswia.redis_client import QUEUE_EVENTS_PENDING, get_redis

# Optional deduplication across ingestion loops
SEEN_EVENTS_KEY = "ingestion:reddit:seen"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/worker_ingest_reddit.py <subreddit> [limit]")
        sys.exit(1)

    subreddit = sys.argv[1]
    limit = 100
    if len(sys.argv) > 2:
        limit = int(sys.argv[2])

    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        logger.error("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set in environment.")
        sys.exit(1)

    r = get_redis()
    db = SessionLocal()
    logger.info(f"Starting Reddit ingestion for r/{subreddit}...")

    # Infinite polling loop typical for ingestion workers
    try:
        while True:
            logger.info(f"Fetching up to {limit} comments from r/{subreddit}...")
            try:
                raw_events = fetch_reddit_comments(
                    subreddit=subreddit,
                    client_id=REDDIT_CLIENT_ID,
                    client_secret=REDDIT_CLIENT_SECRET,
                    user_agent=REDDIT_USER_AGENT,
                    limit=limit
                )
                
                count = 0
                new_count = 0

                for event in normalize_and_dedupe(raw_events):
                    count += 1
                    # Check deduplication set to avoid pushing the same comment every polling cycle
                    if r.sadd(SEEN_EVENTS_KEY, event.event_id) == 0:
                        continue  # Already seen

                    # Persist raw event to DB
                    db_event = EventRaw(
                        event_id=event.event_id,
                        source=event.source.value,
                        source_item_id=event.source_item_id,
                        author_id_hash=event.author_id_hash,
                        text=event.text,
                        language=event.language,
                        timestamp_utc=event.timestamp_utc.replace(tzinfo=event.timestamp_utc.tzinfo or timezone.utc),
                        metadata_json=event.metadata,
                    )
                    db.merge(db_event) # upsert
                    db.commit()

                    # Push to processing queue
                    j = json.dumps(event.model_dump(mode="json"))
                    r.rpush(QUEUE_EVENTS_PENDING, j)
                    new_count += 1

                # Prevent seen set from growing indefinitely (keep for 24 hours of rolling restarts)
                r.expire(SEEN_EVENTS_KEY, 86400)

                logger.info(f"Fetched and normalized events, {new_count} new events queued.")

            except Exception as e:
                logger.error(f"Error fetching Reddit comments: {e}")
                db.rollback()

            # Sleep to avoid hitting rate limits. Reddit allows 60 req/min for OAuth clients.
            # Polling every 30 seconds is safe and retrieves reasonably timely updates.
            logger.info("Sleeping for 30 seconds before next poll...")
            time.sleep(30)
    finally:
        db.close()

if __name__ == "__main__":
    main()
