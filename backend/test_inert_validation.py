"""
Тестирование валидации инертных материалов

ТЕСТ 1: Инертные БЕЗ delivery_time → ОШИБКА
ТЕСТ 2: Инертные С delivery_time → УСПЕХ
ТЕСТ 3: Обычные БЕЗ delivery_time → УСПЕХ
"""

from pydantic import ValidationError
from app.materials.schemas import MaterialRequestCreate, MaterialRequestItemCreate
from app.core.models_base import MaterialType
from datetime import date

print("=" * 80)
print("ТЕСТИРОВАНИЕ ВАЛИДАЦИИ ИНЕРТНЫХ МАТЕРИАЛОВ")
print("=" * 80)

# ================================================
# ТЕСТ 1: INERT без delivery_time → должна быть ОШИБКА
# ================================================
print("\n[ТЕСТ 1] INERT без delivery_time:")
try:
    request = MaterialRequestCreate(
        cost_object_id=1,
        material_type=MaterialType.INERT,  # ← Инертные
        urgency="normal",
        required_date=date.today(),
        delivery_time=None,  # ← НЕ УКАЗАН
        items=[
            MaterialRequestItemCreate(
                material_name="Песок речной",
                quantity=10,
                unit="т",
                description="Для бетона"
            )
        ]
    )
    print("❌ ОШИБКА: Валидация НЕ сработала! Заявка создана без delivery_time")
except ValidationError as e:
    print("✓ УСПЕХ: Валидация сработала корректно")
    print(f"   Ошибка: {e.errors()[0]['msg']}")


# ================================================
# ТЕСТ 2: INERT с delivery_time → должно быть УСПЕШНО
# ================================================
print("\n[ТЕСТ 2] INERT с delivery_time:")
try:
    request = MaterialRequestCreate(
        cost_object_id=1,
        material_type=MaterialType.INERT,  # ← Инертные
        urgency="urgent",
        required_date=date.today(),
        delivery_time="08:00-12:00",  # ← УКАЗАН
        items=[
            MaterialRequestItemCreate(
                material_name="Щебень фракция 5-20",
                quantity=15,
                unit="т"
            )
        ]
    )
    print("✓ УСПЕХ: Заявка создана")
    print(f"   Тип: {request.material_type.value}")
    print(f"   Время доставки: {request.delivery_time}")
    print(f"   Позиций: {len(request.items)}")
except ValidationError as e:
    print(f"❌ ОШИБКА: {e}")


# ================================================
# ТЕСТ 3: REGULAR без delivery_time → должно быть УСПЕШНО
# ================================================
print("\n[ТЕСТ 3] REGULAR без delivery_time:")
try:
    request = MaterialRequestCreate(
        cost_object_id=1,
        material_type=MaterialType.REGULAR,  # ← Обычные
        urgency="normal",
        required_date=date.today(),
        delivery_time=None,  # ← Не указан (и не нужен)
        items=[
            MaterialRequestItemCreate(
                material_name="Гвозди 100мм",
                quantity=5,
                unit="кг"
            )
        ]
    )
    print("✓ УСПЕХ: Заявка создана")
    print(f"   Тип: {request.material_type.value}")
    print(f"   Время доставки: {request.delivery_time or 'не указано'}")
    print(f"   Позиций: {len(request.items)}")
except ValidationError as e:
    print(f"❌ ОШИБКА: {e}")


print("\n" + "=" * 80)
print("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
print("=" * 80)
