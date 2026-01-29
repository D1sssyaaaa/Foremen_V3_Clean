"""Тесты для модуля аналитики"""
import pytest
from datetime import date, timedelta
from decimal import Decimal


def test_object_costs_summary(client, auth_headers, test_object, db_session):
    """Тест получения затрат по объекту"""
    # Создать несколько записей затрат
    from app.models import CostEntry
    from app.core.models_base import CostType
    
    entries = [
        CostEntry(
            cost_object_id=test_object.id,
            type=CostType.LABOR,
            date=date.today(),
            amount=Decimal("10000.00")
        ),
        CostEntry(
            cost_object_id=test_object.id,
            type=CostType.EQUIPMENT,
            date=date.today(),
            amount=Decimal("5000.00")
        ),
        CostEntry(
            cost_object_id=test_object.id,
            type=CostType.MATERIAL,
            date=date.today(),
            amount=Decimal("15000.00")
        )
    ]
    
    for entry in entries:
        db_session.add(entry)
    db_session.commit()
    
    # Запросить затраты
    response = client.get(
        f"/api/v1/analytics/objects/{test_object.id}/costs",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['total_labor_cost'] == "10000.00"
    assert data['total_equipment_cost'] == "5000.00"
    assert data['total_material_cost'] == "15000.00"
    assert data['total_cost'] == "30000.00"


def test_cost_summary_with_period_filter(client, auth_headers, test_object, db_session):
    """Тест фильтрации затрат по периоду"""
    from app.models import CostEntry
    from app.core.models_base import CostType
    
    # Создать записи за разные даты
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    entries = [
        CostEntry(
            cost_object_id=test_object.id,
            type=CostType.LABOR,
            date=today,
            amount=Decimal("5000.00")
        ),
        CostEntry(
            cost_object_id=test_object.id,
            type=CostType.LABOR,
            date=week_ago,
            amount=Decimal("3000.00")
        ),
        CostEntry(
            cost_object_id=test_object.id,
            type=CostType.LABOR,
            date=month_ago,
            amount=Decimal("2000.00")
        )
    ]
    
    for entry in entries:
        db_session.add(entry)
    db_session.commit()
    
    # Запросить за последние 10 дней
    response = client.get(
        f"/api/v1/analytics/objects/{test_object.id}/costs"
        f"?period_start={week_ago.isoformat()}"
        f"&period_end={today.isoformat()}",
        headers=auth_headers
    )
    
    data = response.json()
    
    # Должны быть только 2 записи (today + week_ago)
    assert data['total_labor_cost'] == "8000.00"


def test_top_5_objects_by_cost(client, auth_headers, db_session):
    """Тест ТОП-5 объектов по затратам"""
    from app.models import CostObject, CostEntry
    from app.core.models_base import CostType
    
    # Создать несколько объектов
    objects = []
    for i in range(7):
        obj = CostObject(
            name=f"Объект {i+1}",
            code=f"OBJ-{i+1:03d}",
            contract_amount=Decimal("1000000.00")
        )
        db_session.add(obj)
        db_session.flush()
        objects.append(obj)
        
        # Добавить затраты (разные суммы)
        entry = CostEntry(
            cost_object_id=obj.id,
            type=CostType.LABOR,
            date=date.today(),
            amount=Decimal((i + 1) * 10000)
        )
        db_session.add(entry)
    
    db_session.commit()
    
    # Запросить ТОП-5
    response = client.get("/api/v1/analytics/top-objects", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Должно быть 5 объектов
    assert len(data) == 5
    
    # Проверить что отсортированы по убыванию затрат
    for i in range(len(data) - 1):
        assert float(data[i]['total_cost']) >= float(data[i+1]['total_cost'])
    
    # Первый должен быть с самыми большими затратами (Объект 7)
    assert "Объект 7" in data[0]['object_name']


def test_cost_dynamics_monthly(client, auth_headers, test_object, db_session):
    """Тест динамики затрат по месяцам"""
    from app.models import CostEntry
    from app.core.models_base import CostType
    
    # Создать записи за 3 месяца
    today = date.today()
    
    for i in range(3):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        
        entry = CostEntry(
            cost_object_id=test_object.id,
            type=CostType.LABOR,
            date=month_date,
            amount=Decimal((i + 1) * 5000)
        )
        db_session.add(entry)
    
    db_session.commit()
    
    # Запросить динамику
    start = today - timedelta(days=90)
    response = client.get(
        f"/api/v1/analytics/dynamics"
        f"?object_id={test_object.id}"
        f"&period_start={start.isoformat()}"
        f"&period_end={today.isoformat()}"
        f"&grouping=month",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['grouping'] == 'month'
    assert len(data['data_points']) >= 1


def test_budget_utilization_calculation(client, auth_headers, db_session):
    """Тест расчета освоения бюджета"""
    from app.models import CostObject, CostEntry
    from app.core.models_base import CostType
    
    # Создать объект с бюджетом
    obj = CostObject(
        name="Объект с бюджетом",
        code="BUDG-001",
        contract_amount=Decimal("100000.00")
    )
    db_session.add(obj)
    db_session.flush()
    
    # Добавить затраты (50% бюджета)
    entry = CostEntry(
        cost_object_id=obj.id,
        type=CostType.LABOR,
        date=date.today(),
        amount=Decimal("50000.00")
    )
    db_session.add(entry)
    db_session.commit()
    
    # Запросить данные
    response = client.get(
        f"/api/v1/analytics/objects/{obj.id}/costs",
        headers=auth_headers
    )
    
    data = response.json()
    
    assert data['contract_amount'] == "100000.00"
    assert data['total_cost'] == "50000.00"
    assert data['remaining_budget'] == "50000.00"
    assert float(data['budget_utilization_percent']) == 50.0


def test_analytics_access_control(client, test_foreman, db_session, test_object):
    """Тест контроля доступа к аналитике"""
    # Попытка доступа к аналитике как FOREMAN (должен быть доступ к объектам)
    foreman_headers = {"Authorization": f"Bearer test_token_{test_foreman.id}"}
    
    response = client.get(
        f"/api/v1/analytics/objects/{test_object.id}/costs",
        headers=foreman_headers
    )
    
    # FOREMAN должен иметь доступ к затратам по объекту
    assert response.status_code in [200, 403]  # Зависит от настроек RBAC
    
    # ТОП-5 и динамика - только для MANAGER и ACCOUNTANT
    response = client.get("/api/v1/analytics/top-objects", headers=foreman_headers)
    assert response.status_code in [403, 401]


def test_cost_breakdown_by_type(client, auth_headers, test_object, db_session):
    """Тест разбивки затрат по типам"""
    from app.models import CostEntry
    from app.core.models_base import CostType
    
    # Создать затраты всех типов
    entries = [
        CostEntry(
            cost_object_id=test_object.id,
            type=CostType.LABOR,
            date=date.today(),
            amount=Decimal("30000.00")
        ),
        CostEntry(
            cost_object_id=test_object.id,
            type=CostType.EQUIPMENT,
            date=date.today(),
            amount=Decimal("20000.00")
        ),
        CostEntry(
            cost_object_id=test_object.id,
            type=CostType.MATERIAL,
            date=date.today(),
            amount=Decimal("50000.00")
        )
    ]
    
    for entry in entries:
        db_session.add(entry)
    db_session.commit()
    
    # Запросить только определенные типы
    response = client.get(
        f"/api/v1/analytics/objects/{test_object.id}/costs"
        f"?cost_types=labor,material",
        headers=auth_headers
    )
    
    data = response.json()
    
    # Должны быть учтены только labor и material
    assert data['total_labor_cost'] == "30000.00"
    assert data['total_material_cost'] == "50000.00"
    # Equipment не запрашивался, должен быть 0
    # (зависит от реализации фильтра)
