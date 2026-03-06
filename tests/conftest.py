import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from mswia.db import Base, SessionLocal, get_database_url
from mswia.redis_client import get_redis_url
from redis import Redis

# Use a test database if provided in env, else fallback to dev
TEST_DATABASE_URL = get_database_url() + "_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL.replace("postgresql+psycopg://", "postgresql+asyncpg://"))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine):
    TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def test_redis():
    client = Redis.from_url(get_redis_url(), decode_responses=True)
    # Caution: this might flush the dev redis if not careful
    # For CI, we'd use a dedicated redis container
    yield client
    client.close()
