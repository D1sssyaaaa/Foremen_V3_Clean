import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.auth.security import get_password_hash

DATABASE_URL = "sqlite+aiosqlite:///./construction_costs.db"

async def reset_admin():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        new_password_hash = get_password_hash('admin123')
        
        # Check if admin exists
        result = await session.execute(text("SELECT id FROM users WHERE username = 'admin'"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User 'admin' not found!")
            return

        print(f"Found user 'admin' with ID: {user}")

        await session.execute(
            text("UPDATE users SET hashed_password = :password WHERE username = 'admin'"),
            {"password": new_password_hash}
        )
        await session.commit()
        
        print("✅ Password for 'admin' reset to 'admin'")

if __name__ == "__main__":
    asyncio.run(reset_admin())
