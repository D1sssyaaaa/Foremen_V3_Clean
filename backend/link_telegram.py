"""
Скрипт для привязки Telegram ID к пользователям
"""
import asyncio
from sqlalchemy import select
from app.core.database import async_session
from app.models import User


async def link_telegram_id():
    """Привязать Telegram ID к пользователю"""
    print("=" * 50)
    print("🔗 Привязка Telegram ID к пользователю")
    print("=" * 50)
    
    async with async_session() as session:
        # Получаем всех пользователей
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("\n❌ Пользователи не найдены в базе данных")
            return
        
        # Показываем список пользователей
        print("\n📋 Список пользователей:")
        for i, user in enumerate(users, 1):
            telegram_status = f"✅ {user.telegram_chat_id}" if user.telegram_chat_id else "❌ Не привязан"
            print(f"{i}. {user.username} ({user.full_name}) - Telegram: {telegram_status}")
        
        # Выбираем пользователя
        try:
            choice = int(input("\nВыберите номер пользователя: ")) - 1
            if choice < 0 or choice >= len(users):
                print("❌ Неверный номер")
                return
        except ValueError:
            print("❌ Введите число")
            return
        
        selected_user = users[choice]
        
        print(f"\n📝 Выбран пользователь: {selected_user.username} ({selected_user.full_name})")
        
        # Получаем Telegram ID
        telegram_id = input("\nВведите Telegram ID (получите у @userinfobot): ").strip()
        
        if not telegram_id.isdigit():
            print("❌ Telegram ID должен быть числом")
            return
        
        telegram_id = int(telegram_id)
        
        # Обновляем пользователя
        selected_user.telegram_chat_id = telegram_id
        await session.commit()
        
        print(f"\n✅ Telegram ID {telegram_id} успешно привязан к пользователю {selected_user.username}")
        print(f"\n📱 Теперь пользователь может использовать бота в Telegram!")
        print(f"   1. Найдите бота в Telegram")
        print(f"   2. Отправьте команду /start")
        print(f"   3. Готово! Бот готов к использованию")


async def show_linked_users():
    """Показать всех пользователей с привязанным Telegram"""
    print("=" * 50)
    print("📱 Пользователи с привязанным Telegram")
    print("=" * 50)
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_chat_id.isnot(None))
        )
        users = result.scalars().all()
        
        if not users:
            print("\n❌ Нет пользователей с привязанным Telegram")
            return
        
        print()
        for user in users:
            print(f"✅ {user.username} ({user.full_name})")
            print(f"   Telegram ID: {user.telegram_chat_id}")
            print(f"   Роли: {', '.join(user.roles)}")
            print()


async def unlink_telegram_id():
    """Отвязать Telegram ID от пользователя"""
    print("=" * 50)
    print("🔓 Отвязка Telegram ID от пользователя")
    print("=" * 50)
    
    async with async_session() as session:
        # Получаем пользователей с Telegram
        result = await session.execute(
            select(User).where(User.telegram_chat_id.isnot(None))
        )
        users = result.scalars().all()
        
        if not users:
            print("\n❌ Нет пользователей с привязанным Telegram")
            return
        
        # Показываем список
        print("\n📋 Пользователи с Telegram:")
        for i, user in enumerate(users, 1):
            print(f"{i}. {user.username} ({user.full_name}) - Telegram ID: {user.telegram_chat_id}")
        
        # Выбираем пользователя
        try:
            choice = int(input("\nВыберите номер пользователя: ")) - 1
            if choice < 0 or choice >= len(users):
                print("❌ Неверный номер")
                return
        except ValueError:
            print("❌ Введите число")
            return
        
        selected_user = users[choice]
        
        # Подтверждение
        confirm = input(f"\nВы уверены, что хотите отвязать Telegram от {selected_user.username}? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Отменено")
            return
        
        # Отвязываем
        selected_user.telegram_chat_id = None
        await session.commit()
        
        print(f"\n✅ Telegram ID отвязан от пользователя {selected_user.username}")


async def main():
    """Главное меню"""
    while True:
        print("\n" + "=" * 50)
        print("🤖 Управление Telegram привязками")
        print("=" * 50)
        print("\n1. Привязать Telegram ID к пользователю")
        print("2. Показать пользователей с Telegram")
        print("3. Отвязать Telegram ID")
        print("4. Выход")
        
        choice = input("\nВыберите действие: ").strip()
        
        if choice == "1":
            await link_telegram_id()
        elif choice == "2":
            await show_linked_users()
        elif choice == "3":
            await unlink_telegram_id()
        elif choice == "4":
            print("\n👋 До свидания!")
            break
        else:
            print("\n❌ Неверный выбор")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 До свидания!")
