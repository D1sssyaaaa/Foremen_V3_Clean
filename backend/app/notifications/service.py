"""Сервис для работы с уведомлениями"""
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import TelegramNotification
from app.notifications.schemas import NotificationCreate, NotificationSendByRole
from app.models import User
from app.core.models_base import UserRole

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис уведомлений"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[dict] = None
    ) -> TelegramNotification:
        """Создать уведомление для пользователя"""
        notification = TelegramNotification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data,
            status="pending"
        )
        
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        
        logger.info(f"Created notification {notification.id} for user {user_id}")
        return notification
    
    async def send_notification_by_roles(
        self,
        roles: list[UserRole],
        notification_type: str,
        title: str,
        message: str,
        data: Optional[dict] = None,
        exclude_user_ids: Optional[list[int]] = None
    ) -> list[TelegramNotification]:
        """Отправить уведомления пользователям с указанными ролями"""
        # Получить пользователей с нужными ролями
        # Роли хранятся как JSON массив, используем contains
        from sqlalchemy.dialects.postgresql import ARRAY
        
        query = select(User).where(
            and_(
                User.telegram_chat_id.isnot(None)  # Только те, кто активировал бота
            )
        )
        
        if exclude_user_ids:
            query = query.where(User.id.notin_(exclude_user_ids))
        
        result = await self.db.execute(query)
        all_users = result.scalars().all()
        
        # Фильтруем пользователей по ролям в Python (т.к. роли - JSON массив)
        role_values = [role.value for role in roles]
        users = [u for u in all_users if any(r in role_values for r in u.roles)]
        
        # Создать уведомления
        notifications = []
        for user in users:
            notification = TelegramNotification(
                user_id=user.id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data,
                telegram_chat_id=user.telegram_chat_id,
                status="pending"
            )
            self.db.add(notification)
            notifications.append(notification)
        
        await self.db.commit()
        
        logger.info(f"Created {len(notifications)} notifications for roles {roles}")
        return notifications
    
    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> list[TelegramNotification]:
        """Получить уведомления пользователя"""
        query = select(TelegramNotification).where(
            TelegramNotification.user_id == user_id
        )
        
        if unread_only:
            query = query.where(TelegramNotification.is_read == False)
        
        query = query.order_by(TelegramNotification.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def mark_as_read(self, notification_ids: list[int], user_id: int) -> int:
        """Отметить уведомления как прочитанные"""
        query = select(TelegramNotification).where(
            and_(
                TelegramNotification.id.in_(notification_ids),
                TelegramNotification.user_id == user_id,
                TelegramNotification.is_read == False
            )
        )
        
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
        
        await self.db.commit()
        return len(notifications)
    
    async def mark_as_sent(
        self,
        notification_id: int,
        telegram_message_id: Optional[int] = None
    ):
        """Отметить уведомление как отправленное"""
        query = select(TelegramNotification).where(
            TelegramNotification.id == notification_id
        )
        result = await self.db.execute(query)
        notification = result.scalar_one_or_none()
        
        if notification:
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            if telegram_message_id:
                notification.telegram_message_id = telegram_message_id
            await self.db.commit()
    
    async def mark_as_failed(self, notification_id: int):
        """Отметить уведомление как неудачное"""
        query = select(TelegramNotification).where(
            TelegramNotification.id == notification_id
        )
        result = await self.db.execute(query)
        notification = result.scalar_one_or_none()
        
        if notification:
            notification.status = "failed"
            await self.db.commit()
    
    async def get_pending_notifications(self, limit: int = 100) -> list[TelegramNotification]:
        """Получить неотправленные уведомления"""
        query = select(TelegramNotification).where(
            TelegramNotification.status == "pending"
        ).order_by(TelegramNotification.created_at).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_notification_stats(self, user_id: int) -> dict:
        """Статистика уведомлений пользователя"""
        # Общее количество
        total_query = select(func.count()).select_from(TelegramNotification).where(
            TelegramNotification.user_id == user_id
        )
        total = await self.db.scalar(total_query)
        
        # Непрочитанные
        unread_query = select(func.count()).select_from(TelegramNotification).where(
            and_(
                TelegramNotification.user_id == user_id,
                TelegramNotification.is_read == False
            )
        )
        unread = await self.db.scalar(unread_query)
        
        # Отправленные
        sent_query = select(func.count()).select_from(TelegramNotification).where(
            and_(
                TelegramNotification.user_id == user_id,
                TelegramNotification.status == "sent"
            )
        )
        sent = await self.db.scalar(sent_query)
        
        # По типам
        by_type_query = select(
            TelegramNotification.notification_type,
            func.count()
        ).where(
            TelegramNotification.user_id == user_id
        ).group_by(TelegramNotification.notification_type)
        
        by_type_result = await self.db.execute(by_type_query)
        by_type = {row[0]: row[1] for row in by_type_result.all()}
        
        return {
            "total": total or 0,
            "unread": unread or 0,
            "unread_count": unread or 0,  # Добавлено для фронтенда
            "sent": sent or 0,
            "failed": (total or 0) - (sent or 0),
            "by_type": by_type
        }
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """Отметить все уведомления пользователя как прочитанные"""
        query = select(TelegramNotification).where(
            and_(
                TelegramNotification.user_id == user_id,
                TelegramNotification.is_read == False
            )
        )
        
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
        
        await self.db.commit()
        logger.info(f"Marked {len(notifications)} notifications as read for user {user_id}")
        return len(notifications)
    
    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Удалить уведомление пользователя"""
        query = select(TelegramNotification).where(
            and_(
                TelegramNotification.id == notification_id,
                TelegramNotification.user_id == user_id
            )
        )
        
        result = await self.db.execute(query)
        notification = result.scalar_one_or_none()
        
        if notification:
            await self.db.delete(notification)
            await self.db.commit()
            logger.info(f"Deleted notification {notification_id} for user {user_id}")
            return True
        
        return False


class TelegramNotificationSender:
    """Отправщик уведомлений через Telegram"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_notification(self, notification: TelegramNotification) -> bool:
        """Отправить уведомление в Telegram"""
        if not notification.telegram_chat_id:
            logger.warning(f"No telegram_chat_id for notification {notification.id}")
            return False
        
        try:
            import httpx
            
            text = f"<b>{notification.title}</b>\n\n{notification.message}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": notification.telegram_chat_id,
                        "text": text,
                        "parse_mode": "HTML"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    message_id = data.get("result", {}).get("message_id")
                    logger.info(f"Sent notification {notification.id} to chat {notification.telegram_chat_id}")
                    return True
                else:
                    logger.error(f"Failed to send notification {notification.id}: {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Error sending notification {notification.id}: {e}")
            return False
    
    async def send_websocket_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[dict] = None
    ):
        """
        Отправка уведомления через WebSocket
        
        Args:
            user_id: ID пользователя
            notification_type: тип уведомления
            title: заголовок
            message: текст сообщения
            data: дополнительные данные
        """
        from app.websocket.manager import manager
        from datetime import datetime
        
        notification_data = {
            "type": "notification",
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.send_personal_message(notification_data, user_id)
        logger.info(f"WebSocket notification sent to user {user_id}: {notification_type}")
    
    async def broadcast_websocket_to_roles(
        self,
        roles: list[str],
        notification_type: str,
        title: str,
        message: str,
        data: Optional[dict] = None
    ):
        """
        Broadcast уведомления через WebSocket пользователям с определёнными ролями
        
        Args:
            roles: список ролей (строки)
            notification_type: тип уведомления
            title: заголовок
            message: текст сообщения
            data: дополнительные данные
        """
        from app.websocket.manager import manager
        from datetime import datetime
        
        notification_data = {
            "type": "notification",
            "notification_type": notification_type,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.broadcast_to_roles(notification_data, roles)
        logger.info(f"WebSocket broadcast to roles {roles}: {notification_type}")
    
    async def notify_user(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "general",
        data: Optional[dict] = None,
        send_telegram: bool = True,
        send_websocket: bool = True
    ):
        """
        Универсальный метод отправки уведомления пользователю
        
        Отправляет через:
        - Telegram (если send_telegram=True и у пользователя есть telegram_chat_id)
        - WebSocket (если send_websocket=True и пользователь подключён)
        - Сохраняет в БД
        
        Args:
            user_id: ID пользователя
            title: заголовок
            message: текст сообщения
            notification_type: тип уведомления
            data: дополнительные данные
            send_telegram: отправить в Telegram
            send_websocket: отправить через WebSocket
        """
        # Создание записи в БД
        notification = await self.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data
        )
        
        # Отправка через WebSocket (если пользователь онлайн)
        if send_websocket:
            try:
                await self.send_websocket_notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    data=data
                )
            except Exception as e:
                logger.error(f"Failed to send WebSocket notification: {e}")
        
        # Отправка через Telegram (асинхронно)
        if send_telegram:
            # TODO: интеграция с Telegram ботом
            pass
        
        return notification

