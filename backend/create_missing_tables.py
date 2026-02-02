import asyncio
from app.core.database import engine, Base
from app.models import SavedWorker  # Import to ensure metadata is registered

async def create_tables():
    print("Creating missing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created (if they didn't exist).")

if __name__ == "__main__":
    asyncio.run(create_tables())
