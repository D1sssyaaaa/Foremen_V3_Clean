"""Дать права админа пользователю"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import json

DATABASE_URL = "sqlite+aiosqlite:///./construction_costs.db"

async def grant_admin():
    """Дать права ADMIN пользователю d1syaaaa"""
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Получаем текущие роли
        result = await session.execute(
            text("SELECT roles FROM users WHERE username = 'd1syaaaa'")
        )
        current_roles = result.fetchone()
        
        if current_roles:
            roles = json.loads(current_roles[0]) if current_roles[0] else []
            print(f"Текущие роли: {roles}")
            
            # Добавляем все роли для админа
            admin_roles = ['ADMIN', 'MANAGER', 'ACCOUNTANT', 'HR_MANAGER', 
                          'EQUIPMENT_MANAGER', 'MATERIALS_MANAGER', 'PROCUREMENT_MANAGER']
            
            new_roles = json.dumps(admin_roles)
            
            await session.execute(
                text("UPDATE users SET roles = :roles WHERE username = 'd1syaaaa'"),
                {"roles": new_roles}
            )
            await session.commit()
            
            print(f"\n✅ Роли обновлены!")
            print(f"Новые роли: {admin_roles}")
            print(f"\n🔐 Пользователь d1syaaaa теперь полный АДМИНИСТРАТОР!")

if __name__ == "__main__":
    asyncio.run(grant_admin())
