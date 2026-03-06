"""Normalization and deduplication (Spec 001)."""
import re
from datetime import datetime, timezone
from typing import Iterator

from mswia.schemas import CanonicalEvent, SourceType


def _normalize_text(text: str) -> str:
    """Basic cleanup: strip, collapse whitespace."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())


def _dedupe_key(event: CanonicalEvent) -> str:
    return f"{event.source.value}:{event.source_item_id}:{event.author_id_hash}:{event.text[:200]}"


def normalize_and_dedupe(events: Iterator[CanonicalEvent]) -> Iterator[CanonicalEvent]:
    """Yield events with normalized text; skip duplicates by (source, item, author, text)."""
    seen: set[str] = set()
    for event in events:
        text = _normalize_text(event.text)
        if not text:
            continue
        # Build a copy with normalized text and ensure timestamp has tz
        ts = event.timestamp_utc
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        normalized = CanonicalEvent(
            event_id=event.event_id,
            source=event.source,
            source_item_id=event.source_item_id,
            author_id_hash=event.author_id_hash,
            text=text,
            language=event.language,
            timestamp_utc=ts,
            metadata=event.metadata,
        )
        key = _dedupe_key(normalized)
        if key in seen:
            continue
        seen.add(key)
        yield normalized
