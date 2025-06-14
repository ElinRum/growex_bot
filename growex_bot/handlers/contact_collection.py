from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.validations import is_valid_email, is_valid_phone
from utils.counter import increment_lead
from templates.messages import *
from config import BOT_TOKEN, MANAGER_CHAT_ID
from aiogram import Bot

class ContactStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_contact = State()
    waiting_for_company = State()

async def start_contact_collection(message: types.Message, calc_data: dict):
    """Начало сбора контактных данных"""
    state = Dispatcher.get_current().current_state()
    await ContactStates.waiting_for_name.set()
    await state.update_data(calc_data=calc_data)
    
    await message.answer(NAME_REQUEST_TEXT, reply_markup=get_contact_keyboard())

async def process_name(message: types.Message, state: FSMContext):
    """Обработка имени"""
    name = message.text.strip()
    if len(name) < 2:
        await message.answer(INVALID_NAME_TEXT)
        return
    
    await state.update_data(name=name)
    await ContactStates.waiting_for_contact.set()
    await message.answer(CONTACT_REQUEST_TEXT)

async def process_contact(message: types.Message, state: FSMContext):
    """Обработка контактных данных (телефон или email)"""
    contact = message.text.strip()
    
    # Проверяем, является ли это телефоном или email
    if contact.startswith("+") and is_valid_phone(contact):
        contact_type = "phone"
    elif "@" in contact and is_valid_email(contact):
        contact_type = "email"
    else:
        await message.answer(INVALID_CONTACT_TEXT)
        return
    
    await state.update_data(contact=contact, contact_type=contact_type)
    await ContactStates.waiting_for_company.set()
    await message.answer(COMPANY_REQUEST_TEXT, reply_markup=get_skip_keyboard())

async def process_company(message: types.Message, state: FSMContext):
    """Обработка названия компании"""
    company = message.text.strip()
    
    if company == "⏭ Пропустить":
        company = "Не указано"
    elif len(company) < 2:
        await message.answer(INVALID_COMPANY_TEXT)
        return
    
    await state.update_data(company=company)
    
    # Собираем все данные и отправляем менеджеру
    user_data = await state.get_data()
    await send_lead_to_manager(message, user_data)
    
    # Увеличиваем счетчик лидов
    increment_lead()
    
    await state.finish()
    await message.answer(LEAD_SUCCESS_TEXT, reply_markup=get_main_keyboard())

async def skip_company(message: types.Message, state: FSMContext):
    """Пропуск компании"""
    await state.update_data(company="Не указано")
    
    # Собираем все данные и отправляем менеджеру
    user_data = await state.get_data()
    await send_lead_to_manager(message, user_data)
    
    # Увеличиваем счетчик лидов
    increment_lead()
    
    await state.finish()
    await message.answer(LEAD_SUCCESS_TEXT, reply_markup=get_main_keyboard())

async def send_lead_to_manager(message: types.Message, user_data: dict):
    """Отправка заявки менеджеру"""
    bot = Bot.get_current()
    
    # Формируем сообщение для менеджера
    calc_data = user_data.get("calc_data", {})
    
    lead_text = f"""
🆕 <b>Новая заявка на доставку из Турции</b>

👤 <b>Контактные данные:</b>
• Имя: {user_data.get('name')}
• {user_data.get('contact_type', 'Контакт').capitalize()}: {user_data.get('contact')}
• Компания: {user_data.get('company')}

📦 <b>Параметры груза:</b>
"""
    
    if calc_data.get("flow_type") == "description":
        lead_text += f"• Описание: {calc_data.get('description')}\n"
    else:
        if calc_data.get("volume"):
            lead_text += f"• Объём: {calc_data.get('volume')} м³\n"
        if calc_data.get("weight"):
            lead_text += f"• Вес: {calc_data.get('weight')} кг\n"
    
    lead_text += f"• Город доставки: {calc_data.get('city')}\n"
    
    lead_text += f"""
👤 <b>Telegram пользователя:</b>
• ID: {message.from_user.id}
• Username: @{message.from_user.username or 'не указан'}
• Имя в Telegram: {message.from_user.full_name}
"""
    
    try:
        await bot.send_message(MANAGER_CHAT_ID, lead_text, parse_mode="HTML")
    except Exception as e:
        # Логируем ошибку, но не показываем пользователю
        print(f"Ошибка отправки заявки менеджеру: {e}")

def get_contact_keyboard():
    """Клавиатура для сбора контактов"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("◀️ Назад"))
    return keyboard

def get_skip_keyboard():
    """Клавиатура с кнопкой пропуска"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        types.KeyboardButton("⏭ Пропустить"),
        types.KeyboardButton("◀️ Назад")
    )
    return keyboard

def get_main_keyboard():
    """Основная клавиатура после завершения"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(btn) for btn in ["Указать объём и вес", "Только объём", "Только вес", "Не знаю — опишу"]])
    return keyboard

async def back_to_calc(message: types.Message, state: FSMContext):
    """Возврат к расчету"""
    await state.finish()
    from handlers.start import cmd_start
    await cmd_start(message)

def register_handlers(dp: Dispatcher):
    # Обработчики состояний
    dp.register_message_handler(process_name, state=ContactStates.waiting_for_name)
    dp.register_message_handler(process_contact, state=ContactStates.waiting_for_contact)
    dp.register_message_handler(process_company, state=ContactStates.waiting_for_company)
    dp.register_message_handler(skip_company, text="⏭ Пропустить", state=ContactStates.waiting_for_company)
    
    # Кнопка "Назад" для состояний контактов
    dp.register_message_handler(back_to_calc, text="◀️ Назад", state=[ContactStates.waiting_for_name, ContactStates.waiting_for_contact, ContactStates.waiting_for_company])
