"""
Сервис для управления объектами учёта
"""
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.models import CostObject, MaterialCost, User
from app.core.models_base import ObjectStatus, UPDStatus
from app.services.audit_service import AuditService


class ObjectService:
    """Сервис для работы с объектами"""
    
    @staticmethod
    async def change_status(
        session: AsyncSession,
        object_id: int,
        new_status: ObjectStatus,
        user_id: Optional[int] = None
    ) -> CostObject:
        """
        Изменение статуса объекта
        
        При архивации объекта автоматически архивируются все связанные УПД
        """
        # Получаем объект
        query = select(CostObject).where(CostObject.id == object_id)
        result = await session.execute(query)
        obj = result.scalar_one_or_none()
        
        if not obj:
            raise ValueError(f"Объект с ID {object_id} не найден")
        
        old_status = obj.status
        obj.status = new_status.value
        
        # Если архивируем объект - архивируем все УПД
        if new_status == ObjectStatus.ARCHIVED:
            await ObjectService._archive_object_upd(session, object_id)
            # Деактивируем объект
            obj.is_active = False
        
        # Логируем изменение
        if user_id:
            await AuditService.log_action(
                session=session,
                user_id=user_id,
                action="CHANGE_STATUS",
                entity_type="CostObject",
                entity_id=object_id,
                old_value=old_status,
                new_value=new_status.value,
                description=f"Изменение статуса объекта '{obj.name}' с '{old_status}' на '{new_status.value}'"
            )
        
        await session.commit()
        await session.refresh(obj)
        
        return obj
    
    @staticmethod
    async def _archive_object_upd(session: AsyncSession, object_id: int):
        """
        Архивация всех УПД объекта
        """
        stmt = update(MaterialCost).where(
            and_(
                MaterialCost.cost_object_id == object_id,
                MaterialCost.status != UPDStatus.ARCHIVED.value
            )
        ).values(status=UPDStatus.ARCHIVED.value)
        
        result = await session.execute(stmt)
        archived_count = result.rowcount
        
        return archived_count
    
    @staticmethod
    async def get_objects(
        session: AsyncSession,
        include_archived: bool = False,
        status: Optional[ObjectStatus] = None,
        foreman_id: Optional[int] = None
    ) -> List[CostObject]:
        """
        Получение списка объектов с фильтрацией
        
        Args:
            include_archived: Включать ли архивные объекты
            status: Фильтр по статусу
            foreman_id: Показать только объекты бригадира
        """
        query = select(CostObject)
        
        conditions = []
        
        # По умолчанию скрываем архивные
        if not include_archived:
            conditions.append(CostObject.status != ObjectStatus.ARCHIVED.value)
        
        # Фильтр по статусу
        if status:
            conditions.append(CostObject.status == status.value)
        
        # Фильтр по бригадиру
        if foreman_id:
            from app.models import object_foremen
            query = query.join(object_foremen).where(
                object_foremen.c.foreman_id == foreman_id
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(CostObject.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def calculate_spent_budget(
        session: AsyncSession,
        object_id: int
    ) -> float:
        """
        Расчёт потраченного бюджета объекта
        
        Суммирует все затраты:
        - Материалы (из MaterialCost)
        - Техника (из EquipmentCost)
        - ФОТ (из TimeSheet)
        """
        from app.models import MaterialCost, EquipmentCost
        from sqlalchemy import func, select
        
        # Материалы
        materials_query = select(func.sum(MaterialCost.total_amount)).where(
            MaterialCost.cost_object_id == object_id
        )
        materials_result = await session.execute(materials_query)
        materials_total = materials_result.scalar() or 0.0
        
        # Техника
        equipment_query = select(func.sum(EquipmentCost.total_amount)).where(
            EquipmentCost.cost_object_id == object_id
        )
        equipment_result = await session.execute(equipment_query)
        equipment_total = equipment_result.scalar() or 0.0
        
        # ФОТ (Legacy TimeSheet removed)
        labor_total = 0.0
        
        total_spent = materials_total + equipment_total + labor_total
        
        return total_spent
    
    @staticmethod
    async def check_budget_alerts(
        session: AsyncSession,
        object_id: int
    ) -> dict:
        """
        Проверка бюджета и отправка уведомлений
        
        Returns:
            dict с информацией о бюджете и алертах
        """
        # Получаем объект
        query = select(CostObject).where(CostObject.id == object_id)
        result = await session.execute(query)
        obj = result.scalar_one_or_none()
        
        if not obj or not obj.budget_amount:
            return {
                "has_budget": False,
                "budget": None,
                "spent": 0,
                "percentage": 0,
                "alert_80": False,
                "alert_100": False
            }
        
        # Расчёт потраченного
        spent = await ObjectService.calculate_spent_budget(session, object_id)
        percentage = (spent / obj.budget_amount) * 100 if obj.budget_amount > 0 else 0
        
        # Проверяем алерты
        alert_80 = False
        alert_100 = False
        
        # Алерт 80%
        if percentage >= 80 and not obj.budget_alert_80_sent:
            alert_80 = True
            obj.budget_alert_80_sent = True
            await session.commit()
            
            # Отправка уведомлений через WebSocket
            from app.notifications.service import NotificationService
            from app.core.models_base import UserRole
            
            notif_service = NotificationService(session)
            await notif_service.broadcast_websocket_to_roles(
                roles=[UserRole.MANAGER.value, UserRole.ACCOUNTANT.value],
                notification_type="budget_alert_80",
                title=f"⚠️ Бюджет объекта на 80%",
                message=f"Объект '{obj.name}' израсходовал {percentage:.1f}% бюджета ({spent:,.2f} из {obj.budget_amount:,.2f} ₽)",
                data={
                    "object_id": object_id,
                    "object_name": obj.name,
                    "percentage": percentage,
                    "spent": spent,
                    "budget": obj.budget_amount
                }
            )
        
        # Алерт 100%
        if percentage >= 100 and not obj.budget_alert_100_sent:
            alert_100 = True
            obj.budget_alert_100_sent = True
            await session.commit()
            
            # Отправка уведомлений через WebSocket
            from app.notifications.service import NotificationService
            from app.core.models_base import UserRole
            
            notif_service = NotificationService(session)
            await notif_service.broadcast_websocket_to_roles(
                roles=[UserRole.MANAGER.value, UserRole.ACCOUNTANT.value],
                notification_type="budget_alert_100",
                title=f"🚨 Бюджет объекта превышен!",
                message=f"Объект '{obj.name}' превысил бюджет: {percentage:.1f}% ({spent:,.2f} из {obj.budget_amount:,.2f} ₽)",
                data={
                    "object_id": object_id,
                    "object_name": obj.name,
                    "percentage": percentage,
                    "spent": spent,
                    "budget": obj.budget_amount
                }
            )
        
        return {
            "has_budget": True,
            "budget": obj.budget_amount,
            "spent": spent,
            "percentage": round(percentage, 2),
            "alert_80": alert_80,
            "alert_100": alert_100,
            "object_name": obj.name,
            "object_code": obj.code
        }
