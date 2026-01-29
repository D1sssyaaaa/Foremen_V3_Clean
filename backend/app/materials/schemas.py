"""Схемы данных для модуля заявок на материалы"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class MaterialType(str, Enum):
    """Типы материалов"""
    REGULAR = "regular"  # Обычные материалы
    INERT = "inert"      # Инертные материалы (песок, щебень, ПГС)


class MaterialRequestItemCreate(BaseModel):
    """Позиция в заявке на материалы"""
    material_name: str = Field(description="Название материала")
    quantity: Decimal = Field(description="Количество", gt=0)
    unit: str = Field(description="Единица измерения")
    description: Optional[str] = Field(None, description="Описание")


class MaterialRequestCreate(BaseModel):
    """Создание заявки на материалы"""
    cost_object_id: int = Field(description="ID объекта учета")
    material_type: MaterialType = Field(MaterialType.REGULAR, description="Тип материалов")
    urgency: str = Field(description="Срочность: normal, urgent, critical")
    expected_delivery_date: Optional[date] = Field(None, description="Требуемая дата поставки")
    delivery_time: Optional[str] = Field(None, description="Желаемое время доставки (обязательно для инертных)")
    items: List[MaterialRequestItemCreate] = Field(description="Позиции заявки", min_items=1)
    comment: Optional[str] = Field(None, description="Комментарий")


class MaterialRequestItemResponse(BaseModel):
    """Позиция заявки"""
    id: int
    material_name: str
    quantity: Decimal
    unit: str
    description: Optional[str]
    distributed_quantity: Decimal
    remaining_quantity: Decimal

    class Config:
        from_attributes = True


class MaterialRequestResponse(BaseModel):
    """Заявка на материалы"""
    id: int
    cost_object_id: int
    cost_object_name: str
    foreman_id: int
    foreman_name: str
    status: str
    material_type: str = "regular"
    urgency: str
    expected_delivery_date: Optional[date] = None
    delivery_time: Optional[str] = None
    comment: Optional[str]
    items: List[MaterialRequestItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MaterialRequestListItem(BaseModel):
    """Элемент списка заявок"""
    id: int
    cost_object_name: str
    foreman_name: str
    status: str
    urgency: str
    expected_delivery_date: Optional[date] = None
    items_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class MaterialRequestApproveRequest(BaseModel):
    """Запрос на согласование заявки"""
    comment: Optional[str] = Field(None, description="Комментарий менеджера")


class MaterialRequestProcessRequest(BaseModel):
    """Запрос на взятие заявки в обработку"""
    expected_delivery_date: Optional[date] = Field(None, description="Планируемая дата доставки")


class MaterialRequestOrderRequest(BaseModel):
    """Запрос на размещение заказа"""
    supplier: str = Field(description="Поставщик")
    order_number: Optional[str] = Field(None, description="Номер заказа")
    comment: Optional[str] = Field(None, description="Комментарий")


class MaterialRequestRejectRequest(BaseModel):
    """Запрос на отклонение заявки"""
    reason: str = Field(description="Причина отклонения")
