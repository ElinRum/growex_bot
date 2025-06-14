from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.tariffs import calculate_cost, get_city_coefficient
from utils.counter import increment_calculation
from templates.messages import *
import re

class CalcStates(StatesGroup):
    waiting_for_volume = State()
    waiting_for_weight = State()
    waiting_for_city = State()
    waiting_for_description = State()
    showing_result = State()

# Обработчики для разных типов расчета
async def volume_and_weight_flow(message: types.Message, state: FSMContext):
    """Пользователь выбрал 'Указать объём и вес'"""
    await CalcStates.waiting_for_volume.set()
    await state.update_data(flow_type="volume_and_weight")
    await message.answer(VOLUME_REQUEST_TEXT, reply_markup=get_back_keyboard())

async def volume_only_flow(message: types.Message, state: FSMContext):
    """Пользователь выбрал 'Только объём'"""
    await CalcStates.waiting_for_volume.set()
    await state.update_data(flow_type="volume_only")
    await message.answer(VOLUME_REQUEST_TEXT, reply_markup=get_back_keyboard())

async def weight_only_flow(message: types.Message, state: FSMContext):
    """Пользователь выбрал 'Только вес'"""
    await CalcStates.waiting_for_weight.set()
    await state.update_data(flow_type="weight_only")
    await message.answer(WEIGHT_REQUEST_TEXT, reply_markup=get_back_keyboard())

async def description_flow(message: types.Message, state: FSMContext):
    """Пользователь выбрал 'Не знаю — опишу'"""
    await CalcStates.waiting_for_description.set()
    await state.update_data(flow_type="description")
    await message.answer(DESCRIPTION_REQUEST_TEXT, reply_markup=get_back_keyboard())

async def process_volume(message: types.Message, state: FSMContext):
    """Обработка введенного объема"""
    try:
        volume = float(message.text.replace(",", "."))
        if volume <= 0:
            await message.answer(INVALID_VOLUME_TEXT)
            return
        
        await state.update_data(volume=volume)
        user_data = await state.get_data()
        
        if user_data["flow_type"] == "volume_and_weight":
            await CalcStates.waiting_for_weight.set()
            await message.answer(WEIGHT_REQUEST_TEXT)
        else:
            # Только объём - переходим к городу
            await CalcStates.waiting_for_city.set()
            await message.answer(CITY_REQUEST_TEXT)
            
    except ValueError:
        await message.answer(INVALID_VOLUME_TEXT)

async def process_weight(message: types.Message, state: FSMContext):
    """Обработка введенного веса"""
    try:
        weight = float(message.text.replace(",", "."))
        if weight <= 0:
            await message.answer(INVALID_WEIGHT_TEXT)
            return
        
        await state.update_data(weight=weight)
        await CalcStates.waiting_for_city.set()
        await message.answer(CITY_REQUEST_TEXT)
        
    except ValueError:
        await message.answer(INVALID_WEIGHT_TEXT)

async def process_description(message: types.Message, state: FSMContext):
    """Обработка описания груза"""
    description = message.text.strip()
    if len(description) < 10:
        await message.answer(INVALID_DESCRIPTION_TEXT)
        return
    
    await state.update_data(description=description)
    await CalcStates.waiting_for_city.set()
    await message.answer(CITY_REQUEST_TEXT)

async def process_city(message: types.Message, state: FSMContext):
    """Обработка города доставки и расчет стоимости"""
    city = message.text.strip()
    if len(city) < 2:
        await message.answer(INVALID_CITY_TEXT)
        return
    
    await state.update_data(city=city)
    user_data = await state.get_data()
    
    # Выполняем расчет
    try:
        if user_data["flow_type"] == "description":
            # Для описания даем примерную стоимость
            result_text = DESCRIPTION_RESULT_TEXT.format(
                description=user_data.get("description", ""),
                city=city
            )
        else:
            # Расчет по объему/весу
            cost = calculate_cost(
                volume=user_data.get("volume"),
                weight=user_data.get("weight"),
                city=city
            )
            
            result_text = CALCULATION_RESULT_TEXT.format(
                volume=user_data.get("volume", "-"),
                weight=user_data.get("weight", "-"),
                city=city,
                cost=cost
            )
        
        # Увеличиваем счетчик расчетов
        increment_calculation()
        
        await CalcStates.showing_result.set()
        await message.answer(result_text, reply_markup=get_result_keyboard())
        
    except Exception as e:
        await message.answer(f"Ошибка при расчете: {str(e)}")
        await state.finish()

async def new_calculation(message: types.Message, state: FSMContext):
    """Новый расчет"""
    await state.finish()
    from handlers.start import cmd_start
    await cmd_start(message)

async def get_contacts_handler(message: types.Message, state: FSMContext):
    """Переход к сбору контактов"""
    # Передаем данные расчета в состояние для contact_collection
    user_data = await state.get_data()
    await state.finish()
    
    # Импортируем и вызываем обработчик сбора контактов
    from handlers.contact_collection import start_contact_collection
    await start_contact_collection(message, user_data)

async def back_to_start(message: types.Message, state: FSMContext):
    """Возврат к началу"""
    await state.finish()
    from handlers.start import cmd_start
    await cmd_start(message)

def get_back_keyboard():
    """Клавиатура с кнопкой 'Назад'"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("◀️ Назад"))
    return keyboard

def get_result_keyboard():
    """Клавиатура для экрана результата"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        types.KeyboardButton("💰 Оформить заявку"),
        types.KeyboardButton("🔄 Новый расчёт")
    )
    return keyboard

def register_handlers(dp: Dispatcher):
    # Обработчики выбора типа расчета
    dp.register_message_handler(volume_and_weight_flow, text="Указать объём и вес")
    dp.register_message_handler(volume_only_flow, text="Только объём")
    dp.register_message_handler(weight_only_flow, text="Только вес")
    dp.register_message_handler(description_flow, text="Не знаю — опишу")
    
    # Обработчики состояний
    dp.register_message_handler(process_volume, state=CalcStates.waiting_for_volume)
    dp.register_message_handler(process_weight, state=CalcStates.waiting_for_weight)
    dp.register_message_handler(process_description, state=CalcStates.waiting_for_description)
    dp.register_message_handler(process_city, state=CalcStates.waiting_for_city)
    
    # Обработчики кнопок результата
    dp.register_message_handler(get_contacts_handler, text="💰 Оформить заявку", state=CalcStates.showing_result)
    dp.register_message_handler(new_calculation, text="🔄 Новый расчёт", state=CalcStates.showing_result)
    
    # Кнопка "Назад"
    dp.register_message_handler(back_to_start, text="◀️ Назад", state="*")
