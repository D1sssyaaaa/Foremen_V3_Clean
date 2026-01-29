"""Схемы для модуля уведомлений"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.core.models_base import UserRole


class NotificationCreate(BaseModel):
    """Создание уведомления"""
    user_id: int = Field(description="ID получателя")
    notification_type: str = Field(description="Тип уведомления")
    title: str = Field(description="Заголовок")
    message: str = Field(description="Текст сообщения")
    data: Optional[dict] = Field(None, description="Дополнительные данные JSON")


class NotificationSendByRole(BaseModel):
    """Отправка уведомлений по ролям"""
    roles: list[UserRole] = Field(description="Список ролей получателей")
    notification_type: str = Field(description="Тип уведомления")
    title: str = Field(description="Заголовок")
    message: str = Field(description="Текст сообщения")
    data: Optional[dict] = Field(None, description="Дополнительные данные")
    exclude_user_ids: Optional[list[int]] = Field(None, description="Исключить пользователей")


class NotificationResponse(BaseModel):
    """Уведомление"""
    id: int
    user_id: int
    notification_type: str
    title: str
    message: str
    data: Optional[dict]
    is_read: bool
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    telegram_message_id: Optional[int]
    status: str  # pending, sent, failed
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListItem(BaseModel):
    """Элемент списка уведомлений"""
    id: int
    notification_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationMarkRead(BaseModel):
    """Отметить как прочитанное"""
    notification_ids: list[int] = Field(description="ID уведомлений")


class NotificationStats(BaseModel):
    """Статистика уведомлений"""
    total: int
    unread: int
    sent: int
    failed: int
    by_type: dict[str, int]
