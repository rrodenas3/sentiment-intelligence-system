import pytest
from mswia.modeling.sentiment_service import score_text, process_event
from mswia.schemas import SentimentLabel, CanonicalEvent, SourceType
from datetime import datetime, timezone

def test_score_text_positive():
    result = score_text("I love this product, it is great!")
    assert result.label == SentimentLabel.POSITIVE
    assert result.score > 0.05

def test_score_text_negative():
    result = score_text("I hate this, it is bad.")
    assert result.label == SentimentLabel.NEGATIVE
    assert result.score < -0.05

def test_score_text_neutral():
    result = score_text("This is entirely average.")
    assert result.label == SentimentLabel.NEUTRAL
    assert -0.05 <= result.score <= 0.05

def test_process_event():
    event = CanonicalEvent(
        event_id="test_001",
        source=SourceType.YOUTUBE,
        source_item_id="123",
        author_id_hash="abc",
        text="This is fantastic!",
        timestamp_utc=datetime.now(timezone.utc)
    )
    result = process_event(event)
    assert result.label == SentimentLabel.POSITIVE
    assert result.model_version is not None
