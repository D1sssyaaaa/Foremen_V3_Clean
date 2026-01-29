"""Создание тестового пользователя для веб-интерфейса"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "sqlite+aiosqlite:///./construction_costs.db"

async def create_test_user():
    """Создает тестового пользователя"""
    from app.models import User
    from app.auth.security import get_password_hash
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Проверяем, есть ли уже пользователь
        result = await session.execute(
            text("SELECT id FROM users WHERE username = 'd1syaaaa'")
        )
        existing = result.fetchone()
        
        if existing:
            print("✅ Пользователь d1syaaaa уже существует!")
            return
        
        # Создаем нового пользователя
        user = User(
            username='d1syaaaa',
            phone='+79999999999',
            email='test@test.com',
            hashed_password=get_password_hash('12345678'),
            roles=['MANAGER', 'ADMIN'],
            telegram_chat_id=2032392401,
            is_active=True,
            full_name='Тестовый Менеджер'
        )
        
        session.add(user)
        await session.commit()
        
        print("✅ Пользователь успешно создан!")
        print("\n📝 Данные для входа:")
        print(f"   Username: d1syaaaa")
        print(f"   Password: 12345678")
        print(f"   Roles: MANAGER, ADMIN")

if __name__ == "__main__":
    asyncio.run(create_test_user())
