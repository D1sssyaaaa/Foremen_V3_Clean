"""Роутер для заявок на материалы"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import require_roles, get_current_user
from app.core.models_base import UserRole, MaterialRequestStatus
from app.models import User
from app.materials.service import MaterialRequestService
from app.materials.schemas import (
    MaterialRequestCreate, MaterialRequestResponse, MaterialRequestListItem,
    MaterialRequestApproveRequest, MaterialRequestProcessRequest,
    MaterialRequestOrderRequest, MaterialRequestRejectRequest,
    MaterialRequestItemResponse
)

router = APIRouter()


@router.post("/", response_model=MaterialRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    data: MaterialRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.FOREMAN.value]))
):
    """
    Создание заявки на материалы
    
    - Доступно: FOREMAN
    - Статус: NEW
    - Срочность: normal, urgent, critical
    """
    service = MaterialRequestService(db)
    
    try:
        request = await service.create_request(data, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    request = await service.get_request_by_id(request.id)
    
    return MaterialRequestResponse(
        id=request.id,
        cost_object_id=request.cost_object_id,
        cost_object_name=request.cost_object.name,
        foreman_id=request.foreman_id,
        foreman_name=request.foreman.full_name,
        status=request.status,
        urgency=request.urgency,
        expected_delivery_date=request.expected_delivery_date,
        comment=request.comment,
        items=[
            MaterialRequestItemResponse(
                id=item.id,
                material_name=item.material_name,
                quantity=item.quantity,
                unit=item.unit,
                description=item.description,
                distributed_quantity=item.distributed_quantity,
                remaining_quantity=item.quantity - item.distributed_quantity
            )
            for item in request.items
        ],
        created_at=request.created_at,
        updated_at=request.updated_at
    )


@router.get("/", response_model=List[MaterialRequestListItem])
async def get_requests(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    urgency: Optional[str] = Query(None, description="Фильтр по срочности"),
    cost_object_id: Optional[int] = Query(None, description="Фильтр по объекту"),
    material_type: Optional[str] = Query(None, description="Фильтр по типу материалов: regular/inert"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.FOREMAN.value, 
        UserRole.MATERIALS_MANAGER.value, 
        UserRole.PROCUREMENT_MANAGER.value, 
        UserRole.MANAGER.value, 
        UserRole.ADMIN.value
    ]))
):
    """
    Получение списка заявок
    
    - FOREMAN: только свои заявки
    - MATERIALS_MANAGER, PROCUREMENT_MANAGER, MANAGER, ADMIN: все заявки
    - Фильтры: status, urgency, cost_object_id, material_type
    """
    service = MaterialRequestService(db)
    
    # Преобразование статуса
    status_enum = None
    if status:
        try:
            status_enum = MaterialRequestStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Некорректный статус: {status}"
            )
    
    # Определение прав доступа
    if UserRole.FOREMAN.value in current_user.roles and \
       UserRole.MATERIALS_MANAGER.value not in current_user.roles and \
       UserRole.PROCUREMENT_MANAGER.value not in current_user.roles:
        requests = await service.get_requests_by_foreman(current_user.id, status_enum, material_type)
    else:
        requests = await service.get_all_requests(status_enum, urgency, cost_object_id, material_type)
    
    return [
        MaterialRequestListItem(
            id=req.id,
            cost_object_name=req.cost_object.name,
            foreman_name=req.foreman.full_name,
            status=req.status,
            urgency=req.urgency,
            expected_delivery_date=req.expected_delivery_date,
            items_count=len(req.items),
            created_at=req.created_at
        )
        for req in requests
    ]


@router.get("/{request_id}", response_model=MaterialRequestResponse)
async def get_request_detail(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Детальная информация о заявке
    
    - FOREMAN: только свои заявки
    - MATERIALS_MANAGER, PROCUREMENT_MANAGER, MANAGER, ADMIN: все заявки
    """
    service = MaterialRequestService(db)
    request = await service.get_request_by_id(request_id)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заявка {request_id} не найдена"
        )
    
    # Проверка прав доступа
    if UserRole.FOREMAN.value in current_user.roles and \
       UserRole.MATERIALS_MANAGER.value not in current_user.roles and \
       UserRole.PROCUREMENT_MANAGER.value not in current_user.roles:
        if request.foreman_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен"
            )
    
    return MaterialRequestResponse(
        id=request.id,
        cost_object_id=request.cost_object_id,
        cost_object_name=request.cost_object.name,
        foreman_id=request.foreman_id,
        foreman_name=request.foreman.full_name,
        status=request.status,
        urgency=request.urgency,
        expected_delivery_date=request.expected_delivery_date,
        comment=request.comment,
        items=[
            MaterialRequestItemResponse(
                id=item.id,
                material_name=item.material_name,
                quantity=item.quantity,
                unit=item.unit,
                description=item.description,
                distributed_quantity=item.distributed_quantity,
                remaining_quantity=item.quantity - item.distributed_quantity
            )
            for item in request.items
        ],
        created_at=request.created_at,
        updated_at=request.updated_at
    )


@router.post("/{request_id}/approve", response_model=MaterialRequestResponse)
async def approve_request(
    request_id: int,
    request_data: MaterialRequestApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PROCUREMENT_MANAGER]))
):
    """
    Согласование заявки
    
    Переход: NEW -> APPROVED
    """
    service = MaterialRequestService(db)
    
    try:
        request = await service.approve_request(request_id, request_data.comment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    request = await service.get_request_by_id(request.id)
    
    return MaterialRequestResponse(
        id=request.id,
        cost_object_id=request.cost_object_id,
        cost_object_name=request.cost_object.name,
        foreman_id=request.foreman_id,
        foreman_name=request.foreman.full_name,
        status=request.status,
        urgency=request.urgency,
        expected_delivery_date=request.expected_delivery_date,
        comment=request.comment,
        items=[
            MaterialRequestItemResponse(
                id=item.id,
                material_name=item.material_name,
                quantity=item.quantity,
                unit=item.unit,
                description=item.description,
                distributed_quantity=item.distributed_quantity,
                remaining_quantity=item.quantity - item.distributed_quantity
            )
            for item in request.items
        ],
        created_at=request.created_at,
        updated_at=request.updated_at
    )


@router.post("/{request_id}/process", response_model=MaterialRequestResponse)
async def process_request(
    request_id: int,
    request_data: MaterialRequestProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MATERIALS_MANAGER]))
):
    """
    Взятие заявки в обработку
    
    Переход: APPROVED -> IN_PROCESSING
    """
    service = MaterialRequestService(db)
    
    try:
        request = await service.process_request(
            request_id, request_data.expected_delivery_date
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    request = await service.get_request_by_id(request.id)
    
    return MaterialRequestResponse(
        id=request.id,
        cost_object_id=request.cost_object_id,
        cost_object_name=request.cost_object.name,
        foreman_id=request.foreman_id,
        foreman_name=request.foreman.full_name,
        status=request.status,
        urgency=request.urgency,
        expected_delivery_date=request.expected_delivery_date,
        comment=request.comment,
        items=[
            MaterialRequestItemResponse(
                id=item.id,
                material_name=item.material_name,
                quantity=item.quantity,
                unit=item.unit,
                description=item.description,
                distributed_quantity=item.distributed_quantity,
                remaining_quantity=item.quantity - item.distributed_quantity
            )
            for item in request.items
        ],
        created_at=request.created_at,
        updated_at=request.updated_at
    )


@router.post("/{request_id}/order", response_model=MaterialRequestResponse)
async def order_materials(
    request_id: int,
    request_data: MaterialRequestOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MATERIALS_MANAGER]))
):
    """
    Размещение заказа материалов
    
    Переход: IN_PROCESSING -> ORDERED
    """
    service = MaterialRequestService(db)
    
    try:
        request = await service.order_materials(
            request_id, request_data.supplier, request_data.order_number
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    request = await service.get_request_by_id(request.id)
    
    return MaterialRequestResponse(
        id=request.id,
        cost_object_id=request.cost_object_id,
        cost_object_name=request.cost_object.name,
        foreman_id=request.foreman_id,
        foreman_name=request.foreman.full_name,
        status=request.status,
        urgency=request.urgency,
        expected_delivery_date=request.expected_delivery_date,
        comment=request.comment,
        items=[
            MaterialRequestItemResponse(
                id=item.id,
                material_name=item.material_name,
                quantity=item.quantity,
                unit=item.unit,
                description=item.description,
                distributed_quantity=item.distributed_quantity,
                remaining_quantity=item.quantity - item.distributed_quantity
            )
            for item in request.items
        ],
        created_at=request.created_at,
        updated_at=request.updated_at
    )


@router.post("/{request_id}/partial-delivery", response_model=MaterialRequestResponse)
async def mark_partial_delivery(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MATERIALS_MANAGER]))
):
    """
    Отметка частичной поставки
    
    Переход: ORDERED -> PARTIALLY_DELIVERED
    """
    service = MaterialRequestService(db)
    
    try:
        request = await service.mark_partial_delivery(request_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    request = await service.get_request_by_id(request.id)
    
    return MaterialRequestResponse(
        id=request.id,
        cost_object_id=request.cost_object_id,
        cost_object_name=request.cost_object.name,
        foreman_id=request.foreman_id,
        foreman_name=request.foreman.full_name,
        status=request.status,
        urgency=request.urgency,
        expected_delivery_date=request.expected_delivery_date,
        comment=request.comment,
        items=[
            MaterialRequestItemResponse(
                id=item.id,
                material_name=item.material_name,
                quantity=item.quantity,
                unit=item.unit,
                description=item.description,
                distributed_quantity=item.distributed_quantity,
                remaining_quantity=item.quantity - item.distributed_quantity
            )
            for item in request.items
        ],
        created_at=request.created_at,
        updated_at=request.updated_at
    )


@router.post("/{request_id}/ship", response_model=MaterialRequestResponse)
async def mark_shipped(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MATERIALS_MANAGER]))
):
    """
    Отметка полной отгрузки
    
    Переход: ORDERED/PARTIALLY_DELIVERED -> SHIPPED
    """
    service = MaterialRequestService(db)
    
    try:
        request = await service.mark_shipped(request_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    request = await service.get_request_by_id(request.id)
    
    return MaterialRequestResponse(
        id=request.id,
        cost_object_id=request.cost_object_id,
        cost_object_name=request.cost_object.name,
        foreman_id=request.foreman_id,
        foreman_name=request.foreman.full_name,
        status=request.status,
        urgency=request.urgency,
        expected_delivery_date=request.expected_delivery_date,
        comment=request.comment,
        items=[
            MaterialRequestItemResponse(
                id=item.id,
                material_name=item.material_name,
                quantity=item.quantity,
                unit=item.unit,
                description=item.description,
                distributed_quantity=item.distributed_quantity,
                remaining_quantity=item.quantity - item.distributed_quantity
            )
            for item in request.items
        ],
        created_at=request.created_at,
        updated_at=request.updated_at
    )


@router.post("/{request_id}/complete", response_model=MaterialRequestResponse)
async def complete_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MATERIALS_MANAGER]))
):
    """
    Завершение заявки
    
    Переход: SHIPPED -> COMPLETED
    Требует полного распределения всех позиций
    """
    service = MaterialRequestService(db)
    
    try:
        request = await service.complete_request(request_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    request = await service.get_request_by_id(request.id)
    
    return MaterialRequestResponse(
        id=request.id,
        cost_object_id=request.cost_object_id,
        cost_object_name=request.cost_object.name,
        foreman_id=request.foreman_id,
        foreman_name=request.foreman.full_name,
        status=request.status,
        urgency=request.urgency,
        expected_delivery_date=request.expected_delivery_date,
        comment=request.comment,
        items=[
            MaterialRequestItemResponse(
                id=item.id,
                material_name=item.material_name,
                quantity=item.quantity,
                unit=item.unit,
                description=item.description,
                distributed_quantity=item.distributed_quantity,
                remaining_quantity=item.quantity - item.distributed_quantity
            )
            for item in request.items
        ],
        created_at=request.created_at,
        updated_at=request.updated_at
    )


@router.post("/{request_id}/reject", response_model=MaterialRequestResponse)
async def reject_request(
    request_id: int,
    request_data: MaterialRequestRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.PROCUREMENT_MANAGER]))
):
    """
    Отклонение заявки
    
    Переход: NEW -> REJECTED
    """
    service = MaterialRequestService(db)
    
    try:
        request = await service.reject_request(request_id, request_data.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    request = await service.get_request_by_id(request.id)
    
    return MaterialRequestResponse(
        id=request.id,
        cost_object_id=request.cost_object_id,
        cost_object_name=request.cost_object.name,
        foreman_id=request.foreman_id,
        foreman_name=request.foreman.full_name,
        status=request.status,
        urgency=request.urgency,
        expected_delivery_date=request.expected_delivery_date,
        comment=request.comment,
        items=[
            MaterialRequestItemResponse(
                id=item.id,
                material_name=item.material_name,
                quantity=item.quantity,
                unit=item.unit,
                description=item.description,
                distributed_quantity=item.distributed_quantity,
                remaining_quantity=item.quantity - item.distributed_quantity
            )
            for item in request.items
        ],
        created_at=request.created_at,
        updated_at=request.updated_at
    )
