"""Background worker для отправки Telegram уведомлений"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.notifications.models import TelegramNotification

logger = logging.getLogger(__name__)


class NotificationWorker:
    """Worker для отправки уведомлений через Telegram"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.engine = create_async_engine(settings.database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.is_running = False
        self.retry_delay = 60  # Повтор через 60 секунд для failed
        self.max_retries = 3
        
    async def start(self):
        """Запуск worker"""
        self.is_running = True
        logger.info("🚀 Notification Worker started")
        
        while self.is_running:
            try:
                await self._process_pending_notifications()
            except Exception as e:
                logger.error(f"❌ Worker error: {e}", exc_info=True)
            
            await asyncio.sleep(5)  # Проверка каждые 5 секунд
    
    async def stop(self):
        """Остановка worker"""
        self.is_running = False
        await self.engine.dispose()
        logger.info("🛑 Notification Worker stopped")
    
    async def _process_pending_notifications(self):
        """Обработка pending уведомлений"""
        async with self.async_session() as db:
            # Получить pending уведомления
            query = select(TelegramNotification).where(
                and_(
                    TelegramNotification.status == "pending",
                    TelegramNotification.telegram_chat_id.isnot(None)
                )
            ).limit(50)
            
            result = await db.execute(query)
            notifications = result.scalars().all()
            
            if not notifications:
                return
            
            logger.info(f"📬 Processing {len(notifications)} pending notifications")
            
            for notif in notifications:
                try:
                    await self._send_notification(notif)
                    notif.status = "sent"
                    notif.sent_at = datetime.now()
                    logger.info(f"✅ Sent notification {notif.id} to user {notif.user_id}")
                    
                except Exception as e:
                    # Увеличиваем счетчик попыток
                    retry_count = notif.data.get("retry_count", 0) if notif.data else 0
                    retry_count += 1
                    
                    if retry_count >= self.max_retries:
                        notif.status = "failed"
                        logger.error(
                            f"❌ Failed to send notification {notif.id} after {retry_count} retries: {e}"
                        )
                    else:
                        # Сохраняем счетчик попыток
                        if not notif.data:
                            notif.data = {}
                        notif.data["retry_count"] = retry_count
                        notif.data["last_error"] = str(e)
                        logger.warning(
                            f"⚠️ Failed to send notification {notif.id}, retry {retry_count}/{self.max_retries}: {e}"
                        )
            
            await db.commit()
    
    async def _send_notification(self, notif: TelegramNotification):
        """Отправка одного уведомления"""
        text = self._format_notification(notif)
        
        # Отправка через Telegram Bot API
        await self.bot.send_message(
            chat_id=notif.telegram_chat_id,
            text=text,
            parse_mode="HTML"
        )
    
    def _format_notification(self, notif: TelegramNotification) -> str:
        """Форматирование текста уведомления"""
        # Получаем данные
        data = notif.data or {}
        
        # Формируем сообщение
        text = f"<b>{notif.title}</b>\n\n"
        text += f"{notif.message}"
        
        # Добавляем дополнительные данные если есть
        if "object_name" in data:
            text += f"\n\n🏗 <b>Объект:</b> {data['object_name']}"
        
        if "urgency" in data:
            urgency_emoji = {"critical": "🔴", "urgent": "🟠", "high": "🟡", "medium": "🟢", "low": "⚪"}
            emoji = urgency_emoji.get(data["urgency"], "")
            text += f"\n{emoji} <b>Срочность:</b> {data['urgency']}"
        
        if "amount" in data:
            text += f"\n💰 <b>Сумма:</b> {data['amount']} руб."
        
        # Добавляем время
        text += f"\n\n🕐 {notif.created_at.strftime('%d.%m.%Y %H:%M')}"
        
        return text


async def start_notification_worker(bot: Bot) -> NotificationWorker:
    """Запуск worker в фоновой задаче"""
    worker = NotificationWorker(bot)
    asyncio.create_task(worker.start())
    return worker
