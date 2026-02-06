"""
Скрипт для заполнения таблицы estimate_items тестовыми данными
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import select

# Добавить backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import CostObject, EstimateItem

async def seed_estimates():
    print("Подключение к БД...")
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 1. Получаем объекты
        stmt = select(CostObject)
        result = await session.execute(stmt)
        objects = result.scalars().all()

        if not objects:
            print("❌ Объекты не найдены! Сначала запустите create_test_data.py")
            return

        print(f"Найдено {len(objects)} объектов. Создаем сметы...")

        # Данные для генерации (категория, имя, ед.изм, кол-во, цена)
        materials_template = [
            ("Общестроительные работы", "Бетон М300", "м3", 100, 4500),
            ("Общестроительные работы", "Арматура A500C d12", "т", 5, 65000),
            ("Общестроительные работы", "Кирпич полнотелый", "шт", 10000, 25),
            ("Отделка", "Штукатурка гипсовая", "меш.", 200, 450),
            ("Отделка", "Грунтовка глубокого проникновения", "л", 50, 120),
            ("Отделка", "Плитка керамическая", "м2", 150, 1200),
            ("Электрика", "Кабель ВВГнг 3х2.5", "м", 1000, 85),
            ("Электрика", "Розетка встраиваемая", "шт", 50, 250),
            ("Сантехника", "Труба полипропиленовая d20", "м", 100, 60),
            ("Сантехника", "Радиатор биметаллический", "секц", 80, 800),
        ]

        created_count = 0
        
        for obj in objects:
            print(f"  -> Обработка объекта: {obj.name} (ID: {obj.id})")
            
            # Проверяем, есть ли уже сметы
            stmt_check = select(EstimateItem).where(EstimateItem.cost_object_id == obj.id)
            res_check = await session.execute(stmt_check)
            if res_check.first():
                print("     ⚠️ Смета уже существует, пропускаем.")
                continue

            for category, name, unit, quantity, price in materials_template:
                # Генерируем разные статусы остатков для проверки UI
                
                # 1. Нормальный остаток
                if name == "Бетон М300":
                    delivered = quantity * 0.4
                # 2. Низкий остаток (меньше 20%)
                elif name == "Арматура A500C d12":
                    delivered = quantity * 0.85
                # 3. Перерасход (отрицательный остаток)
                elif name == "Штукатурка гипсовая":
                    delivered = quantity * 1.1 
                # 4. Полный остаток (ничего не отгружено)
                elif name == "Кабель ВВГнг 3х2.5":
                    delivered = 0
                else:
                    delivered = quantity * 0.5

                item = EstimateItem(
                    cost_object_id=obj.id,
                    category=category,
                    name=name,
                    unit=unit,
                    quantity=quantity,
                    price=price,
                    total_amount=quantity * price,
                    # Важно: заполняем поля для отслеживания прогресса
                    ordered_quantity=delivered 
                )
                session.add(item)
                created_count += 1
        
        await session.commit()
        print(f"\n✅ Завершено. Добавлено позиций: {created_count}")

if __name__ == "__main__":
    asyncio.run(seed_estimates())
