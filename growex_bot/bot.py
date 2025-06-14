from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, calc_flow, contact_collection, fallback, admin_commands, update_tariffs, analytics_callbacks
from utils.scheduler import tariff_scheduler
from utils.logger import bot_logger
import logging
import os
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем директории если их нет
os.makedirs("data", exist_ok=True)

# Инициализируем бота с хранилищем состояний
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# Регистрируем обработчики в правильном порядке
start.register_handlers(dp)
admin_commands.register_handlers(dp)
analytics_callbacks.register_handlers(dp)
update_tariffs.register_handlers(dp)
calc_flow.register_handlers(dp)
contact_collection.register_handlers(dp)
fallback.register_handlers(dp)  # fallback должен быть последним

async def on_startup():
    """Действия при запуске бота"""
    logging.info("Бот запускается...")
    
    # Запускаем планировщик тарифов
    tariff_scheduler.start(bot)
    
    logging.info("Бот успешно запущен!")

async def on_shutdown():
    """Действия при остановке бота"""
    logging.info("Бот останавливается...")
    
    # Останавливаем планировщик
    tariff_scheduler.stop()
    
    # Очищаем старые логи
    bot_logger.cleanup_old_logs()
    
    logging.info("Бот остановлен!")

async def main():
    """Основная функция запуска бота"""
    try:
        # Выполняем действия при запуске
        await on_startup()
        
        # Запускаем поллинг
        await dp.start_polling(bot, skip_updates=True)
        
    except KeyboardInterrupt:
        logging.info("Получен сигнал остановки")
    finally:
        # Выполняем действия при остановке
        await on_shutdown()
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
