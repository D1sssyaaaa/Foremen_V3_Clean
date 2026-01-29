"""
Pydantic схемы для аутентификации
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class Token(BaseModel):
    """Ответ с токенами"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Данные из токена"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    roles: List[str] = []


class LoginRequest(BaseModel):
    """Запрос на вход"""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление токена"""
    refresh_token: str


class RegisterRequest(BaseModel):
    """Запрос на регистрацию"""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    phone: str = Field(..., min_length=10, max_length=20)
    full_name: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = Field(default=["FOREMAN"])
