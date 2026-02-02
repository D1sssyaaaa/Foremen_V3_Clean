import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text
import json

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT username, roles FROM users LIMIT 1"))
        row = res.fetchone()
        if row:
            print(f"User: {row[0]}")
            print(f"Roles raw value: {row[1]}")
            print(f"Roles type: {type(row[1])}")
            if isinstance(row[1], str):
                try:
                    parsed = json.loads(row[1])
                    print(f"Parsed JSON: {parsed}, Type: {type(parsed)}")
                except:
                    print("Could not parse as JSON")
        else:
            print("No users found")

if __name__ == "__main__":
    asyncio.run(main())
