"""
Схемы для управления пользователями
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class UserListResponse(BaseModel):
    """Пользователь в списке"""
    id: int
    username: str
    phone: str
    roles: List[str]
    is_active: bool
    telegram_chat_id: Optional[int] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Ответ с данными пользователя"""
    id: int
    username: str
    phone: str
    roles: List[str]
    is_active: bool
    telegram_chat_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserUpdateRolesRequest(BaseModel):
    """Запрос на обновление ролей"""
    roles: List[str]


class UserUpdateActiveRequest(BaseModel):
    """Запрос на изменение статуса активности"""
    is_active: bool
