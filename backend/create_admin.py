"""
Скрипт для создания первого пользователя-администратора
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.models import User
from app.auth.security import get_password_hash
from app.core.config import settings
from app.core.models_base import UserRole


async def create_admin_user():
    """Создание администратора по умолчанию"""
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            admin = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                phone="+7-900-000-00-00",
                full_name="Системный администратор",
                email="admin@construction.local",
                roles=[UserRole.ADMIN.value, UserRole.MANAGER.value],
                is_active=True
            )
            
            session.add(admin)
            await session.commit()
            
            print("✅ Администратор создан успешно!")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Роли: ADMIN, MANAGER")
            
        except Exception as e:
            print(f"❌ Ошибка при создании администратора: {e}")
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_admin_user())
