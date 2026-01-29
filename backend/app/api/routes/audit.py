"""
API для работы с журналом аудита
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.models import User
from app.core.models_base import UserRole
from app.services.audit_service import AuditService
from pydantic import BaseModel, Field


router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditLogResponse(BaseModel):
    """Ответ с записью аудита"""
    id: int
    timestamp: str
    user_id: Optional[int]
    user_name: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[int]
    description: Optional[str]
    ip_address: Optional[str]
    
    class Config:
        from_attributes = True


class AuditLogsListResponse(BaseModel):
    """Список записей аудита"""
    logs: List[AuditLogResponse]
    total: int


@router.get("/", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Фильтр по пользователю"),
    action: Optional[str] = Query(None, description="Фильтр по действию"),
    entity_type: Optional[str] = Query(None, description="Фильтр по типу сущности"),
    entity_id: Optional[int] = Query(None, description="Фильтр по ID сущности"),
    date_from: Optional[date] = Query(None, description="Дата от"),
    date_to: Optional[date] = Query(None, description="Дата до"),
    limit: int = Query(100, ge=1, le=1000, description="Количество записей"),
    offset: int = Query(0, ge=0, description="Смещение"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER])),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение журнала аудита (только для ADMIN и MANAGER)
    """
    logs = await AuditService.get_audit_logs(
        session=db,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )
    
    # Формируем ответ
    result = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "user_name": log.user.username if log.user else "Система",
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
            "ip_address": log.ip_address
        }
        result.append(AuditLogResponse(**log_dict))
    
    return result


@router.get("/user/{user_id}", response_model=List[AuditLogResponse])
async def get_user_activity(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Количество дней"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER])),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение активности пользователя
    """
    logs = await AuditService.get_user_activity(
        session=db,
        user_id=user_id,
        days=days
    )
    
    result = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "user_name": log.user.username if log.user else "Система",
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
            "ip_address": log.ip_address
        }
        result.append(AuditLogResponse(**log_dict))
    
    return result


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
async def get_entity_history(
    entity_type: str,
    entity_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER])),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение истории изменений сущности
    """
    logs = await AuditService.get_entity_history(
        session=db,
        entity_type=entity_type,
        entity_id=entity_id
    )
    
    result = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "user_name": log.user.username if log.user else "Система",
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
            "ip_address": log.ip_address
        }
        result.append(AuditLogResponse(**log_dict))
    
    return result


class AuditStatsResponse(BaseModel):
    """Статистика аудита"""
    total_logs: int
    actions: dict
    entities: dict
    top_users: List[dict]


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365, description="Период в днях"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER])),
    db: AsyncSession = Depends(get_db)
):
    """
    Статистика по журналу аудита
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func, select
    from app.models import AuditLog
    
    date_from = datetime.now() - timedelta(days=days)
    
    # Общее количество
    total_query = select(func.count(AuditLog.id)).where(AuditLog.timestamp >= date_from)
    total_result = await db.execute(total_query)
    total_logs = total_result.scalar()
    
    # По действиям
    actions_query = select(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).where(
        AuditLog.timestamp >= date_from
    ).group_by(AuditLog.action)
    
    actions_result = await db.execute(actions_query)
    actions = {row.action: row.count for row in actions_result}
    
    # По типам сущностей
    entities_query = select(
        AuditLog.entity_type,
        func.count(AuditLog.id).label('count')
    ).where(
        AuditLog.timestamp >= date_from
    ).group_by(AuditLog.entity_type)
    
    entities_result = await db.execute(entities_query)
    entities = {row.entity_type: row.count for row in entities_result}
    
    # Топ пользователей
    top_users_query = select(
        AuditLog.user_id,
        User.username,
        func.count(AuditLog.id).label('count')
    ).join(
        User, AuditLog.user_id == User.id
    ).where(
        AuditLog.timestamp >= date_from
    ).group_by(
        AuditLog.user_id, User.username
    ).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10)
    
    top_users_result = await db.execute(top_users_query)
    top_users = [
        {"user_id": row.user_id, "username": row.username, "actions_count": row.count}
        for row in top_users_result
    ]
    
    return AuditStatsResponse(
        total_logs=total_logs,
        actions=actions,
        entities=entities,
        top_users=top_users
    )
