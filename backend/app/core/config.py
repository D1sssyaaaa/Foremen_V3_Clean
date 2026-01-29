"""
Конфигурация приложения
Загрузка переменных окружения и настроек
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Настройки приложения"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Database
    # По умолчанию используем PostgreSQL (значения можно переопределить через .env)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/construction_costs"
    database_echo: bool = False
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # MinIO/S3
    s3_endpoint: str = "localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "upd-documents"
    s3_use_ssl: bool = False
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""
    telegram_admin_ids: str = ""
    api_base_url: str = "http://localhost:8000/api/v1"
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    # App
    environment: str = "development"
    debug: bool = True
    
    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Construction Costs Management System"
    version: str = "1.0.0"


settings = Settings()
