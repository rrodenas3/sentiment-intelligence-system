"""YouTube comments ingestion -> canonical events (Spec 001)."""
import hashlib
from datetime import datetime, timezone
from typing import Iterator

from mswia.schemas import CanonicalEvent, SourceType

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    HAS_YOUTUBE_API = True
except ImportError:
    HAS_YOUTUBE_API = False


def _hash_author(author_id: str) -> str:
    return hashlib.sha256(author_id.encode()).hexdigest()[:32]


def fetch_youtube_comments(
    video_id: str,
    api_key: str,
    max_results: int = 100,
) -> Iterator[CanonicalEvent]:
    """Fetch top-level comments for a video and yield canonical events."""
    if not HAS_YOUTUBE_API:
        raise RuntimeError("google-api-python-client not installed; pip install google-api-python-client")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY required")

    youtube = build("youtube", "v3", developerKey=api_key)
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        textFormat="plainText",
        maxResults=min(max_results, 100),
        order="relevance",
    )
    page_token = None
    seen = set()

    while True:
        if page_token:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                textFormat="plainText",
                maxResults=min(max_results, 100),
                order="relevance",
                pageToken=page_token,
            )
        response = request.execute()
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            top = snippet.get("topLevelComment", {}).get("snippet", {})
            comment_id = top.get("id") or item.get("id")
            text = (top.get("textDisplay") or top.get("textOriginal") or "").strip()
            if not text or comment_id in seen:
                continue
            seen.add(comment_id)
            author = top.get("authorDisplayName") or top.get("authorChannelId", {}).get("value") or "unknown"
            published = top.get("publishedAt")
            try:
                ts = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else datetime.now(timezone.utc)
            except Exception:
                ts = datetime.now(timezone.utc)

            event_id = f"yt_{video_id}_{comment_id}"
            yield CanonicalEvent(
                event_id=event_id,
                source=SourceType.YOUTUBE,
                source_item_id=video_id,
                author_id_hash=_hash_author(str(author)),
                text=text,
                language="en",
                timestamp_utc=ts,
                metadata={"comment_id": comment_id},
            )

        page_token = response.get("nextPageToken")
        if not page_token:
            break
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=min(max_results, 100),
            order="relevance",
            pageToken=page_token,
        )
