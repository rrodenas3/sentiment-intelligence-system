from __future__ import annotations

"""
Redis client helpers for queue/cache and pub/sub.

Queues / channels (Spec 001 v2):
- events:pending  : list/stream of CanonicalEvent JSON awaiting scoring
- sentiment:live  : pub/sub channel for SentimentOutput JSON
- sentiment:recent: list of recent SentimentOutput JSON (for fast summary)
"""

import os
from functools import lru_cache

from redis import Redis


def get_redis_url() -> str:
    return os.environ.get("REDIS_URL", "redis://localhost:6379/0")


@lru_cache(maxsize=1)
def get_redis() -> Redis:
    return Redis.from_url(get_redis_url(), decode_responses=True)


QUEUE_EVENTS_PENDING = "events:pending"
CHANNEL_SENTIMENT_LIVE = "sentiment:live"
LIST_SENTIMENT_RECENT = "sentiment:recent"

