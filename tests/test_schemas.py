"""Contract tests: score range and label thresholds (Spec 001)."""
from datetime import datetime, timezone

import pytest
from mswia.schemas import score_to_label, SentimentLabel


def test_score_to_label_negative():
    assert score_to_label(-0.5) == SentimentLabel.NEGATIVE
    assert score_to_label(-1.0) == SentimentLabel.NEGATIVE
    assert score_to_label(-0.06) == SentimentLabel.NEGATIVE


def test_score_to_label_positive():
    assert score_to_label(0.5) == SentimentLabel.POSITIVE
    assert score_to_label(1.0) == SentimentLabel.POSITIVE
    assert score_to_label(0.06) == SentimentLabel.POSITIVE


def test_score_to_label_neutral():
    assert score_to_label(0.0) == SentimentLabel.NEUTRAL
    assert score_to_label(-0.05) == SentimentLabel.NEUTRAL
    assert score_to_label(0.05) == SentimentLabel.NEUTRAL
