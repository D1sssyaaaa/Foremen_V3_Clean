import asyncio
from app.core.database import AsyncSessionLocal
from app.models import CostObject, MaterialCost
from sqlalchemy import select, func

async def debug_analytics():
    async with AsyncSessionLocal() as db:
        print("--- 1. Cost Objects ---")
        result = await db.execute(select(CostObject))
        objects = result.scalars().all()
        for obj in objects:
            print(f"ID: {obj.id}, Name: '{obj.name}'")

        print("\n--- 2. Material Costs Linked to Objects ---")
        query = select(
            MaterialCost.id, 
            MaterialCost.cost_object_id, 
            MaterialCost.total_amount,
            MaterialCost.status
        ).where(MaterialCost.cost_object_id.isnot(None))
        
        result = await db.execute(query)
        costs = result.all()
        for c in costs:
            print(f"UPD ID: {c.id}, Linked to Object: {c.cost_object_id}, Amount: {c.total_amount}, Status: {c.status}")

        print("\n--- 3. Running Actual Analytics Query ---")
        # Reproducing logic from service.py
        query = select(
            CostObject.id,
            CostObject.name,
            func.coalesce(func.sum(MaterialCost.total_amount), 0).label('deliveries')
        ).outerjoin(
            MaterialCost, CostObject.id == MaterialCost.cost_object_id
        ).group_by(
            CostObject.id, CostObject.name
        ).order_by(
            func.coalesce(func.sum(MaterialCost.total_amount), 0).desc()
        )
        
        result = await db.execute(query)
        rows = result.all()
        print("\nQuery Results:")
        for row in rows:
            print(f"Object: '{row.name}' (ID: {row.id}) -> Sum: {row.deliveries}")

if __name__ == "__main__":
    asyncio.run(debug_analytics())
