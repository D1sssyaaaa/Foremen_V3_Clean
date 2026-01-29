"""Схемы данных для модуля аренды техники"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class EquipmentOrderCreate(BaseModel):
    """Создание заявки на технику"""
    cost_object_id: int = Field(description="ID объекта учета")
    equipment_type: str = Field(description="Тип техники")
    start_date: date = Field(description="Дата начала аренды")
    end_date: date = Field(description="Дата окончания аренды")
    supplier: Optional[str] = Field(None, description="Поставщик")
    comment: Optional[str] = Field(None, description="Комментарий")


class EquipmentOrderResponse(BaseModel):
    """Заявка на технику"""
    id: int
    cost_object_id: int
    cost_object_name: str
    foreman_id: int
    foreman_name: str
    equipment_type: str
    start_date: date
    end_date: date
    supplier: Optional[str]
    comment: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EquipmentOrderListItem(BaseModel):
    """Элемент списка заявок"""
    id: int
    cost_object_name: str
    foreman_name: str
    equipment_type: str
    start_date: date
    end_date: Optional[date]  # Может быть NULL
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class EquipmentApproveRequest(BaseModel):
    """Запрос на утверждение заявки"""
    hour_rate: Decimal = Field(description="Ставка за час работы", gt=0)
    supplier: Optional[str] = Field(None, description="Поставщик")
    comment: Optional[str] = Field(None, description="Комментарий")


class EquipmentCostCreate(BaseModel):
    """Учет фактических часов работы техники"""
    hours_worked: Decimal = Field(description="Отработанные часы", ge=0)
    work_date: date = Field(description="Дата работы")
    description: Optional[str] = Field(None, description="Описание работ")


class EquipmentCostResponse(BaseModel):
    """Запись затрат по технике"""
    id: int
    equipment_order_id: int
    hours_worked: Decimal
    work_date: date
    hour_rate: Decimal
    total_amount: Decimal
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CancelOrderRequest(BaseModel):
    """Запрос на отмену заявки"""
    reason: str = Field(description="Причина отмены")
