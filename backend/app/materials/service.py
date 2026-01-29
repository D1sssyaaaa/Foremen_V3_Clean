"""Бизнес-логика модуля заявок на материалы"""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    MaterialRequest, MaterialRequestItem, CostObject,
    User, UPDDistribution
)
from app.core.models_base import MaterialRequestStatus, UserRole
from app.materials.schemas import MaterialRequestCreate, MaterialRequestItemCreate
from app.notifications.service import NotificationService


class MaterialRequestService:
    """Сервис для работы с заявками на материалы"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)
        self.db = db
    
    async def create_request(
        self,
        data: MaterialRequestCreate,
        foreman_id: int
    ) -> MaterialRequest:
        """
        Создание заявки на материалы
        
        Args:
            data: данные заявки
            foreman_id: ID бригадира
            
        Returns:
            Созданная заявка
            
        Raises:
            ValueError: если валидация не прошла
        """
        # Валидация срочности
        if data.urgency not in ["normal", "urgent", "critical"]:
            raise ValueError("Некорректная срочность (normal/urgent/critical)")
        
        # Проверка объекта
        obj = await self.db.get(CostObject, data.cost_object_id)
        if not obj:
            raise ValueError(f"Объект учета {data.cost_object_id} не найден")
        
        # Создание заявки
        request = MaterialRequest(
            cost_object_id=data.cost_object_id,
            foreman_id=foreman_id,
            material_type=data.material_type,
            status=MaterialRequestStatus.NEW,
            urgency=data.urgency,
            expected_delivery_date=data.expected_delivery_date,
            delivery_time=data.delivery_time,
            comment=data.comment
        )
        
        self.db.add(request)
        await self.db.flush()
        
        # Создание позиций
        for item_data in data.items:
            item = MaterialRequestItem(
                request_id=request.id,
                material_name=item_data.material_name,
                quantity=float(item_data.quantity),
                unit=item_data.unit,
                description=item_data.description
            )
            self.db.add(item)
        
        await self.db.commit()
        await self.db.refresh(request)
        
        # 🔔 УВЕДОМЛЕНИЕ: Новая заявка создана
        await self._notify_new_request(request, obj)
        
        return request
    
    async def _notify_new_request(self, request: MaterialRequest, obj: CostObject):
        """Отправить уведомление о новой заявке"""
        try:
            # Получить имя бригадира
            foreman = await self.db.get(User, request.foreman_id)
            foreman_name = foreman.username if foreman else "Неизвестен"
            
            # Перевод срочности
            urgency_ru = {
                "critical": "Критическая",
                "urgent": "Срочная",
                "high": "Высокая",
                "medium": "Средняя",
                "low": "Низкая"
            }.get(request.urgency, request.urgency)
            
            # Отправить менеджерам
            await self.notification_service.send_notification_by_roles(
                roles=[UserRole.MATERIALS_MANAGER, UserRole.PROCUREMENT_MANAGER, UserRole.MANAGER],
                notification_type="material_request_created",
                title="🆕 Новая заявка на материалы",
                message=(
                    f"Заявка <b>#{request.id}</b> от бригадира <b>{foreman_name}</b>\n"
                    f"Тип: {request.material_type}\n"
                    f"Срочность: {urgency_ru}"
                ),
                data={
                    "request_id": request.id,
                    "foreman_name": foreman_name,
                    "object_name": obj.name,
                    "urgency": request.urgency
                },
                exclude_user_ids=[request.foreman_id]
            )
        except Exception as e:
            # Не прерываем основной процесс если уведомление не отправилось
            import logging
            logging.error(f"Failed to send notification for material request {request.id}: {e}")
    
    async def get_request_by_id(
        self,
        request_id: int
    ) -> Optional[MaterialRequest]:
        """Получение заявки по ID с загрузкой связанных данных"""
        query = (
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.cost_object),
                selectinload(MaterialRequest.foreman),
                selectinload(MaterialRequest.items)
            )
            .where(MaterialRequest.id == request_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_requests_by_foreman(
        self,
        foreman_id: int,
        status: Optional[MaterialRequestStatus] = None,
        material_type: Optional[str] = None
    ) -> List[MaterialRequest]:
        """Получение заявок бригадира"""
        query = (
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.cost_object),
                selectinload(MaterialRequest.foreman),
                selectinload(MaterialRequest.items)
            )
            .where(MaterialRequest.foreman_id == foreman_id)
        )
        
        if status:
            query = query.where(MaterialRequest.status == status)
        
        if material_type:
            query = query.where(MaterialRequest.material_type == material_type)
        
        query = query.order_by(MaterialRequest.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_all_requests(
        self,
        status: Optional[MaterialRequestStatus] = None,
        urgency: Optional[str] = None,
        cost_object_id: Optional[int] = None,
        material_type: Optional[str] = None
    ) -> List[MaterialRequest]:
        """Получение всех заявок (для менеджеров)"""
        query = (
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.cost_object),
                selectinload(MaterialRequest.foreman),
                selectinload(MaterialRequest.items)
            )
        )
        
        if status:
            query = query.where(MaterialRequest.status == status)
        
        if urgency:
            query = query.where(MaterialRequest.urgency == urgency)
        
        if cost_object_id:
            query = query.where(MaterialRequest.cost_object_id == cost_object_id)
        
        if material_type:
            query = query.where(MaterialRequest.material_type == material_type)
        
        query = query.order_by(MaterialRequest.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def approve_request(
        self,
        request_id: int,
        comment: Optional[str] = None
    ) -> MaterialRequest:
        """
        Согласование заявки
        
        Переход: NEW -> APPROVED
        """
        request = await self.get_request_by_id(request_id)
        if not request:
            raise ValueError(f"Заявка {request_id} не найдена")
        
        # Проверка статуса
        if request.status != MaterialRequestStatus.NEW:
            raise ValueError(
                f"Заявка в статусе {request.status}, согласование невозможно"
            )
        
        request.status = MaterialRequestStatus.APPROVED
        # TODO: сохранить комментарий
        
        await self.db.commit()
        await self.db.refresh(request)
        
        # 🔔 УВЕДОМЛЕНИЕ: Заявка согласована
        await self._notify_request_approved(request)
        
        return request
    
    async def _notify_request_approved(self, request: MaterialRequest):
        """Уведомление бригадиру о согласовании"""
        try:
            await self.notification_service.create_notification(
                user_id=request.foreman_id,
                notification_type="material_request_approved",
                title="✅ Заявка согласована",
                message=f"Ваша заявка <b>#{request.id}</b> на материалы согласована и передана в обработку.",
                data={"request_id": request.id}
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send approval notification for request {request.id}: {e}")
    
    async def process_request(
        self,
        request_id: int,
        expected_delivery_date: Optional[date] = None
    ) -> MaterialRequest:
        """
        Взятие заявки в обработку
        
        Переход: APPROVED -> IN_PROCESSING
        """
        request = await self.get_request_by_id(request_id)
        if not request:
            raise ValueError(f"Заявка {request_id} не найдена")
        
        # Проверка статуса
        if request.status != MaterialRequestStatus.APPROVED:
            raise ValueError(
                f"Заявка в статусе {request.status}, обработка невозможна"
            )
        
        request.status = MaterialRequestStatus.IN_PROCESSING
        # TODO: сохранить expected_delivery_date
        
        await self.db.commit()
        await self.db.refresh(request)
        
        # 🔔 УВЕДОМЛЕНИЕ: Взято в обработку
        await self._notify_request_processing(request)
        
        return request
    
    async def _notify_request_processing(self, request: MaterialRequest):
        """Уведомление о взятии в обработку"""
        try:
            await self.notification_service.create_notification(
                user_id=request.foreman_id,
                notification_type="material_request_processed",
                title="🔄 Заявка в обработке",
                message=f"Заявка <b>#{request.id}</b> взята в обработку менеджером по материалам.",
                data={"request_id": request.id}
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send processing notification for request {request.id}: {e}")
    
    async def order_materials(
        self,
        request_id: int,
        supplier: str,
        order_number: Optional[str] = None
    ) -> MaterialRequest:
        """
        Размещение заказа материалов
        
        Переход: IN_PROCESSING -> ORDERED
        """
        request = await self.get_request_by_id(request_id)
        if not request:
            raise ValueError(f"Заявка {request_id} не найдена")
        
        # Проверка статуса
        if request.status != MaterialRequestStatus.IN_PROCESSING:
            raise ValueError(
                f"Заявка в статусе {request.status}, размещение заказа невозможно"
            )
        
        request.status = MaterialRequestStatus.ORDERED
        # TODO: сохранить supplier, order_number
        
        await self.db.commit()
        await self.db.refresh(request)
        
        # 🔔 УВЕДОМЛЕНИЕ: Материалы заказаны
        await self._notify_materials_ordered(request, supplier)
        
        return request
    
    async def _notify_materials_ordered(self, request: MaterialRequest, supplier: str):
        """Уведомление о заказе материалов"""
        try:
            await self.notification_service.create_notification(
                user_id=request.foreman_id,
                notification_type="material_request_ordered",
                title="📦 Материалы заказаны",
                message=(
                    f"По заявке <b>#{request.id}</b> материалы заказаны\n"
                    f"Поставщик: <b>{supplier}</b>"
                ),
                data={"request_id": request.id, "supplier": supplier}
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send order notification for request {request.id}: {e}")
    
    async def mark_partial_delivery(
        self,
        request_id: int
    ) -> MaterialRequest:
        """
        Частичная поставка
        
        Переход: ORDERED -> PARTIALLY_DELIVERED
        """
        request = await self.get_request_by_id(request_id)
        if not request:
            raise ValueError(f"Заявка {request_id} не найдена")
        
        # Проверка статуса
        if request.status != MaterialRequestStatus.ORDERED:
            raise ValueError(
                f"Заявка в статусе {request.status}, отметка частичной поставки невозможна"
            )
        
        request.status = MaterialRequestStatus.PARTIALLY_DELIVERED
        
        await self.db.commit()
        await self.db.refresh(request)
        
        return request
    
    async def mark_shipped(
        self,
        request_id: int
    ) -> MaterialRequest:
        """
        Полная отгрузка материалов
        
        Переход: ORDERED/PARTIALLY_DELIVERED -> SHIPPED
        """
        request = await self.get_request_by_id(request_id)
        if not request:
            raise ValueError(f"Заявка {request_id} не найдена")
        
        # Проверка статуса
        if request.status not in [
            MaterialRequestStatus.ORDERED,
            MaterialRequestStatus.PARTIALLY_DELIVERED
        ]:
            raise ValueError(
                f"Заявка в статусе {request.status}, отметка отгрузки невозможна"
            )
        
        request.status = MaterialRequestStatus.SHIPPED
        
        await self.db.commit()
        await self.db.refresh(request)
        
        return request
    
    async def complete_request(
        self,
        request_id: int
    ) -> MaterialRequest:
        """
        Завершение заявки
        
        Переход: SHIPPED -> COMPLETED
        """
        request = await self.get_request_by_id(request_id)
        if not request:
            raise ValueError(f"Заявка {request_id} не найдена")
        
        # Проверка статуса
        if request.status != MaterialRequestStatus.SHIPPED:
            raise ValueError(
                f"Заявка в статусе {request.status}, завершение невозможно"
            )
        
        # Проверка распределения всех позиций
        for item in request.items:
            if item.distributed_quantity < item.quantity:
                raise ValueError(
                    f"Позиция '{item.material_name}' не полностью распределена"
                )
        
        request.status = MaterialRequestStatus.COMPLETED
        
        await self.db.commit()
        await self.db.refresh(request)
        
        return request
    
    async def reject_request(
        self,
        request_id: int,
        reason: str
    ) -> MaterialRequest:
        """
        Отклонение заявки
        
        Переход: NEW -> REJECTED
        """
        request = await self.get_request_by_id(request_id)
        if not request:
            raise ValueError(f"Заявка {request_id} не найдена")
        
        # Проверка статуса
        if request.status != MaterialRequestStatus.NEW:
            raise ValueError(
                f"Заявка в статусе {request.status}, отклонение невозможно"
            )
        
        request.status = MaterialRequestStatus.REJECTED
        # TODO: сохранить причину
        
        await self.db.commit()
        await self.db.refresh(request)
        
        # 🔔 УВЕДОМЛЕНИЕ: Заявка отклонена
        await self._notify_request_rejected(request, reason)
        
        return request
    
    async def _notify_request_rejected(self, request: MaterialRequest, reason: str):
        """Уведомление об отклонении заявки"""
        try:
            await self.notification_service.create_notification(
                user_id=request.foreman_id,
                notification_type="material_request_rejected",
                title="❌ Заявка отклонена",
                message=(
                    f"Заявка <b>#{request.id}</b> на материалы отклонена\n\n"
                    f"Причина: {reason}"
                ),
                data={"request_id": request.id, "reason": reason}
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send rejection notification for request {request.id}: {e}")
    
    async def get_distributed_quantity(
        self,
        item_id: int
    ) -> Decimal:
        """Получение распределенного количества для позиции"""
        query = select(func.sum(UPDDistribution.distributed_quantity)).where(
            UPDDistribution.material_request_id == item_id
        )
        result = await self.db.execute(query)
        total = result.scalar_one_or_none()
        return total or Decimal("0")
