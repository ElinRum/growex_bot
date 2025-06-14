from aiogram import types, Dispatcher
from templates.messages import WELCOME_TEXT, CHOOSE_FLOW_BUTTONS

async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    # Создаем клавиатуру с кнопками выбора
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(*[types.KeyboardButton(btn) for btn in CHOOSE_FLOW_BUTTONS])
    
    await message.answer(WELCOME_TEXT, reply_markup=keyboard)

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"])
