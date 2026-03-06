"""Reviews ingestion worker: reads generic reviews from a local directory or stream and pushes to events:pending queue (Spec 001).

Usage:
    PYTHONPATH=src python scripts/worker_ingest_reviews.py <product_id> <path_to_json>
"""
import json
import logging
import os
import sys
from datetime import timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mswia.db import EventRaw, SessionLocal
from mswia.ingestion.reviews import ingest_reviews_from_json
from mswia.processing.normalize import normalize_and_dedupe
from mswia.redis_client import QUEUE_EVENTS_PENDING, get_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scripts/worker_ingest_reviews.py <product_id> <path_to_json>")
        sys.exit(1)

    product_id = sys.argv[1]
    file_path = sys.argv[2]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON file: {file_path}")
        sys.exit(1)

    reviews = data.get("reviews", []) if isinstance(data, dict) else data
    if not isinstance(reviews, list):
        logger.error(f"Expected a list of reviews in the JSON payload, got {type(reviews)}")
        sys.exit(1)

    r = get_redis()
    db = SessionLocal()
    logger.info(f"Starting Reviews ingestion for product {product_id} from {file_path}...")

    try:
        raw_events = ingest_reviews_from_json(
            product_id=product_id,
            reviews=reviews,
        )

        count = 0
        for event in normalize_and_dedupe(raw_events):
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

            # Push to processing queue directly (since it's a one-off import from a file)
            j = json.dumps(event.model_dump(mode="json"))
            r.rpush(QUEUE_EVENTS_PENDING, j)
            count += 1

        logger.info(f"Successfully processed and queued {count} review events for sentiment analysis.")

    except Exception as e:
        logger.error(f"Error ingesting reviews: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
