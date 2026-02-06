"""
Роутер для аутентификации
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
import logging
import json
import os
import uuid
from pathlib import Path
from app.core.database import get_db
from app.models import User
from app.auth import schemas
from app.auth.security import (
    verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
)
from app.auth.dependencies import get_current_user

# Настройка логирования
logger = logging.getLogger(__name__)

router = APIRouter()

# Директория для загрузки фотографий профиля
UPLOAD_DIR = Path("uploads/profile_photos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Разрешенные форматы изображений
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".jfif", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
async def register(
    request: schemas.RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя
    """
    try:
        logger.info(f"Registration attempt for username: {request.username}")
        
        # Проверка существования пользователя
        result = await db.execute(select(User).where(User.username == request.username))
        if result.scalar_one_or_none():
            logger.warning(f"Username already exists: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        result = await db.execute(select(User).where(User.phone == request.phone))
        if result.scalar_one_or_none():
            logger.warning(f"Phone already exists: {request.phone}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone already registered"
            )
        
        # Создание пользователя
        user = User(
            username=request.username,
            hashed_password=get_password_hash(request.password),
            phone=request.phone,
            full_name=request.full_name,
            email=request.email,
            roles=request.roles,
            is_active=True
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User created successfully: {request.username}, id={user.id}")
        
        # Парсинг ролей из JSON (для SQLite совместимости)
        roles = user.roles if isinstance(user.roles, list) else json.loads(user.roles) if isinstance(user.roles, str) else []
        
        # Создание токенов - конвертируем user.id в строку для JWT
        user_id_str = str(user.id)
        access_token = create_access_token(data={"sub": user_id_str, "roles": roles})
        refresh_token = create_refresh_token(data={"sub": user_id_str})
        
        return schemas.Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/login", response_model=schemas.Token)
async def login(
    request: schemas.LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Вход в систему (получение JWT токенов)
    """
    try:
        logger.info(f"Login attempt for user: {request.username}")
        
        # Поиск пользователя
        result = await db.execute(select(User).where(User.username == request.username))
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User not found: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Проверка пароля
        if not verify_password(request.password, user.hashed_password):
            logger.warning(f"Invalid password for user: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted login: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        # Парсинг ролей из JSON (для SQLite совместимости)
        # Парсинг ролей из JSON (для SQLite совместимости)
        roles = []
        if isinstance(user.roles, list):
            roles = user.roles
        elif isinstance(user.roles, str):
            try:
                roles = json.loads(user.roles)
            except (json.JSONDecodeError, TypeError):
                logger.error(f"Failed to parse roles for user {request.username}: {user.roles}")
                roles = []
        else:
            roles = []
        logger.debug(f"Parsed roles for {request.username}: {roles}")
        
        # Создание токенов - конвертируем user.id в строку для JWT
        user_id_str = str(user.id)
        logger.debug(f"Creating tokens for user_id: {user_id_str}")
        
        access_token = create_access_token(data={"sub": user_id_str, "roles": roles})
        refresh_token = create_refresh_token(data={"sub": user_id_str})
        
        logger.info(f"Successful login for user: {request.username}")
        
        return schemas.Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("LOGIN CRASH TRACEBACK:")
        traceback.print_exc()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(
    request: schemas.RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление access токена по refresh токену
    """
    try:
        logger.debug("Refresh token request received")
        
        payload = decode_token(request.refresh_token)
        
        if payload is None or payload.get("type") != "refresh":
            logger.warning("Invalid refresh token type")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            logger.warning("Missing user ID in refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Конвертируем обратно в int для поиска в БД
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id format in token: {user_id_str}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Проверка существования пользователя
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            logger.warning(f"User not found or inactive: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Парсинг ролей из JSON (для SQLite совместимости)
        roles = user.roles if isinstance(user.roles, list) else json.loads(user.roles) if isinstance(user.roles, str) else []
        
        # Создание новых токенов
        access_token = create_access_token(data={"sub": user_id_str, "roles": roles})
        new_refresh_token = create_refresh_token(data={"sub": user_id_str})
        
        logger.info(f"Tokens refreshed successfully for user_id: {user_id}")
        
        return schemas.Token(
            access_token=access_token,
            refresh_token=new_refresh_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Получение данных текущего пользователя
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "phone": current_user.phone,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "birth_date": current_user.birth_date,
        "profile_photo_url": current_user.profile_photo_url,
        "roles": current_user.roles,
        "telegram_chat_id": current_user.telegram_chat_id,
        "is_active": current_user.is_active
    }


@router.patch("/me/profile")
async def update_profile(
    full_name: Optional[str] = Body(None),
    email: Optional[str] = Body(None),
    birth_date: Optional[str] = Body(None),
    profile_photo_url: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление профиля пользователя
    """
    from datetime import datetime
    
    if full_name is not None:
        current_user.full_name = full_name
    
    if email is not None:
        # Проверка уникальности email если он изменился
        if email != current_user.email:
            result = await db.execute(select(User).where(User.email == email))
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email уже используется другим пользователем"
                )
        current_user.email = email
    
    if birth_date is not None:
        try:
            current_user.birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат даты. Используйте YYYY-MM-DD"
            )
    
    if profile_photo_url is not None:
        current_user.profile_photo_url = profile_photo_url
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "birth_date": current_user.birth_date,
        "profile_photo_url": current_user.profile_photo_url,
        "message": "Профиль обновлен"
    }


@router.post("/me/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Загрузка фотографии профиля
    """
    # Логирование полученного файла
    logger.info(f"Photo upload attempt: filename={file.filename}, content_type={file.content_type}")
    
    # Проверка наличия имени файла
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Имя файла не указано"
        )
    
    # Проверка расширения файла
    file_ext = os.path.splitext(file.filename)[1].lower()
    logger.info(f"Extracted file extension: {file_ext}")
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый формат файла '{file_ext}'. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Проверка размера файла
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимум {MAX_FILE_SIZE // (1024*1024)} МБ"
        )
    
    # Удаление старого файла если есть
    if current_user.profile_photo_url and current_user.profile_photo_url.startswith('/uploads/'):
        old_file_path = Path(current_user.profile_photo_url.lstrip('/'))
        if old_file_path.exists():
            try:
                old_file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete old photo: {e}")
    
    # Генерация уникального имени файла
    unique_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Сохранение файла
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Обновление URL в БД
    photo_url = f"/uploads/profile_photos/{unique_filename}"
    current_user.profile_photo_url = photo_url
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "profile_photo_url": photo_url,
        "message": "Фото профиля загружено"
    }


@router.delete("/me/photo")
async def delete_profile_photo(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Удаление фотографии профиля
    """
    if not current_user.profile_photo_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фото профиля не установлено"
        )
    
    # Удаление файла
    if current_user.profile_photo_url.startswith('/uploads/'):
        file_path = Path(current_user.profile_photo_url.lstrip('/'))
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete photo file: {e}")
    
    # Очистка URL в БД
    current_user.profile_photo_url = None
    await db.commit()
    
    return {"message": "Фото профиля удалено"}


@router.post("/telegram/login", response_model=schemas.Token)
async def telegram_login(
    telegram_user_id: int = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    """
    Авторизация пользователя через Telegram ID
    
    - Используется ботом для получения токена доступа
    - Требует предварительной привязки telegram_chat_id к пользователю
    """
    try:
        # Поиск пользователя по Telegram ID
        result = await db.execute(
            select(User).where(User.telegram_chat_id == telegram_user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Telegram login failed: user not found for ID {telegram_user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь с таким Telegram ID не найден. Обратитесь к администратору для привязки аккаунта."
            )
        
        if not user.is_active:
            logger.warning(f"Telegram login failed: user {user.username} is not active")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Аккаунт деактивирован"
            )
        
        # Создание токенов (sub должен быть user.id как строка)
        user_id_str = str(user.id)
        roles = user.roles or []
        access_token = create_access_token(data={"sub": user_id_str, "roles": roles})
        refresh_token = create_refresh_token(data={"sub": user_id_str})
        
        logger.info(f"Telegram login successful for user {user.username} (TG ID: {telegram_user_id})")
        
        return schemas.Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Telegram login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


class TelegramMiniAppAuthRequest(BaseModel):
    """Схема запроса авторизации через Telegram Mini App"""
    init_data: str


@router.post("/telegram", response_model=schemas.Token)
async def telegram_miniapp_auth(
    request: TelegramMiniAppAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Авторизация через Telegram Mini App
    
    - Проверяет подпись initData от Telegram Web App
    - Возвращает JWT токены для доступа к API
    """
    from hashlib import sha256
    import hmac
    from urllib.parse import parse_qsl
    from app.core.config import settings
    
    try:
        logger.info("Telegram Mini App auth attempt")
        
        # 1. Парсинг initData
        parsed_data = dict(parse_qsl(request.init_data))
        received_hash = parsed_data.pop('hash', '')
        
        if not received_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing hash in init data"
            )
        
        # 2. Проверка подписи
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        secret_key = sha256(settings.telegram_bot_token.encode()).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), sha256).hexdigest()
        
        if calculated_hash != received_hash:
            logger.warning("Invalid Telegram Mini App signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication data"
            )
        
        # 3. Извлечение telegram_id
        user_data = json.loads(parsed_data.get('user', '{}'))
        telegram_id = user_data.get('id')
        
        if not telegram_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user ID in init data"
            )
        
        # 4. Поиск пользователя
        result = await db.execute(
            select(User).where(User.telegram_chat_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User not found for Telegram ID {telegram_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден. Обратитесь к администратору."
            )
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted Mini App login: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Аккаунт деактивирован"
            )
        
        # 5. Создание JWT токенов
        user_id_str = str(user.id)
        roles = user.roles if isinstance(user.roles, list) else json.loads(user.roles) if isinstance(user.roles, str) else []
        
        access_token = create_access_token(data={"sub": user_id_str, "roles": roles})
        refresh_token = create_refresh_token(data={"sub": user_id_str})
        
        logger.info(f"Telegram Mini App auth successful for user {user.username} (TG ID: {telegram_id})")
        
        return schemas.Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Telegram Mini App auth: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


class TelegramRegisterRequest(BaseModel):
    """Схема запроса регистрации через Telegram"""
    username: str
    password: str
    full_name: str
    phone: str | None = None
    email: str | None = None
    telegram_chat_id: int


@router.post("/telegram/register", response_model=schemas.Token)
async def telegram_register(
    data: TelegramRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя через Telegram бота
    
    - Создает нового пользователя с привязкой к Telegram
    - Автоматически возвращает токены для входа
    """
    try:
        # Проверяем, не существует ли уже пользователь с таким telegram_chat_id
        result = await db.execute(
            select(User).where(User.telegram_chat_id == data.telegram_chat_id)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.warning(f"Telegram registration failed: user already exists for TG ID {data.telegram_chat_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с этим Telegram аккаунтом уже зарегистрирован"
            )
        
        # Проверяем уникальность username
        result = await db.execute(
            select(User).where(User.username == data.username)
        )
        if result.scalar_one_or_none():
            # Генерируем уникальный username
            data.username = f"{data.username}_{data.telegram_chat_id}"
        
        # Создаем нового пользователя
        hashed_password = get_password_hash(data.password)
        
        new_user = User(
            username=data.username,
            hashed_password=hashed_password,
            full_name=data.full_name,
            phone=data.phone,
            email=data.email,
            telegram_chat_id=data.telegram_chat_id,
            roles=["FOREMAN"],  # Базовая роль для новых пользователей
            is_active=True
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # Создание токенов (sub должен быть user.id как строка)
        user_id_str = str(new_user.id)
        roles = new_user.roles or []
        access_token = create_access_token(data={"sub": user_id_str, "roles": roles})
        refresh_token = create_refresh_token(data={"sub": user_id_str})
        
        logger.info(f"Telegram registration successful for user {new_user.username} (TG ID: {data.telegram_chat_id})")
        
        return schemas.Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Telegram registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )



