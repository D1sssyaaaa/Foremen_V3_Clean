import asyncio
import json
from app.core.database import AsyncSessionLocal
from app.models import User
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        fixed_count = 0
        for user in users:
            print(f"Checking user {user.username}, roles type: {type(user.roles)}, value: {user.roles}")
            
            if isinstance(user.roles, str):
                try:
                    # Parse the stringified JSON
                    parsed_roles = json.loads(user.roles)
                    if isinstance(parsed_roles, list):
                        print(f"  -> Fixing roles to: {parsed_roles}")
                        user.roles = parsed_roles
                        fixed_count += 1
                except json.JSONDecodeError:
                    print(f"  -> Failed to parse roles for {user.username}")
            elif user.roles is None:
                 print(f"  -> Roles is None, setting to []")
                 user.roles = []
                 fixed_count += 1
                 
        if fixed_count > 0:
            await session.commit()
            print(f"Fixed {fixed_count} users.")
        else:
            print("No users needed fixing.")

if __name__ == "__main__":
    asyncio.run(main())
