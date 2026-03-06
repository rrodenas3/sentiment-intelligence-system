import pytest
import pytest_asyncio
from datetime import timedelta
from jose import jwt
from mswia.auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_jwt_secret, get_jwt_algorithm
)
from mswia.db import User
from sqlalchemy import select

def test_password_hashing():
    password = "super-secret-pw"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-pw", hashed) is False

def test_create_access_token():
    data = {"sub": "test@example.com"}
    token = create_access_token(data, expires_delta=timedelta(minutes=15))
    payload = jwt.decode(token, get_jwt_secret(), algorithms=[get_jwt_algorithm()])
    assert payload["sub"] == "test@example.com"
    assert "exp" in payload

@pytest.mark.asyncio
async def test_get_current_user_valid(db_session):
    # Seed user
    email = "current_user@test.com"
    pw_hash = get_password_hash("password")
    user = User(email=email, hashed_password=pw_hash)
    db_session.add(user)
    await db_session.commit()
    
    token = create_access_token(data={"sub": email})
    retrieved_user = await get_current_user(token=token, db=db_session)
    assert retrieved_user.email == email

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db_session):
    with pytest.raises(Exception): # Credentials exception
        await get_current_user(token="invalid-token", db=db_session)
