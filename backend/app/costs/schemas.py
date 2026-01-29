"""Схемы для затрат"""
from pydantic import BaseModel, Field
from datetime import date as DateType
from typing import Optional


class LaborCostCreate(BaseModel):
    """Создание затраты на рабочих"""
    cost_object_id: int = Field(..., description="ID объекта учета")
    date: DateType = Field(..., description="Дата затраты")
    amount: float = Field(..., gt=0, description="Сумма затраты")
    comment: Optional[str] = Field(None, description="Комментарий")


class LaborCostUpdate(BaseModel):
    """Обновление затраты на рабочих"""
    date: Optional[DateType] = None
    amount: Optional[float] = Field(None, gt=0)
    comment: Optional[str] = None


class LaborCostResponse(BaseModel):
    """Ответ с затратой на рабочих"""
    id: int
    cost_object_id: int
    date: DateType
    amount: float
    comment: Optional[str]
    created_by_id: int
    created_at: DateType
    
    class Config:
        from_attributes = True


class OtherCostCreate(BaseModel):
    """Создание иной затраты"""
    cost_object_id: int = Field(..., description="ID объекта учета")
    date: DateType = Field(..., description="Дата затраты")
    amount: float = Field(..., gt=0, description="Сумма затраты")
    comment: Optional[str] = Field(None, description="Комментарий")


class OtherCostUpdate(BaseModel):
    """Обновление иной затраты"""
    date: Optional[DateType] = None
    amount: Optional[float] = Field(None, gt=0)
    comment: Optional[str] = None


class OtherCostResponse(BaseModel):
    """Ответ с иной затратой"""
    id: int
    cost_object_id: int
    date: DateType
    amount: float
    comment: Optional[str]
    created_by_id: int
    created_at: DateType
    
    class Config:
        from_attributes = True


class DeliveryCostCreate(BaseModel):
    """Создание затраты на доставку/спецтехнику"""
    cost_object_id: int = Field(..., description="ID объекта учета")
    date: DateType = Field(..., description="Дата затраты")
    amount: float = Field(..., gt=0, description="Сумма затраты")
    cost_type: str = Field(..., description="Тип: 'delivery' или 'equipment'")
    comment: Optional[str] = Field(None, description="Комментарий")


class DeliveryCostUpdate(BaseModel):
    """Обновление затраты на доставку/спецтехнику"""
    date: Optional[DateType] = None
    amount: Optional[float] = Field(None, gt=0)
    cost_type: Optional[str] = None
    comment: Optional[str] = None


class DeliveryCostResponse(BaseModel):
    """Ответ с затратой на доставку/спецтехнику"""
    id: int
    cost_object_id: int
    date: DateType
    amount: float
    cost_type: str
    comment: Optional[str]
    created_by_id: int
    created_at: DateType
    
    class Config:
        from_attributes = True
