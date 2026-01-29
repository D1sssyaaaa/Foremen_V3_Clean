"""Модуль уведомлений"""

__version__ = "1.0.0"

from .service import NotificationService, TelegramNotificationSender
from .schemas import NotificationCreate, NotificationSendByRole, NotificationResponse
from .router import router

__all__ = [
    "NotificationService",
    "TelegramNotificationSender",
    "NotificationCreate",
    "NotificationSendByRole",
    "NotificationResponse",
    "router"
]
