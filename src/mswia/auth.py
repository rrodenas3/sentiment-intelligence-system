from __future__ import annotations

"""
JWT auth helpers for the sentiment API.

This module provides:
- password hashing/verification
- JWT token creation/decoding
- FastAPI dependency to get the current user
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from mswia.db import SessionLocal, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_jwt_secret() -> str:
    return os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")


def get_jwt_algorithm() -> str:
    return os.environ.get("JWT_ALGORITHM", "HS256")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    # bcrypt limits passwords to 72 bytes natively. Trim to prevent 500 crashes
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password[:72].encode('utf-8'), salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_jwt_secret(), algorithm=get_jwt_algorithm())
    return encoded_jwt


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalars().first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[get_jwt_algorithm()])
        email: str = payload.get("sub")  # type: ignore[assignment]
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    with SessionLocal() as db:
        user = get_user_by_email(db, email)
        if user is None:
            raise credentials_exception
        return user

