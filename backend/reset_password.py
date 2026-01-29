"""Сброс пароля пользователя"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "sqlite+aiosqlite:///./construction_costs.db"

async def reset_password():
    """Сброс пароля пользователя d1syaaaa"""
    from app.auth.security import get_password_hash
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Обновляем пароль
        new_password_hash = get_password_hash('12345678')
        
        await session.execute(
            text("UPDATE users SET hashed_password = :password WHERE username = 'd1syaaaa'"),
            {"password": new_password_hash}
        )
        await session.commit()
        
        print("✅ Пароль успешно сброшен!")
        print("\n📝 Данные для входа:")
        print(f"   Username: d1syaaaa")
        print(f"   Password: 12345678")

if __name__ == "__main__":
    asyncio.run(reset_password())
