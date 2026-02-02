"""Конфигурация Telegram бота"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Конфигурация бота"""
    token: str
    admin_ids: list[int]
    api_base_url: str
    webhook_url: str | None = None
    webhook_path: str = "/bot/webhook"
    web_app_url: str = "https://D1sssyaaaa.github.io/Foremen_test/index.html"
    
    @classmethod
    def from_env(cls) -> "BotConfig":
        """Загрузка конфигурации из переменных окружения"""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN не задан в .env")
        
        admin_ids_str = os.getenv("TELEGRAM_ADMIN_IDS", "")
        admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
        
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
        webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        web_app_url = os.getenv("TELEGRAM_WEB_APP_URL", "https://D1sssyaaaa.github.io/Foremen_test/index.html")
        
        return cls(
            token=token,
            admin_ids=admin_ids,
            api_base_url=api_base_url,
            webhook_url=webhook_url,
            web_app_url=web_app_url
        )


# Глобальный экземпляр конфигурации
config = BotConfig.from_env()
