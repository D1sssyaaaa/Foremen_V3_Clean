"""Схемы данных для модуля UPD"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class UPDItemResponse(BaseModel):
    """Строка УПД документа"""
    id: int
    product_name: str
    quantity: Decimal
    unit: str
    price: Decimal
    amount: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total_with_vat: Decimal
    okei_code: Optional[str] = None

    class Config:
        from_attributes = True


class ParsingIssueResponse(BaseModel):
    """Проблема при парсинге"""
    severity: str
    element: str
    message: str
    generator: Optional[str] = None
    value: Optional[str] = None


class UPDUploadResponse(BaseModel):
    """Ответ при загрузке УПД"""
    id: int
    document_number: str
    document_date: datetime
    supplier_name: str
    supplier_inn: Optional[str]
    total_amount: Decimal
    total_vat: Decimal
    total_with_vat: Decimal
    items_count: int
    status: str
    xml_file_path: str
    generator: Optional[str]
    parsing_issues_count: int
    parsing_issues: List[ParsingIssueResponse] = []


class UPDDetailResponse(BaseModel):
    """Детальная информация об УПД"""
    id: int
    document_number: str
    document_date: datetime
    supplier_name: str
    supplier_inn: Optional[str]
    buyer_name: Optional[str]
    buyer_inn: Optional[str]
    total_amount: Decimal
    total_vat: Decimal
    total_with_vat: Decimal
    status: str
    xml_file_path: str
    generator: Optional[str]
    format_version: Optional[str]
    items: List[UPDItemResponse]
    parsing_issues: List[ParsingIssueResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DistributionItemCreate(BaseModel):
    """Распределение одной строки УПД"""
    material_cost_item_id: int = Field(description="ID строки УПД")
    material_request_id: Optional[int] = Field(None, description="ID заявки на материалы")
    cost_object_id: Optional[int] = Field(None, description="ID объекта напрямую")
    distributed_quantity: Decimal = Field(description="Распределенное количество")
    distributed_amount: Decimal = Field(description="Распределенная сумма")


class DistributeUPDRequest(BaseModel):
    """Запрос на распределение УПД"""
    distributions: List[DistributionItemCreate] = Field(
        description="Массив распределений по строкам УПД"
    )


class DistributeUPDResponse(BaseModel):
    """Ответ после распределения УПД"""
    upd_id: int
    new_status: str
    total_distributed_amount: Decimal
    distributions_count: int
    cost_entries_created: int


class UPDListItem(BaseModel):
    """Элемент списка УПД"""
    id: int
    document_number: str
    document_date: datetime
    supplier_name: str
    total_with_vat: Decimal
    items_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
