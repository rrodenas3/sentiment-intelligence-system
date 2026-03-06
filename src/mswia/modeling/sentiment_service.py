import logging
from typing import Optional
from ..schemas import SentimentLabel, SentimentOutput, CanonicalEvent
from ..config import (
    SCORE_NEGATIVE_THRESHOLD,
    SCORE_POSITIVE_THRESHOLD,
    SENTIMENT_MODEL_VERSION,
)

# Attempt to import VADER
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader_analyzer = SentimentIntensityAnalyzer()
except ImportError:
    vader_analyzer = None
    logging.warning("vaderSentiment not installed. Using mock scoring.")

from datetime import datetime, timezone

def score_text(text: str, event_id: str = "api-single") -> SentimentOutput:
    """Score text using VADER and map to canonical labels."""
    if vader_analyzer:
        scores = vader_analyzer.polarity_scores(text)
        compound_score = scores['compound']
    else:
        # Mock scoring for demonstration/fallback
        compound_score = 0.0
        if "love" in text.lower() or "great" in text.lower():
            compound_score = 0.8
        elif "hate" in text.lower() or "bad" in text.lower():
            compound_score = -0.8

    # Map score to label based on config thresholds
    if compound_score > SCORE_POSITIVE_THRESHOLD:
        label = SentimentLabel.POSITIVE
    elif compound_score < SCORE_NEGATIVE_THRESHOLD:
        label = SentimentLabel.NEGATIVE
    else:
        label = SentimentLabel.NEUTRAL

    return SentimentOutput(
        event_id=event_id,
        score=compound_score,
        label=label,
        confidence=0.9, # VADER doesn't provide per-instance confidence; using baseline
        model_version=SENTIMENT_MODEL_VERSION,
        scored_at_utc=datetime.now(timezone.utc)
    )

def process_event(event: CanonicalEvent) -> SentimentOutput:
    """Higher-level service to process a CanonicalEvent."""
    return score_text(event.text)
