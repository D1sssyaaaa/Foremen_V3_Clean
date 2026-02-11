"""Бизнес-логика модуля аренды техники"""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    EquipmentOrder, EquipmentCost, CostObject,
    User, CostEntry
)
from app.core.models_base import EquipmentOrderStatus, UserRole
from app.equipment.schemas import EquipmentOrderCreate, EquipmentCostCreate
from app.notifications.service import NotificationService

class EquipmentService:
    """Сервис для работы с заявками на технику"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def create_order(
        self,
        data: EquipmentOrderCreate,
        foreman_id: int
    ) -> EquipmentOrder:
        """
        Создание заявки на технику
        
        Args:
            data: данные заявки
            foreman_id: ID бригадира
            
        Returns:
            Созданная заявка
            
        Raises:
            ValueError: если валидация не прошла
        """
        # Валидация дат
        if data.start_date > data.end_date:
            raise ValueError("Дата начала не может быть позже даты окончания")
        
        # Проверка объекта
        obj = await self.db.get(CostObject, data.cost_object_id)
        if not obj:
            raise ValueError(f"Объект учета {data.cost_object_id} не найден")
        
        # Создание заявки
        order = EquipmentOrder(
            cost_object_id=data.cost_object_id,
            foreman_id=foreman_id,
            equipment_type=data.equipment_type,
            
            start_date=data.start_date,
            end_date=data.end_date,
            supplier=data.supplier,
            comment=data.comment,
            status=EquipmentOrderStatus.NEW,
            
        )
        
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        
        # 🔔 УВЕДОМЛЕНИЕ: Новая заявка на технику
        await self._notify_new_order(order, obj)
        
        return order
    
    async def _notify_new_order(self, order: EquipmentOrder, obj: CostObject):
        """Уведомление о новой заявке"""
        try:
            foreman = await self.db.get(User, order.foreman_id)
            foreman_name = foreman.username if foreman else "Неизвестен"
            
            equipment_type_ru = {
                "loader": "Погрузчик",
                "excavator": "Экскаватор",
                "crane": "Кран",
                "truck": "Грузовик",
                "bulldozer": "Бульдозер",
                "concrete_mixer": "Бетономешалка"
            }.get(order.equipment_type, order.equipment_type)
            
            await self.notification_service.send_notification_by_roles(
                roles=[UserRole.EQUIPMENT_MANAGER, UserRole.MANAGER],
                notification_type="equipment_order_created",
                title="🏭 Новая заявка на технику",
                message=(
                    f"Заявка <b>#{order.id}</b> от бригадира <b>{foreman_name}</b>\n"
                    f"Техника: {equipment_type_ru}\n"
                    f"Период: {order.start_date} — {order.end_date}"
                ),
                data={
                    "order_id": order.id,
                    "foreman_name": foreman_name,
                    "object_name": obj.name,
                    "equipment_type": order.equipment_type
                },
                exclude_user_ids=[order.foreman_id]
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send notification for equipment order {order.id}: {e}")
    
    async def get_order_by_id(
        self,
        order_id: int
    ) -> Optional[EquipmentOrder]:
        """Получение заявки по ID с загрузкой связанных данных"""
        query = (
            select(EquipmentOrder)
            .options(
                selectinload(EquipmentOrder.cost_object),
                selectinload(EquipmentOrder.foreman),
                selectinload(EquipmentOrder.costs)
            )
            .where(EquipmentOrder.id == order_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_orders_by_foreman(
        self,
        foreman_id: int,
        status: Optional[EquipmentOrderStatus] = None
    ) -> List[EquipmentOrder]:
        """Получение заявок бригадира"""
        query = (
            select(EquipmentOrder)
            .options(
                selectinload(EquipmentOrder.cost_object),
                selectinload(EquipmentOrder.foreman)
            )
            .where(EquipmentOrder.foreman_id == foreman_id)
        )
        
        if status:
            query = query.where(EquipmentOrder.status == status)
        
        query = query.order_by(EquipmentOrder.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_all_orders(
        self,
        status: Optional[EquipmentOrderStatus] = None,
        cost_object_id: Optional[int] = None
    ) -> List[EquipmentOrder]:
        """Получение всех заявок (для менеджеров)"""
        query = (
            select(EquipmentOrder)
            .options(
                selectinload(EquipmentOrder.cost_object),
                selectinload(EquipmentOrder.foreman)
            )
        )
        
        if status:
            query = query.where(EquipmentOrder.status == status)
        
        if cost_object_id:
            query = query.where(EquipmentOrder.cost_object_id == cost_object_id)
        
        query = query.order_by(EquipmentOrder.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def approve_order(
        self,
        order_id: int,
        hour_rate: Decimal,
        supplier: Optional[str] = None
    ) -> EquipmentOrder:
        """
        Утверждение заявки
        
        Переход: NEW -> APPROVED
        Устанавливает ставку за час
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Заявка {order_id} не найдена")
        
        # Проверка статуса
        if order.status != EquipmentOrderStatus.NEW:
            raise ValueError(
                f"Заявка в статусе {order.status}, утверждение невозможно"
            )
        
        # Утверждение
        order.status = EquipmentOrderStatus.APPROVED
        order.hour_rate = hour_rate
        if supplier:
            order.supplier = supplier
        
        await self.db.commit()
        await self.db.refresh(order)
        
        # 🔔 УВЕДОМЛЕНИЕ: Заявка утверждена
        await self._notify_order_approved(order, hour_rate)
        
        return order
    
    async def _notify_order_approved(self, order: EquipmentOrder, hour_rate: Decimal):
        """Уведомление об утверждении заявки"""
        try:
            await self.notification_service.create_notification(
                user_id=order.foreman_id,
                notification_type="equipment_order_approved",
                title="✅ Заявка на технику утверждена",
                message=(
                    f"Ваша заявка <b>#{order.id}</b> на технику утверждена.\n"
                    f"Ставка: {hour_rate} руб/час"
                ),
                data={"order_id": order.id, "hour_rate": float(hour_rate)}
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send approval notification for order {order.id}: {e}")
    
    async def start_work(
        self,
        order_id: int
    ) -> EquipmentOrder:
        """
        Начало работ
        
        Переход: APPROVED -> IN_PROGRESS
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Заявка {order_id} не найдена")
        
        # Проверка статуса
        if order.status != EquipmentOrderStatus.APPROVED:
            raise ValueError(
                f"Заявка в статусе {order.status}, начало работ невозможно"
            )
        
        order.status = EquipmentOrderStatus.IN_PROGRESS
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return order
    
    async def add_hours(
        self,
        order_id: int,
        data: EquipmentCostCreate
    ) -> EquipmentCost:
        """
        Учет отработанных часов
        
        Создает запись затрат и обновляет итоговые суммы
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Заявка {order_id} не найдена")
        
        # Проверка статуса
        if order.status not in [EquipmentOrderStatus.APPROVED, EquipmentOrderStatus.IN_PROGRESS]:
            raise ValueError(
                f"Учет часов возможен только для заявок в статусе APPROVED или IN_PROGRESS"
            )
        
        # Проверка ставки
        if not order.hour_rate:
            raise ValueError("Ставка за час не установлена")
        
        # Переход в IN_PROGRESS при первом учете часов
        if order.status == EquipmentOrderStatus.APPROVED:
            order.status = EquipmentOrderStatus.IN_PROGRESS
        
        # Создание записи затрат
        equipment_cost = EquipmentCost(
            equipment_order_id=order.id,
            hours_worked=data.hours_worked,
            work_date=data.work_date,
            hour_rate=order.hour_rate,
            total_amount=data.hours_worked * order.hour_rate,
            description=data.description
        )
        
        self.db.add(equipment_cost)
        
        # Обновление итоговых сумм
        order.total_hours += data.hours_worked
        order.total_amount = order.total_hours * order.hour_rate
        
        # Создание записи в общих затратах
        cost_entry = CostEntry(
            type="equipment",
            cost_object_id=order.cost_object_id,
            date=data.work_date,
            amount=equipment_cost.total_amount,
            description=f"{order.equipment_type}: {data.hours_worked}ч × {order.hour_rate}₽/ч"
        )
        self.db.add(cost_entry)
        
        await self.db.commit()
        await self.db.refresh(equipment_cost)
        
        return equipment_cost
    
    async def complete_order(
        self,
        order_id: int
    ) -> EquipmentOrder:
        """
        Завершение заявки
        
        Переход: IN_PROGRESS -> COMPLETED
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Заявка {order_id} не найдена")
        
        # Проверка статуса
        if order.status != EquipmentOrderStatus.IN_PROGRESS:
            raise ValueError(
                f"Заявка в статусе {order.status}, завершение невозможно"
            )
        
        order.status = EquipmentOrderStatus.COMPLETED
        
        await self.db.commit()
        await self.db.refresh(order)
        
        # 🔔 УВЕДОМЛЕНИЕ: Заявка завершена, нужно подать часы
        await self._notify_order_completed(order)
        
        return order
    
    async def _notify_order_completed(self, order: EquipmentOrder):
        """Уведомление о завершении заявки и необходимости подать часы"""
        try:
            await self.notification_service.create_notification(
                user_id=order.foreman_id,
                notification_type="equipment_order_completed",
                title="🏁 Работы с техникой завершены",
                message=(
                    f"Менеджер завершил работы по заявке <b>#{order.id}</b>.\n"
                    f"Техника: {order.equipment_type}\n"
                    f"Пожалуйста, укажите количество отработанных часов."
                ),
                data={
                    "order_id": order.id,
                    "action": "submit_hours" # Флаг для кнопки
                }
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send completion notification for order {order.id}: {e}")
    
    async def request_cancel(
        self,
        order_id: int,
        foreman_id: int,
        reason: str
    ) -> EquipmentOrder:
        """
        Запрос на отмену заявки (бригадиром)
        
        Переход: NEW/APPROVED -> CANCEL_REQUESTED
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Заявка {order_id} не найдена")
        
        # Проверка прав
        if order.foreman_id != foreman_id:
            raise ValueError("Вы не являетесь автором этой заявки")
        
        # Проверка статуса
        if order.status not in [EquipmentOrderStatus.NEW, EquipmentOrderStatus.APPROVED]:
            raise ValueError(
                f"Заявка в статусе {order.status}, запрос отмены невозможен"
            )
        
        order.status = EquipmentOrderStatus.CANCEL_REQUESTED
        # TODO: Сохранить причину (добавить поле в модель)
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return order
    
    async def cancel_order(
        self,
        order_id: int
    ) -> EquipmentOrder:
        """
        Отмена заявки (менеджером)
        
        Переход: CANCEL_REQUESTED -> CANCELLED
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Заявка {order_id} не найдена")
        
        # Проверка статуса
        if order.status != EquipmentOrderStatus.CANCEL_REQUESTED:
            raise ValueError(
                f"Заявка в статусе {order.status}, отмена невозможна"
            )
        
        order.status = EquipmentOrderStatus.CANCELLED
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return order
