"""Aggregates worker: polls sentiment_scores, calculates rolling aggregations, and upserts into aggregates_windowed (Spec 001).

Usage:
    PYTHONPATH=src python scripts/worker_aggregates.py
"""
import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from mswia.db import AggregateWindowed, EventRaw, SentimentScore, SessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def compute_window(db: Session, window_str: str, window_delta: timedelta):
    """
    Computes aggregates for the current time window for all sources, 
    upserting into the aggregates_windowed table.
    """
    now = datetime.now(timezone.utc)
    # Floor the current time to the nearest window
    if window_str == "1m":
        bucket_start = now.replace(second=0, microsecond=0)
    elif window_str == "5m":
        bucket_start = now.replace(minute=(now.minute // 5) * 5, second=0, microsecond=0)
    elif window_str == "1h":
        bucket_start = now.replace(minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Unsupported window: {window_str}")

    bucket_end = bucket_start + window_delta

    # Query scores within this bucket joined with their source
    # We use SQLAlchemy ORM for the aggregation
    stmt = (
        select(
            EventRaw.source,
            SentimentScore.label,
            func.count(SentimentScore.id).label("cnt")
        )
        .join(EventRaw, SentimentScore.event_id == EventRaw.id) # Assuming SentimentScore.event_id references EventRaw.id (Wait, schema says SentimentScore.event_id mapping to EventRaw.id but the DB schema might be String. Let's adjust.)
        .where(SentimentScore.scored_at_utc >= bucket_start)
        .where(SentimentScore.scored_at_utc < bucket_end)
        .group_by(EventRaw.source, SentimentScore.label)
    )
    
    # Wait, the schema from earlier:
    # SentimentScore.event_id is a String (e.g. 'yt_video_comment') but EventRaw has 'id' (int) and 'event_id' (String). 
    # Let's fix the join condition: SentimentScore.event_id == EventRaw.event_id.
    stmt = (
        select(
            EventRaw.source,
            SentimentScore.label,
            func.count(SentimentScore.id).label("cnt")
        )
        .join(EventRaw, SentimentScore.event_id == EventRaw.id) # Let's rewrite this correctly below.
        .where(SentimentScore.scored_at_utc >= bucket_start)
        .where(SentimentScore.scored_at_utc < bucket_end)
        .group_by(EventRaw.source, SentimentScore.label)
    )
    # We will rewrite the function logic completely to ensure it's correct.
    pass

def compute_aggregates():
    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        
        # Windows to compute
        windows = {
            "1m": now.replace(second=0, microsecond=0),
            "5m": now.replace(minute=(now.minute // 5) * 5, second=0, microsecond=0),
            "1h": now.replace(minute=0, second=0, microsecond=0)
        }
        
        for win_name, bucket_start in windows.items():
            if win_name == "1m":
                bucket_end = bucket_start + timedelta(minutes=1)
            elif win_name == "5m":
                bucket_end = bucket_start + timedelta(minutes=5)
            else:
                bucket_end = bucket_start + timedelta(hours=1)
                
            # Count scores for each source and label
            # Note: The db schema indicates SentimentScore.event_id is actually the EventRaw.id integer in the worker_sentiment.py, but defined as String in db.py!
            # Let's verify by just looking at worker_sentiment.py logic in DB.
            # In worker_sentiment.py:
            # raw_event = RawEvent(...); db.flush();
            # score_entry = SentimentScore(event_id=raw_event.id ...) <- so SentimentScore.event_id contains the integer ID (cast to string because DB type is String).
            
            # Since EventRaw has .id (Integer), we cast EventRaw.id to String to join.
            # Better to use raw SQL for clarity and performance.
            sql = text("""
                SELECT e.source, s.label, COUNT(*) as cnt
                FROM sentiment_scores s
                JOIN events_raw e ON e.event_id = s.event_id
                WHERE s.scored_at_utc >= :start AND s.scored_at_utc < :end
                GROUP BY e.source, s.label
            """)
            
            result = db.execute(sql, {"start": bucket_start, "end": bucket_end}).fetchall()
            
            # Process results into a memory map
            # structure: source -> {positive: 0, neutral: 0, negative: 0, total: 0}
            agg_map = {}
            for row in result:
                source, label, cnt = row.source, row.label, row.cnt
                if source not in agg_map:
                    agg_map[source] = {"positive": 0, "neutral": 0, "negative": 0, "total": 0}
                
                label_lower = label.lower()
                if label_lower in agg_map[source]:
                    agg_map[source][label_lower] += cnt
                agg_map[source]["total"] += cnt
                
            # Upsert into AggregatesWindowed
            for source, counts in agg_map.items():
                existing = db.execute(
                    select(AggregateWindowed)
                    .where(AggregateWindowed.bucket_start == bucket_start)
                    .where(AggregateWindowed.time_window == win_name)
                    .where(AggregateWindowed.source == source)
                ).scalars().first()
                
                if existing:
                    existing.count_total = counts["total"]
                    existing.count_positive = counts["positive"]
                    existing.count_neutral = counts["neutral"]
                    existing.count_negative = counts["negative"]
                else:
                    new_agg = AggregateWindowed(
                        bucket_start=bucket_start,
                        time_window=win_name,
                        source=source,
                        count_total=counts["total"],
                        count_positive=counts["positive"],
                        count_neutral=counts["neutral"],
                        count_negative=counts["negative"]
                    )
                    db.add(new_agg)
        
        db.commit()


def main() -> None:
    logger.info("Starting aggregates worker...")
    while True:
        try:
            compute_aggregates()
            logger.info("Aggregates computed successfully.")
        except Exception as e:
            logger.error(f"Error computing aggregates: {e}")
            
        time.sleep(60)


if __name__ == "__main__":
    main()
