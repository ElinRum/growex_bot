from aiogram import types, Dispatcher

async def fallback_handler(message: types.Message):
    await message.answer("Пожалуйста, используйте кнопки или команду /start.")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(fallback_handler)