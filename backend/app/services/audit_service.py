"""
Сервис для работы с журналом аудита
"""
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, date

from app.models import AuditLog, User
from app.core.models_base import UserRole


class AuditService:
    """Сервис аудита"""
    
    @staticmethod
    async def log_action(
        session: AsyncSession,
        user_id: Optional[int],
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Создание записи аудита
        
        Args:
            session: Сессия БД
            user_id: ID пользователя
            action: Действие (CREATE, UPDATE, DELETE, APPROVE, etc.)
            entity_type: Тип сущности (User, TimeSheet, etc.)
            entity_id: ID сущности
            old_value: Старое значение (JSON строка)
            new_value: Новое значение (JSON строка)
            description: Описание
            ip_address: IP адрес
            user_agent: User-Agent
        """
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        session.add(audit_entry)
        await session.flush()
        
        return audit_entry
    
    @staticmethod
    async def get_audit_logs(
        session: AsyncSession,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Получение записей аудита с фильтрацией
        """
        query = select(AuditLog).join(User, AuditLog.user_id == User.id, isouter=True)
        
        # Фильтры
        conditions = []
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if entity_id:
            conditions.append(AuditLog.entity_id == entity_id)
        if date_from:
            conditions.append(AuditLog.timestamp >= date_from)
        if date_to:
            # Включаем весь день date_to
            from datetime import timedelta
            date_to_end = datetime.combine(date_to, datetime.max.time())
            conditions.append(AuditLog.timestamp <= date_to_end)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Сортировка и лимиты
        query = query.order_by(desc(AuditLog.timestamp))
        query = query.limit(limit).offset(offset)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_user_activity(
        session: AsyncSession,
        user_id: int,
        days: int = 30
    ) -> List[AuditLog]:
        """Получение активности пользователя за последние N дней"""
        from datetime import timedelta
        date_from = datetime.now() - timedelta(days=days)
        
        query = select(AuditLog).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= date_from
            )
        ).order_by(desc(AuditLog.timestamp))
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_entity_history(
        session: AsyncSession,
        entity_type: str,
        entity_id: int
    ) -> List[AuditLog]:
        """Получение истории изменений сущности"""
        query = select(AuditLog).where(
            and_(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
        ).order_by(AuditLog.timestamp)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def cleanup_old_logs(
        session: AsyncSession,
        days: int = 365
    ) -> int:
        """
        Удаление старых записей аудита
        
        Returns:
            Количество удалённых записей
        """
        from datetime import timedelta
        from sqlalchemy import delete
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stmt = delete(AuditLog).where(AuditLog.timestamp < cutoff_date)
        result = await session.execute(stmt)
        await session.commit()
        
        return result.rowcount
