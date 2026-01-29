"""
Создание тестовых данных для разработки
"""
import asyncio
import sys
from pathlib import Path

# Добавить backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
from app.core.config import settings
from app.models import (
    User, CostObject, Brigade, BrigadeMember,
    TimeSheet, MaterialRequest, EquipmentOrder
)
import hashlib

def hash_password(password: str) -> str:
    """Простое хеширование для тестовых данных"""
    return hashlib.sha256(password.encode()).hexdigest()


async def create_test_data():
    """Создание тестовых данных"""
    
    # Подключение к БД
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        print("\n=== Создание пользователей ===")
        
        # 1. Admin
        admin = User(
            username="admin",
            phone="+79001111111",
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            roles=["ADMIN", "MANAGER"],
            full_name="Администратор Системы",
            is_active=True
        )
        session.add(admin)
        
        # 2. Бухгалтер
        accountant = User(
            username="accountant",
            phone="+79002222222",
            email="accountant@example.com",
            hashed_password=hash_password("acc123"),
            roles=["ACCOUNTANT"],
            full_name="Иванова Мария Петровна",
            is_active=True
        )
        session.add(accountant)
        
        # 3. HR менеджер
        hr = User(
            username="hr_manager",
            phone="+79003333333",
            email="hr@example.com",
            hashed_password=hash_password("hr123"),
            roles=["HR_MANAGER"],
            full_name="Сидоров Алексей Иванович",
            is_active=True
        )
        session.add(hr)
        
        # 4-6. Бригадиры
        foreman1 = User(
            username="foreman1",
            phone="+79004444444",
            email="foreman1@example.com",
            hashed_password=hash_password("for123"),
            roles=["FOREMAN"],
            full_name="Петров Иван Сергеевич",
            telegram_chat_id="123456789",
            is_active=True
        )
        session.add(foreman1)
        
        foreman2 = User(
            username="foreman2",
            phone="+79005555555",
            hashed_password=hash_password("for123"),
            roles=["FOREMAN"],
            full_name="Смирнов Петр Дмитриевич",
            is_active=True
        )
        session.add(foreman2)
        
        # 7. Менеджер материалов
        materials_mgr = User(
            username="materials_manager",
            phone="+79006666666",
            hashed_password=hash_password("mat123"),
            roles=["MATERIALS_MANAGER"],
            full_name="Козлова Елена Викторовна",
            is_active=True
        )
        session.add(materials_mgr)
        
        # 8. Менеджер техники
        equipment_mgr = User(
            username="equipment_manager",
            phone="+79007777777",
            hashed_password=hash_password("eq123"),
            roles=["EQUIPMENT_MANAGER"],
            full_name="Морозов Сергей Александрович",
            is_active=True
        )
        session.add(equipment_mgr)
        
        await session.commit()
        print("+ Создано 8 пользователей")
        
        print("\n=== Создание объектов ===")
        
        # Объекты учета
        obj1 = CostObject(
            name="Жилой комплекс 'Светлый'",
            code="ZHK-001",
            contract_number="Д-2025-001",
            contract_amount=150000000.0,
            description="Строительство 3-х секционного жилого дома",
            is_active=True
        )
        session.add(obj1)
        
        obj2 = CostObject(
            name="Торговый центр 'Галерея'",
            code="TC-002",
            contract_number="Д-2025-002",
            contract_amount=85000000.0,
            description="Реконструкция торгового центра",
            is_active=True
        )
        session.add(obj2)
        
        obj3 = CostObject(
            name="Офисное здание 'Бизнес-Парк'",
            code="OF-003",
            contract_number="Д-2025-003",
            contract_amount=120000000.0,
            description="Строительство офисного комплекса класса А",
            is_active=True
        )
        session.add(obj3)
        
        obj4 = CostObject(
            name="Школа №45",
            code="SH-004",
            contract_number="Д-2025-004",
            contract_amount=95000000.0,
            description="Строительство общеобразовательной школы",
            is_active=True
        )
        session.add(obj4)
        
        obj5 = CostObject(
            name="Спортивный комплекс",
            code="SK-005",
            contract_number="Д-2025-005",
            contract_amount=65000000.0,
            description="Строительство универсального спортзала",
            is_active=True
        )
        session.add(obj5)
        
        await session.commit()
        print("+ Создано 5 объектов")
        
        # Обновить связи
        await session.refresh(foreman1)
        await session.refresh(foreman2)
        await session.refresh(obj1)
        await session.refresh(obj2)
        await session.refresh(obj3)
        
        # Назначить бригадиров на объекты
        obj1.foremen.append(foreman1)
        obj2.foremen.append(foreman1)
        obj3.foremen.append(foreman2)
        await session.commit()
        
        print("\n=== Создание бригад ===")
        
        # Бригады
        brigade1 = Brigade(
            foreman_id=foreman1.id,
            name="Бригада №1 (Общестрой)",
            is_active=True
        )
        session.add(brigade1)
        
        brigade2 = Brigade(
            foreman_id=foreman2.id,
            name="Бригада №2 (Отделка)",
            is_active=True
        )
        session.add(brigade2)
        
        await session.commit()
        print("+ Создано 2 бригады")
        
        # Обновить бригады
        await session.refresh(brigade1)
        await session.refresh(brigade2)
        
        print("\n=== Создание рабочих ===")
        
        # Рабочие бригады 1
        members1 = [
            BrigadeMember(brigade_id=brigade1.id, full_name="Кузнецов Андрей", position="Прораб", hourly_rate=500.0),
            BrigadeMember(brigade_id=brigade1.id, full_name="Волков Дмитрий", position="Каменщик", hourly_rate=400.0),
            BrigadeMember(brigade_id=brigade1.id, full_name="Зайцев Михаил", position="Каменщик", hourly_rate=400.0),
            BrigadeMember(brigade_id=brigade1.id, full_name="Соколов Николай", position="Подсобник", hourly_rate=300.0),
            BrigadeMember(brigade_id=brigade1.id, full_name="Лебедев Виктор", position="Подсобник", hourly_rate=300.0),
        ]
        for m in members1:
            session.add(m)
        
        # Рабочие бригады 2
        members2 = [
            BrigadeMember(brigade_id=brigade2.id, full_name="Новиков Александр", position="Мастер", hourly_rate=480.0),
            BrigadeMember(brigade_id=brigade2.id, full_name="Федоров Игорь", position="Маляр", hourly_rate=380.0),
            BrigadeMember(brigade_id=brigade2.id, full_name="Егоров Василий", position="Штукатур", hourly_rate=390.0),
            BrigadeMember(brigade_id=brigade2.id, full_name="Макаров Олег", position="Плиточник", hourly_rate=420.0),
        ]
        for m in members2:
            session.add(m)
        
        await session.commit()
        print("+ Создано 9 рабочих")
        
        print("\n=== Создание заявок ===")
        
        # Заявка на материалы
        mat_req1 = MaterialRequest(
            cost_object_id=obj1.id,
            foreman_id=foreman1.id,
            status="НОВАЯ",
            urgency="срочная",
            notes="Для секции №1, 3 этаж",
            material_type="regular"
        )
        session.add(mat_req1)
        
        # Заявка на технику
        eq_order1 = EquipmentOrder(
            cost_object_id=obj1.id,
            foreman_id=foreman1.id,
            equipment_type="Автокран 25т",
            quantity=1,
            description="Для монтажа плит перекрытия",
            status="НОВАЯ",
            start_date=date.today()
        )
        session.add(eq_order1)
        
        await session.commit()
        print("+ Создано 2 заявки")
        
        print("\n" + "="*50)
        print("[OK] ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО СОЗДАНЫ!")
        print("="*50)
        print("\n Итого:")
        print("   • Пользователей: 8")
        print("   • Объектов: 5")
        print("   • Бригад: 2")
        print("   • Рабочих: 9")
        print("   • Заявок: 2")
        print("\n Учетные данные:")
        print("   admin / admin123")
        print("   accountant / acc123")
        print("   hr_manager / hr123")
        print("   foreman1 / for123")
        print("   materials_manager / mat123")
        print("   equipment_manager / eq123")
        print()


if __name__ == "__main__":
    asyncio.run(create_test_data())
