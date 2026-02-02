import asyncio
from app.core.database import AsyncSessionLocal
from app.models import Delivery, MaterialCost, EquipmentCost, CostObject, EquipmentOrder
from sqlalchemy import select, func

async def check_data():
    async with AsyncSessionLocal() as db:
        print("--- Checking Delivery Table ---")
        result = await db.execute(select(Delivery))
        deliveries = result.scalars().all()
        print(f"Total Delivery records: {len(deliveries)}")
        for d in deliveries:
            print(f"  ID: {d.id}, Object: {d.cost_object_id}, Amount: {d.amount}")

        print("\n--- Checking MaterialCost Table (UPDs) ---")
        result = await db.execute(select(MaterialCost))
        materials = result.scalars().all()
        print(f"Total MaterialCost records: {len(materials)}")
        for m in materials:
            print(f"  ID: {m.id}, Object: {m.cost_object_id}, Total: {m.total_amount}")

        print("\n--- Checking EquipmentCost Table ---")
        result = await db.execute(select(EquipmentCost))
        eq_costs = result.scalars().all()
        print(f"Total EquipmentCost records: {len(eq_costs)}")
        for e in eq_costs:
            print(f"  ID: {e.id}, Order: {e.equipment_order_id}, Total: {e.total_amount}")
            
        print("\n--- Checking Equipment Orders ---")
        result = await db.execute(select(EquipmentOrder))
        orders = result.scalars().all()
        print(f"Total EquipmentOrder records: {len(orders)}")

if __name__ == "__main__":
    asyncio.run(check_data())
