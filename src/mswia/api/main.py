"""FastAPI: POST /analyze/text, GET /sentiment/summary, GET /stream/sentiment (SSE only). Spec 001 MVP."""
import json
import os
from datetime import datetime, timezone
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import desc, select

from mswia.auth import create_access_token, get_current_user, get_password_hash, get_db
from mswia.config import DATA_RAW_DIR, DATA_PROCESSED_DIR, YOUTUBE_API_KEY
from mswia.db import SentimentScore, SessionLocal, User
from mswia.modeling import sentiment_service
from mswia.processing import normalize_and_dedupe
from mswia.redis_client import (
    CHANNEL_SENTIMENT_LIVE,
    LIST_SENTIMENT_RECENT,
    get_redis,
)
from mswia.schemas import CanonicalEvent, SentimentOutput, SourceType

app = FastAPI(title="Sentiment API (Spec 001)", version="0.1.0")

allowed_origins = os.environ.get("API_CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,http://0.0.0.0:3000,http://host.docker.internal:3000").split(",")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

@app.get("/")
def read_root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict:
    """
    Basic health check:
    - DB connectivity
    - Redis connectivity
    """
    db_ok = False
    redis_ok = False
    try:
        with SessionLocal() as db:
            db.execute(select(1))
            db_ok = True
    except Exception:
        db_ok = False

    try:
        r = get_redis()
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    status = "ok" if db_ok and redis_ok else "degraded" if db_ok or redis_ok else "down"
    return {
        "status": status,
        "database": db_ok,
        "redis": redis_ok,
        "version": app.version,
    }


class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000)


class AnalyzeTextResponse(BaseModel):
    label: str
    score: float
    confidence: float
    model_version: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/analyze/text", response_model=AnalyzeTextResponse)
@limiter.limit("60/minute")
def analyze_text(request: Request, body: AnalyzeTextRequest, current_user: User = Depends(get_current_user)) -> AnalyzeTextResponse:
    """Single text inference (Spec 001)."""
    from mswia.modeling.sentiment import score_text
    out = score_text(body.text, event_id="api-single")
    return AnalyzeTextResponse(
        label=out.label.value,
        score=out.score,
        confidence=out.confidence,
        model_version=out.model_version,
    )


@app.post("/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    from mswia.auth import authenticate_user

    with SessionLocal() as db:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = create_access_token({"sub": user.email})
        return TokenResponse(access_token=token)


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "user"


@app.post("/auth/register", response_model=TokenResponse)
@limiter.limit("3/minute")
def register(request: Request, body: RegisterRequest) -> TokenResponse:
    with SessionLocal() as db:
        from mswia.auth import get_user_by_email
        existing = get_user_by_email(db, body.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        hashed_pw = get_password_hash(body.password)
        new_user = User(email=body.email, hashed_password=hashed_pw, role=body.role)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        token = create_access_token({"sub": new_user.email})
        return TokenResponse(access_token=token)


@app.get("/sentiment/summary")
def sentiment_summary(
    source: str | None = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Aggregate snapshot: recent sentiment results backed by Redis/Postgres."""
    r = get_redis()
    raw_items = r.lrange(LIST_SENTIMENT_RECENT, 0, limit - 1)
    items: list[SentimentOutput] = []
    for raw in raw_items:
        try:
            data = json.loads(raw)
            items.append(
                SentimentOutput(
                    event_id=data["event_id"],
                    label=data["label"],
                    score=data["score"],
                    confidence=data["confidence"],
                    model_version=data["model_version"],
                    scored_at_utc=datetime.fromisoformat(data["scored_at_utc"]),
                )
            )
        except Exception:
            continue

    # Fallback to Postgres if Redis has no data yet
    if not items:
        with SessionLocal() as db:
            stmt = select(SentimentScore).order_by(desc(SentimentScore.scored_at_utc)).limit(limit)
            rows = db.execute(stmt).scalars().all()
            for row in rows:
                items.append(
                    SentimentOutput(
                        event_id=row.event_id,
                        label=row.label,  # type: ignore[arg-type]
                        score=row.score,
                        confidence=row.confidence,
                        model_version=row.model_version,
                        scored_at_utc=row.scored_at_utc,
                    )
                )

    by_label = {"positive": 0, "neutral": 0, "negative": 0}
    for r in items:
        key = r.label.value if isinstance(r.label, str) is False else r.label
        by_label[key] = by_label.get(key, 0) + 1

    recent_list = []
    for r in items[:20]:
        key = r.label.value if isinstance(r.label, str) is False else r.label
        recent_list.append({
            "event_id": r.event_id,
            "label": key,
            "score": r.score,
            "scored_at_utc": r.scored_at_utc.isoformat(),
        })

    return {
        "window": "recent",
        "count": len(items),
        "by_label": by_label,
        "recent": recent_list,
    }


@app.get("/sentiment/aggregates")
@limiter.limit("30/minute")
def get_aggregates(
    request: Request,
    window: str = "1h",
    source: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Retrieve time-windowed aggregates (e.g. 1m, 5m, 1h)."""
    from mswia.db import AggregateWindowed

    if window not in ("1m", "5m", "1h"):
        raise HTTPException(status_code=400, detail="Window must be 1m, 5m, or 1h")

    with SessionLocal() as db:
        stmt = select(AggregateWindowed).where(AggregateWindowed.time_window == window)
        
        if source:
            stmt = stmt.where(AggregateWindowed.source == source)
        if start_time:
            stmt = stmt.where(AggregateWindowed.bucket_start >= start_time)
        if end_time:
            stmt = stmt.where(AggregateWindowed.bucket_start <= end_time)
            
        stmt = stmt.order_by(desc(AggregateWindowed.bucket_start)).limit(limit)
        rows = db.execute(stmt).scalars().all()

        return [
            {
                "bucket_start": row.bucket_start.isoformat(),
                "window": row.time_window,
                "source": row.source,
                "count_total": row.count_total,
                "count_positive": row.count_positive,
                "count_neutral": row.count_neutral,
                "count_negative": row.count_negative,
            }
            for row in rows
        ]


def _redis_sse_stream() -> Generator[str, None, None]:
    """Yield SSE events from Redis pub/sub channel."""
    r = get_redis()
    pubsub = r.pubsub()
    try:
        pubsub.subscribe(CHANNEL_SENTIMENT_LIVE)
        for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            data = message.get("data")
            if not isinstance(data, str):
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                else:
                    continue
            yield f"data: {data}\n\n"
    finally:
        try:
            pubsub.unsubscribe(CHANNEL_SENTIMENT_LIVE)
            pubsub.close()
        except Exception:
            pass


@app.get("/stream/sentiment")
def stream_sentiment(current_user: User = Depends(get_current_user)):
    """Live sentiment updates (SSE only, Spec 001)."""
    return StreamingResponse(
        _redis_sse_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def run_pipeline_youtube(video_id: str) -> None:
    """Legacy pipeline: ingest -> normalize -> score -> write to data/processed only. No Redis/DB. Prefer workers in production."""
    from mswia.ingestion.youtube import fetch_youtube_comments
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    events = fetch_youtube_comments(video_id, YOUTUBE_API_KEY, max_results=50)
    for event in normalize_and_dedupe(events):
        result = sentiment_service(event)
        (DATA_PROCESSED_DIR / f"{event.event_id}.json").write_text(
            result.model_dump_json(), encoding="utf-8"
        )
