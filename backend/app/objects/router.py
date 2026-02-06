"""
Роутер для объектов учета
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, desc, func
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from sqlalchemy import func, desc, select, cast, Float
from app.models import User, CostObject, ObjectAccessRequest, MaterialCost
from app.auth.dependencies import get_current_user, require_roles
from app.core.models_base import UserRole, ObjectStatus, ObjectAccessRequestStatus
from app.services.object_service import ObjectService
from app.services.estimate_service import EstimateService
from app.services.estimate_service import EstimateService
from fastapi import UploadFile, File

router = APIRouter()

@router.post("/{object_id}/estimate")
async def upload_estimate(
    object_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Загрузка сметы из Excel (с заменой старой)
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
         raise HTTPException(status_code=400, detail="Файл должен быть Excel (.xlsx, .xls)")
         
    result = await EstimateService.parse_and_save_excel(
        session=db,
        object_id=object_id,
        file=file
    )
    
    return result

router = APIRouter()


class CreateObjectRequest(BaseModel):
    name: str
    code: Optional[str] = None  # Опционально - генерируется автоматически
    contract_number: Optional[str] = None
    customer_name: Optional[str] = None
    material_amount: Optional[float] = None
    labor_amount: Optional[float] = None
    # contract_amount оставляем для обратной совместимости
    contract_amount: Optional[float] = None


class UpdateObjectRequest(BaseModel):
    name: Optional[str] = None
    customer_name: Optional[str] = None
    contract_number: Optional[str] = None
    contract_amount: Optional[float] = None
    material_amount: Optional[float] = None
    labor_amount: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None


@router.get("/")
async def get_objects(
    include_archived: bool = False,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка объектов учета
    
    Параметры:
    - include_archived: включить архивные объекты (по умолчанию False)
    - status_filter: фильтр по статусу (Активен, Готовится к закрытию, Закрыт, Архив)
    """
    # Преобразуем фильтр статуса
    status_enum = None
    if status_filter:
        try:
            status_enum = ObjectStatus(status_filter)
        except ValueError:
            pass
    
    # Для бригадиров показываем только их объекты
    foreman_id = None
    if UserRole.FOREMAN in current_user.roles and UserRole.MANAGER not in current_user.roles:
        foreman_id = current_user.id
    
    # Получаем объекты через сервис
    objects = await ObjectService.get_objects(
        session=db,
        include_archived=include_archived,
        status=status_enum,
        foreman_id=foreman_id
    )
    
    
    # Calculate detailed stats for table view
    objects_with_stats = []
    
    for obj in objects:
        # Plan
        plan_materials = obj.material_amount or 0
        plan_labor = obj.labor_amount or 0
        plan_total = obj.contract_amount or (plan_materials + plan_labor)
        
        # Fact - Materials
        mat_res = await db.execute(
            select(func.sum(MaterialCost.total_amount))
            .where(MaterialCost.cost_object_id == obj.id)
        )
        fact_materials = mat_res.scalar() or 0
        
        # Fact - Labor (Legacy TimeSheet removed)
        fact_labor = 0
        
        # Balance
        diff_materials = plan_materials - fact_materials
        diff_labor = plan_labor - fact_labor
        diff_total = plan_total - (fact_materials + fact_labor)
        
        # Margin %
        margin_mat_pct = (diff_materials / plan_materials * 100) if plan_materials > 0 else 0
        margin_labor_pct = (diff_labor / plan_labor * 100) if plan_labor > 0 else 0

        objects_with_stats.append({
            "id": obj.id,
            "name": obj.name,
            "customer_name": obj.customer_name,
            "code": obj.code,
            "contract_number": obj.contract_number,
            "contract_amount": obj.contract_amount,
            "material_amount": obj.material_amount,
            "labor_amount": obj.labor_amount,
            "start_date": obj.start_date,
            "end_date": obj.end_date,
            "status": obj.status,
            "is_active": obj.is_active,
            "budget_amount": obj.budget_amount,
            "stats": {
                "plan": {
                    "materials": plan_materials,
                    "labor": plan_labor,
                    "total": plan_total
                },
                "fact": {
                    "materials": fact_materials,
                    "labor": fact_labor,
                    "total": fact_materials + fact_labor
                },
                "balance": {
                    "materials": diff_materials,
                    "labor": diff_labor,
                    "total": diff_total
                },
                "margin_pct": {
                    "materials": margin_mat_pct,
                    "labor": margin_labor_pct
                }
            }
        })
        
    return objects_with_stats


@router.get("/my")
async def get_my_objects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение объектов, назначенных текущему бригадиру
    
    - Используется в Telegram Mini App
    - Возвращает только активные объекты
    """
    # Проверка роли
    if UserRole.FOREMAN not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only foremen can access this endpoint"
        )
    
    # Загружаем пользователя с объектами
    result = await db.execute(
        select(User)
        .options(selectinload(User.assigned_objects))
        .where(User.id == current_user.id)
    )
    user = result.scalar_one()
    
    # Фильтруем только активные объекты
    active_objects = [obj for obj in user.assigned_objects if obj.is_active]
    
    return [
        {
            "id": obj.id,
            "name": obj.name,
            "code": obj.code,
            "status": obj.status,
            "customer_name": obj.customer_name
        }
        for obj in active_objects
    ]


@router.get("/{object_id}")
async def get_object(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение детальной информации по объекту
    """
    result = await db.execute(select(CostObject).where(CostObject.id == object_id))
    obj = result.scalar_one_or_none()
    
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    return {
        "id": obj.id,
        "name": obj.name,
        "customer_name": obj.customer_name,
        "code": obj.code,
        "contract_number": obj.contract_number,
        "contract_amount": obj.contract_amount,
        "material_amount": obj.material_amount,
        "labor_amount": obj.labor_amount,
        "start_date": obj.start_date,
        "end_date": obj.end_date,
        "description": obj.description,
        "status": obj.status,
        "is_active": obj.is_active
    }


@router.post("/")
async def create_object(
    name: str = Form(...),
    customer_name: Optional[str] = Form(None),
    contract_number: Optional[str] = Form(None),
    labor_amount: Optional[float] = Form(None),
    contract_amount: Optional[float] = Form(None),
    code: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Создание нового объекта учета с обязательной загрузкой сметы
    Доступно: MANAGER, ADMIN
    """
    from datetime import datetime
    
    # 1. Валидация файла
    if not file.filename.endswith(('.xlsx', '.xls')):
         raise HTTPException(status_code=400, detail="Смета должна быть Excel файлом (.xlsx, .xls)")

    # 2. Генерация кода (если нет)
    if code:
        # Проверка unikальности кода
        result = await db.execute(select(CostObject).where(CostObject.code == code))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Объект с таким кодом уже существует"
            )
    else:
        current_year = datetime.now().year
        prefix = f"OBJ-{current_year}-"
        
        result = await db.execute(
            select(CostObject)
            .where(CostObject.code.like(f"{prefix}%"))
            .order_by(CostObject.code.desc())
        )
        last_object = result.scalars().first()
        
        if last_object and last_object.code.startswith(prefix):
            try:
                last_num = int(last_object.code.split('-')[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        code = f"{prefix}{next_num:03d}"
    
    # 3. Создаем объект
    obj = CostObject(
        name=name,
        code=code,
        contract_number=contract_number,
        customer_name=customer_name,
        contract_amount=contract_amount,
        material_amount=0, 
        labor_amount=labor_amount,
        is_active=True,
        status='ACTIVE'
    )
    
    db.add(obj)
    await db.flush() 
    
    try:
        # 4. Парсим смету
        # file это UploadFile
        parse_result = await EstimateService.parse_and_save_excel(
            session=db,
            object_id=obj.id,
            file=file,
            commit=False 
        )
        
        if parse_result.get("status") != "success":
             raise HTTPException(status_code=400, detail="Ошибка в файле сметы: пустой или некорректный файл")

        # 5. Обновляем сумму
        if contract_amount is None:
            mat_sum = obj.material_amount or 0
            lab_sum = labor_amount or 0
            obj.contract_amount = mat_sum + lab_sum
            
        await db.commit()
        await db.refresh(obj)
        
        return {
            "id": obj.id,
            "name": obj.name,
            "code": obj.code,
            "material_amount": obj.material_amount,
            "contract_amount": obj.contract_amount,
            "estimate_items_count": parse_result.get("items_count")
        }
        
    except Exception as e:
        await db.rollback()
        # Если parse_and_save_excel кинул HTTPException, он пролетит дальше
        # Если другое исключение - логируем (FastAPI сам залогирует) и кидаем 500
        raise e


@router.put("/{object_id}")
async def update_object(
    object_id: int,
    request: UpdateObjectRequest,
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление данных объекта
    """
    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")

    if request.name is not None:
        obj.name = request.name
    if request.customer_name is not None:
        obj.customer_name = request.customer_name
    if request.contract_number is not None:
        obj.contract_number = request.contract_number
    if request.contract_amount is not None:
        obj.contract_amount = request.contract_amount
    if request.material_amount is not None:
        obj.material_amount = request.material_amount
    if request.labor_amount is not None:
        obj.labor_amount = request.labor_amount
    if request.description is not None:
        obj.description = request.description
        
    if request.status is not None:
        allowed_statuses = ["ACTIVE", "PREPARATION_TO_CLOSE", "CLOSED", "ARCHIVE"]
        if request.status not in allowed_statuses:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый статус. Разрешены: {', '.join(allowed_statuses)}"
            )
        obj.status = request.status

    await db.commit()
    await db.refresh(obj)
    
    return {
        "id": obj.id,
        "name": obj.name,
        "status": obj.status
    }


@router.patch("/{object_id}/status")
async def update_object_status(
    object_id: int,
    status_value: str = Body(..., embed=True, alias="status"),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Изменение статуса объекта
    Доступные статусы: ACTIVE, PREPARATION_TO_CLOSE, CLOSED, ARCHIVE
    Доступно: MANAGER, ADMIN
    """
    allowed_statuses = ["ACTIVE", "PREPARATION_TO_CLOSE", "CLOSED", "ARCHIVE"]
    if status_value not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый статус. Разрешены: {', '.join(allowed_statuses)}"
        )
    
    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    obj.status = status_value
    await db.commit()
    await db.refresh(obj)
    
    return {
        "id": obj.id,
        "status": obj.status,
        "message": f"Статус объекта изменен на {status_value}"
    }


@router.get("/{object_id}/stats")
async def get_object_stats(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение статистики по объекту
    Доступно: всем кроме FOREMAN
    """
    # Проверка прав (блокируем FOREMAN)
    user_roles = current_user.roles or []
    if UserRole.FOREMAN.value in user_roles and len(user_roles) == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра статистики"
        )
    
    from sqlalchemy import func
    from app.models import MaterialRequest, EquipmentOrder, MaterialCost
    
    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    # Статистика по заявкам на материалы (только количество, т.к. сумма рассчитывается через items)
    material_requests_result = await db.execute(
        select(
            func.count(MaterialRequest.id).label('count')
        ).where(MaterialRequest.cost_object_id == object_id)
    )
    material_requests = material_requests_result.first()
    
    # Статистика по статусам заявок на материалы
    material_by_status = await db.execute(
        select(
            MaterialRequest.status,
            func.count(MaterialRequest.id).label('count')
        )
        .where(MaterialRequest.cost_object_id == object_id)
        .group_by(MaterialRequest.status)
    )
    material_status_breakdown = {row.status: row.count for row in material_by_status}
    
    # Статистика по заявкам на технику (сумма через связанные EquipmentCost)
    from app.models import EquipmentCost
    equipment_count_result = await db.execute(
        select(func.count(EquipmentOrder.id))
        .where(EquipmentOrder.cost_object_id == object_id)
    )
    equipment_count = equipment_count_result.scalar() or 0
    
    equipment_total_result = await db.execute(
        select(func.coalesce(func.sum(EquipmentCost.total_amount), 0))
        .join(EquipmentOrder, EquipmentOrder.id == EquipmentCost.equipment_order_id)
        .where(EquipmentOrder.cost_object_id == object_id)
    )
    equipment_total = equipment_total_result.scalar() or 0
    
    # Статистика по УПД документам
    upd_result = await db.execute(
        select(
            func.count(MaterialCost.id).label('count'),
            func.coalesce(func.sum(MaterialCost.total_amount), 0).label('total')
        ).where(MaterialCost.cost_object_id == object_id)
    )
    upd_docs = upd_result.first()
    
    # Статистика по табелям РТБ
    timesheets_count = 0
    labor_costs_total = 0
    
    # Общие затраты (материалы учитываем через УПД)
    total_costs = (
        float(equipment_total or 0) +
        float(upd_docs.total or 0) +
        float(labor_costs_total or 0)
    )
    
    return {
        "object_id": object_id,
        "object_name": obj.name,
        "object_code": obj.code,
        "object_status": obj.status,
        "material_requests": {
            "count": material_requests.count or 0,
            "total": 0,  # Сумма рассчитывается через УПД
            "by_status": material_status_breakdown
        },
        "equipment_orders": {
            "count": equipment_count,
            "total": float(equipment_total)
        },
        "upd_documents": {
            "count": upd_docs.count or 0,
            "total": float(upd_docs.total or 0)
        },
        "timesheets": {
            "count": timesheets_count,
            "labor_costs_total": float(labor_costs_total)
        },
        "total_costs": total_costs,
        "budget": {
            "material_budget": float(obj.material_amount or 0),
            "labor_budget": float(obj.labor_amount or 0),
            "total_budget": float(obj.contract_amount or 0)
        }
    }


@router.get("/{object_id}/timesheets")
async def get_object_timesheets(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка табелей, в которых есть работы по этому объекту.
    Восстановленный эндпоинт.
    """
    from app.models import TimeSheet, TimeSheetItem
    
    # Check permissions (exclude FOREMAN just in case, or allow if they need it)
    user_roles = current_user.roles or []
    # Similar check as others
    if UserRole.FOREMAN.value in user_roles and len(user_roles) == 1:
         # If foremen need this, remove this check. Assuming Managers use ObjectDetail.
         pass 

    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")

    # Select TimeSheets that have at least one item for this object
    # Use distinct to avoid duplicates
    query = (
        select(TimeSheet)
        .join(TimeSheetItem, TimeSheetItem.time_sheet_id == TimeSheet.id)
        .where(TimeSheetItem.cost_object_id == object_id)
        .distinct()
        .order_by(desc(TimeSheet.period_start))
    )
    
    result = await db.execute(query)
    timesheets = result.scalars().all()
    
    return [
        {
            "id": ts.id,
            "period_start": ts.period_start,
            "period_end": ts.period_end,
            "status": ts.status,
            "foreman_id": ts.user_id,
            "created_at": ts.created_at,
            # Add other fields if needed by TimeSheetSummary
        }
        for ts in timesheets
    ]


@router.get("/{object_id}/details")
async def get_object_details(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение детальной информации по объекту с полными списками
    Доступно: всем кроме FOREMAN
    """
    # Проверка прав
    user_roles = current_user.roles or []
    if UserRole.FOREMAN.value in user_roles and len(user_roles) == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра деталей"
        )
    
    from app.models import MaterialRequest, EquipmentOrder, MaterialCost
    
    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    # Заявки на материалы
    material_requests_result = await db.execute(
        select(MaterialRequest)
        .where(MaterialRequest.cost_object_id == object_id)
        .order_by(MaterialRequest.created_at.desc())
    )
    material_requests = material_requests_result.scalars().all()
    
    # Заявки на технику
    equipment_orders_result = await db.execute(
        select(EquipmentOrder)
        .where(EquipmentOrder.cost_object_id == object_id)
        .order_by(EquipmentOrder.created_at.desc())
    )
    equipment_orders = equipment_orders_result.scalars().all()
    
    # УПД документы
    upd_docs_result = await db.execute(
        select(MaterialCost)
        .where(MaterialCost.cost_object_id == object_id)
        .order_by(MaterialCost.document_date.desc())
    )
    upd_docs = upd_docs_result.scalars().all()
    
    return {
        "object": {
            "id": obj.id,
            "name": obj.name,
            "code": obj.code,
            "contract_number": obj.contract_number,
            "contract_amount": obj.contract_amount,
            "material_amount": obj.material_amount,
            "labor_amount": obj.labor_amount,
            "start_date": obj.start_date,
            "end_date": obj.end_date,
            "status": obj.status,
            "description": obj.description,
            "is_active": obj.is_active
        },
        "material_requests": [
            {
                "id": req.id,
                "number": req.number,
                "created_at": req.created_at,
                "status": req.status,
                "urgency": req.urgency,
                "supplier": req.supplier,
                "expected_delivery_date": req.expected_delivery_date
            }
            for req in material_requests
        ],
        "equipment_orders": [
            {
                "id": order.id,
                "number": order.number,
                "created_at": order.created_at,
                "equipment_type": order.equipment_type,
                "status": order.status,
                "supplier": order.supplier,
                "start_date": order.start_date,
                "end_date": order.end_date
            }
            for order in equipment_orders
        ],
        "upd_documents": [
            {
                "id": doc.id,
                "document_number": doc.document_number,
                "document_date": doc.document_date,
                "supplier_name": doc.supplier_name,
                "total_amount": doc.total_amount
            }
            for doc in upd_docs
        ]
    }


@router.delete("/{object_id}")
async def delete_object(
    object_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Удаление объекта (мягкое - is_active = False)
    Доступно: ADMIN
    """
    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    obj.is_active = False
    await db.commit()
    
    return {"message": "Object deleted successfully"}


@router.patch("/{object_id}/change-status")
async def change_object_status(
    object_id: int,
    new_status: str = Body(..., embed=True, alias="status"),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Изменение статуса объекта (новая версия)
    
    Доступные статусы: Активен, Готовится к закрытию, Закрыт, Архив
    При архивации объекта автоматически архивируются все УПД
    """
    # Преобразуем строку в ObjectStatus
    try:
        status_enum = ObjectStatus(new_status)
    except ValueError:
        allowed = [s.value for s in ObjectStatus]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый статус. Разрешены: {', '.join(allowed)}"
        )
    
    # Изменяем статус через сервис
    obj = await ObjectService.change_status(
        session=db,
        object_id=object_id,
        new_status=status_enum,
        user_id=current_user.id
    )
    
    return {
        "id": obj.id,
        "name": obj.name,
        "status": obj.status,
        "is_active": obj.is_active,
        "message": f"Статус объекта изменён на '{new_status}'"
    }


    return {
        "budget": budget.amount if budget else 0.0,
        "labor_limit": budget.labor_limit if budget else None,
        "material_limit": budget.material_limit if budget else None,
        "equipment_limit": budget.equipment_limit if budget else None,
        "updated_at": budget.updated_at if budget else None
    }


@router.get("/{object_id}/estimate")
async def get_object_estimate(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение сметы объекта (список позиций)
    
    - Для бригадиров: БЕЗ цен (price, total_amount)
    - Для менеджеров: со всеми данными
    """
    items = await EstimateService.get_estimate_items(db, object_id)
    
    # Для бригадиров НЕ возвращаем цены
    if UserRole.FOREMAN in current_user.roles and UserRole.MANAGER not in current_user.roles:
        return [
            {
                "id": item.id,
                "category": item.category,
                "name": item.name,
                "unit": item.unit,
                "quantity": item.quantity,
                "delivered_quantity": item.ordered_quantity,
                "remaining_quantity": item.quantity - item.ordered_quantity
            }
            for item in items
        ]
    
    # Для менеджеров возвращаем всё
    return [
        {
            "id": item.id,
            "category": item.category,
            "name": item.name,
            "unit": item.unit,
            "quantity": item.quantity,
            "price": item.price,
            "total_amount": item.total_amount,
            "delivered_quantity": item.ordered_quantity,
            "remaining_quantity": item.quantity - item.ordered_quantity,
            "price": item.price,
            "total_amount": item.total_amount,
            "ordered_quantity": item.ordered_quantity,
            "delivered_quantity": 0.0,  # Заглушка для будущей интеграции УПД
            "remaining_quantity": item.quantity - 0.0  # Остаток = Кол-во по смете - Отгружено
        }
        for item in items
    ]


@router.get("/{object_id}/material-items")
async def get_object_material_items(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка вех позиций материалов по объекту 
    (детализация всех УПД)
    """
    # 1. Проверяем доступ к объекту
    # TODO: Добавить проверку прав? Пока разрешаем всем авторизованным смотреть

    # 2. Запрашиваем items
    from app.models import MaterialCost, MaterialCostItem
    
    query = (
        select(MaterialCostItem)
        .join(MaterialCost, MaterialCostItem.material_cost_id == MaterialCost.id)
        .where(MaterialCost.cost_object_id == object_id)
        .order_by(desc(MaterialCost.document_date))
    )
    
    # Подгружаем родительский MaterialCost чтобы взять дату/поставщика
    from sqlalchemy.orm import selectinload
    query = query.options(selectinload(MaterialCostItem.material_cost))

    result = await db.execute(query)
    items = result.scalars().all()

    return [
        {
            "id": item.id,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "price": item.price,
            "amount": item.amount,
            
            # Данные из "шапки" УПД
            "document_date": item.material_cost.document_date if item.material_cost.document_date else None,
            "document_number": item.material_cost.document_number,
            "supplier_name": item.material_cost.supplier_name
        }
        for item in items
    ]


@router.get("/{object_id}/budget")
async def get_object_budget(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение информации о бюджете объекта
    """
    budget_info = await ObjectService.check_budget_alerts(
        session=db,
        object_id=object_id
    )
    
    return budget_info


@router.put("/{object_id}/budget")
async def update_object_budget(
    object_id: int,
    budget_amount: float = Body(..., embed=True),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Установка бюджета объекта
    """
    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    old_budget = obj.budget_amount
    obj.budget_amount = budget_amount
    
    # Сброс флагов алертов при изменении бюджета
    obj.budget_alert_80_sent = False
    obj.budget_alert_100_sent = False
    
    await db.commit()
    await db.refresh(obj)
    
    # Логируем изменение бюджета
    from app.services.audit_service import AuditService
    await AuditService.log_action(
        session=db,
        user_id=current_user.id,
        action="UPDATE_BUDGET",
        entity_type="CostObject",
        entity_id=object_id,
        old_value=str(old_budget) if old_budget else None,
        new_value=str(budget_amount),
        description=f"Изменение бюджета объекта '{obj.name}' с {old_budget} на {budget_amount}"
    )
    

    return {
        "id": obj.id,
        "name": obj.name,
        "budget_amount": obj.budget_amount,
        "message": "Бюджет объекта обновлён"
    }


# ===== ЭНДПОИНТЫ ДЛЯ ЗАПРОСА ДОСТУПА К ОБЪЕКТАМ =====

class RequestAccessRequest(BaseModel):
    """Запрос на доступ к объекту"""
    reason: Optional[str] = None


class RejectAccessRequest(BaseModel):
    """Запрос на отклонение доступа"""
    rejection_reason: Optional[str] = None


@router.post("/{object_id}/request-access")
async def request_object_access(
    object_id: int,
    request: RequestAccessRequest,
    current_user: User = Depends(require_roles([UserRole.FOREMAN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Запрос доступа бригадира к объекту
    Доступно: FOREMAN
    """
    from datetime import datetime
    
    # Проверка существования объекта
    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    # Проверка наличия уже существующего запроса (активного)
    existing_result = await db.execute(
        select(ObjectAccessRequest).where(
            (ObjectAccessRequest.foreman_id == current_user.id) &
            (ObjectAccessRequest.cost_object_id == object_id) &
            (ObjectAccessRequest.status == ObjectAccessRequestStatus.PENDING.value)
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже отправили запрос на доступ к этому объекту"
        )
    
    # Проверка наличия уже имеющегося доступа
    has_access_result = await db.execute(
        select(CostObject).where(
            (CostObject.id == object_id) &
            (CostObject.foremen.any(User.id == current_user.id))
        )
    )
    if has_access_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У вас уже есть доступ к этому объекту"
        )
    
    # Создание нового запроса
    access_request = ObjectAccessRequest(
        foreman_id=current_user.id,
        cost_object_id=object_id,
        status=ObjectAccessRequestStatus.PENDING.value,
        reason=request.reason
    )
    
    db.add(access_request)
    await db.commit()
    await db.refresh(access_request)
    
    return {
        "id": access_request.id,
        "object_name": obj.name,
        "status": access_request.status,
        "message": "Запрос на доступ отправлен. Ожидание рассмотрения администратором"
    }


@router.get("/{object_id}/access-requests")
async def get_object_access_requests(
    object_id: int,
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка запросов доступа к объекту
    Доступно: MANAGER, ADMIN
    """
    from sqlalchemy import desc
    from sqlalchemy.orm import selectinload
    
    # Проверка существования объекта
    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    # Формирование запроса с явной загрузкой relationships
    query = select(ObjectAccessRequest).where(
        ObjectAccessRequest.cost_object_id == object_id
    ).options(
        selectinload(ObjectAccessRequest.foreman),
        selectinload(ObjectAccessRequest.processed_by)
    )
    
    # Фильтр по статусу если указан
    if status_filter:
        try:
            status_enum = ObjectAccessRequestStatus(status_filter)
            query = query.where(ObjectAccessRequest.status == status_enum.value)
        except ValueError:
            pass
    
    # Сортировка по дате создания (новые сверху)
    query = query.order_by(desc(ObjectAccessRequest.created_at))
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return [
        {
            "id": req.id,
            "foreman_id": req.foreman_id,
            "foreman_name": req.foreman.full_name or req.foreman.username,
            "foreman_phone": req.foreman.phone,
            "status": req.status,
            "reason": req.reason,
            "created_at": req.created_at.isoformat() if req.created_at else None,
            "processed_at": req.processed_at.isoformat() if req.processed_at else None,
            "processed_by_name": (req.processed_by.full_name or req.processed_by.username) if req.processed_by else None,
            "rejection_reason": req.rejection_reason
        }
        for req in requests
    ]


@router.post("/{object_id}/access-requests/{request_id}/approve")
async def approve_access_request(
    object_id: int,
    request_id: int,
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Одобрение запроса доступа бригадира к объекту
    Доступно: MANAGER, ADMIN
    """
    from datetime import datetime
    
    # Проверка существования объекта
    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    # Получение запроса
    access_request = await db.get(ObjectAccessRequest, request_id)
    if not access_request:
        raise HTTPException(status_code=404, detail="Запрос на доступ не найден")
    
    # Проверка что запрос относится к этому объекту
    if access_request.cost_object_id != object_id:
        raise HTTPException(status_code=404, detail="Запрос не относится к этому объекту")
    
    # Проверка что запрос в статусе PENDING
    if access_request.status != ObjectAccessRequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Запрос уже обработан (статус: {access_request.status})"
        )
    
    # Обновление статуса запроса
    access_request.status = ObjectAccessRequestStatus.APPROVED.value
    access_request.processed_by_id = current_user.id
    access_request.processed_at = datetime.utcnow()
    
    # Получение бригадира
    foreman = await db.get(User, access_request.foreman_id)
    
    # Добавление бригадира к объекту через прямую вставку в таблицу (работает с async)
    from sqlalchemy import insert
    from app.models import object_foremen
    
    # Проверка что связи еще нет
    check_result = await db.execute(
        select(object_foremen).where(
            (object_foremen.c.foreman_id == access_request.foreman_id) &
            (object_foremen.c.object_id == object_id)
        )
    )
    
    if not check_result.scalar():
        # Добавляем связь
        await db.execute(
            insert(object_foremen).values(
                foreman_id=access_request.foreman_id,
                object_id=object_id
            )
        )
    
    await db.commit()
    await db.refresh(access_request)
    
    # Логирование действия
    from app.services.audit_service import AuditService
    await AuditService.log_action(
        session=db,
        user_id=current_user.id,
        action="APPROVE_ACCESS_REQUEST",
        entity_type="ObjectAccessRequest",
        entity_id=request_id,
        description=f"Одобрен запрос доступа бригадира {foreman.username} к объекту '{obj.name}'"
    )
    
    return {
        "id": access_request.id,
        "status": access_request.status,
        "foreman_id": access_request.foreman_id,
        "object_id": object_id,
        "message": f"Запрос одобрен. Бригадир {foreman.username} получил доступ к объекту"
    }


@router.post("/{object_id}/access-requests/{request_id}/reject")
async def reject_access_request(
    object_id: int,
    request_id: int,
    request: RejectAccessRequest = Body(...),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Отклонение запроса доступа бригадира к объекту
    Доступно: MANAGER, ADMIN
    """
    from datetime import datetime
    
    # Проверка существования объекта
    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    # Получение запроса
    access_request = await db.get(ObjectAccessRequest, request_id)
    if not access_request:
        raise HTTPException(status_code=404, detail="Запрос на доступ не найден")
    
    # Проверка что запрос относится к этому объекту
    if access_request.cost_object_id != object_id:
        raise HTTPException(status_code=404, detail="Запрос не относится к этому объекту")
    
    # Проверка что запрос в статусе PENDING
    if access_request.status != ObjectAccessRequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Запрос уже обработан (статус: {access_request.status})"
        )
    
    # Обновление статуса запроса
    access_request.status = ObjectAccessRequestStatus.REJECTED.value
    access_request.processed_by_id = current_user.id
    access_request.processed_at = datetime.utcnow()
    access_request.rejection_reason = request.rejection_reason
    
    # Получение бригадира
    foreman = await db.get(User, access_request.foreman_id)
    
    await db.commit()
    await db.refresh(access_request)
    
    # Логирование действия
    from app.services.audit_service import AuditService
    await AuditService.log_action(
        session=db,
        user_id=current_user.id,
        action="REJECT_ACCESS_REQUEST",
        entity_type="ObjectAccessRequest",
        entity_id=request_id,
        description=f"Отклонён запрос доступа бригадира {foreman.username} к объекту '{obj.name}'. Причина: {request.rejection_reason or 'не указана'}"
    )
    
    return {
        "id": access_request.id,
        "status": access_request.status,
        "foreman_id": access_request.foreman_id,
        "object_id": object_id,
        "rejection_reason": request.rejection_reason,
        "message": "Запрос отклонён"
    }


@router.get("/access-requests/my")
async def get_my_access_requests(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_roles([UserRole.FOREMAN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение моих запросов на доступ (для бригадира)
    Доступно: FOREMAN
    """
    from sqlalchemy import desc
    from sqlalchemy.orm import selectinload
    
    # Формирование запроса с явной загрузкой relationships
    query = select(ObjectAccessRequest).where(
        ObjectAccessRequest.foreman_id == current_user.id
    ).options(
        selectinload(ObjectAccessRequest.cost_object)
    )
    
    # Фильтр по статусу если указан
    if status_filter:
        try:
            status_enum = ObjectAccessRequestStatus(status_filter)
            query = query.where(ObjectAccessRequest.status == status_enum.value)
        except ValueError:
            pass
    
    # Сортировка по дате создания (новые сверху)
    query = query.order_by(desc(ObjectAccessRequest.created_at))
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return [
        {
            "id": req.id,
            "object_id": req.cost_object_id,
            "object_name": req.cost_object.name,
            "object_code": req.cost_object.code,
            "status": req.status,
            "reason": req.reason,
            "created_at": req.created_at.isoformat() if req.created_at else None,
            "processed_at": req.processed_at.isoformat() if req.processed_at else None,
            "rejection_reason": req.rejection_reason
        }
        for req in requests
    ]


@router.get("/{object_id}/costs")
async def get_object_costs(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение детальных списков затрат по объекту
    Возвращает таблицы с конкретными записями затрат по категориям:
    - materials: Закупка материалов (УПД)
    - equipment_deliveries: Техника и доставки
    - labor: Зарплаты РТБ
    - other: Иные затраты
    Доступно: всем кроме FOREMAN
    """
    # Проверка прав
    user_roles = current_user.roles or []
    if UserRole.FOREMAN.value in user_roles and len(user_roles) == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра затрат"
        )
    
    from app.models import MaterialCost, EquipmentCost, EquipmentOrder, OtherCost, DeliveryCost, TimeSheet, TimeSheetItem
    from sqlalchemy import func
    from sqlalchemy.orm import selectinload
    
    obj = await db.get(CostObject, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    # 1. Материалы (УПД документы) с детализацией
    materials_result = await db.execute(
        select(MaterialCost)
        .options(selectinload(MaterialCost.items))
        .where(MaterialCost.cost_object_id == object_id)
        .order_by(MaterialCost.document_date.desc())
        .limit(100)
    )
    materials = materials_result.scalars().all()
    
    # 2. Техника (связанные затраты через EquipmentCost)
    equipment_result = await db.execute(
        select(EquipmentCost, EquipmentOrder)
        .join(EquipmentOrder, EquipmentOrder.id == EquipmentCost.equipment_order_id)
        .where(EquipmentOrder.cost_object_id == object_id)
        .order_by(EquipmentCost.work_date.desc())
        .limit(100)
    )
    equipment_rows = equipment_result.all()
    
    # 3. Доставки
    deliveries_result = await db.execute(
        select(DeliveryCost)
        .where(DeliveryCost.cost_object_id == object_id)
        .order_by(DeliveryCost.date.desc())
        .limit(100)
    )
    deliveries = deliveries_result.scalars().all()
    
    # 4. РТБ (Зарплаты из табелей)
    labor_result = await db.execute(
        select(
            TimeSheetItem.id,
            TimeSheetItem.date,
            TimeSheetItem.hours,
            TimeSheet.hour_rate,
            TimeSheet.period_start,
            TimeSheet.period_end
        )
        .join(TimeSheet, TimeSheet.id == TimeSheetItem.time_sheet_id)
        .where(TimeSheetItem.cost_object_id == object_id)
        .order_by(TimeSheet.period_start.desc())
        .limit(100)
    )
    labor_rows = labor_result.all()
    
    # 5. Иные затраты
    other_result = await db.execute(
        select(OtherCost)
        .where(OtherCost.cost_object_id == object_id)
        .order_by(OtherCost.date.desc())
        .limit(100)
    )
    other_costs = other_result.scalars().all()
    
    # Расчет сумм
    materials_total = sum(float(m.total_amount or 0) for m in materials)
    equipment_total = sum(float(row[0].total_amount or 0) for row in equipment_rows)
    deliveries_total = sum(float(d.amount or 0) for d in deliveries)
    labor_total = sum(float(row.hours or 0) * float(row.hour_rate or 0) for row in labor_rows)
    other_total = sum(float(o.amount or 0) for o in other_costs)
    
    return {
        "object_id": object_id,
        "object_name": obj.name,
        "summary": {
            "materials_total": materials_total,
            "equipment_deliveries_total": equipment_total + deliveries_total,
            "labor_total": labor_total,
            "other_total": other_total,
            "work_total": equipment_total + deliveries_total + labor_total + other_total,
            "grand_total": materials_total + equipment_total + deliveries_total + labor_total + other_total
        },
        "materials": [
            {
                "id": m.id,
                "date": m.document_date.isoformat() if m.document_date else None,
                "amount": float(m.total_amount or 0),
                "description": m.supplier_name,
                "document_number": m.document_number,
                "items": [
                    {
                        "id": item.id,
                        "name": item.product_name,
                        "quantity": float(item.quantity or 0),
                        "unit": item.unit,
                        "price": float(item.price or 0),
                        "amount": float(item.amount or 0)
                    }
                    for item in m.items
                ]
            }
            for m in materials
        ],
        "equipment_deliveries": [
            # Техника
            *[
                {
                    "id": f"eq_{row[0].id}",
                    "date": row[0].work_date.isoformat() if row[0].work_date else None,
                    "amount": float(row[0].total_amount or 0),
                    "description": row[1].equipment_type if row[1] else "Техника",
                    "type": "equipment"
                }
                for row in equipment_rows
            ],
            # Доставки
            *[
                {
                    "id": f"del_{d.id}",
                    "date": d.date.isoformat() if d.date else None,
                    "amount": float(d.amount or 0),
                    "description": d.comment or "Доставка",
                    "type": "delivery"
                }
                for d in deliveries
            ]
        ],
        "labor": [
            {
                "id": row.id,
                "date": row.date.isoformat() if row.date else None,
                "amount": float(row.hours or 0) * float(row.hour_rate or 0),
                "description": f"РТБ {row.period_start} - {row.period_end}" if row.period_start else "Рабочие часы",
                "hours": float(row.hours or 0)
            }
            for row in labor_rows
        ],
        "other": [
            {
                "id": o.id,
                "date": o.date.isoformat() if o.date else None,
                "amount": float(o.amount or 0),
                "description": o.comment or "Иные затраты"
            }
            for o in other_costs
        ]
    }


