"""Модели для уведомлений"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class TelegramNotification(Base):
    """История Telegram уведомлений"""
    __tablename__ = "telegram_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Дополнительные данные
    
    # Статус
    is_read = Column(Boolean, default=False, index=True)
    status = Column(String(20), default="pending", index=True)  # pending, sent, failed
    
    # Telegram специфика
    telegram_message_id = Column(Integer, nullable=True)
    telegram_chat_id = Column(Integer, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<TelegramNotification {self.id}: {self.notification_type} to user {self.user_id}>"
