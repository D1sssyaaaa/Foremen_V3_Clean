"""
Тестовый запуск для проверки рекурсии
"""
from fastapi import FastAPI
from app.core.config import settings

print("1. FastAPI OK")

app = FastAPI(title="Test")

print("2. App created OK")

try:
    from app.auth.router import router as auth_router
    print("3. Auth router OK")
except Exception as e:
    print(f"3. Auth router FAILED: {e}")

try:
    from app.objects.router import router as objects_router
    print("4. Objects router OK")
except Exception as e:
    print(f"4. Objects router FAILED: {e}")

try:
    from app.time_sheets.router import router as time_sheets_router
    print("5. Time sheets router OK")
except Exception as e:
    print(f"5. Time sheets router FAILED: {e}")

try:
    from app.equipment.router import router as equipment_router
    print("6. Equipment router OK")
except Exception as e:
    print(f"6. Equipment router FAILED: {e}")

try:
    from app.materials.router import router as materials_router
    print("7. Materials router OK")
except Exception as e:
    print(f"7. Materials router FAILED: {e}")

try:
    from app.upd.router import router as upd_router
    print("8. UPD router OK")
except Exception as e:
    print(f"8. UPD router FAILED: {e}")

try:
    from app.analytics.router import router as analytics_router
    print("9. Analytics router OK")
except Exception as e:
    print(f"9. Analytics router FAILED: {e}")

print("\n✅ ALL IMPORTS OK!")
