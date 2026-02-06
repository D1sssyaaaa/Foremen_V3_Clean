"""
Главный файл FastAPI приложения
Инициализация, middleware, маршруты
"""
from contextlib import asynccontextmanager
import logging
import traceback
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info(f"Starting {settings.project_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.project_name}")


# Создание приложения
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальный exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    logger.error("=" * 80)
    logger.error(f"EXCEPTION IN REQUEST: {request.method} {request.url}")
    logger.error(f"Exception type: {type(exc).__name__}")
    logger.error(f"Exception message: {str(exc)}")
    logger.error("Traceback:")
    logger.error(traceback.format_exc())
    logger.error("=" * 80)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__
        }
    )


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Construction Costs Management System API",
        "version": settings.version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# Подключение роутеров модулей
from app.auth.router import router as auth_router
from app.objects.router import router as objects_router

from app.equipment.router import router as equipment_router
from app.materials.router import router as materials_router
from app.upd.router import router as upd_router
from app.analytics.router import router as analytics_router
from app.notifications.router import router as notifications_router
from app.users.registration_router import router as registration_router
from app.users.router import router as users_router
from app.users.telegram_link_router import router as telegram_link_router
from app.api.routes.audit import router as audit_router
from app.websocket.router import router as websocket_router
from app.costs.router import router as costs_router
from app.api.v2.timesheets import router as timesheets_v2_router

# Audit middleware (должен быть после CORS)
from app.middleware.audit import AuditMiddleware
app.add_middleware(AuditMiddleware)

# Подключение статических файлов для загруженных изображений
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router, prefix=f"{settings.api_v1_prefix}/auth", tags=["Authentication"])
app.include_router(objects_router, prefix=f"{settings.api_v1_prefix}/objects", tags=["Objects"])

app.include_router(equipment_router, prefix=f"{settings.api_v1_prefix}/equipment-orders", tags=["Equipment"])
app.include_router(materials_router, prefix=f"{settings.api_v1_prefix}/material-requests", tags=["Materials"])
app.include_router(upd_router, prefix=f"{settings.api_v1_prefix}/material-costs", tags=["UPD Documents"])
app.include_router(analytics_router, prefix=f"{settings.api_v1_prefix}/analytics", tags=["Analytics"])
app.include_router(costs_router, prefix=f"{settings.api_v1_prefix}/costs", tags=["Costs"])
app.include_router(notifications_router, prefix=f"{settings.api_v1_prefix}/notifications", tags=["Notifications"])
app.include_router(registration_router, prefix=f"{settings.api_v1_prefix}/registration-requests", tags=["Registration Requests"])
app.include_router(users_router, prefix=f"{settings.api_v1_prefix}/users", tags=["Users"])
app.include_router(telegram_link_router, prefix=f"{settings.api_v1_prefix}/users", tags=["Telegram Link"])
app.include_router(audit_router, prefix=f"{settings.api_v1_prefix}/audit", tags=["Audit Log"])
app.include_router(timesheets_v2_router, prefix="/api/v2/miniapp", tags=["Mini App Timesheets"])
app.include_router(websocket_router, prefix=f"{settings.api_v1_prefix}", tags=["WebSocket"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
