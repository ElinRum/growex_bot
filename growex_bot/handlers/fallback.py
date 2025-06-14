from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

async def fallback_handler(message: types.Message, state: FSMContext):
    """Обработчик неопознанных сообщений"""
    current_state = await state.get_state()
    
    if current_state:
        # Если пользователь в процессе диалога, подсказываем что делать
        await message.answer(
            "Пожалуйста, следуйте инструкциям или воспользуйтесь кнопкой '◀️ Назад' для возврата."
        )
    else:
        # Если состояния нет, предлагаем начать заново
        await message.answer(
            "Я вас не понимаю. Используйте команду /start или выберите действие из кнопок."
        )

def register_handlers(dp: Dispatcher):
    # Этот обработчик должен быть зарегистрирован последним
    dp.register_message_handler(fallback_handler, state="*")
