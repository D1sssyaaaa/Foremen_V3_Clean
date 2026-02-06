import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    try:
        async with AsyncSessionLocal() as db:
            print("Checking distinct statuses in time_sheets table...")
            result = await db.execute(text("SELECT DISTINCT status FROM time_sheets"))
            rows = result.fetchall()
            print("Statuses found:")
            for row in rows:
                print(f"'{row[0]}'")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
