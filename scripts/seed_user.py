import asyncio
from mswia.db import SessionLocal, User, init_db
from mswia.auth import get_password_hash
from sqlalchemy import select

async def seed():
    async with SessionLocal() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        if result.scalar_one_or_none():
            print("Admin user already exists.")
            return

        user = User(
            email="admin@example.com",
            hashed_password=get_password_hash("password123"),
            role="admin"
        )
        db.add(user)
        await db.commit()
        print("Admin user seeded: admin@example.com / password123")

if __name__ == "__main__":
    asyncio.run(seed())
