"""Reddit comments ingestion -> canonical events (Spec 001)."""
import hashlib
import json
from datetime import datetime, timezone
from typing import Iterator

import httpx

from mswia.schemas import CanonicalEvent, SourceType


def _hash_author(author_name: str) -> str:
    return hashlib.sha256(author_name.encode()).hexdigest()[:32]


def fetch_reddit_comments(
    subreddit: str,
    client_id: str,
    client_secret: str,
    user_agent: str,
    limit: int = 100,
) -> Iterator[CanonicalEvent]:
    """Fetch recent comments from a subreddit and yield canonical events."""
    if not client_id or not client_secret:
        raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are required")

    # 1. Get access token
    auth = httpx.BasicAuth(client_id, client_secret)
    data = {"grant_type": "client_credentials"}
    headers = {"User-Agent": user_agent}

    try:
        response = httpx.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth,
            data=data,
            headers=headers,
            timeout=10.0,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
    except httpx.HTTPError as e:
        raise RuntimeError(f"Failed to fetch Reddit access token: {e}")

    if not token:
        raise RuntimeError("Reddit API did not return an access token")

    # 2. Fetch comments
    api_headers = {
        "Authorization": f"bearer {token}",
        "User-Agent": user_agent,
    }
    
    try:
        url = f"https://oauth.reddit.com/r/{subreddit}/comments.json?limit={min(limit, 100)}"
        res = httpx.get(url, headers=api_headers, timeout=10.0)
        res.raise_for_status()
        listing = res.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"Failed to fetch Reddit comments: {e}")
        
    for child in listing.get("data", {}).get("children", []):
        data = child.get("data", {})
        comment_id = data.get("id")
        text = (data.get("body") or "").strip()
        if not text or not comment_id:
            continue
            
        author = data.get("author") or "unknown"
        created_utc = data.get("created_utc")
        try:
            ts = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        except Exception:
            ts = datetime.now(timezone.utc)

        # Derive source_item_id (the post ID) from link_id (e.g., "t3_xxxxx" -> "xxxxx")
        link_id = data.get("link_id") or ""
        source_item_id = link_id.replace("t3_", "") if link_id.startswith("t3_") else comment_id

        event_id = f"rd_{subreddit}_{comment_id}"
        yield CanonicalEvent(
            event_id=event_id,
            source=SourceType.REDDIT,
            source_item_id=source_item_id,
            author_id_hash=_hash_author(str(author)),
            text=text,
            language="en",
            timestamp_utc=ts,
            metadata={
                "comment_id": comment_id,
                "subreddit": subreddit,
                "permalink": data.get("permalink", "")
            },
        )
