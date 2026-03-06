"""Canonical event and sentiment contracts (Spec 001)."""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    REVIEWS = "reviews"


class CanonicalEvent(BaseModel):
    """Normalized input event from any source."""
    event_id: str
    source: SourceType
    source_item_id: str
    author_id_hash: str
    text: str
    language: str = "en"
    timestamp_utc: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class SentimentOutput(BaseModel):
    """Sentiment result: score in [-1, 1], label by Spec 001 thresholds."""
    event_id: str
    label: SentimentLabel
    score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str
    scored_at_utc: datetime


def score_to_label(score: float) -> SentimentLabel:
    """Map continuous score to label (Spec 001: negative < -0.05, positive > 0.05)."""
    if score < -0.05:
        return SentimentLabel.NEGATIVE
    if score > 0.05:
        return SentimentLabel.POSITIVE
    return SentimentLabel.NEUTRAL
