"""Схемы данных для модуля аналитики"""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class CostBreakdown(BaseModel):
    """Разбивка затрат по типу"""
    type: str = Field(description="Тип затрат: labor, equipment, material")
    amount: Decimal = Field(description="Сумма")
    percentage: Decimal = Field(description="Процент от общей суммы")


class ObjectCostSummary(BaseModel):
    """Сводка затрат по объекту"""
    object_id: int
    object_name: str
    total_labor_cost: Decimal
    total_equipment_cost: Decimal
    total_material_cost: Decimal
    total_cost: Decimal
    contract_amount: Optional[Decimal]
    remaining_budget: Optional[Decimal]
    budget_utilization_percent: Optional[Decimal]
    planned_labor_cost: Optional[Decimal]
    planned_material_cost: Optional[Decimal]


class PeriodCostReport(BaseModel):
    """Отчет по затратам за период"""
    period_start: date
    period_end: date
    total_cost: Decimal
    cost_breakdown: List[CostBreakdown]
    objects_summary: List[ObjectCostSummary]


class ObjectDetailedReport(BaseModel):
    """Детальный отчет по объекту"""
    object_id: int
    object_name: str
    contract_number: Optional[str]
    contract_amount: Optional[Decimal]
    start_date: Optional[date]
    end_date: Optional[date]
    
    # Затраты
    total_labor_cost: Decimal
    total_labor_hours: Decimal
    total_equipment_cost: Decimal
    total_equipment_hours: Decimal
    total_material_cost: Decimal
    total_cost: Decimal
    
    # Бюджет
    remaining_budget: Optional[Decimal]
    budget_utilization_percent: Optional[Decimal]
    
    # Детализация
    timesheets_count: int
    equipment_orders_count: int
    material_requests_count: int
    upd_documents_count: int


class CostTrendItem(BaseModel):
    """Элемент тренда затрат"""
    date: date
    labor_cost: Decimal
    equipment_cost: Decimal
    material_cost: Decimal
    total_cost: Decimal


class CostTrendReport(BaseModel):
    """Отчет по динамике затрат"""
    object_id: int
    object_name: str
    period_start: date
    period_end: date
    trend: List[CostTrendItem]


class ExportRequest(BaseModel):
    """Запрос на экспорт данных"""
    format: str = Field(description="Формат экспорта: csv, excel, json", default="excel")
    period_start: date
    period_end: date
    object_ids: Optional[List[int]] = Field(None, description="ID объектов (все если не указано)")
    cost_types: Optional[List[str]] = Field(None, description="Типы затрат (все если не указано)")


class Top5Object(BaseModel):
    """Объект в ТОП-5 по затратам"""
    object_id: int
    object_name: str
    total_cost: Decimal
    contract_amount: Optional[Decimal]
    budget_utilization_percent: Optional[Decimal]


class CostDynamicsPoint(BaseModel):
    """Точка данных динамики затрат"""
    period: date = Field(description="Дата периода (начало недели/месяца)")
    total_cost: Decimal
    labor_cost: Decimal
    equipment_cost: Decimal
    material_cost: Decimal


class CostDynamics(BaseModel):
    """Динамика затрат по периодам"""
    object_id: Optional[int] = Field(None, description="ID объекта (None = все объекты)")
    period_start: Optional[date]
    period_end: Optional[date]
    grouping: str = Field(description="Группировка: day, week, month")
    data_points: List[CostDynamicsPoint]
