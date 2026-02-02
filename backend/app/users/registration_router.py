"""
Роутер для заявок на регистрацию
"""
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models import User, RegistrationRequest
from app.auth.dependencies import get_current_user, require_roles
from app.auth.security import get_password_hash
from app.core.models_base import RegistrationRequestStatus, UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


# ===== Schemas =====

class RegistrationRequestCreate(BaseModel):
    """Схема создания заявки на регистрацию (из бота)"""
    full_name: str
    birth_date: str  # YYYY-MM-DD
    phone: str
    telegram_chat_id: str
    telegram_username: Optional[str] = None
    requested_role: Optional[str] = None


class RegistrationRequestResponse(BaseModel):
    """Схема ответа заявки на регистрацию"""
    id: int
    full_name: str
    birth_date: str
    phone: str
    telegram_chat_id: str
    telegram_username: Optional[str]
    requested_role: Optional[str]
    status: str
    created_at: datetime
    processed_by_id: Optional[int]
    processed_at: Optional[datetime]
    rejection_reason: Optional[str]
    
    class Config:
        from_attributes = True


class ApproveRequest(BaseModel):
    """Схема для одобрения заявки"""
    roles: List[str]

class RejectRequest(BaseModel):
    """Схема для отклонения заявки"""
    reason: str

@router.post("/", response_model=RegistrationRequestResponse)
async def create_registration_request(
    data: RegistrationRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Создание заявки на регистрацию
    Публичный endpoint (без авторизации)
    """
    # Проверяем, есть ли уже заявка с таким телефоном
    existing_phone = await db.execute(
        select(RegistrationRequest).where(
            RegistrationRequest.phone == data.phone,
            RegistrationRequest.status == RegistrationRequestStatus.PENDING.value
        )
    )
    if existing_phone.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заявка с таким номером телефона уже существует и находится на рассмотрении"
        )

    # Проверяем, есть ли уже заявка с таким telegram_chat_id
    existing_tg = await db.execute(
        select(RegistrationRequest).where(
            RegistrationRequest.telegram_chat_id == data.telegram_chat_id,
            RegistrationRequest.status == RegistrationRequestStatus.PENDING.value
        )
    )
    if existing_tg.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заявка с этого аккаунта Telegram уже существует"
        )
    
    # Парсим дату рождения
    try:
        birth_date = datetime.strptime(data.birth_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат даты. Используйте YYYY-MM-DD"
        )
    request = RegistrationRequest(
        full_name=data.full_name,
        birth_date=birth_date,
        phone=data.phone,
        telegram_chat_id=data.telegram_chat_id,
        telegram_username=data.telegram_username,
        requested_role=data.requested_role,
        status=RegistrationRequestStatus.PENDING.value
    )
    
    db.add(request)
    await db.commit()
    await db.refresh(request)
    
    logger.info(f"Created registration request #{request.id} for {data.full_name} (Role: {data.requested_role})")
    
    # TODO: Отправить уведомление менеджерам
    
    return RegistrationRequestResponse(
        id=request.id,
        full_name=request.full_name,
        birth_date=request.birth_date.isoformat(),
        phone=request.phone,
        telegram_chat_id=request.telegram_chat_id,
        telegram_username=request.telegram_username,
        requested_role=request.requested_role,
        status=request.status,
        created_at=request.created_at,
        processed_by_id=request.processed_by_id,
        processed_at=request.processed_at,
        rejection_reason=request.rejection_reason
    )


@router.get("/", response_model=List[RegistrationRequestResponse])
async def get_registration_requests(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_roles([
        UserRole.MANAGER.value, 
        UserRole.ADMIN.value
    ])),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка заявок на регистрацию
    Только для MANAGER и ADMIN
    """
    query = select(RegistrationRequest).order_by(RegistrationRequest.created_at.desc())
    
    if status_filter:
        query = query.where(RegistrationRequest.status == status_filter)
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return [
        RegistrationRequestResponse(
            id=r.id,
            full_name=r.full_name,
            birth_date=r.birth_date.isoformat(),
            phone=r.phone,
            telegram_chat_id=r.telegram_chat_id,
            telegram_username=r.telegram_username,
            status=r.status,
            created_at=r.created_at,
            processed_by_id=r.processed_by_id,
            processed_at=r.processed_at,
            rejection_reason=r.rejection_reason
        )
        for r in requests
    ]


@router.get("/pending/count")
async def get_pending_count(
    current_user: User = Depends(require_roles([
        UserRole.MANAGER.value, 
        UserRole.ADMIN.value
    ])),
    db: AsyncSession = Depends(get_db)
):
    """Количество ожидающих заявок"""
    result = await db.execute(
        select(RegistrationRequest).where(
            RegistrationRequest.status == RegistrationRequestStatus.PENDING.value
        )
    )
    count = len(result.scalars().all())
    return {"count": count}


@router.post("/{request_id}/approve")
async def approve_registration(
    request_id: int,
    data: ApproveRequest,
    current_user: User = Depends(require_roles([
        UserRole.MANAGER.value, 
        UserRole.ADMIN.value
    ])),
    db: AsyncSession = Depends(get_db)
):
    """
    Одобрение заявки на регистрацию
    Создает нового пользователя
    """
    # Получаем заявку
    result = await db.execute(
        select(RegistrationRequest).where(RegistrationRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    if request.status != RegistrationRequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Заявка уже обработана (статус: {request.status})"
        )
    
    # Генерируем username из telegram_username или chat_id
    username = request.telegram_username or f"tg_{request.telegram_chat_id}"
    
    # Проверяем уникальность username
    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none():
        username = f"{username}_{request.id}"
    
    # Проверяем уникальность телефона
    existing_phone = await db.execute(select(User).where(User.phone == request.phone))
    if existing_phone.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким номером телефона уже существует"
        )
    
    # Создаем пользователя
    new_user = User(
        username=username,
        phone=request.phone,
        hashed_password=get_password_hash(f"tg_{request.telegram_chat_id}"),
        roles=data.roles,
        telegram_chat_id=request.telegram_chat_id,
        full_name=request.full_name,
        birth_date=request.birth_date,
        is_active=True
    )
    
    db.add(new_user)
    await db.flush()
    
    # Обновляем заявку
    request.status = RegistrationRequestStatus.APPROVED.value
    request.processed_by_id = current_user.id
    request.processed_at = datetime.utcnow()
    request.created_user_id = new_user.id
    
    await db.commit()
    
    logger.info(f"Approved registration request #{request_id}, created user #{new_user.id}")
    
    # TODO: Отправить уведомление пользователю в Telegram
    
    return {
        "message": "Заявка одобрена, пользователь создан",
        "user_id": new_user.id,
        "username": new_user.username
    }


@router.post("/{request_id}/reject")
async def reject_registration(
    request_id: int,
    data: RejectRequest,
    current_user: User = Depends(require_roles([
        UserRole.MANAGER.value, 
        UserRole.ADMIN.value
    ])),
    db: AsyncSession = Depends(get_db)
):
    """
    Отклонение заявки на регистрацию
    """
    # Получаем заявку
    result = await db.execute(
        select(RegistrationRequest).where(RegistrationRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    if request.status != RegistrationRequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Заявка уже обработана (статус: {request.status})"
        )
    
    # Обновляем заявку
    request.status = RegistrationRequestStatus.REJECTED.value
    request.processed_by_id = current_user.id
    request.processed_at = datetime.utcnow()
    request.rejection_reason = data.reason
    
    await db.commit()
    
    logger.info(f"Rejected registration request #{request_id}: {data.reason}")
    
    # TODO: Отправить уведомление пользователю в Telegram
    
    return {"message": "Заявка отклонена", "reason": data.reason}


@router.get("/by-telegram/{telegram_chat_id}", response_model=RegistrationRequestResponse)
async def get_registration_request_by_telegram(
    telegram_chat_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение заявки по telegram_chat_id (публичный endpoint для бота)
    """
    result = await db.execute(
        select(RegistrationRequest).where(
            RegistrationRequest.telegram_chat_id == telegram_chat_id
        )
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    return RegistrationRequestResponse(
        id=request.id,
        full_name=request.full_name,
        birth_date=request.birth_date.isoformat(),
        phone=request.phone,
        telegram_chat_id=request.telegram_chat_id,
        telegram_username=request.telegram_username,
        status=request.status,
        created_at=request.created_at,
        processed_by_id=request.processed_by_id,
        processed_at=request.processed_at,
        rejection_reason=request.rejection_reason
    )


@router.get("/{request_id}", response_model=RegistrationRequestResponse)
async def get_registration_request(
    request_id: int,
    current_user: User = Depends(require_roles([
        UserRole.MANAGER.value, 
        UserRole.ADMIN.value
    ])),
    db: AsyncSession = Depends(get_db)
):
    """Получение заявки по ID"""
    result = await db.execute(
        select(RegistrationRequest).where(RegistrationRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    return RegistrationRequestResponse(
        id=request.id,
        full_name=request.full_name,
        birth_date=request.birth_date.isoformat(),
        phone=request.phone,
        telegram_chat_id=request.telegram_chat_id,
        telegram_username=request.telegram_username,
        status=request.status,
        created_at=request.created_at,
        processed_by_id=request.processed_by_id,
        processed_at=request.processed_at,
        rejection_reason=request.rejection_reason
    )