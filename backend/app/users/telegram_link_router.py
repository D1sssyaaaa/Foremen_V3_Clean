"""
Роутер для привязки Telegram аккаунтов
"""
import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models import User, TelegramLinkCode
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ===== Schemas =====

class LinkCodeResponse(BaseModel):
    """Ответ с кодом привязки"""
    code: str
    expires_at: datetime
    instructions: str
    
    class Config:
        from_attributes = True


class LinkTelegramRequest(BaseModel):
    """Запрос на привязку Telegram"""
    code: str
    telegram_chat_id: int
    telegram_username: Optional[str] = None


class LinkTelegramResponse(BaseModel):
    """Ответ на привязку Telegram"""
    success: bool
    message: str
    user_id: Optional[int] = None
    username: Optional[str] = None


# ===== Helper functions =====

def generate_link_code() -> str:
    """Генерация случайного 6-значного кода"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))


async def cleanup_expired_codes(db: AsyncSession):
    """Удаление истекших кодов"""
    result = await db.execute(
        select(TelegramLinkCode).where(
            TelegramLinkCode.expires_at < datetime.now(),
            TelegramLinkCode.used == False
        )
    )
    expired_codes = result.scalars().all()
    
    for code in expired_codes:
        await db.delete(code)
    
    if expired_codes:
        await db.commit()
        logger.info(f"Удалено {len(expired_codes)} истекших кодов привязки")


# ===== Endpoints =====

@router.post("/me/telegram/generate-link-code", response_model=LinkCodeResponse)
async def generate_telegram_link_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Генерация кода для привязки Telegram аккаунта
    
    Используется существующими пользователями для связи с ботом
    """
    # Проверяем, не привязан ли уже Telegram
    if current_user.telegram_chat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram аккаунт уже привязан к этому пользователю"
        )
    
    # Очистка истекших кодов
    await cleanup_expired_codes(db)
    
    # Проверяем, нет ли активного неиспользованного кода
    existing = await db.execute(
        select(TelegramLinkCode).where(
            TelegramLinkCode.user_id == current_user.id,
            TelegramLinkCode.used == False,
            TelegramLinkCode.expires_at > datetime.now()
        )
    )
    existing_code = existing.scalar_one_or_none()
    
    if existing_code:
        return LinkCodeResponse(
            code=existing_code.code,
            expires_at=existing_code.expires_at,
            instructions=(
                f"Отправьте этот код боту командой:\n"
                f"/link {existing_code.code}\n\n"
                f"Код действителен до {existing_code.expires_at.strftime('%d.%m.%Y %H:%M')}"
            )
        )
    
    # Генерируем новый код
    code = generate_link_code()
    expires_at = datetime.now() + timedelta(minutes=15)
    
    link_code = TelegramLinkCode(
        code=code,
        user_id=current_user.id,
        expires_at=expires_at
    )
    
    db.add(link_code)
    await db.commit()
    await db.refresh(link_code)
    
    logger.info(f"Создан код привязки {code} для пользователя {current_user.username}")
    
    return LinkCodeResponse(
        code=code,
        expires_at=expires_at,
        instructions=(
            f"Отправьте этот код боту командой:\n"
            f"/link {code}\n\n"
            f"Код действителен 15 минут"
        )
    )


@router.post("/link-telegram", response_model=LinkTelegramResponse)
async def link_telegram_account(
    data: LinkTelegramRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Привязка Telegram аккаунта по коду (публичный endpoint для бота)
    
    Используется ботом для связи существующего пользователя с Telegram
    """
    # Очистка истекших кодов
    await cleanup_expired_codes(db)
    
    # Ищем код
    result = await db.execute(
        select(TelegramLinkCode).where(
            TelegramLinkCode.code == data.code
        )
    )
    link_code = result.scalar_one_or_none()
    
    if not link_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Неверный код привязки"
        )
    
    # Проверяем, не истек ли код
    if link_code.expires_at < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Код привязки истек. Создайте новый код в веб-приложении"
        )
    
    # Проверяем, не использован ли код
    if link_code.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Код привязки уже использован"
        )
    
    # Получаем пользователя
    user_result = await db.execute(
        select(User).where(User.id == link_code.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверяем, не привязан ли уже этот telegram_chat_id к другому пользователю
    existing_user = await db.execute(
        select(User).where(
            User.telegram_chat_id == data.telegram_chat_id,
            User.id != user.id
        )
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот Telegram аккаунт уже привязан к другому пользователю"
        )
    
    # Привязываем Telegram
    user.telegram_chat_id = data.telegram_chat_id
    
    # Помечаем код как использованный
    link_code.used = True
    link_code.used_at = datetime.now()
    
    await db.commit()
    await db.refresh(user)
    
    logger.info(
        f"Telegram аккаунт {data.telegram_chat_id} привязан к пользователю "
        f"{user.username} (ID: {user.id})"
    )
    
    return LinkTelegramResponse(
        success=True,
        message=(
            f"✅ Telegram успешно привязан к аккаунту {user.full_name or user.username}!\n\n"
            f"Теперь вы можете получать уведомления и работать с системой через бота."
        ),
        user_id=user.id,
        username=user.username
    )


@router.delete("/me/telegram/unlink")
async def unlink_telegram_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Отвязка Telegram аккаунта
    """
    if not current_user.telegram_chat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram аккаунт не привязан"
        )
    
    old_chat_id = current_user.telegram_chat_id
    current_user.telegram_chat_id = None
    
    await db.commit()
    
    logger.info(
        f"Telegram аккаунт {old_chat_id} отвязан от пользователя "
        f"{current_user.username} (ID: {current_user.id})"
    )
    
    return {"success": True, "message": "Telegram аккаунт успешно отвязан"}


@router.get("/me/telegram/status")
async def get_telegram_link_status(
    current_user: User = Depends(get_current_user)
):
    """
    Проверка статуса привязки Telegram
    """
    return {
        "linked": bool(current_user.telegram_chat_id),
        "telegram_chat_id": current_user.telegram_chat_id
    }
