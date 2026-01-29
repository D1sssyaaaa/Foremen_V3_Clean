"""Роутер для работы с УПД (Универсальные Передаточные Документы)"""
import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import require_roles
from app.core.models_base import UserRole
from app.upd.service import UPDService
from app.upd.schemas import (
    UPDUploadResponse, UPDDetailResponse, UPDListItem,
    DistributeUPDRequest, DistributeUPDResponse,
    ParsingIssueResponse, UPDItemResponse
)

router = APIRouter()


@router.post("/upload", response_model=UPDUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_upd(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles([UserRole.ACCOUNTANT, UserRole.MATERIALS_MANAGER]))
):
    """
    Загрузка УПД из XML файла
    
    - Парсит XML в формате 5.01/5.03
    - Извлекает поставщика, номер, дату, строки товаров
    - Сохраняет в БД со статусом NEW
    - Поддерживает генераторы: Elewise, 1С, Diadoc, VO2_xslt
    - Автоматически проверяет на дубликаты
    - Отправляет WebSocket уведомления
    """
    # Проверка формата файла
    if not file.filename.endswith('.xml'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только XML файлы"
        )
    
    # Чтение содержимого
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка чтения файла: {str(e)}"
        )
    
    # Генерация пути для сохранения
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"uploads/upd/{filename}"
    
    # Создание директории если не существует
    os.makedirs("uploads/upd", exist_ok=True)
    
    # Сохранение файла
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Парсинг и сохранение в БД
    service = UPDService(db)
    try:
        upd = await service.upload_upd(content, file_path, auto_check_duplicate=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Подготовка ответа
    issues = service._deserialize_issues(upd.parsing_issues)
    
    # WebSocket уведомления
    from app.notifications.service import TelegramNotificationSender
    from app.core.models_base import UPDStatus
    
    notifier = TelegramNotificationSender("")
    
    if upd.status == UPDStatus.DUPLICATE:
        # Уведомление о дубликате
        await notifier.broadcast_websocket_to_roles(
            roles=[UserRole.ACCOUNTANT.value, UserRole.MATERIALS_MANAGER.value],
            notification_type="upd_duplicate_detected",
            title="Обнаружен дубликат УПД",
            message=f"УПД №{upd.document_number} от {upd.document_date} является дубликатом УПД #{upd.duplicate_of_id}",
            data={
                "upd_id": upd.id,
                "document_number": upd.document_number,
                "duplicate_of_id": upd.duplicate_of_id,
                "supplier_name": upd.supplier_name
            }
        )
    else:
        # Уведомление о новом УПД
        await notifier.broadcast_websocket_to_roles(
            roles=[UserRole.ACCOUNTANT.value, UserRole.MATERIALS_MANAGER.value],
            notification_type="upd_uploaded",
            title="Новый УПД загружен",
            message=f"УПД №{upd.document_number} от {upd.document_date}, поставщик: {upd.supplier_name}, сумма: {upd.total_with_vat:.2f} ₽",
            data={
                "upd_id": upd.id,
                "document_number": upd.document_number,
                "supplier_name": upd.supplier_name,
                "total_amount": upd.total_with_vat
            }
        )
    
    return UPDUploadResponse(
        id=upd.id,
        document_number=upd.document_number,
        document_date=upd.document_date,
        supplier_name=upd.supplier_name,
        supplier_inn=upd.supplier_inn,
        total_amount=upd.total_amount,
        total_vat=upd.total_vat,
        total_with_vat=upd.total_with_vat,
        items_count=len(upd.items),
        status=upd.status,
        xml_file_path=upd.xml_file_path,
        generator=upd.generator,
        parsing_issues_count=len(issues),
        parsing_issues=[ParsingIssueResponse(**issue) for issue in issues]
    )


@router.get("/unprocessed", response_model=List[UPDListItem])
async def get_unprocessed_upds(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles([UserRole.MATERIALS_MANAGER, UserRole.ACCOUNTANT]))
):
    """
    Получение необработанных УПД (статус NEW)
    
    Возвращает список УПД, ожидающих распределения
    """
    service = UPDService(db)
    upds = await service.get_unprocessed_upds()
    
    return [
        UPDListItem(
            id=upd.id,
            document_number=upd.document_number,
            document_date=upd.document_date,
            supplier_name=upd.supplier_name,
            total_with_vat=upd.total_with_vat,
            items_count=len(upd.items),
            status=upd.status,
            created_at=upd.created_at
        )
        for upd in upds
    ]


@router.get("/{upd_id}", response_model=UPDDetailResponse)
async def get_upd_detail(
    upd_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles([UserRole.MATERIALS_MANAGER, UserRole.ACCOUNTANT, UserRole.MANAGER]))
):
    """
    Детальная информация об УПД
    
    Возвращает все данные УПД включая строки товаров и проблемы парсинга
    """
    service = UPDService(db)
    upd = await service.get_upd_by_id(upd_id)
    
    if not upd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"УПД с ID {upd_id} не найден"
        )
    
    issues = service._deserialize_issues(upd.parsing_issues)
    
    return UPDDetailResponse(
        id=upd.id,
        document_number=upd.document_number,
        document_date=upd.document_date,
        supplier_name=upd.supplier_name,
        supplier_inn=upd.supplier_inn,
        buyer_name=None,
        buyer_inn=None,
        total_amount=upd.total_amount,
        total_vat=upd.total_vat,
        total_with_vat=upd.total_with_vat,
        status=upd.status,
        xml_file_path=upd.xml_file_path,
        generator=upd.generator,
        format_version=None,
        items=[
            UPDItemResponse(
                id=item.id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit=item.unit,
                price=item.price,
                amount=item.amount,
                vat_rate=item.vat_rate,
                vat_amount=item.vat_amount,
                total_with_vat=item.total_with_vat,
                okei_code=None
            )
            for item in upd.items
        ],
        parsing_issues=[ParsingIssueResponse(**issue) for issue in issues],
        created_at=upd.created_at,
        updated_at=upd.updated_at
    )


@router.post("/{upd_id}/distribute", response_model=DistributeUPDResponse)
async def distribute_upd(
    upd_id: int,
    request: DistributeUPDRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles([UserRole.MATERIALS_MANAGER]))
):
    """
    Распределение УПД по объектам/заявкам
    
    - Создает записи распределения
    - Создает записи затрат по объектам
    - Переводит УПД в статус DISTRIBUTED
    - Отправляет WebSocket уведомления
    - Логирует в историю распределения
    """
    service = UPDService(db)
    
    try:
        upd = await service.distribute_upd(upd_id, request.distributions, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Подсчет созданных записей
    total_distributed = sum(d.distributed_amount for d in request.distributions)
    
    # WebSocket уведомления
    from app.notifications.service import TelegramNotificationSender
    
    notifier = TelegramNotificationSender("")
    
    # Уведомление о распределении УПД
    await notifier.broadcast_websocket_to_roles(
        roles=[UserRole.ACCOUNTANT.value, UserRole.MANAGER.value],
        notification_type="upd_distributed",
        title="УПД распределён",
        message=f"УПД №{upd.document_number} распределён на {len(request.distributions)} объектов/заявок на сумму {total_distributed:.2f} ₽",
        data={
            "upd_id": upd.id,
            "document_number": upd.document_number,
            "total_distributed": total_distributed,
            "distributions_count": len(request.distributions)
        }
    )
    
    return DistributeUPDResponse(
        upd_id=upd.id,
        new_status=upd.status,
        total_distributed_amount=total_distributed,
        distributions_count=len(request.distributions),
        cost_entries_created=len(request.distributions)
    )


@router.get("/{upd_id}/duplicates", response_model=List[UPDListItem])
async def find_duplicates(
    upd_id: int,
    tolerance_days: int = 3,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles([UserRole.ACCOUNTANT, UserRole.MATERIALS_MANAGER, UserRole.MANAGER]))
):
    """
    Поиск потенциальных дубликатов УПД
    
    Ищет УПД с таким же номером документа и датой в пределах tolerance_days
    
    Args:
        upd_id: ID УПД для проверки
        tolerance_days: допустимое отклонение по дате (по умолчанию 3 дня)
    """
    service = UPDService(db)
    
    try:
        duplicates = await service.find_potential_duplicates(upd_id, tolerance_days)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return [
        UPDListItem(
            id=dup.id,
            document_number=dup.document_number,
            document_date=dup.document_date,
            supplier_name=dup.supplier_name,
            total_with_vat=dup.total_with_vat,
            items_count=len(dup.items) if dup.items else 0,
            status=dup.status,
            created_at=dup.created_at
        )
        for dup in duplicates
    ]


@router.post("/{upd_id}/mark-duplicate")
async def mark_upd_as_duplicate(
    upd_id: int,
    original_upd_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles([UserRole.ACCOUNTANT, UserRole.MANAGER]))
):
    """
    Пометить УПД как дубликат другого УПД
    
    Args:
        upd_id: ID УПД, который является дубликатом
        original_upd_id: ID оригинального УПД
    """
    service = UPDService(db)
    
    try:
        upd = await service.mark_as_duplicate(upd_id, original_upd_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return {
        "message": f"УПД #{upd_id} помечен как дубликат УПД #{original_upd_id}",
        "upd_id": upd.id,
        "status": upd.status,
        "duplicate_of_id": upd.duplicate_of_id,
        "duplicate_checked_at": upd.duplicate_checked_at
    }


@router.get("/{upd_id}/distribution-history")
async def get_distribution_history(
    upd_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles([UserRole.ACCOUNTANT, UserRole.MATERIALS_MANAGER, UserRole.MANAGER]))
):
    """
    Получение истории распределения УПД
    
    Возвращает все изменения распределения с информацией о пользователях и датах
    
    Args:
        upd_id: ID УПД
        limit: максимальное количество записей (по умолчанию 50)
    """
    service = UPDService(db)
    
    # Проверка существования УПД
    upd = await service.get_upd_by_id(upd_id)
    if not upd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"УПД с ID {upd_id} не найден"
        )
    
    history = await service.get_distribution_history(upd_id, limit)
    
    return {
        "upd_id": upd_id,
        "document_number": upd.document_number,
        "history": [
            {
                "id": h.id,
                "action": h.action,
                "user_id": h.user_id,
                "old_distribution": h.old_distribution,
                "new_distribution": h.new_distribution,
                "description": h.description,
                "created_at": h.created_at
            }
            for h in history
        ],
        "total_changes": len(history)
    }


@router.put("/{upd_id}/redistribute", response_model=DistributeUPDResponse)
async def redistribute_upd(
    upd_id: int,
    request: DistributeUPDRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles([UserRole.MATERIALS_MANAGER, UserRole.MANAGER]))
):
    """
    Корректировка распределения УПД
    
    - Удаляет старое распределение
    - Создаёт новое распределение
    - Пересчитывает затраты по объектам
    - Логирует изменения в историю
    - Отправляет WebSocket уведомления
    
    Нельзя изменить архивированные или дубликаты УПД
    """
    service = UPDService(db)
    
    try:
        upd = await service.redistribute_upd(upd_id, current_user.id, request.distributions)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Подсчет нового распределения
    total_distributed = sum(d.distributed_amount for d in request.distributions)
    
    # WebSocket уведомления
    from app.notifications.service import TelegramNotificationSender
    
    notifier = TelegramNotificationSender("")
    
    # Уведомление о корректировке распределения
    await notifier.broadcast_websocket_to_roles(
        roles=[UserRole.ACCOUNTANT.value, UserRole.MANAGER.value],
        notification_type="upd_redistributed",
        title="УПД корректирован",
        message=f"Распределение УПД №{upd.document_number} изменено. Новая сумма: {total_distributed:.2f} ₽",
        data={
            "upd_id": upd.id,
            "document_number": upd.document_number,
            "total_distributed": total_distributed,
            "distributions_count": len(request.distributions),
            "user_id": current_user.id
        }
    )
    
    return DistributeUPDResponse(
        upd_id=upd.id,
        new_status=upd.status,
        total_distributed_amount=total_distributed,
        distributions_count=len(request.distributions),
        cost_entries_created=len(request.distributions)
    )

