"""Generic product reviews ingestion -> canonical events (Spec 001)."""
import hashlib
from datetime import datetime, timezone
from typing import Iterator

from mswia.schemas import CanonicalEvent, SourceType


def _hash_author(author_name: str) -> str:
    return hashlib.sha256(author_name.encode()).hexdigest()[:32]


def ingest_reviews_from_json(
    product_id: str,
    reviews: list[dict],
) -> Iterator[CanonicalEvent]:
    """
    Ingest product reviews from a standard dictionary format and yield canonical events.
    Expected format for each review:
    {
        "review_id": "rev123",
        "author": "Alice",
        "text": "Great product!",
        "published_at": "2026-03-01T12:00:00Z" # optional
    }
    """
    for review in reviews:
        review_id = review.get("review_id")
        text = (review.get("text") or "").strip()
        
        if not text or not review_id:
            continue
            
        author = review.get("author") or "anonymous"
        published_str = review.get("published_at")
        
        try:
            if published_str:
                ts = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
            else:
                ts = datetime.now(timezone.utc)
        except Exception:
            ts = datetime.now(timezone.utc)

        event_id = f"rv_{product_id}_{review_id}"
        yield CanonicalEvent(
            event_id=event_id,
            source=SourceType.REVIEWS,
            source_item_id=product_id,
            author_id_hash=_hash_author(str(author)),
            text=text,
            language="en",
            timestamp_utc=ts,
            metadata={
                "review_id": review_id,
                "rating": review.get("rating", 0)  # Preserving standard review metadata if present
            },
        )
