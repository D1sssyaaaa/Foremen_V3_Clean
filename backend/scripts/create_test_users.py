"""
Скрипт создания тестовых пользователей для разработки
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import *  # Импортируем все модели для корректной инициализации relationships
from app.notifications.models import TelegramNotification  # Добавляем модель уведомлений
from app.auth.security import get_password_hash


async def create_test_users():
    """Создание тестовых пользователей"""
    print("👥 Создание тестовых пользователей...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Проверяем, есть ли уже пользователи
            result = await session.execute(select(User))
            existing_users = result.scalars().all()
            
            if existing_users:
                print(f"⚠️  Найдено {len(existing_users)} пользователей в БД")
                response = input("Удалить существующих пользователей? (yes/no): ")
                if response.lower() == 'yes':
                    for user in existing_users:
                        await session.delete(user)
                    await session.commit()
                    print("🗑️  Существующие пользователи удалены")
                else:
                    print("❌ Отменено")
                    return
            
            # Создаём тестовых пользователей
            test_users = [
                {
                    "username": "admin",
                    "phone": "+79991111111",
                    "email": "admin@example.com",
                    "password": "admin123",
                    "roles": ["ADMIN", "MANAGER"],
                    "full_name": "Администратор Системы",
                    "is_active": True
                },
                {
                    "username": "manager",
                    "phone": "+79991111112",
                    "email": "manager@example.com",
                    "password": "manager123",
                    "roles": ["MANAGER"],
                    "full_name": "Менеджер Проектов",
                    "is_active": True
                },
                {
                    "username": "accountant",
                    "phone": "+79991111113",
                    "email": "accountant@example.com",
                    "password": "accountant123",
                    "roles": ["ACCOUNTANT"],
                    "full_name": "Главный Бухгалтер",
                    "is_active": True
                },
                {
                    "username": "foreman",
                    "phone": "+79991111114",
                    "email": "foreman@example.com",
                    "password": "foreman123",
                    "roles": ["FOREMAN"],
                    "full_name": "Бригадир Иванов И.И.",
                    "is_active": True
                },
                {
                    "username": "hr_manager",
                    "phone": "+79991111115",
                    "email": "hr@example.com",
                    "password": "hr123",
                    "roles": ["HR_MANAGER"],
                    "full_name": "Менеджер по персоналу",
                    "is_active": True
                },
                {
                    "username": "materials_manager",
                    "phone": "+79991111116",
                    "email": "materials@example.com",
                    "password": "materials123",
                    "roles": ["MATERIALS_MANAGER"],
                    "full_name": "Менеджер по материалам",
                    "is_active": True
                },
                {
                    "username": "equipment_manager",
                    "phone": "+79991111117",
                    "email": "equipment@example.com",
                    "password": "equipment123",
                    "roles": ["EQUIPMENT_MANAGER"],
                    "full_name": "Менеджер по технике",
                    "is_active": True
                }
            ]
            
            created_count = 0
            for user_data in test_users:
                password = user_data.pop("password")
                user = User(
                    **user_data,
                    hashed_password=get_password_hash(password)
                )
                session.add(user)
                created_count += 1
                print(f"   ✓ {user.username} ({', '.join(user.roles)})")
            
            await session.commit()
            print(f"\n✅ Создано пользователей: {created_count}")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return
            
        # Выводим информацию для входа
        print("\n" + "="*60)
        print("📋 УЧЁТНЫЕ ДАННЫЕ ДЛЯ ТЕСТИРОВАНИЯ")
        print("="*60)
        for user_data in test_users:
            password = "admin123" if user_data["username"] == "admin" else f"{user_data['username']}123"
            print(f"\n{user_data['full_name']}")
            print(f"  Логин:    {user_data['username']}")
            print(f"  Пароль:   {password}")
            print(f"  Роли:     {', '.join(user_data['roles'])}")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(create_test_users())
