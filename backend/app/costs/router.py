"""Роутер для управления затратами"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.auth.dependencies import require_roles, get_current_user
from app.core.models_base import UserRole
from app.models import User, LaborCost, OtherCost, DeliveryCost, CostObject
from app.costs.schemas import (
    LaborCostCreate, LaborCostUpdate, LaborCostResponse,
    OtherCostCreate, OtherCostUpdate, OtherCostResponse,
    DeliveryCostCreate, DeliveryCostUpdate, DeliveryCostResponse
)

router = APIRouter()


# ===== LABOR COSTS =====

@router.post("/labor", response_model=LaborCostResponse, status_code=status.HTTP_201_CREATED)
async def create_labor_cost(
    data: LaborCostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Создание затраты на рабочих"""
    # Проверка существования объекта
    obj = await db.get(CostObject, data.cost_object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    labor_cost = LaborCost(
        cost_object_id=data.cost_object_id,
        date=data.date,
        amount=data.amount,
        comment=data.comment,
        created_by_id=current_user.id
    )
    
    db.add(labor_cost)
    await db.commit()
    await db.refresh(labor_cost)
    
    return labor_cost


@router.get("/labor", response_model=List[LaborCostResponse])
async def get_labor_costs(
    object_id: Optional[int] = Query(None, description="Фильтр по объекту"),
    date_from: Optional[date] = Query(None, description="Дата с"),
    date_to: Optional[date] = Query(None, description="Дата по"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Получение списка затрат на рабочих"""
    query = select(LaborCost)
    
    if object_id:
        query = query.where(LaborCost.cost_object_id == object_id)
    if date_from:
        query = query.where(LaborCost.date >= date_from)
    if date_to:
        query = query.where(LaborCost.date <= date_to)
    
    query = query.order_by(LaborCost.date.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/labor/{cost_id}", response_model=LaborCostResponse)
async def get_labor_cost(
    cost_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Получение затраты на рабочих по ID"""
    cost = await db.get(LaborCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Затрата не найдена")
    return cost


@router.put("/labor/{cost_id}", response_model=LaborCostResponse)
async def update_labor_cost(
    cost_id: int,
    data: LaborCostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Обновление затраты на рабочих"""
    cost = await db.get(LaborCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Затрата не найдена")
    
    if data.date is not None:
        cost.date = data.date
    if data.amount is not None:
        cost.amount = data.amount
    if data.comment is not None:
        cost.comment = data.comment
    
    await db.commit()
    await db.refresh(cost)
    return cost


@router.delete("/labor/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_labor_cost(
    cost_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Удаление затраты на рабочих"""
    cost = await db.get(LaborCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Затрата не найдена")
    
    await db.delete(cost)
    await db.commit()


# ===== OTHER COSTS =====

@router.post("/other", response_model=OtherCostResponse, status_code=status.HTTP_201_CREATED)
async def create_other_cost(
    data: OtherCostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Создание иной затраты"""
    obj = await db.get(CostObject, data.cost_object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    other_cost = OtherCost(
        cost_object_id=data.cost_object_id,
        date=data.date,
        amount=data.amount,
        comment=data.comment,
        created_by_id=current_user.id
    )
    
    db.add(other_cost)
    await db.commit()
    await db.refresh(other_cost)
    
    return other_cost


@router.get("/other", response_model=List[OtherCostResponse])
async def get_other_costs(
    object_id: Optional[int] = Query(None, description="Фильтр по объекту"),
    date_from: Optional[date] = Query(None, description="Дата с"),
    date_to: Optional[date] = Query(None, description="Дата по"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Получение списка иных затрат"""
    query = select(OtherCost)
    
    if object_id:
        query = query.where(OtherCost.cost_object_id == object_id)
    if date_from:
        query = query.where(OtherCost.date >= date_from)
    if date_to:
        query = query.where(OtherCost.date <= date_to)
    
    query = query.order_by(OtherCost.date.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/other/{cost_id}", response_model=OtherCostResponse)
async def get_other_cost(
    cost_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Получение иной затраты по ID"""
    cost = await db.get(OtherCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Затрата не найдена")
    return cost


@router.put("/other/{cost_id}", response_model=OtherCostResponse)
async def update_other_cost(
    cost_id: int,
    data: OtherCostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Обновление иной затраты"""
    cost = await db.get(OtherCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Затрата не найдена")
    
    if data.date is not None:
        cost.date = data.date
    if data.amount is not None:
        cost.amount = data.amount
    if data.comment is not None:
        cost.comment = data.comment
    
    await db.commit()
    await db.refresh(cost)
    return cost


@router.delete("/other/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_other_cost(
    cost_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Удаление иной затраты"""
    cost = await db.get(OtherCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Затрата не найдена")
    
    await db.delete(cost)
    await db.commit()


# ===== DELIVERY COSTS =====

@router.post("/delivery", response_model=DeliveryCostResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_cost(
    data: DeliveryCostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Создание затраты на доставку/спецтехнику"""
    if data.cost_type not in ['delivery', 'equipment']:
        raise HTTPException(status_code=400, detail="cost_type должен быть 'delivery' или 'equipment'")
    
    obj = await db.get(CostObject, data.cost_object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    delivery_cost = DeliveryCost(
        cost_object_id=data.cost_object_id,
        date=data.date,
        amount=data.amount,
        cost_type=data.cost_type,
        comment=data.comment,
        created_by_id=current_user.id
    )
    
    db.add(delivery_cost)
    await db.commit()
    await db.refresh(delivery_cost)
    
    return delivery_cost


@router.get("/delivery", response_model=List[DeliveryCostResponse])
async def get_delivery_costs(
    object_id: Optional[int] = Query(None, description="Фильтр по объекту"),
    cost_type: Optional[str] = Query(None, description="Фильтр по типу: delivery/equipment"),
    date_from: Optional[date] = Query(None, description="Дата с"),
    date_to: Optional[date] = Query(None, description="Дата по"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Получение списка затрат на доставку/спецтехнику"""
    query = select(DeliveryCost)
    
    if object_id:
        query = query.where(DeliveryCost.cost_object_id == object_id)
    if cost_type:
        query = query.where(DeliveryCost.cost_type == cost_type)
    if date_from:
        query = query.where(DeliveryCost.date >= date_from)
    if date_to:
        query = query.where(DeliveryCost.date <= date_to)
    
    query = query.order_by(DeliveryCost.date.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/delivery/{cost_id}", response_model=DeliveryCostResponse)
async def get_delivery_cost(
    cost_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Получение затраты на доставку/спецтехнику по ID"""
    cost = await db.get(DeliveryCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Затрата не найдена")
    return cost


@router.put("/delivery/{cost_id}", response_model=DeliveryCostResponse)
async def update_delivery_cost(
    cost_id: int,
    data: DeliveryCostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Обновление затраты на доставку/спецтехнику"""
    cost = await db.get(DeliveryCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Затрата не найдена")
    
    if data.date is not None:
        cost.date = data.date
    if data.amount is not None:
        cost.amount = data.amount
    if data.cost_type is not None:
        if data.cost_type not in ['delivery', 'equipment']:
            raise HTTPException(status_code=400, detail="cost_type должен быть 'delivery' или 'equipment'")
        cost.cost_type = data.cost_type
    if data.comment is not None:
        cost.comment = data.comment
    
    await db.commit()
    await db.refresh(cost)
    return cost


@router.delete("/delivery/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_delivery_cost(
    cost_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ACCOUNTANT]))
):
    """Удаление затраты на доставку/спецтехнику"""
    cost = await db.get(DeliveryCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Затрата не найдена")
    
    await db.delete(cost)
    await db.commit()
