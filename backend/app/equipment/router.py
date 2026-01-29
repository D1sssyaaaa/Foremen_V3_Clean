"""Роутер для заявок на аренду техники"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import require_roles, get_current_user
from app.core.models_base import UserRole, EquipmentOrderStatus
from app.models import User
from app.equipment.service import EquipmentService
from app.equipment.schemas import (
    EquipmentOrderCreate, EquipmentOrderResponse, EquipmentOrderListItem,
    EquipmentApproveRequest, EquipmentCostCreate,
    EquipmentCostResponse, CancelOrderRequest
)

router = APIRouter()

@router.post("/", response_model=EquipmentOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: EquipmentOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.FOREMAN.value]))
):
    """
    Создание заявки на технику
    
    - Доступно: FOREMAN
    - Статус: NEW
    """
    service = EquipmentService(db)
    
    try:
        order = await service.create_order(data, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    order = await service.get_order_by_id(order.id)
    
    return EquipmentOrderResponse(
        id=order.id,
        cost_object_id=order.cost_object_id,
        cost_object_name=order.cost_object.name,
        foreman_id=order.foreman_id,
        foreman_name=order.foreman.full_name,
        equipment_type=order.equipment_type,
        
        start_date=order.start_date,
        end_date=order.end_date,
        supplier=order.supplier,
        comment=order.comment,
        status=order.status,

        created_at=order.created_at,
        updated_at=order.updated_at
    )

@router.get("/", response_model=List[EquipmentOrderListItem])
async def get_orders(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    cost_object_id: Optional[int] = Query(None, description="Фильтр по объекту"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.FOREMAN.value,
        UserRole.EQUIPMENT_MANAGER.value,
        UserRole.MANAGER.value,
        UserRole.ADMIN.value
    ]))
):
    """
    Получение списка заявок
    
    - FOREMAN: только свои заявки
    - EQUIPMENT_MANAGER, MANAGER, ADMIN: все заявки
    """
    service = EquipmentService(db)
    
    # Преобразование статуса
    status_enum = None
    if status:
        try:
            status_enum = EquipmentOrderStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Некорректный статус: {status}"
            )
    
    # Определение прав доступа
    if UserRole.FOREMAN.value in current_user.roles and \
       UserRole.EQUIPMENT_MANAGER.value not in current_user.roles:
        orders = await service.get_orders_by_foreman(current_user.id, status_enum)
    else:
        orders = await service.get_all_orders(status_enum, cost_object_id)
    
    return [
        EquipmentOrderListItem(
            id=order.id,
            cost_object_name=order.cost_object.name,
            foreman_name=order.foreman.full_name,
            equipment_type=order.equipment_type,
            start_date=order.start_date,
            end_date=order.end_date,
            status=order.status,
            created_at=order.created_at
        )
        for order in orders
    ]

@router.get("/{order_id}", response_model=EquipmentOrderResponse)
async def get_order_detail(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Детальная информация о заявке
    
    - FOREMAN: только свои заявки
    - EQUIPMENT_MANAGER, MANAGER, ADMIN: все заявки
    """
    service = EquipmentService(db)
    order = await service.get_order_by_id(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заявка {order_id} не найдена"
        )
    
    # Проверка прав доступа
    if UserRole.FOREMAN.value in current_user.roles and \
       UserRole.EQUIPMENT_MANAGER.value not in current_user.roles:
        if order.foreman_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен"
            )
    
    return EquipmentOrderResponse(
        id=order.id,
        cost_object_id=order.cost_object_id,
        cost_object_name=order.cost_object.name,
        foreman_id=order.foreman_id,
        foreman_name=order.foreman.full_name,
        equipment_type=order.equipment_type,
        
        start_date=order.start_date,
        end_date=order.end_date,
        supplier=order.supplier,
        comment=order.comment,
        status=order.status,

        created_at=order.created_at,
        updated_at=order.updated_at
    )

@router.post("/{order_id}/approve", response_model=EquipmentOrderResponse)
async def approve_order(
    order_id: int,
    request: EquipmentApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.EQUIPMENT_MANAGER]))
):
    """
    Утверждение заявки
    
    Переход: NEW -> APPROVED
    """
    service = EquipmentService(db)
    
    try:
        order = await service.approve_order(
            order_id, request.hour_rate, request.supplier
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    order = await service.get_order_by_id(order.id)
    
    return EquipmentOrderResponse(
        id=order.id,
        cost_object_id=order.cost_object_id,
        cost_object_name=order.cost_object.name,
        foreman_id=order.foreman_id,
        foreman_name=order.foreman.full_name,
        equipment_type=order.equipment_type,
        
        start_date=order.start_date,
        end_date=order.end_date,
        supplier=order.supplier,
        comment=order.comment,
        status=order.status,

        created_at=order.created_at,
        updated_at=order.updated_at
    )

@router.post("/{order_id}/hours", response_model=EquipmentCostResponse, status_code=status.HTTP_201_CREATED)
async def add_hours(
    order_id: int,
    data: EquipmentCostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.EQUIPMENT_MANAGER, UserRole.FOREMAN]))
):
    """
    Учет фактических часов работы техники
    
    Создает запись затрат и обновляет итоговые суммы
    """
    service = EquipmentService(db)
    
    try:
        equipment_cost = await service.add_hours(order_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return EquipmentCostResponse(
        id=equipment_cost.id,
        equipment_order_id=equipment_cost.equipment_order_id,
        hours_worked=equipment_cost.hours_worked,
        work_date=equipment_cost.work_date,
        hour_rate=equipment_cost.hour_rate,
        total_amount=equipment_cost.total_amount,
        description=equipment_cost.description,
        created_at=equipment_cost.created_at
    )

@router.post("/{order_id}/complete", response_model=EquipmentOrderResponse)
async def complete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.EQUIPMENT_MANAGER]))
):
    """
    Завершение заявки
    
    Переход: IN_PROGRESS -> COMPLETED
    """
    service = EquipmentService(db)
    
    try:
        order = await service.complete_order(order_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    order = await service.get_order_by_id(order.id)
    
    return EquipmentOrderResponse(
        id=order.id,
        cost_object_id=order.cost_object_id,
        cost_object_name=order.cost_object.name,
        foreman_id=order.foreman_id,
        foreman_name=order.foreman.full_name,
        equipment_type=order.equipment_type,
        
        start_date=order.start_date,
        end_date=order.end_date,
        supplier=order.supplier,
        comment=order.comment,
        status=order.status,

        created_at=order.created_at,
        updated_at=order.updated_at
    )

@router.post("/{order_id}/request-cancel", response_model=EquipmentOrderResponse)
async def request_cancel(
    order_id: int,
    request: CancelOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.FOREMAN]))
):
    """
    Запрос на отмену заявки (бригадиром)
    
    Переход: NEW/APPROVED -> CANCEL_REQUESTED
    """
    service = EquipmentService(db)
    
    try:
        order = await service.request_cancel(order_id, current_user.id, request.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    order = await service.get_order_by_id(order.id)
    
    return EquipmentOrderResponse(
        id=order.id,
        cost_object_id=order.cost_object_id,
        cost_object_name=order.cost_object.name,
        foreman_id=order.foreman_id,
        foreman_name=order.foreman.full_name,
        equipment_type=order.equipment_type,
        
        start_date=order.start_date,
        end_date=order.end_date,
        supplier=order.supplier,
        comment=order.comment,
        status=order.status,

        created_at=order.created_at,
        updated_at=order.updated_at
    )

@router.post("/{order_id}/cancel", response_model=EquipmentOrderResponse)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.EQUIPMENT_MANAGER]))
):
    """
    Отмена заявки (менеджером)
    
    Переход: CANCEL_REQUESTED -> CANCELLED
    """
    service = EquipmentService(db)
    
    try:
        order = await service.cancel_order(order_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Получение детальной информации
    order = await service.get_order_by_id(order.id)
    
    return EquipmentOrderResponse(
        id=order.id,
        cost_object_id=order.cost_object_id,
        cost_object_name=order.cost_object.name,
        foreman_id=order.foreman_id,
        foreman_name=order.foreman.full_name,
        equipment_type=order.equipment_type,
        
        start_date=order.start_date,
        end_date=order.end_date,
        supplier=order.supplier,
        comment=order.comment,
        status=order.status,

        created_at=order.created_at,
        updated_at=order.updated_at
    )
