import asyncio
import os
import sys

# Добавляем путь к корню проекта в PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Force SQLite URL explicitly
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./backend/construction_costs.db" 

from app.core.database import engine, Base
# Импортируем все модели чтобы они зарегистрировались в Base
from app.models import *

async def create_tables():
    print("Creating missing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
