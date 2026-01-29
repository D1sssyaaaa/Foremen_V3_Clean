"""
WebSocket Router
Endpoints для WebSocket подключений
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_db
from app.websocket.manager import manager
from app.auth.dependencies import get_current_user_ws
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT токен для аутентификации"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint для реального времени
    
    Использование:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws?token=YOUR_JWT_TOKEN');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Notification:', data);
    };
    ```
    
    Типы сообщений:
    - connection_established — соединение установлено
    - notification — новое уведомление
    - budget_alert — превышение бюджета
    - comment_added — новый комментарий
    - status_changed — изменение статуса
    - upd_uploaded — новый УПД
    - ping — heartbeat
    - error — ошибка
    """
    current_user = None
    
    try:
        # Аутентификация пользователя по токену
        from app.auth.security import decode_token
        
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            
            # Получение пользователя из БД
            current_user = await db.get(User, int(user_id))
            
            if not current_user or not current_user.is_active:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        
        except Exception as e:
            logger.error(f"WebSocket auth error: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Подключение к менеджеру
        await manager.connect(
            websocket=websocket,
            user_id=current_user.id,
            user_roles=current_user.roles
        )
        
        try:
            # Основной цикл получения сообщений
            while True:
                # Ожидание сообщения от клиента
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    # Обработка различных типов сообщений от клиента
                    if message_type == "ping":
                        # Heartbeat
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": message.get("timestamp")
                        })
                    
                    elif message_type == "subscribe":
                        # Подписка на определённые события
                        # TODO: реализовать подписки
                        await websocket.send_json({
                            "type": "subscribed",
                            "events": message.get("events", [])
                        })
                    
                    else:
                        # Неизвестный тип сообщения
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        })
                
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON"
                    })
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: user_id={current_user.id}")
        
        except Exception as e:
            logger.error(f"WebSocket error for user {current_user.id}: {e}")
    
    finally:
        # Отключение от менеджера
        if current_user:
            manager.disconnect(websocket)


@router.get("/ws/stats")
async def get_websocket_stats(
    current_user: User = Depends(get_current_user_ws)
):
    """
    Получение статистики WebSocket подключений
    
    Доступно: ADMIN, MANAGER
    """
    from app.core.models_base import UserRole
    
    # Проверка прав
    if not any(role in [UserRole.ADMIN.value, UserRole.MANAGER.value] for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    
    stats = manager.get_stats()
    
    return {
        "status": "ok",
        "stats": stats
    }
