
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
        # 1. Check if user 'admin' exists or list users
        print("Checking users...")
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Found {len(users)} users.")
        
        if not users:
            print("No users found!")
            return

        # Try to find a user to "login" as.
        # We can't know the password, but we can test the critical parts that crash:
        # 1. DB Fetch (done above)
        # 2. Role parsing
        # 3. Token generation
        
        test_user = users[0]
        print(f"Testing with user: {test_user.username}")
        
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
                print(f"Role parsing FAILED: {e}")
                raise

            # 3. Token generation logic
            user_id_str = str(test_user.id)
            print(f"Creating tokens for user_id: {user_id_str}")
            
            try:
                access_token = create_access_token(data={"sub": user_id_str, "roles": roles})
                print(f"Access token created: {access_token[:10]}...")
            except Exception as e:
                print(f"create_access_token FAILED: {e}")
                # Analyze why
                import traceback
                traceback.print_exc()
                raise

            try:
                refresh_token = create_refresh_token(data={"sub": user_id_str})
                print(f"Refresh token created: {refresh_token[:10]}...")
            except Exception as e:
                print(f"create_refresh_token FAILED: {e}")
                raise
                
            print("Login reproduction steps COMPLETED successfully (excluding password check).")

        except Exception as e:
            print(f"Login Logic CRASHED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import os
    sys.path.append(os.getcwd())
    asyncio.run(reproduce_login())
