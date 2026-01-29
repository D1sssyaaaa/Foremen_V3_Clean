"""Утилиты для работы с API"""
import httpx
from typing import Any, Dict, Optional
from app.bot.config import config


class APIClient:
    """Клиент для взаимодействия с backend API"""
    
    def __init__(self, token: Optional[str] = None):
        self.base_url = config.api_base_url
        self.token = token
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @property
    def headers(self) -> Dict[str, str]:
        """Заголовки запросов"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def close(self):
        """Закрытие клиента"""
        await self.client.aclose()
    
    # ===== Objects =====
    async def get_objects(self, token: Optional[str] = None) -> list[Dict[str, Any]]:
        """Получить список объектов"""
        headers = {"Content-Type": "application/json"}
        actual_token = token or self.token
        if actual_token:
            headers["Authorization"] = f"Bearer {actual_token}"
        response = await self.client.get(
            f"{self.base_url}/objects/",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def request_object_access(
        self, 
        object_id: int, 
        reason: Optional[str] = None,
        token: Optional[str] = None
    ) -> bool:
        """Запросить доступ к объекту"""
        headers = {"Content-Type": "application/json"}
        actual_token = token or self.token
        if actual_token:
            headers["Authorization"] = f"Bearer {actual_token}"
        
        try:
            response = await self.client.post(
                f"{self.base_url}/objects/{object_id}/request-access",
                json={"reason": reason},
                headers=headers
            )
            response.raise_for_status()
            return True
        except Exception:
            return False
    
    async def get_my_access_requests(self, token: Optional[str] = None) -> list[Dict[str, Any]]:
        """Получить свои запросы на доступ"""
        headers = {"Content-Type": "application/json"}
        actual_token = token or self.token
        if actual_token:
            headers["Authorization"] = f"Bearer {actual_token}"
        
        try:
            response = await self.client.get(
                f"{self.base_url}/objects/access-requests/my",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return []
    
    # ===== Material Requests =====
    async def create_material_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать заявку на материалы"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = await self.client.post(
            f"{self.base_url}/material-requests/",
            json=data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def get_my_material_requests(self) -> list[Dict[str, Any]]:
        """Получить мои заявки на материалы"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = await self.client.get(
            f"{self.base_url}/material-requests/",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def get_material_request_details(self, request_id: int) -> Dict[str, Any]:
        """Получить детали заявки на материалы (включая items)"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = await self.client.get(
            f"{self.base_url}/material-requests/{request_id}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    # ===== Equipment Requests =====
    async def create_equipment_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать заявку на технику"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = await self.client.post(
            f"{self.base_url}/equipment-orders/",
            json=data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def get_my_equipment_requests(self) -> list[Dict[str, Any]]:
        """Получить мои заявки на технику"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = await self.client.get(
            f"{self.base_url}/equipment-orders/",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def request_cancel_equipment(self, order_id: int, reason: str) -> Dict[str, Any]:
        """Запросить отмену заявки на технику"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = await self.client.post(
            f"{self.base_url}/equipment-orders/{order_id}/request-cancel",
            json={"reason": reason},
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    # ===== Time Sheets =====
    async def create_timesheet(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать табель РТБ"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = await self.client.post(
            f"{self.base_url}/time-sheets/",
            json=data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    # ===== Auth =====
    async def login_telegram(self, telegram_user_id: int) -> Optional[str]:
        """Авторизация через Telegram"""
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/telegram/login",
                json={"telegram_user_id": telegram_user_id}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("access_token")
        except Exception:
            return None
    
    async def register_telegram(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Регистрация нового пользователя через Telegram (прямая)"""
        response = await self.client.post(
            f"{self.base_url}/auth/telegram/register",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def create_registration_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание заявки на регистрацию (новый flow)"""
        response = await self.client.post(
            f"{self.base_url}/registration-requests/",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def check_registration_request_status(self, telegram_chat_id: str) -> Optional[Dict[str, Any]]:
        """Проверка статуса заявки на регистрацию"""
        try:
            response = await self.client.get(
                f"{self.base_url}/registration-requests/by-telegram/{telegram_chat_id}"
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    async def check_username_exists(self, username: str) -> bool:
        """Проверка существования username"""
        try:
            response = await self.client.get(
                f"{self.base_url}/auth/check-username/{username}"
            )
            return response.status_code == 200
        except Exception:
            return False    
    async def link_telegram_account(
        self, 
        code: str, 
        telegram_chat_id: str,
        telegram_username: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Привязка Telegram аккаунта по коду"""
        try:
            response = await self.client.post(
                f"{self.base_url}/users/link-telegram",
                json={
                    "code": code,
                    "telegram_chat_id": int(telegram_chat_id),
                    "telegram_username": telegram_username
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                return e.response.json()
            except Exception:
                return {
                    "success": False,
                    "detail": f"HTTP {e.response.status_code}: {e.response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "detail": str(e)
            }