"""
Модели базы данных
Все таблицы системы
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean, Text,
    ForeignKey, Table, ARRAY, JSON, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base
from app.core.models_base import (
    MaterialRequestStatus, UPDStatus, RegistrationRequestStatus, ObjectStatus,
    TimestampMixin, EquipmentOrderStatus, MaterialType
)


# Связующая таблица для многие-ко-многим (бригадиры-объекты)
object_foremen = Table(
    'object_foremen',
    Base.metadata,
    Column('object_id', Integer, ForeignKey('cost_objects.id', ondelete='CASCADE')),
    Column('foreman_id', Integer, ForeignKey('users.id', ondelete='CASCADE'))
)


class User(Base, TimestampMixin):
    """Пользователи системы"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    roles = Column(JSON, nullable=False, default=[])  # JSON массив ролей (для SQLite совместимости)
    telegram_chat_id = Column(Integer, nullable=True, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    birth_date = Column(Date, nullable=True)
    profile_photo_url = Column(String(500), nullable=True)
    
    # Связи
    brigades = relationship("Brigade", back_populates="foreman")
    assigned_objects = relationship("CostObject", secondary=object_foremen, back_populates="foremen")
    equipment_orders = relationship("EquipmentOrder", back_populates="foreman")
    material_requests = relationship("MaterialRequest", back_populates="foreman")
    notifications = relationship("TelegramNotification", back_populates="user")


class CostObject(Base, TimestampMixin):
    """Объекты учета (стройки)"""
    __tablename__ = "cost_objects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    contract_number = Column(String(100), nullable=True)
    contract_amount = Column(Float, nullable=True)
    material_amount = Column(Float, nullable=True)
    labor_amount = Column(Float, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, default=ObjectStatus.ACTIVE.value, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Бюджет объекта
    budget_amount = Column(Float, nullable=True)
    budget_alert_80_sent = Column(Boolean, default=False, nullable=False)
    budget_alert_100_sent = Column(Boolean, default=False, nullable=False)
    
    # Связи
    foremen = relationship("User", secondary=object_foremen, back_populates="assigned_objects")
    equipment_orders = relationship("EquipmentOrder", back_populates="cost_object")
    material_requests = relationship("MaterialRequest", back_populates="cost_object")
    material_costs = relationship("MaterialCost", back_populates="cost_object")
    cost_entries = relationship("CostEntry", back_populates="cost_object")


class Brigade(Base, TimestampMixin):
    """Бригады"""
    __tablename__ = "brigades"
    
    id = Column(Integer, primary_key=True, index=True)
    foreman_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Связи
    foreman = relationship("User", back_populates="brigades")
    members = relationship("BrigadeMember", back_populates="brigade", cascade="all, delete-orphan")


class BrigadeMember(Base, TimestampMixin):
    """Члены бригады"""
    __tablename__ = "brigade_members"
    
    id = Column(Integer, primary_key=True, index=True)
    brigade_id = Column(Integer, ForeignKey("brigades.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    position = Column(String(100), nullable=True)
    
    # Связи
    brigade = relationship("Brigade", back_populates="members")


class SavedWorker(Base, TimestampMixin):
    """Сохраненные работники бригадира (для быстрого выбора в WebApp)"""
    __tablename__ = "saved_workers"

    id = Column(Integer, primary_key=True, index=True)
    foreman_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # ФИО или Имя
    role = Column(String(100), nullable=True)  # Разнорабочий, Мастер и т.д.
    
    # Связи
    foreman = relationship("User", backref="saved_workers")





class EquipmentOrder(Base, TimestampMixin):
    """Заявки на аренду техники/инструмента"""
    __tablename__ = "equipment_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    cost_object_id = Column(Integer, ForeignKey("cost_objects.id", ondelete="CASCADE"), nullable=False)
    foreman_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    number = Column(String(50), unique=True, nullable=True)  # EQ-2024-001
    equipment_type = Column(String(100), nullable=False)  # Экскаватор, бетономешалка и т.д.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default=EquipmentOrderStatus.NEW.value, index=True)
    supplier = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    cancel_reason = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)  # Причина отклонения заявки
    
    # Связи
    cost_object = relationship("CostObject", back_populates="equipment_orders")
    foreman = relationship("User", back_populates="equipment_orders")
    costs = relationship("EquipmentCost", back_populates="equipment_order", cascade="all, delete-orphan")


class EquipmentCost(Base, TimestampMixin):
    """Расчет стоимости аренды техники"""
    __tablename__ = "equipment_costs"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_order_id = Column(Integer, ForeignKey("equipment_orders.id", ondelete="CASCADE"), nullable=False)
    hours_worked = Column(Float, nullable=False)
    work_date = Column(Date, nullable=False)
    hour_rate = Column(Float, nullable=False)
    delivery_included = Column(Boolean, default=False)
    delivery_amount = Column(Float, default=0.0)
    penalty_included = Column(Boolean, default=False)
    penalty_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    
    # Связи
    equipment_order = relationship("EquipmentOrder", back_populates="costs")


class MaterialRequest(Base, TimestampMixin):
    """Заявки на материалы"""
    __tablename__ = "material_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    cost_object_id = Column(Integer, ForeignKey("cost_objects.id", ondelete="CASCADE"), nullable=False)
    foreman_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    number = Column(String(50), unique=True, nullable=True)  # MR-2024-001
    status = Column(String(50), nullable=False, default=MaterialRequestStatus.NEW.value, index=True)
    material_type = Column(String(20), nullable=False, default="regular", index=True)  # regular/inert
    urgency = Column(String(20), nullable=True)  # СРОЧНО, ОБЫЧНАЯ
    delivery_address = Column(Text, nullable=True)
    delivery_time = Column(String(50), nullable=True)  # Желаемое время доставки (для инертных)
    notes = Column(Text, nullable=True)
    
    # Новые поля для трекинга
    comment = Column(Text, nullable=True)  # Комментарии к заявке
    expected_delivery_date = Column(Date, nullable=True)  # Ожидаемая дата доставки
    supplier = Column(String(255), nullable=True)  # Поставщик
    order_number = Column(String(100), nullable=True)  # Номер заказа у поставщика
    rejection_reason = Column(Text, nullable=True)  # Причина отклонения заявки
    
    # Связи
    cost_object = relationship("CostObject", back_populates="material_requests")
    foreman = relationship("User", back_populates="material_requests")
    items = relationship("MaterialRequestItem", back_populates="request", cascade="all, delete-orphan")
    distributions = relationship("UPDDistribution", back_populates="material_request")


class MaterialRequestItem(Base):
    """Позиции заявки на материалы"""
    __tablename__ = "material_request_items"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("material_requests.id", ondelete="CASCADE"), nullable=False)
    material_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)  # шт, м, кг и т.д.
    description = Column(Text, nullable=True)  # Описание/примечание к позиции
    distributed_quantity = Column(Float, nullable=False, default=0.0)  # Распределенное количество
    
    # Optional link to original estimate item
    estimate_item_id = Column(Integer, ForeignKey("estimate_items.id", ondelete="SET NULL"), nullable=True)
    
    # Связи
    request = relationship("MaterialRequest", back_populates="items")
    estimate_item = relationship("EstimateItem")


class MaterialCost(Base, TimestampMixin):
    """УПД (универсальные передаточные документы)"""
    __tablename__ = "material_costs"
    
    id = Column(Integer, primary_key=True, index=True)
    cost_object_id = Column(Integer, ForeignKey("cost_objects.id", ondelete="SET NULL"), nullable=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_inn = Column(String(12), nullable=True)
    document_number = Column(String(100), nullable=False, index=True)
    document_date = Column(Date, nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    vat_amount = Column(Float, default=0.0)
    status = Column(String(20), nullable=False, default=UPDStatus.NEW.value, index=True)
    xml_file_path = Column(String(500), nullable=True)  # Путь в S3/MinIO
    generator = Column(String(100), nullable=True)  # Elewise, 1C, Diadoc и т.д.
    parsing_issues = Column(JSON, nullable=True)  # Проблемы парсинга
    
    @property
    def total_with_vat(self):
        return self.total_amount + self.vat_amount
        
    @property
    def total_vat(self):
        return self.vat_amount
        
    @property
    def items_count(self):
        return len(self.items)
    
    # Поля для работы с дубликатами
    duplicate_of_id = Column(Integer, ForeignKey("material_costs.id", ondelete="SET NULL"), nullable=True)
    duplicate_checked_at = Column(DateTime, nullable=True)  # Когда проверяли на дубликаты
    
    # Связи
    cost_object = relationship("CostObject", back_populates="material_costs")
    items = relationship("MaterialCostItem", back_populates="material_cost", cascade="all, delete-orphan")
    distributions = relationship("UPDDistribution", back_populates="material_cost")
    duplicate_of = relationship("MaterialCost", remote_side=[id], foreign_keys=[duplicate_of_id])


class MaterialCostItem(Base):
    """Строки УПД (товары/услуги)"""
    __tablename__ = "material_cost_items"
    
    id = Column(Integer, primary_key=True, index=True)
    material_cost_id = Column(Integer, ForeignKey("material_costs.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(500), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    vat_rate = Column(Float, default=20.0)  # Ставка НДС
    vat_amount = Column(Float, default=0.0)
    
    @property
    def total_with_vat(self):
        return self.amount + self.vat_amount
    
    # Связи
    material_cost = relationship("MaterialCost", back_populates="items")


class UPDDistribution(Base, TimestampMixin):
    """Распределение УПД по заявкам"""
    __tablename__ = "upd_distribution"
    
    id = Column(Integer, primary_key=True, index=True)
    material_cost_id = Column(Integer, ForeignKey("material_costs.id", ondelete="CASCADE"), nullable=False)
    material_cost_item_id = Column(Integer, ForeignKey("material_cost_items.id", ondelete="CASCADE"), nullable=False)
    material_request_id = Column(Integer, ForeignKey("material_requests.id", ondelete="CASCADE"), nullable=True)
    cost_object_id = Column(Integer, ForeignKey("cost_objects.id", ondelete="CASCADE"), nullable=True)
    distributed_quantity = Column(Float, nullable=False)
    distributed_amount = Column(Float, nullable=False)
    
    # Связи
    material_cost = relationship("MaterialCost", back_populates="distributions")
    material_request = relationship("MaterialRequest", back_populates="distributions")
    material_cost_item = relationship("MaterialCostItem")
    cost_object = relationship("CostObject")


class UPDDistributionHistory(Base, TimestampMixin):
    """История изменений распределения УПД"""
    __tablename__ = "upd_distribution_history"
    
    id = Column(Integer, primary_key=True, index=True)
    material_cost_id = Column(Integer, ForeignKey("material_costs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    
    # Данные до изменения (JSON)
    old_distribution = Column(JSON, nullable=True)
    
    # Данные после изменения (JSON)
    new_distribution = Column(JSON, nullable=False)
    
    # Описание изменения
    description = Column(Text, nullable=True)
    
    # Связи
    material_cost = relationship("MaterialCost")
    user = relationship("User")


class CostEntry(Base, TimestampMixin):
    """Общая таблица затрат (для отчетности)"""
    __tablename__ = "cost_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False, index=True)  # РТБ, ТЕХНИКА, МАТЕРИАЛЫ
    cost_object_id = Column(Integer, ForeignKey("cost_objects.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    reference_id = Column(Integer, nullable=True)  # ID связанной записи
    reference_type = Column(String(50), nullable=True)  # Тип связанной записи
    
    # Связи
    cost_object = relationship("CostObject", back_populates="cost_entries")


class RegistrationRequest(Base, TimestampMixin):
    """Заявки на регистрацию пользователей"""
    __tablename__ = "registration_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    birth_date = Column(Date, nullable=False)
    phone = Column(String(20), nullable=False)
    telegram_chat_id = Column(String(50), nullable=False, unique=True)
    telegram_username = Column(String(100), nullable=True)
    requested_role = Column(String(50), nullable=True)  # Запрашиваемая роль
    status = Column(String(20), nullable=False, default=RegistrationRequestStatus.PENDING.value, index=True)
    
    # Кто обработал заявку
    processed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Созданный пользователь (после одобрения)
    created_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Связи
    processed_by = relationship("User", foreign_keys=[processed_by_id])
    created_user = relationship("User", foreign_keys=[created_user_id])


class ObjectAccessRequest(Base, TimestampMixin):
    """Запросы на доступ к объектам учета (для прорабов)"""
    __tablename__ = "object_access_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    foreman_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cost_object_id = Column(Integer, ForeignKey("cost_objects.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    reason = Column(Text, nullable=True)  # Причина запроса доступа
    
    # Кто одобрил/отклонил
    processed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Связи
    foreman = relationship("User", foreign_keys=[foreman_id])
    cost_object = relationship("CostObject")
    processed_by = relationship("User", foreign_keys=[processed_by_id])


class AuditLog(Base):
    """Журнал аудита всех критичных действий"""
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # CREATE, UPDATE, DELETE, APPROVE, REJECT и т.д.
    entity_type = Column(String(50), nullable=False, index=True)  # User, TimeSheet, MaterialRequest и т.д.
    entity_id = Column(Integer, nullable=True, index=True)
    old_value = Column(Text, nullable=True)  # JSON строка со старыми значениями
    new_value = Column(Text, nullable=True)  # JSON строка с новыми значениями
    ip_address = Column(String(45), nullable=True)  # IPv4 или IPv6
    user_agent = Column(Text, nullable=True)
    description = Column(Text, nullable=True)  # Человекочитаемое описание
    
    # Связь с пользователем
    user = relationship("User", foreign_keys=[user_id])


class TelegramLinkCode(Base, TimestampMixin):
    """Временные коды для привязки Telegram аккаунтов"""
    __tablename__ = "telegram_link_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связь с пользователем
    user = relationship("User")


class Delivery(Base, TimestampMixin):
    """Самостоятельно заказанные доставки материалов
    
    Учитывает доставки, которые заказаны через Telegram бот
    (не встроенные в УПД). Статус: NEW → APPROVED → PAID
    """
    __tablename__ = "deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    cost_object_id = Column(Integer, ForeignKey("cost_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)  # Сумма доставки
    delivery_date = Column(Date, nullable=False, index=True)  # Дата доставки
    comment = Column(Text, nullable=True)  # Комментарий к доставке
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="NEW", index=True)  # NEW, APPROVED, PAID
    
    # Связи
    cost_object = relationship("CostObject", backref="deliveries")
    created_by = relationship("User", foreign_keys=[created_by_id])


class LaborCost(Base, TimestampMixin):
    """Затраты на рабочих (дополнительные к табелям РТБ)
    
    Используется для учета разовых затрат на рабочих,
    которые не входят в регулярные табели.
    """
    __tablename__ = "labor_costs"
    
    id = Column(Integer, primary_key=True, index=True)
    cost_object_id = Column(Integer, ForeignKey("cost_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    # Связи
    cost_object = relationship("CostObject", backref="labor_costs")
    created_by = relationship("User", foreign_keys=[created_by_id])


class OtherCost(Base, TimestampMixin):
    """Иные затраты
    
    Используется для учета прочих затрат на объекте,
    которые не попадают в другие категории (материалы, техника, зарплаты).
    """
    __tablename__ = "other_costs"
    
    id = Column(Integer, primary_key=True, index=True)
    cost_object_id = Column(Integer, ForeignKey("cost_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    # Связи
    cost_object = relationship("CostObject", backref="other_costs")
    created_by = relationship("User", foreign_keys=[created_by_id])


class DeliveryCost(Base, TimestampMixin):
    """Затраты на доставку и спецтехнику (дополнительные)
    
    Используется для учета разовых затрат на доставку или аренду спецтехники,
    которые не входят в основные заказы EquipmentOrder.
    """
    __tablename__ = "delivery_costs"
    
    id = Column(Integer, primary_key=True, index=True)
    cost_object_id = Column(Integer, ForeignKey("cost_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    cost_type = Column(String(50), nullable=False, index=True)  # 'delivery' или 'equipment'
    comment = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    # Связи
    cost_object = relationship("CostObject", backref="delivery_costs")
    created_by = relationship("User", foreign_keys=[created_by_id])


class EstimateItem(Base, TimestampMixin):
    """Позиции сметы (загружаются из Excel)"""
    __tablename__ = "estimate_items"
    
    id = Column(Integer, primary_key=True, index=True)
    cost_object_id = Column(Integer, ForeignKey("cost_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    category = Column(String(255), nullable=True)  # Раздел сметы (напр. "Кабельные линии")
    name = Column(String(500), nullable=False)     # Наименование материала
    unit = Column(String(50), nullable=False)      # Ед. измерения
    quantity = Column(Float, nullable=False)       # Количество по смете
    price = Column(Float, nullable=False)          # Цена за единицу
    total_amount = Column(Float, nullable=False)   # Общая сумма позиции
    
    # Для отслеживания прогресса (Soft Limits)
    ordered_quantity = Column(Float, default=0.0)  # Сколько уже заказано (через MaterialRequest)
    
    # Связи
    cost_object = relationship("CostObject", backref="estimate_items")


# Импорт дополнительных моделей из отдельных модулей
from app.notifications.models import TelegramNotification

# Обновление __all__ для полного экспорта
__all__ = [
    "User", "CostObject", "Brigade", "BrigadeMember", "EquipmentOrder", "EquipmentCost", "MaterialRequest",
    "MaterialRequestItem", "MaterialCost", "MaterialCostItem", "CostEntry",
    "RegistrationRequest", "ObjectAccessRequest", "AuditLog", "TelegramNotification",
    "EstimateItem",
    "TelegramLinkCode", "Delivery",
    "TimeEntry",
    "RecentWorker",
    "LaborCost", "OtherCost", "DeliveryCost",
    "object_foremen", "UPDDistribution", "SavedWorker"
]


class TimeEntry(Base):
    __tablename__ = "rtb_time_entries"

    id = Column(Integer, primary_key=True)
    date = Column(Date, index=True, nullable=False)
    object_id = Column(Integer, ForeignKey("cost_objects.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    foreman_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hours = Column(Float, default=0.0)
    status = Column(String, default="APPROVED")
    created_at = Column(DateTime, default=func.now())

    cost_object = relationship("CostObject")
    worker = relationship("User", foreign_keys=[worker_id])
    foreman = relationship("User", foreign_keys=[foreman_id])


class RecentWorker(Base):
    __tablename__ = "rtb_recent_workers"

    foreman_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    worker_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    last_used_at = Column(DateTime, default=func.now(), onupdate=func.now())

    worker = relationship("User", foreign_keys=[worker_id])

