"""Главный файл Telegram бота"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.config import config
from app.bot.handlers import common, materials, equipment, time_sheets, objects, deliveries, registration, admin
from app.bot.notification_worker import start_notification_worker

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота"""
    # Инициализация бота
    bot = Bot(token=config.token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация роутеров
    dp.include_router(common.router)
    dp.include_router(registration.router)
    dp.include_router(materials.router)
    dp.include_router(equipment.router)
    dp.include_router(deliveries.router)
    dp.include_router(time_sheets.router)
    dp.include_router(objects.router)
    dp.include_router(admin.router)
    
    logger.info("🤖 Construction Costs Bot started")
    logger.info(f"📡 API Base URL: {config.api_base_url}")
    
    # Запуск notification worker
    worker = await start_notification_worker(bot)
    logger.info("📬 Notification Worker started")
    
    # Запуск polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await worker.stop()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped")
