from aiogram import Bot, Dispatcher, executor, types
from config import BOT_TOKEN
from handlers import start, calc_flow, contact_collection, fallback

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Регистрируем обработчики
start.register_handlers(dp)
calc_flow.register_handlers(dp)
contact_collection.register_handlers(dp)
fallback.register_handlers(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)