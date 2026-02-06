"""Схемы данных для модуля табелей рабочего времени"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, Field


class TimeSheetItemCreate(BaseModel):
    """Создание записи в табеле"""
    member_id: int
    date: date
    cost_object_id: int
    hours: Decimal


class TimeSheetCreate(BaseModel):
    """Создание табеля (items как список словарей для избежания рекурсии)"""
    brigade_id: int
    period_start: date
    period_end: date
    items: list[dict[str, Any]] = Field(description="Записи табеля: [{member_id, date, cost_object_id, hours}, ...]")


class TimeSheetItemResponse(BaseModel):
    """Запись табеля (без Config для избежания рекурсии Pydantic v2)"""
    id: int
    member_id: int
    member_name: str
    date: date
    cost_object_id: int
    cost_object_name: str
    hours: Decimal


class TimeSheetResponse(BaseModel):
    """Табель РТБ (без Config для избежания рекурсии Pydantic v2)"""
    id: int
    brigade_id: int
    brigade_name: str
    period_start: date
    period_end: date
    status: str
    hour_rate: Decimal | None = None
    total_hours: Decimal | None = None
    total_amount: Decimal | None = None
    items: list[dict[str, Any]] = Field(default_factory=list, description="Список записей табеля")
    created_at: datetime
    updated_at: datetime


class TimeSheetListItem(BaseModel):
    """Элемент списка табелей (без Config для избежания рекурсии Pydantic v2)"""
    id: int
    brigade_name: str
    foreman_name: str | None = None
    objects_info: str | None = None
    period_start: date
    period_end: date
    status: str
    total_hours: Decimal | None = None
    total_amount: Decimal | None = None
    created_at: datetime


class TimeSheetSubmitRequest(BaseModel):
    """Запрос на отправку табеля на рассмотрение"""
    comment: str | None = Field(None, description="Комментарий бригадира")


class TimeSheetItemRate(BaseModel):
    """Ставка для конкретной записи табеля"""
    id: int
    hour_rate: Decimal = Field(gt=0, description="Ставка за час")

class TimeSheetApproveRequest(BaseModel):
    """Запрос на утверждение табеля"""
    items: list[TimeSheetItemRate] = Field(description="Список ставок для работников")
    comment: str | None = Field(None, description="Комментарий менеджера")


class TimeSheetRejectRequest(BaseModel):
    """Запрос на отклонение табеля"""
    comment: str = Field(description="Причина отклонения")
