from __future__ import annotations

"""
Database configuration and core models for Spec 001.

This module provides:
- SQLAlchemy engine/session factory using DATABASE_URL
- ORM models for events_raw, sentiment_scores, aggregates_windowed
- a simple init_db() helper for local development
"""

import os
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/sentiment"


class Base(DeclarativeBase):
    metadata = MetaData()


class EventRaw(Base):
    __tablename__ = "events_raw"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_item_id: Mapped[str] = mapped_column(String, nullable=False)
    author_id_hash: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False, default="en")
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events_raw.event_id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String, nullable=False)
    scored_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AggregateWindowed(Base):
    __tablename__ = "aggregates_windowed"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_window: Mapped[str] = mapped_column(String, nullable=False)  # 1m | 5m | 1h
    source: Mapped[str] = mapped_column(String, nullable=False)
    count_total: Mapped[int] = mapped_column(Integer, nullable=False)
    count_positive: Mapped[int] = mapped_column(Integer, nullable=False)
    count_neutral: Mapped[int] = mapped_column(Integer, nullable=False)
    count_negative: Mapped[int] = mapped_column(Integer, nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


engine = create_engine(get_database_url(), future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def init_db() -> None:
    """
    Create tables based on ORM models.

    In production, prefer Alembic migrations; this helper is mainly for local
    development and tests.
    """
    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

