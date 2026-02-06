"""Бизнес-логика модуля табелей рабочего времени"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    TimeSheet, TimeSheetItem, Brigade, BrigadeMember,
    CostObject, CostEntry, User
)
from app.core.models_base import TimeSheetStatus, UserRole
from app.time_sheets.schemas import TimeSheetCreate, TimeSheetItemCreate
from app.notifications.service import NotificationService


class TimeSheetService:
    """Сервис для работы с табелями РТБ"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)
        self.db = db
    
    async def create_timesheet(
        self,
        data: TimeSheetCreate,
        foreman_id: int
    ) -> TimeSheet:
        """
        Создание табеля
        
        Args:
            data: данные табеля
            foreman_id: ID бригадира (для проверки прав)
            
        Returns:
            Созданный TimeSheet
            
        Raises:
            ValueError: если валидация не прошла
        """
        # Проверка прав бригадира
        brigade = await self.db.get(Brigade, data.brigade_id)
        if not brigade:
            raise ValueError(f"Бригада {data.brigade_id} не найдена")
        
        if brigade.foreman_id != foreman_id:
            raise ValueError("Вы не являетесь бригадиром этой бригады")
        
        # Валидация периода
        if data.period_start > data.period_end:
            raise ValueError("Начало периода не может быть позже конца")
        
        # Проверка на дубликаты
        existing = await self._check_duplicate_period(
            data.brigade_id,
            data.period_start,
            data.period_end
        )
        if existing:
            raise ValueError(
                f"Табель за период {data.period_start} - {data.period_end} уже существует"
            )
        
        # Валидация записей
        await self._validate_items(data.items, data.brigade_id)
        
        # Создание табеля
        timesheet = TimeSheet(
            brigade_id=data.brigade_id,
            period_start=data.period_start,
            period_end=data.period_end,
            status=TimeSheetStatus.DRAFT,
            total_hours=sum(item.hours for item in data.items)
        )
        
        self.db.add(timesheet)
        await self.db.flush()
        
        # Создание записей
        for item_data in data.items:
            item = TimeSheetItem(
                time_sheet_id=timesheet.id,
                member_id=item_data.member_id,
                date=item_data.date,
                cost_object_id=item_data.cost_object_id,
                hours=item_data.hours
            )
            self.db.add(item)
        
        await self.db.commit()
        await self.db.refresh(timesheet)
        
        return timesheet
    
    async def get_timesheet_by_id(
        self,
        timesheet_id: int
    ) -> Optional[TimeSheet]:
        """Получение табеля по ID с загрузкой связанных данных"""
        query = (
            select(TimeSheet)
            .options(
                selectinload(TimeSheet.brigade),
                selectinload(TimeSheet.items)
                    .selectinload(TimeSheetItem.member),
                selectinload(TimeSheet.items)
                    .selectinload(TimeSheetItem.cost_object)
            )
            .where(TimeSheet.id == timesheet_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_timesheets_by_brigade(
        self,
        brigade_id: int,
        status: Optional[TimeSheetStatus] = None
    ) -> List[TimeSheet]:
        """Получение табелей бригады"""
        query = (
            select(TimeSheet)
            .options(selectinload(TimeSheet.brigade))
            .where(TimeSheet.brigade_id == brigade_id)
        )
        
        if status:
            query = query.where(TimeSheet.status == status)
        
        query = query.order_by(TimeSheet.period_start.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_all_timesheets(
        self,
        status: Optional[TimeSheetStatus] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> List[TimeSheet]:
        """Получение всех табелей (для менеджеров)"""
        query = (
            select(TimeSheet)
            .options(
                selectinload(TimeSheet.brigade).selectinload(Brigade.foreman),
                selectinload(TimeSheet.items).selectinload(TimeSheetItem.cost_object)
            )
        )
        
        if status:
            query = query.where(TimeSheet.status == status)
        
        if period_start:
            query = query.where(TimeSheet.period_start >= period_start)
        
        if period_end:
            query = query.where(TimeSheet.period_end <= period_end)
        
        query = query.order_by(TimeSheet.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def submit_timesheet(
        self,
        timesheet_id: int,
        foreman_id: int
    ) -> TimeSheet:
        """
        Отправка табеля на рассмотрение
        
        Переход: DRAFT -> UNDER_REVIEW
        """
        timesheet = await self.get_timesheet_by_id(timesheet_id)
        if not timesheet:
            raise ValueError(f"Табель {timesheet_id} не найден")
        
        # Проверка прав
        if timesheet.brigade.foreman_id != foreman_id:
            raise ValueError("Вы не являетесь бригадиром этой бригады")
        
        # Проверка статуса
        if timesheet.status != TimeSheetStatus.DRAFT:
            raise ValueError(f"Табель в статусе {timesheet.status}, отправка невозможна")
        
        # Переход статуса
        timesheet.status = TimeSheetStatus.UNDER_REVIEW
        
        await self.db.commit()
        await self.db.refresh(timesheet)
        
        # 🔔 УВЕДОМЛЕНИЕ: Табель подан
        await self._notify_timesheet_submitted(timesheet)
        
        return timesheet
    
    async def _notify_timesheet_submitted(self, timesheet: TimeSheet):
        """Уведомление о подаче табеля"""
        try:
            await self.notification_service.send_notification_by_roles(
                roles=[UserRole.HR_MANAGER, UserRole.MANAGER],
                notification_type="timesheet_submitted",
                title="🏭 Новый табель на проверку",
                message=(
                    f"Табель <b>#{timesheet.id}</b> от бригады <b>{timesheet.brigade.name}</b>\n"
                    f"Период: {timesheet.period_start} — {timesheet.period_end}\n"
                    f"Часов: {timesheet.total_hours}"
                ),
                data={
                    "timesheet_id": timesheet.id,
                    "brigade_name": timesheet.brigade.name,
                    "total_hours": float(timesheet.total_hours)
                }
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send notification for timesheet {timesheet.id}: {e}")
    
    async def approve_timesheet(
        self,
        timesheet_id: int,
        items_data: List[Any] # List[TimeSheetItemRate]
    ) -> TimeSheet:
        """
        Утверждение табеля
        
        Переход: UNDER_REVIEW -> APPROVED
        Устанавливает ставки для КАЖДОЙ записи и рассчитывает итоговые суммы
        """
        timesheet = await self.get_timesheet_by_id(timesheet_id)
        if not timesheet:
            raise ValueError(f"Табель {timesheet_id} не найден")
        
        # Проверка статуса
        if timesheet.status != TimeSheetStatus.UNDER_REVIEW:
            raise ValueError(
                f"Табель в статусе {timesheet.status}, утверждение невозможно"
            )
            
        # Создаем мапу ставок для быстрого доступа
        rates_map = {item.id: item.hour_rate for item in items_data}
        
        total_amount = Decimal("0")
        total_items_updated = 0
        
        # Обновляем записи
        for item in timesheet.items:
            if item.id in rates_map:
                rate = rates_map[item.id]
                item.hour_rate = float(rate)
                item.amount = float(item.hours) * float(rate)
                
                total_amount += Decimal(str(item.amount))
                total_items_updated += 1
            else:
                # Если ставки нет, кидаем ошибку или пропускаем?
                # Лучше требовать ставку для всех
                raise ValueError(f"Не указана ставка для записи #{item.id} ({item.member.full_name})")
        
        # Обновляем итоги табеля
        timesheet.total_amount = float(total_amount)
        timesheet.status = TimeSheetStatus.APPROVED
        
        # Создание записей затрат по объектам
        await self._create_cost_entries(timesheet)
        
        await self.db.commit()
        await self.db.refresh(timesheet)
        
        # 🔔 УВЕДОМЛЕНИЕ: Табель утвержден
        await self._notify_timesheet_approved(timesheet)
        
        return timesheet
    
    async def _notify_timesheet_approved(self, timesheet: TimeSheet):
        """Уведомление об утверждении табеля"""
        try:
            await self.notification_service.create_notification(
                user_id=timesheet.brigade.foreman_id,
                notification_type="timesheet_approved",
                title="✅ Табель утвержден",
                message=(
                    f"Табель <b>#{timesheet.id}</b> утвержден.\n"
                    f"Сумма: <b>{timesheet.total_amount}</b> руб."
                ),
                data={
                    "timesheet_id": timesheet.id,
                    "amount": float(timesheet.total_amount)
                }
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send approval notification for timesheet {timesheet.id}: {e}")
    
    async def reject_timesheet(
        self,
        timesheet_id: int,
        comment: str
    ) -> TimeSheet:
        """
        Отклонение табеля
        
        Переход: UNDER_REVIEW -> CORRECTED
        """
        timesheet = await self.get_timesheet_by_id(timesheet_id)
        if not timesheet:
            raise ValueError(f"Табель {timesheet_id} не найден")
        
        # Проверка статуса
        if timesheet.status != TimeSheetStatus.UNDER_REVIEW:
            raise ValueError(
                f"Табель в статусе {timesheet.status}, отклонение невозможно"
            )
        
        # Переход статуса
        timesheet.status = TimeSheetStatus.CORRECTED
        
        # Сохранение комментария отклонения в поле notes
        if comment:
            from datetime import datetime
            rejection_note = f"[ОТКЛОНЕНО {datetime.now().strftime('%Y-%m-%d %H:%M')}]: {comment}"
            if timesheet.notes:
                timesheet.notes = f"{timesheet.notes}\n\n{rejection_note}"
            else:
                timesheet.notes = rejection_note
        
        await self.db.commit()
        await self.db.refresh(timesheet)
        
        # 🔔 УВЕДОМЛЕНИЕ: Табель отклонен
        await self._notify_timesheet_rejected(timesheet, comment)
        
        return timesheet
    
    async def _notify_timesheet_rejected(self, timesheet: TimeSheet, comment: str):
        """Уведомление об отклонении табеля"""
        try:
            await self.notification_service.create_notification(
                user_id=timesheet.brigade.foreman_id,
                notification_type="timesheet_rejected",
                title="❌ Табель отклонен",
                message=(
                    f"Табель <b>#{timesheet.id}</b> отклонен и возвращен на корректировку.\n\n"
                    f"Комментарий: {comment}"
                ),
                data={
                    "timesheet_id": timesheet.id,
                    "comment": comment
                }
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send rejection notification for timesheet {timesheet.id}: {e}")
    
    async def _check_duplicate_period(
        self,
        brigade_id: int,
        period_start: date,
        period_end: date
    ) -> bool:
        """Проверка на дублирование периода"""
        query = select(TimeSheet).where(
            TimeSheet.brigade_id == brigade_id,
            TimeSheet.period_start == period_start,
            TimeSheet.period_end == period_end
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def _validate_items(
        self,
        items: List[TimeSheetItemCreate],
        brigade_id: int
    ) -> None:
        """Валидация записей табеля"""
        if not items:
            raise ValueError("Табель должен содержать хотя бы одну запись")
        
        # Получение членов бригады
        brigade = await self.db.get(Brigade, brigade_id)
        if not brigade:
            raise ValueError(f"Бригада {brigade_id} не найдена")
        
        member_ids = {m.id for m in brigade.members}
        
        for item in items:
            # Проверка члена бригады
            if item.member_id not in member_ids:
                raise ValueError(
                    f"Работник {item.member_id} не является членом бригады {brigade_id}"
                )
            
            # Проверка объекта
            obj = await self.db.get(CostObject, item.cost_object_id)
            if not obj:
                raise ValueError(f"Объект учета {item.cost_object_id} не найден")
            
            # Проверка часов
            if item.hours <= 0 or item.hours > 24:
                raise ValueError(f"Некорректное количество часов: {item.hours}")
    
    async def _create_cost_entries(self, timesheet: TimeSheet) -> None:
        """Создание записей затрат по объектам"""
        # Группировка СУММ по объектам
        object_amounts = {}
        
        for item in timesheet.items:
            object_id = item.cost_object_id
            if object_id not in object_amounts:
                object_amounts[object_id] = Decimal("0")
            
            # item.amount уже посчитан при утверждении
            if item.amount:
                 object_amounts[object_id] += Decimal(str(item.amount))
        
        # Создание записей затрат
        for object_id, amount in object_amounts.items():
            cost_entry = CostEntry(
                type="labor",
                cost_object_id=object_id,
                date=timesheet.period_end,  # Используем конец периода
                amount=float(amount),
                description=f"Табель #{timesheet.id} (Бригада {timesheet.brigade.name})"
            )
            self.db.add(cost_entry)
    
    async def cancel_timesheet(
        self,
        timesheet_id: int,
        user_id: int,
        cancellation_reason: str
    ) -> TimeSheet:
        """
        Отмена табеля (только для FOREMAN)
        
        Args:
            timesheet_id: ID табеля
            user_id: ID пользователя (бригадира)
            cancellation_reason: Причина отмены
            
        Returns:
            Обновленный табель
            
        Raises:
            ValueError: если табель нельзя отменить
        """
        timesheet = await self.get_timesheet_by_id(timesheet_id)
        if not timesheet:
            raise ValueError(f"Табель {timesheet_id} не найден")
        
        # Проверка прав (только бригадир может отменить свой табель)
        if timesheet.brigade.foreman_id != user_id:
            raise ValueError("Вы не можете отменить чужой табель")
        
        # Проверка статуса (нельзя отменить утверждённый)
        if timesheet.status == TimeSheetStatus.APPROVED.value:
            raise ValueError("Нельзя отменить утверждённый табель")
        
        if timesheet.status == TimeSheetStatus.CANCELLED.value:
            raise ValueError("Табель уже отменён")
        
        # Изменение статуса
        timesheet.status = TimeSheetStatus.CANCELLED.value
        timesheet.cancellation_reason = cancellation_reason
        
        # Добавление комментария об отмене
        from app.models import TimeSheetComment
        from app.core.models_base import CommentType
        
        comment = TimeSheetComment(
            time_sheet_id=timesheet_id,
            user_id=user_id,
            comment_type=CommentType.CANCELLATION.value,
            text=f"Табель отменён. Причина: {cancellation_reason}"
        )
        self.db.add(comment)
        
        await self.db.commit()
        await self.db.refresh(timesheet)
        
        # Уведомление HR-менеджера
        await self._notify_managers(
            timesheet,
            f"Табель #{timesheet.id} отменён бригадиром",
            [UserRole.HR_MANAGER]
        )
        
        return timesheet
    
    async def add_comment(
        self,
        timesheet_id: int,
        user_id: int,
        comment_text: str,
        comment_type: str = "GENERAL"
    ) -> dict:
        """
        Добавление комментария к табелю (от HR-менеджера)
        
        Args:
            timesheet_id: ID табеля
            user_id: ID пользователя (HR-менеджер)
            comment_text: Текст комментария
            comment_type: Тип комментария (GENERAL, HR_CORRECTION, CANCELLATION)
            
        Returns:
            Словарь с данными комментария
        """
        from app.models import TimeSheetComment
        
        timesheet = await self.get_timesheet_by_id(timesheet_id)
        if not timesheet:
            raise ValueError(f"Табель {timesheet_id} не найден")
        
        comment = TimeSheetComment(
            time_sheet_id=timesheet_id,
            user_id=user_id,
            comment_type=comment_type,
            text=comment_text
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        
        # Уведомление бригадира через WebSocket
        await self.notification_service.send_websocket_notification(
            user_id=timesheet.brigade.foreman_id,
            notification_type="timesheet_comment",
            title="💬 Новый комментарий к табелю",
            message=f"HR-менеджер оставил комментарий к табелю #{timesheet.id}",
            data={
                "timesheet_id": timesheet_id,
                "comment_id": comment.id,
                "comment_type": comment_type,
                "text": comment_text
            }
        )
        
        # Также отправим через Telegram (старый механизм)
        await self.notification_service.notify_user(
            user_id=timesheet.brigade.foreman_id,
            title="Новый комментарий к табелю",
            message=f"HR-менеджер оставил комментарий к табелю #{timesheet.id}",
            notification_type="timesheet_comment"
        )
        
        return {
            "id": comment.id,
            "timesheet_id": timesheet_id,
            "user_id": user_id,
            "comment_type": comment.comment_type,
            "text": comment.text,
            "created_at": comment.created_at
        }
    
    async def get_comments(
        self,
        timesheet_id: int
    ) -> List[dict]:
        """
        Получение всех комментариев к табелю
        
        Args:
            timesheet_id: ID табеля
            
        Returns:
            Список комментариев
        """
        from app.models import TimeSheetComment
        
        query = select(TimeSheetComment).where(
            TimeSheetComment.time_sheet_id == timesheet_id
        ).order_by(TimeSheetComment.created_at)
        
        result = await self.db.execute(query)
        comments = result.scalars().all()
        
        return [
            {
                "id": c.id,
                "timesheet_id": c.time_sheet_id,
                "user_id": c.user_id,
                "comment_type": c.comment_type,
                "text": c.text,
                "created_at": c.created_at
            }
            for c in comments
        ]
    
    async def validate_overtime(
        self,
        timesheet_id: int
    ) -> dict:
        """
        Проверка переработок (>12 часов в день)
        
        Args:
            timesheet_id: ID табеля
            
        Returns:
            Словарь с информацией о переработках
        """
        timesheet = await self.get_timesheet_by_id(timesheet_id)
        if not timesheet:
            raise ValueError(f"Табель {timesheet_id} не найден")
        
        # Группировка часов по дням и работникам
        daily_hours = {}
        for item in timesheet.items:
            key = (item.member_id, item.date)
            if key not in daily_hours:
                daily_hours[key] = 0
            daily_hours[key] += item.hours
        
        # Поиск переработок
        overtime_cases = []
        for (member_id, date), hours in daily_hours.items():
            if hours > 12:
                member = await self.db.get(BrigadeMember, member_id)
                overtime_cases.append({
                    "member_id": member_id,
                    "member_name": member.full_name if member else "Неизвестно",
                    "date": date.isoformat(),
                    "hours": hours,
                    "overtime_hours": hours - 12
                })
        
        return {
            "has_overtime": len(overtime_cases) > 0,
            "overtime_count": len(overtime_cases),
            "cases": overtime_cases,
            "warning": "Обнаружены переработки более 12 часов в день!" if overtime_cases else None
        }
    
    async def get_brigade_by_id(self, brigade_id: int) -> Optional[Brigade]:
        """
        Получение бригады по ID
        
        Args:
            brigade_id: ID бригады
            
        Returns:
            Brigade или None
        """
        from sqlalchemy.orm import selectinload
        
        stmt = select(Brigade).where(Brigade.id == brigade_id).options(
            selectinload(Brigade.members)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


