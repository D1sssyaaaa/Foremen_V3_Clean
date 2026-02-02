import asyncio
from app.core.database import AsyncSessionLocal
from app.models import DeliveryCost
from sqlalchemy import select

async def check_delivery_costs():
    async with AsyncSessionLocal() as db:
        print("\n--- Checking DeliveryCost Table ---")
        result = await db.execute(select(DeliveryCost))
        costs = result.scalars().all()
        print(f"Total DeliveryCost records: {len(costs)}")
        for c in costs:
            print(f"  ID: {c.id}, Object: {c.cost_object_id}, Amount: {c.amount}, Type: {c.cost_type}")

if __name__ == "__main__":
    asyncio.run(check_delivery_costs())
