"""
Базовые модели SQLAlchemy
Роли, статусы, общие поля
"""
from sqlalchemy import Column, Integer, DateTime, String, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum


class UserRole(str, PyEnum):
    """Роли пользователей"""
    FOREMAN = "FOREMAN"  # Бригадир
    ACCOUNTANT = "ACCOUNTANT"  # Бухгалтер
    HR_MANAGER = "HR_MANAGER"  # Менеджер по персоналу
    EQUIPMENT_MANAGER = "EQUIPMENT_MANAGER"  # Менеджер по технике
    MATERIALS_MANAGER = "MATERIALS_MANAGER"  # Менеджер по снабжению
    PROCUREMENT_MANAGER = "PROCUREMENT_MANAGER"  # Менеджер по закупкам
    MANAGER = "MANAGER"  # Руководитель
    ADMIN = "ADMIN"  # Администратор





class EquipmentOrderStatus(str, PyEnum):
    """Статусы заявок на технику"""
    NEW = "НОВАЯ"
    APPROVED = "УТВЕРЖДЕНА"
    IN_PROGRESS = "В РАБОТЕ"
    COMPLETED = "ЗАВЕРШЕНА"
    CANCEL_REQUESTED = "ОТМЕНА ЗАПРОШЕНА"
    CANCELLED = "ОТМЕНЕНА"


class MaterialType(str, PyEnum):
    """Типы материалов"""
    REGULAR = "regular"  # Обычные материалы (кабель, крепеж, etc)
    INERT = "inert"      # Инертные материалы (песок, щебень, ПГС)


class MaterialRequestStatus(str, PyEnum):
    """Статусы заявок на материалы"""
    NEW = "НОВАЯ"
    APPROVED = "НА СОГЛАСОВАНИИ"  # Согласована, ждёт обработки
    IN_PROCESSING = "В ОБРАБОТКЕ"
    ORDERED = "ЗАКАЗАНО"
    PARTIALLY_DELIVERED = "ЧАСТИЧНО ПОСТАВЛЕНО"
    SHIPPED = "ОТГРУЖЕНО"
    COMPLETED = "ВЫПОЛНЕНА"
    REJECTED = "ОТКЛОНЕНА"


class UPDStatus(str, PyEnum):
    """Статусы УПД"""
    NEW = "NEW"
    DISTRIBUTED = "DISTRIBUTED"
    ARCHIVED = "ARCHIVED"
    DUPLICATE = "DUPLICATE"  # Дубликат (уже загружен)


class ObjectStatus(str, PyEnum):
    """Статусы объектов учёта"""
    ACTIVE = "Активен"
    CLOSING = "Готовится к закрытию"
    CLOSED = "Закрыт"
    ARCHIVED = "Архив"


class RegistrationRequestStatus(str, PyEnum):
    """Статусы заявок на регистрацию"""
    PENDING = "PENDING"      # Ожидает рассмотрения
    APPROVED = "APPROVED"    # Одобрена
    REJECTED = "REJECTED"    # Отклонена



class ObjectAccessRequestStatus(str, PyEnum):
    """Статусы запросов доступа к объектам"""
    PENDING = "PENDING"      # Ожидает рассмотрения
    APPROVED = "APPROVED"    # Одобрена
    REJECTED = "REJECTED"    # Отклонена


class TimeSheetStatus(str, PyEnum):
    """Статусы табелей рабочего времени"""
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    CORRECTED = "CORRECTED"
    CANCELLED = "CANCELLED"



class TimestampMixin:
    """Миксин для добавления временных меток"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
