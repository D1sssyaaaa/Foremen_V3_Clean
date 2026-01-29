"""API роутер для уведомлений"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.core.models_base import UserRole
from app.models import User
from app.notifications.service import NotificationService
from app.notifications.schemas import (
    NotificationCreate,
    NotificationSendByRole,
    NotificationResponse,
    NotificationListItem,
    NotificationMarkRead,
    NotificationStats
)

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False, description="Только непрочитанные"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить уведомления текущего пользователя
    
    - Доступно: всем авторизованным пользователям
    - Фильтр: unread_only, пагинация
    """
    service = NotificationService(db)
    notifications = await service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )
    
    return [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            data=n.data,
            is_read=n.is_read,
            sent_at=n.sent_at,
            read_at=n.read_at,
            telegram_message_id=n.telegram_message_id,
            status=n.status,
            created_at=n.created_at
        )
        for n in notifications
    ]


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Статистика уведомлений текущего пользователя
    
    - Доступно: всем авторизованным пользователям
    """
    service = NotificationService(db)
    stats = await service.get_notification_stats(current_user.id)
    
    return NotificationStats(**stats)


@router.post("/mark-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notifications_as_read(
    data: NotificationMarkRead,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отметить уведомления как прочитанные
    
    - Доступно: всем авторизованным пользователям
    - Можно отметить только свои уведомления
    """
    service = NotificationService(db)
    count = await service.mark_as_read(data.notification_ids, current_user.id)
    
    return {"marked": count}


@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
):
    """
    Создать уведомление для пользователя
    
    - Доступно: MANAGER, ADMIN
    - Создает уведомление, которое будет отправлено через фоновый процесс
    """
    service = NotificationService(db)
    
    notification = await service.create_notification(
        user_id=data.user_id,
        notification_type=data.notification_type,
        title=data.title,
        message=data.message,
        data=data.data
    )
    
    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        data=notification.data,
        is_read=notification.is_read,
        sent_at=notification.sent_at,
        read_at=notification.read_at,
        telegram_message_id=notification.telegram_message_id,
        status=notification.status,
        created_at=notification.created_at
    )


@router.post("/send-by-role", status_code=status.HTTP_201_CREATED)
async def send_notification_by_role(
    data: NotificationSendByRole,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
):
    """
    Отправить уведомления пользователям по ролям
    
    - Доступно: MANAGER, ADMIN
    - Создает уведомления для всех пользователей с указанными ролями
    - Отправка происходит через фоновый процесс
    """
    service = NotificationService(db)
    
    notifications = await service.send_notification_by_roles(
        roles=data.roles,
        notification_type=data.notification_type,
        title=data.title,
        message=data.message,
        data=data.data,
        exclude_user_ids=data.exclude_user_ids
    )
    
    return {
        "created": len(notifications),
        "roles": [role.value for role in data.roles],
        "notification_type": data.notification_type
    }


@router.get("/pending", response_model=List[NotificationResponse])
async def get_pending_notifications(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Получить неотправленные уведомления
    
    - Доступно: только ADMIN
    - Для отладки и мониторинга
    """
    service = NotificationService(db)
    notifications = await service.get_pending_notifications(limit=limit)
    
    return [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            data=n.data,
            is_read=n.is_read,
            sent_at=n.sent_at,
            read_at=n.read_at,
            telegram_message_id=n.telegram_message_id,
            status=n.status,
            created_at=n.created_at
        )
        for n in notifications
    ]


@router.get("/badge")
async def get_notification_badge(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить badge с количеством непрочитанных и последними уведомлениями
    
    - Доступно: всем авторизованным пользователям
    - Используется для колокольчика уведомлений
    """
    service = NotificationService(db)
    
    # Получаем последние 5 уведомлений
    latest_notifications = await service.get_user_notifications(
        user_id=current_user.id,
        unread_only=False,
        limit=5,
        offset=0
    )
    
    # Получаем количество непрочитанных
    stats = await service.get_notification_stats(current_user.id)
    
    return {
        "unread_count": stats.get("unread_count", 0),
        "latest_notifications": [
            NotificationResponse(
                id=n.id,
                user_id=n.user_id,
                notification_type=n.notification_type,
                title=n.title,
                message=n.message,
                data=n.data,
                is_read=n.is_read,
                sent_at=n.sent_at,
                read_at=n.read_at,
                telegram_message_id=n.telegram_message_id,
                status=n.status,
                created_at=n.created_at
            )
            for n in latest_notifications
        ]
    }


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отметить одно уведомление как прочитанное
    
    - Доступно: всем авторизованным пользователям
    """
    service = NotificationService(db)
    count = await service.mark_as_read([notification_id], current_user.id)
    
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or not yours"
        )
    
    return None


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отметить все уведомления как прочитанные
    
    - Доступно: всем авторизованным пользователям
    """
    service = NotificationService(db)
    await service.mark_all_as_read(current_user.id)
    
    return None


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить уведомление
    
    - Доступно: всем авторизованным пользователям
    - Можно удалить только свое уведомление
    """
    service = NotificationService(db)
    deleted = await service.delete_notification(notification_id, current_user.id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or not yours"
        )
    
    return None

