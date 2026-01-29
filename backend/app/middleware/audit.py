"""
Middleware для аудита действий
Автоматическое логирование критичных операций
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
import json
from typing import Optional
from datetime import datetime

from app.core.database import AsyncSessionLocal
from app.models import AuditLog


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware для аудита HTTP запросов"""
    
    # Действия которые логируем
    AUDIT_PATHS = {
        "POST": ["/api/v1/users/roles", "/api/v1/time-sheets", "/api/v1/equipment-orders", 
                 "/api/v1/material-requests", "/api/v1/material-costs"],
        "PUT": ["/api/v1/users", "/api/v1/time-sheets", "/api/v1/equipment-orders",
                "/api/v1/material-requests", "/api/v1/material-costs", "/api/v1/objects"],
        "DELETE": ["/api/v1/users", "/api/v1/time-sheets", "/api/v1/equipment-orders",
                   "/api/v1/material-requests"],
        "PATCH": ["/api/v1/users/roles", "/api/v1/users/active"]
    }
    
    async def dispatch(self, request: Request, call_next):
        """Обработка запроса"""
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Проверяем нужно ли логировать
        if self._should_audit(request, response):
            await self._log_action(request, response)
        
        return response
    
    def _should_audit(self, request: Request, response: Response) -> bool:
        """Проверка нужно ли логировать запрос"""
        
        # Логируем только успешные операции
        if response.status_code >= 400:
            return False
        
        # Проверяем метод и путь
        method = request.method
        path = request.url.path
        
        if method not in self.AUDIT_PATHS:
            return False
        
        # Проверяем совпадение пути
        for audit_path in self.AUDIT_PATHS[method]:
            if path.startswith(audit_path):
                return True
        
        return False
    
    async def _log_action(self, request: Request, response: Response):
        """Логирование действия"""
        try:
            async with AsyncSessionLocal() as session:
                # Получаем пользователя из state (устанавливается в dependencies)
                user_id = getattr(request.state, "user_id", None)
                
                # Определяем тип действия и сущность из пути
                path = request.url.path
                method = request.method
                
                action, entity_type = self._parse_action(method, path)
                
                # Получаем IP и User-Agent
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                
                # Создаём запись аудита
                audit_entry = {
                    "user_id": user_id,
                    "action": action,
                    "entity_type": entity_type,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "description": f"{action} {entity_type} via {method} {path}"
                }
                
                stmt = insert(AuditLog).values(**audit_entry)
                await session.execute(stmt)
                await session.commit()
                
        except Exception as e:
            # Не ломаем запрос если аудит упал
            print(f"Audit logging failed: {e}")
    
    def _parse_action(self, method: str, path: str) -> tuple[str, str]:
        """Определение действия и типа сущности из пути"""
        
        # Маппинг методов на действия
        action_map = {
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE"
        }
        
        action = action_map.get(method, "UNKNOWN")
        
        # Определяем тип сущности из пути
        if "users" in path:
            if "roles" in path:
                action = "CHANGE_ROLES"
            elif "active" in path:
                action = "CHANGE_STATUS"
            entity_type = "User"
        elif "time-sheets" in path:
            if "submit" in path:
                action = "SUBMIT"
            elif "approve" in path:
                action = "APPROVE"
            entity_type = "TimeSheet"
        elif "equipment-orders" in path:
            if "approve" in path:
                action = "APPROVE"
            elif "cancel" in path:
                action = "CANCEL"
            entity_type = "EquipmentOrder"
        elif "material-requests" in path:
            if "approve" in path:
                action = "APPROVE"
            elif "reject" in path:
                action = "REJECT"
            entity_type = "MaterialRequest"
        elif "material-costs" in path:
            if "distribute" in path:
                action = "DISTRIBUTE"
            entity_type = "MaterialCost"
        elif "objects" in path:
            entity_type = "CostObject"
        else:
            entity_type = "Unknown"
        
        return action, entity_type
