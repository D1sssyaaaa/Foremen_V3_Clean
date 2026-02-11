"""
Модели для «умного» сопоставления материалов.

ProductAlias — таблица обучения: запоминает связи
"название от поставщика" ↔ "название в системе (или ID позиции сметы)".

Каждый раз, когда пользователь вручную подтверждает или исправляет
маппинг, создаётся новый Алиас (или инкрементируется use_count).
"""
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey,
    DateTime, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ProductAlias(Base):
    """
    Алиас продукта — связь "внешнее название" → "внутренний продукт".
    
    Пример:
        supplier_name = "Кабель ВВГ 3х2,5"
        canonical_name = "Кабель ВВГнг-LS 3*2.5"
        estimate_item_id = 42  (опционально)
        confidence = 1.0 (подтверждено пользователем)
    """
    __tablename__ = "product_aliases"

    id = Column(Integer, primary_key=True, index=True)
    
    # Внешнее название (от поставщика / из УПД)
    supplier_name = Column(String(500), nullable=False, index=True)
    
    # Каноническое название в нашей системе
    canonical_name = Column(String(500), nullable=False, index=True)
    
    # Опциональная привязка к позиции сметы
    estimate_item_id = Column(
        Integer, 
        ForeignKey("estimate_items.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # Контекст: для какого поставщика этот алиас (NULL = универсальный)
    supplier_inn = Column(String(12), nullable=True, index=True)
    
    # Метрики использования
    confidence = Column(Float, default=1.0)       # 0.0–1.0, 1.0 = подтверждён вручную
    use_count = Column(Integer, default=1)         # Сколько раз использован
    
    # Кто создал / подтвердил
    created_by_user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("supplier_name", "canonical_name", "supplier_inn", name="uq_alias"),
    )

    # Связи
    estimate_item = relationship("EstimateItem", foreign_keys=[estimate_item_id])

    def __repr__(self):
        return f"<ProductAlias '{self.supplier_name}' → '{self.canonical_name}' ({self.use_count}x)>"
