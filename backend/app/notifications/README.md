# Модуль Уведомлений

## Описание
Система уведомлений через Telegram с историей и ролевой рассылкой.

## Функции

### Для всех пользователей:
- ✅ Получение своих уведомлений
- ✅ Фильтрация (непрочитанные)
- ✅ Отметка как прочитанное
- ✅ Статистика уведомлений

### Для MANAGER/ADMIN:
- ✅ Создание уведомлений для пользователя
- ✅ Рассылка по ролям
- ✅ Просмотр неотправленных (только ADMIN)

## API Endpoints

### GET /api/v1/notifications
Получить свои уведомления
- Query: `unread_only`, `limit`, `offset`
- Response: `List[NotificationResponse]`

### GET /api/v1/notifications/stats
Статистика уведомлений
- Response: `NotificationStats` (total, unread, sent, failed, by_type)

### POST /api/v1/notifications/mark-read
Отметить как прочитанные
- Body: `NotificationMarkRead` (notification_ids)
- Response: 204 No Content

### POST /api/v1/notifications/send
Создать уведомление для пользователя
- Access: MANAGER, ADMIN
- Body: `NotificationCreate`
- Response: `NotificationResponse`

### POST /api/v1/notifications/send-by-role
Рассылка по ролям
- Access: MANAGER, ADMIN
- Body: `NotificationSendByRole`
- Response: `{"created": int, "roles": list, "notification_type": str}`

### GET /api/v1/notifications/pending
Неотправленные уведомления
- Access: только ADMIN
- Response: `List[NotificationResponse]`

## Типы уведомлений

```python
# Заявки на материалы
"material_request_created"       # Новая заявка (→ MATERIALS_MANAGER)
"material_request_approved"      # Согласована (→ FOREMAN)
"material_request_rejected"      # Отклонена (→ FOREMAN)
"material_request_delivered"     # Поставлено (→ FOREMAN)

# Заявки на технику
"equipment_order_created"        # Новая заявка (→ EQUIPMENT_MANAGER)
"equipment_order_approved"       # Утверждена (→ FOREMAN)
"equipment_order_rejected"       # Отклонена (→ FOREMAN)

# Табели РТБ
"timesheet_submitted"            # Подан (→ HR_MANAGER)
"timesheet_approved"             # Утвержден (→ FOREMAN)
"timesheet_rejected"             # Отклонен (→ FOREMAN)

# УПД
"upd_uploaded"                   # Загружен (→ MATERIALS_MANAGER)
"upd_distributed"                # Распределен (→ ACCOUNTANT)

# Системные
"system_notification"            # Системное (→ ALL)
"urgent_notification"            # Срочное (→ CUSTOM)
```

## Схема БД

```sql
CREATE TABLE telegram_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSON,  -- дополнительные данные
    
    is_read BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, sent, failed
    
    telegram_message_id INTEGER,
    telegram_chat_id INTEGER,
    
    created_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    read_at TIMESTAMP
);

-- Индексы
CREATE INDEX ix_telegram_notifications_user_id ON telegram_notifications(user_id);
CREATE INDEX ix_telegram_notifications_is_read ON telegram_notifications(is_read);
CREATE INDEX ix_telegram_notifications_status ON telegram_notifications(status);
CREATE INDEX ix_telegram_notifications_user_unread ON telegram_notifications(user_id, is_read, created_at);
```

## Примеры использования

### Создание уведомления
```python
from app.notifications.service import NotificationService

service = NotificationService(db)

notification = await service.create_notification(
    user_id=123,
    notification_type="material_request_approved",
    title="Заявка утверждена",
    message="Ваша заявка MR-2026-001 утверждена к закупке",
    data={"request_id": 1, "request_number": "MR-2026-001"}
)
```

### Рассылка по ролям
```python
notifications = await service.send_notification_by_roles(
    roles=[UserRole.FOREMAN],
    notification_type="urgent_notification",
    title="Срочно: изменение графика",
    message="Завтра работы на объекте Северный переносятся на 2 часа",
    exclude_user_ids=[456]  # Исключить конкретных пользователей
)
```

### Отправка через Telegram
```python
from app.notifications.service import TelegramNotificationSender

sender = TelegramNotificationSender(bot_token=config.TELEGRAM_BOT_TOKEN)

# Получить неотправленные
pending = await service.get_pending_notifications(limit=100)

# Отправить
for notification in pending:
    success = await sender.send_notification(notification)
    
    if success:
        await service.mark_as_sent(notification.id)
    else:
        await service.mark_as_failed(notification.id)
```

## Интеграция с бизнес-логикой

### При создании заявки на материалы
```python
# В materials/router.py после создания заявки:
from app.notifications.service import NotificationService

notification_service = NotificationService(db)

# Уведомить MATERIALS_MANAGER
await notification_service.send_notification_by_roles(
    roles=[UserRole.MATERIALS_MANAGER],
    notification_type="material_request_created",
    title="Новая заявка на материалы",
    message=f"Создана заявка {request.id} на объект {request.cost_object.name}",
    data={"request_id": request.id}
)
```

### При утверждении табеля
```python
# Уведомить бригадира
await notification_service.create_notification(
    user_id=timesheet.brigade.foreman_id,
    notification_type="timesheet_approved",
    title="Табель утвержден",
    message=f"Табель за период {timesheet.period_start} - {timesheet.period_end} утвержден",
    data={"timesheet_id": timesheet.id, "amount": str(timesheet.total_amount)}
)
```

## Фоновая отправка

Для production рекомендуется использовать фоновые задачи:

```python
# background_tasks.py
import asyncio
from app.notifications.service import NotificationService, TelegramNotificationSender
from app.core.config import settings

async def send_pending_notifications():
    """Отправка неотправленных уведомлений (запуск каждые 10 секунд)"""
    while True:
        async with get_db() as db:
            service = NotificationService(db)
            sender = TelegramNotificationSender(settings.TELEGRAM_BOT_TOKEN)
            
            pending = await service.get_pending_notifications(limit=50)
            
            for notification in pending:
                success = await sender.send_notification(notification)
                
                if success:
                    await service.mark_as_sent(notification.id)
                else:
                    await service.mark_as_failed(notification.id)
        
        await asyncio.sleep(10)
```

## Тестирование

```python
# tests/test_notifications.py
import pytest
from app.notifications.service import NotificationService
from app.core.models_base import UserRole

@pytest.mark.asyncio
async def test_send_by_role(db_session):
    service = NotificationService(db_session)
    
    notifications = await service.send_notification_by_roles(
        roles=[UserRole.FOREMAN],
        notification_type="test",
        title="Test",
        message="Test message"
    )
    
    assert len(notifications) > 0
    assert all(n.status == "pending" for n in notifications)
```

## TODO
- [ ] Webhook для Telegram (вместо polling в боте)
- [ ] Web Push уведомления (для фронтенда)
- [ ] Email уведомления (опционально)
- [ ] Шаблоны уведомлений
- [ ] Группировка уведомлений
- [ ] Настройки пользователей (какие типы получать)
