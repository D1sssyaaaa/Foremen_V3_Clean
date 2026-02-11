
import asyncio
import sys
import os
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.models import User
from app.auth.security import verify_password, get_password_hash, create_access_token, create_refresh_token

# Force using the real DB
DATABASE_URL = settings.database_url

async def reproduce_login():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. List users
        print("Checking users...")
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("No users found!")
            return

        print(f"Found {len(users)} users. Testing each one...")
        
        for test_user in users:
            print(f"\n--- Testing user: {test_user.username} (ID: {test_user.id}) ---")
            
            try:
                # 2. Role parsing logic from router.py
                print(f"Raw roles: {test_user.roles} (type: {type(test_user.roles)})")
                
                roles = []
                try:
                    if isinstance(test_user.roles, list):
                        roles = test_user.roles
                    elif isinstance(test_user.roles, str):
                        roles = json.loads(test_user.roles)
                    else:
                        roles = []
                    print(f"Parsed roles: {roles}")
                except Exception as e:
                    print(f"❌ Role parsing FAILED: {e}")
                    # This might cause 500 in app!
                    continue
                
                # 3. Token generation logic
                user_id_str = str(test_user.id)
                
                try:
                    access_token = create_access_token(data={"sub": user_id_str, "roles": roles})
                except Exception as e:
                    print(f"❌ create_access_token FAILED: {e}")
                    continue

                try:
                    refresh_token = create_refresh_token(data={"sub": user_id_str})
                except Exception as e:
                    print(f"❌ create_refresh_token FAILED: {e}")
                    continue
                    
                print(f"✅ Token generation OK")

                # Test verify_password (dummy)
                try:
                    verify_password("dummy", test_user.hashed_password)
                    print(f"✅ verify_password execution OK")
                except Exception as e:
                    print(f"❌ verify_password CRASHED: {e}")

            except Exception as e:
                print(f"❌ User processing CRASHED: {e}")
                import traceback
                traceback.print_exc()

        print("\nAll users processed.")

if __name__ == "__main__":
    import os
    sys.path.append(os.getcwd())
    asyncio.run(reproduce_login())
