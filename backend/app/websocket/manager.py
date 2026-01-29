"""
WebSocket Connection Manager
Управление WebSocket подключениями для реального времени
"""
import logging
from typing import Dict, Set, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Менеджер WebSocket подключений
    
    Функции:
    - Управление активными подключениями
    - Отправка сообщений пользователям
    - Broadcast по ролям
    - Heartbeat/ping для проверки соединения
    """
    
    def __init__(self):
        # Активные подключения: {user_id: set(WebSocket)}
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        
        # Метаданные подключений: {websocket: {user_id, roles, connected_at}}
        self.connection_metadata: Dict[WebSocket, dict] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        user_roles: List[str]
    ):
        """
        Подключение нового WebSocket клиента
        
        Args:
            websocket: WebSocket соединение
            user_id: ID пользователя
            user_roles: роли пользователя
        """
        await websocket.accept()
        
        # Добавление в список активных подключений
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        # Сохранение метаданных
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "roles": user_roles,
            "connected_at": datetime.now(),
            "last_ping": datetime.now()
        }
        
        logger.info(f"WebSocket connected: user_id={user_id}, total={len(self.active_connections[user_id])}")
        
        # Отправка приветственного сообщения
        await self.send_personal_message(
            message={
                "type": "connection_established",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "message": "WebSocket соединение установлено"
            },
            user_id=user_id
        )
    
    def disconnect(self, websocket: WebSocket):
        """
        Отключение WebSocket клиента
        
        Args:
            websocket: WebSocket соединение
        """
        # Получение метаданных
        metadata = self.connection_metadata.get(websocket)
        
        if metadata:
            user_id = metadata["user_id"]
            
            # Удаление из активных подключений
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                # Удаление пользователя если нет подключений
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Удаление метаданных
            del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected: user_id={user_id}")
    
    async def send_personal_message(
        self,
        message: dict,
        user_id: int
    ):
        """
        Отправка сообщения конкретному пользователю
        
        Args:
            message: словарь с данными сообщения
            user_id: ID пользователя
        """
        if user_id not in self.active_connections:
            logger.debug(f"User {user_id} not connected via WebSocket")
            return
        
        # Отправка всем подключениям пользователя
        disconnected = []
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
                logger.debug(f"Message sent to user {user_id}: {message.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                disconnected.append(websocket)
        
        # Очистка отвалившихся подключений
        for ws in disconnected:
            self.disconnect(ws)
    
    async def send_to_multiple_users(
        self,
        message: dict,
        user_ids: List[int]
    ):
        """
        Отправка сообщения нескольким пользователям
        
        Args:
            message: словарь с данными сообщения
            user_ids: список ID пользователей
        """
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
    
    async def broadcast_to_roles(
        self,
        message: dict,
        roles: List[str]
    ):
        """
        Broadcast сообщения пользователям с определёнными ролями
        
        Args:
            message: словарь с данными сообщения
            roles: список ролей (MANAGER, HR_MANAGER и т.д.)
        """
        target_users = set()
        
        # Поиск пользователей с нужными ролями
        for websocket, metadata in self.connection_metadata.items():
            user_roles = metadata.get("roles", [])
            if any(role in user_roles for role in roles):
                target_users.add(metadata["user_id"])
        
        # Отправка сообщений
        await self.send_to_multiple_users(message, list(target_users))
        
        logger.info(f"Broadcast to roles {roles}: {len(target_users)} users")
    
    async def broadcast_all(self, message: dict):
        """
        Broadcast всем подключённым пользователям
        
        Args:
            message: словарь с данными сообщения
        """
        all_user_ids = list(self.active_connections.keys())
        await self.send_to_multiple_users(message, all_user_ids)
        
        logger.info(f"Broadcast to all: {len(all_user_ids)} users")
    
    def get_active_users(self) -> List[int]:
        """Получение списка ID активных пользователей"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self, user_id: Optional[int] = None) -> int:
        """
        Получение количества активных подключений
        
        Args:
            user_id: ID пользователя (опционально)
            
        Returns:
            количество подключений
        """
        if user_id:
            return len(self.active_connections.get(user_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_stats(self) -> dict:
        """Получение статистики подключений"""
        return {
            "total_users": len(self.active_connections),
            "total_connections": self.get_connection_count(),
            "active_users": self.get_active_users(),
            "connections_per_user": {
                uid: len(conns)
                for uid, conns in self.active_connections.items()
            }
        }


# Глобальный экземпляр менеджера
manager = ConnectionManager()
