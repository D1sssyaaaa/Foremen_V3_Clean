"""
Скрипт для создания тестовых уведомлений
Уведомления будут реально отправлены воркером в Telegram
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime
import json

DATABASE_URL = "sqlite+aiosqlite:///./construction_costs.db"

async def create_test_notifications():
    """Создает тестовые уведомления для проверки системы"""
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Проверяем пользователя с telegram_chat_id
        result = await session.execute(
            text("SELECT id, username, telegram_chat_id FROM users WHERE telegram_chat_id IS NOT NULL LIMIT 1")
        )
        user = result.fetchone()
        
        if not user:
            print("❌ Нет пользователей с привязанным Telegram!")
            return
        
        user_id, username, chat_id = user
        print(f"✅ Найден пользователь: {username} (ID: {user_id}, Chat ID: {chat_id})")
        
        # Создаем тестовые уведомления разных типов
        test_notifications = [
            {
                "user_id": user_id,
                "notification_type": "material_request_created",
                "title": "📦 Новая заявка на материалы",
                "message": "Бригадир Иванов создал заявку на материалы для объекта 'ЖК Солнечный'",
                "data": json.dumps({
                    "request_id": 1,
                    "object_name": "ЖК Солнечный",
                    "foreman": "Иванов И.И.",
                    "items_count": 5
                })
            },
            {
                "user_id": user_id,
                "notification_type": "equipment_order_created",
                "title": "🚜 Новая заявка на технику",
                "message": "Бригадир Петров запросил погрузчик для объекта 'БЦ Северный'",
                "data": json.dumps({
                    "order_id": 1,
                    "equipment_type": "loader",
                    "object_name": "БЦ Северный",
                    "foreman": "Петров П.П.",
                    "period": "1-15 фев"
                })
            },
            {
                "user_id": user_id,
                "notification_type": "timesheet_submitted",
                "title": "⏰ Табель на проверку",
                "message": "Табель бригады №3 за период 20-26 янв отправлен на проверку",
                "data": json.dumps({
                    "timesheet_id": 1,
                    "brigade_name": "Бригада №3",
                    "period": "20-26 янв",
                    "total_hours": 240,
                    "members_count": 6
                })
            },
            {
                "user_id": user_id,
                "notification_type": "material_request_approved",
                "title": "✅ Заявка согласована",
                "message": "Ваша заявка на материалы №15 согласована менеджером",
                "data": json.dumps({
                    "request_id": 15,
                    "object_name": "ЖК Солнечный",
                    "approved_by": "Сидоров С.С."
                })
            },
            {
                "user_id": user_id,
                "notification_type": "materials_ordered",
                "title": "🚚 Материалы заказаны",
                "message": "Материалы по заявке №15 заказаны у поставщика 'СтройСнаб'",
                "data": json.dumps({
                    "request_id": 15,
                    "supplier": "СтройСнаб",
                    "delivery_date": "1 фев"
                })
            }
        ]
        
        # Вставляем уведомления в БД
        for notif in test_notifications:
            await session.execute(
                text("""
                    INSERT INTO telegram_notifications 
                    (user_id, notification_type, title, message, data, status, telegram_chat_id, created_at)
                    VALUES (:user_id, :notification_type, :title, :message, :data, 'pending', :chat_id, :created_at)
                """),
                {
                    **notif,
                    "chat_id": chat_id,
                    "created_at": datetime.now()
                }
            )
        
        await session.commit()
        
        print(f"\n✅ Создано {len(test_notifications)} тестовых уведомлений!")
        print("📬 Уведомления будут отправлены воркером в течение 5 секунд...")
        print("\nСписок уведомлений:")
        for i, notif in enumerate(test_notifications, 1):
            print(f"{i}. {notif['title']}")
        
        # Показываем статистику
        result = await session.execute(
            text("SELECT COUNT(*) FROM telegram_notifications WHERE status = 'pending'")
        )
        pending_count = result.scalar()
        print(f"\n📊 Всего в очереди: {pending_count} уведомлений")

if __name__ == "__main__":
    asyncio.run(create_test_notifications())
