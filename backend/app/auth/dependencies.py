"""
Dependencies для аутентификации и авторизации
"""
from typing import List
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models import User
from app.auth.security import decode_token
from app.core.models_base import UserRole

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Получение текущего пользователя из JWT токена
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        if payload is None:
            logger.warning("Failed to decode token")
            raise credentials_exception
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            logger.warning("Missing user ID in token payload")
            raise credentials_exception
        
        # Конвертируем user_id из строки в int
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id format in token: {user_id_str}")
            raise credentials_exception
        
        # Получение пользователя из БД
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None:
            logger.warning(f"User not found: {user_id}")
            raise credentials_exception
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}", exc_info=True)
        raise credentials_exception


def require_roles(allowed_roles: List[str]):
    """
    Декоратор для проверки ролей пользователя
    Использование: current_user: User = Depends(require_roles(["MANAGER", "ADMIN"]))
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles = current_user.roles or []
        
        # ADMIN и MANAGER имеют полный доступ
        if UserRole.ADMIN.value in user_roles or UserRole.MANAGER.value in user_roles:
            return current_user
        
        # Проверка разрешенных ролей
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return role_checker


# Готовые dependencies для разных ролей
require_foreman = require_roles([UserRole.FOREMAN.value])
require_accountant = require_roles([UserRole.ACCOUNTANT.value])
require_hr_manager = require_roles([UserRole.HR_MANAGER.value])
require_equipment_manager = require_roles([UserRole.EQUIPMENT_MANAGER.value])
require_materials_manager = require_roles([UserRole.MATERIALS_MANAGER.value])
require_procurement_manager = require_roles([UserRole.PROCUREMENT_MANAGER.value])
require_manager = require_roles([UserRole.MANAGER.value])
require_admin = require_roles([UserRole.ADMIN.value])


async def get_current_user_ws(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Получение текущего пользователя для WebSocket stats endpoint
    (используется обычная HTTP аутентификация)
    """
    return await get_current_user(credentials, db)

