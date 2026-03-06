"""Smoke tests for Spec 001 MVP API (Slice A)."""
import pytest
from fastapi.testclient import TestClient

from mswia.api.main import app
from mswia.auth import get_current_user
from mswia.db import User

app.dependency_overrides[get_current_user] = lambda: User(email="test@example.com", role="user")

client = TestClient(app)


def test_analyze_text():
    r = client.post("/analyze/text", json={"text": "I love this product!"})
    assert r.status_code == 200
    data = r.json()
    assert data["label"] in ("positive", "neutral", "negative")
    assert -1 <= data["score"] <= 1
    assert 0 <= data["confidence"] <= 1
    assert "model_version" in data


def test_sentiment_summary():
    r = client.get("/sentiment/summary")
    assert r.status_code == 200
    data = r.json()
    assert "by_label" in data
    assert "count" in data
    assert data["by_label"].keys() >= {"positive", "neutral", "negative"}


@pytest.mark.skip(reason="SSE stream blocks TestClient; verify manually via GET /stream/sentiment")
def test_stream_sentiment_sse():
    r = client.get("/stream/sentiment", timeout=1.0)
    assert r.status_code == 200
    assert "text/event-stream" in r.headers.get("content-type", "")
