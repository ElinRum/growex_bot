from aiogram import types, Dispatcher

async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я помогу рассчитать стоимость доставки сборного груза из Турции.\n"
        "Выберите, какие данные у вас есть для расчёта:",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
            types.KeyboardButton("Указать объём и вес"),
            types.KeyboardButton("Только объём"),
            types.KeyboardButton("Только вес"),
            types.KeyboardButton("Не знаю — опишу")
        )
    )

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"])