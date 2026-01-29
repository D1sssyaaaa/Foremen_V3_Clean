"""
Эндпоинты для управления пользователями (админ-панель)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..auth.dependencies import get_current_user, require_roles
from ..models import User
from .schemas import (
    UserListResponse,
    UserUpdateRolesRequest,
    UserUpdateActiveRequest,
    UserResponse
)

router = APIRouter(tags=["users"])


@router.get("", response_model=List[UserListResponse])
async def get_all_users(
    current_user: User = Depends(require_roles(["ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список всех пользователей (только для ADMIN)
    """
    result = await db.execute(
        select(User).order_by(User.username)
    )
    users = result.scalars().all()
    
    return [
        UserListResponse(
            id=user.id,
            username=user.username,
            phone=user.phone or "",
            roles=user.roles or [],
            is_active=user.is_active,
            telegram_chat_id=user.telegram_chat_id,
            full_name=user.full_name,
            email=user.email,
            created_at=user.created_at
        )
        for user in users
    ]


@router.put("/{user_id}/roles", response_model=UserResponse)
async def update_user_roles(
    user_id: int,
    request: UserUpdateRolesRequest,
    current_user: User = Depends(require_roles(["ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновить роли пользователя (только для ADMIN)
    """
    # Нельзя изменять роли самому себе
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя изменять роли самому себе"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Валидация ролей
    valid_roles = [
        "ADMIN", "MANAGER", "ACCOUNTANT", "HR_MANAGER",
        "EQUIPMENT_MANAGER", "MATERIALS_MANAGER", 
        "PROCUREMENT_MANAGER", "FOREMAN"
    ]
    
    for role in request.roles:
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимая роль: {role}"
            )
    
    user.roles = request.roles
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        phone=user.phone or "",
        roles=user.roles or [],
        is_active=user.is_active,
        telegram_chat_id=user.telegram_chat_id
    )


@router.put("/{user_id}/active", response_model=UserResponse)
async def update_user_active_status(
    user_id: int,
    request: UserUpdateActiveRequest,
    current_user: User = Depends(require_roles(["ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Активировать/деактивировать пользователя (только для ADMIN)
    """
    # Нельзя деактивировать самого себя
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя деактивировать самого себя"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user.is_active = request.is_active
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        phone=user.phone or "",
        roles=user.roles or [],
        is_active=user.is_active,
        telegram_chat_id=user.telegram_chat_id
    )
