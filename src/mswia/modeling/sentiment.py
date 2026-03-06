"""Baseline sentiment: score in [-1, 1], label by Spec 001 thresholds."""
from datetime import datetime, timezone

from mswia.config import SENTIMENT_MODEL_VERSION
from mswia.schemas import CanonicalEvent, SentimentOutput, score_to_label

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _analyzer = SentimentIntensityAnalyzer()
    _engine = "vader"
except ImportError:
    _analyzer = None
    _engine = "textblob"


def _vader_score(text: str) -> tuple[float, float]:
    """Returns (compound in [-1,1], confidence-like 0..1)."""
    if not _analyzer:
        raise RuntimeError("vaderSentiment not installed; pip install vaderSentiment")
    d = _analyzer.polarity_scores(text)
    compound = float(d["compound"])
    # Use max of pos/neg as proxy for confidence
    conf = max(d["pos"], d["neg"]) if (d["pos"] or d["neg"]) else 0.5
    return compound, min(1.0, conf + 0.3)


def _textblob_score(text: str) -> tuple[float, float]:
    """Returns (polarity in [-1,1], confidence proxy)."""
    try:
        from textblob import TextBlob
    except ImportError:
        raise RuntimeError("textblob not installed; pip install textblob")
    blob = TextBlob(text)
    # TextBlob polarity is roughly [-1, 1]
    pol = blob.sentiment.polarity
    subj = blob.sentiment.subjectivity
    conf = min(1.0, 0.5 + abs(pol) * 0.5)
    return pol, conf


def score_text(text: str, event_id: str = "") -> SentimentOutput:
    """Score a single text; returns SentimentOutput."""
    if _engine == "vader":
        raw_score, confidence = _vader_score(text)
    else:
        raw_score, confidence = _textblob_score(text)
    score = max(-1.0, min(1.0, raw_score))
    label = score_to_label(score)
    return SentimentOutput(
        event_id=event_id,
        label=label,
        score=score,
        confidence=confidence,
        model_version=SENTIMENT_MODEL_VERSION,
        scored_at_utc=datetime.now(timezone.utc),
    )


def sentiment_service(event: CanonicalEvent) -> SentimentOutput:
    """Score a canonical event; t_ingest = event.timestamp_utc, t_ready = scored_at_utc for latency."""
    return score_text(event.text, event_id=event.event_id)
