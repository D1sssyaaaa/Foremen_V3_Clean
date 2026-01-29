"""Простой тест логина"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import User
from app.auth.security import create_access_token, create_refresh_token
import json

async def test_login():
    # Подключение к БД
    engine = create_async_engine("sqlite+aiosqlite:///./construction_costs.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Поиск пользователя
        result = await db.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User not found")
            return
        
        print(f"✅ User found: {user.username}, id={user.id}, type={type(user.id)}")
        print(f"   Roles (raw): {user.roles}, type={type(user.roles)}")
        
        # Парсинг ролей
        roles = user.roles if isinstance(user.roles, list) else json.loads(user.roles) if isinstance(user.roles, str) else []
        print(f"   Roles (parsed): {roles}")
        
        # Создание токенов
        try:
            user_id_str = str(user.id)
            print(f"   Creating tokens for user_id_str: {user_id_str}")
            
            access_token = create_access_token(data={"sub": user_id_str, "roles": roles})
            refresh_token = create_refresh_token(data={"sub": user_id_str})
            
            print(f"✅ Access token created (first 50 chars): {access_token[:50]}...")
            print(f"✅ Refresh token created (first 50 chars): {refresh_token[:50]}...")
            
        except Exception as e:
            print(f"❌ Error creating tokens: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_login())
