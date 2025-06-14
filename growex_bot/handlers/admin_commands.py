"""
Обработчики административных команд
"""

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import is_admin
from utils.tariffs import tariff_manager, get_available_cities
from utils.logger import bot_logger
from utils.validations import check_spam_protection, get_validation_error_message
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("rates"))
async def cmd_rates(message: Message):
    """Команда для расчета тарифов (только для администраторов)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступно только сотрудникам компании.")
        return
    
    # Проверка защиты от спама
    allowed, remaining = check_spam_protection(message.from_user.id)
    if not allowed:
        await message.answer(get_validation_error_message("spam", ""))
        return
    
    try:
        # Парсим аргументы команды
        args = message.text.split()[1:]  # Убираем /rates
        
        if len(args) < 2:
            await message.answer(
                "📊 <b>Использование команды /rates</b>\n\n"
                "Формат: <code>/rates [город] [объем]</code>\n"
                "Пример: <code>/rates Москва 2</code>\n\n"
                "Доступные города:\n" + 
                "\n".join([f"• {city}" for city in get_available_cities()[:10]]),
                parse_mode='HTML'
            )
            return
        
        city = args[0]
        try:
            volume = int(args[1])
            weight = 500  # Стандартный вес для расчета
        except ValueError:
            await message.answer("❌ Объем должен быть числом")
            return
        
        # Выполняем расчет
        rate, calc_type, details = tariff_manager.calculate_rate(volume, weight, city)
        
        # Формируем ответ
        if calc_type == "composite":
            response = f"💰 <b>Расчет тарифа</b>\n\n" \
                      f"🏙 Город: {details['city']}\n" \
                      f"📦 Объем: {details['volume']} м³\n" \
                      f"⚖️ Вес: {details['weight']} кг\n" \
                      f"💵 Стоимость: <b>{rate} {details['currency']}</b>\n\n" \
                      f"📅 Действует до: {details['valid_until']}"
        else:
            response = f"💰 <b>Расчет тарифа</b>\n\n" \
                      f"🏙 Запрошенный город: {details['original_city']}\n" \
                      f"📍 Доставка до: {details['city']}\n" \
                      f"📦 Объем: {details['volume']} м³\n" \
                      f"⚖️ Вес: {details['weight']} кг\n" \
                      f"💵 Стоимость: <b>{rate} {details['currency']}</b>\n\n" \
                      f"ℹ️ {details['note']}\n" \
                      f"📅 Действует до: {details['valid_until']}"
        
        await message.answer(response, parse_mode='HTML')
        
        # Логируем расчет
        bot_logger.log_calculation(
            user_id=message.from_user.id,
            username=message.from_user.username or "Unknown",
            calculation_data={
                "city": city,
                "volume": volume,
                "weight": weight,
                "rate": rate,
                "calc_type": calc_type
            },
            step="completed"
        )
        
    except Exception as e:
        logger.error(f"Ошибка расчета тарифа: {e}")
        await message.answer("❌ Ошибка при расчете тарифа. Попробуйте позже.")

@router.message(Command("last_requests"))
async def cmd_last_requests(message: Message):
    """Команда для просмотра последних заявок"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступно только сотрудникам компании.")
        return
    
    try:
        requests = bot_logger.get_last_requests(5)
        
        if not requests:
            await message.answer("📋 Заявок пока нет")
            return
        
        response = "📋 <b>Последние 5 заявок:</b>\n\n"
        
        for i, req in enumerate(reversed(requests), 1):
            data = req.get("data", {})
            timestamp = req.get("timestamp", "")[:16]  # Убираем секунды
            
            response += f"<b>{i}. Заявка {req.get('request_id', 'N/A')}</b>\n" \
                       f"📅 {timestamp}\n" \
                       f"👤 {data.get('name', 'N/A')}\n" \
                       f"📞 {data.get('phone_display', data.get('phone', 'N/A'))}\n" \
                       f"🏙 {data.get('city', 'N/A')}\n" \
                       f"📦 {data.get('volume', 'N/A')} м³, {data.get('weight', 'N/A')} кг\n" \
                       f"💰 {data.get('rate', 'N/A')} USD\n\n"
        
        await message.answer(response, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка получения заявок: {e}")
        await message.answer("❌ Ошибка при получении заявок")

@router.message(Command("last_uploads"))
async def cmd_last_uploads(message: Message):
    """Команда для просмотра последних загрузок тарифов"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступно только сотрудникам компании.")
        return
    
    try:
        uploads = bot_logger.get_last_uploads(3)
        
        if not uploads:
            await message.answer("📁 Загрузок тарифов пока нет")
            return
        
        response = "📁 <b>Последние 3 загрузки тарифов:</b>\n\n"
        
        for i, upload in enumerate(reversed(uploads), 1):
            data = upload.get("data", {})
            timestamp = upload.get("timestamp", "")[:16]
            username = upload.get("username", "Unknown")
            
            response += f"<b>{i}. {data.get('filename', 'N/A')}</b>\n" \
                       f"📅 {timestamp}\n" \
                       f"👤 @{username}\n" \
                       f"✅ {data.get('status', 'N/A')}\n" \
                       f"📝 {data.get('details', 'N/A')}\n\n"
        
        await message.answer(response, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка получения загрузок: {e}")
        await message.answer("❌ Ошибка при получении истории загрузок")

@router.message(Command("analytics"))
async def cmd_analytics(message: Message):
    """Команда для просмотра аналитики"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступно только сотрудникам компании.")
        return
    
    try:
        # Создаем клавиатуру для выбора периода
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Неделя", callback_data="analytics_weekly"),
                InlineKeyboardButton(text="📅 Месяц", callback_data="analytics_monthly")
            ],
            [
                InlineKeyboardButton(text="📅 3 месяца", callback_data="analytics_quarterly"),
                InlineKeyboardButton(text="📅 Все время", callback_data="analytics_all_time")
            ],
            [
                InlineKeyboardButton(text="📊 Незавершенные", callback_data="analytics_incomplete")
            ]
        ])
        
        await message.answer(
            "📊 <b>Аналитика бота</b>\n\n"
            "Выберите период для просмотра статистики:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа аналитики: {e}")
        await message.answer("❌ Ошибка при получении аналитики")

@router.message(Command("info"))
async def cmd_info(message: Message):
    """Справка по административным командам"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступно только сотрудникам компании.")
        return
    
    help_text = """
📚 <b>Справка по командам для сотрудников</b>

🔧 <b>Основные команды:</b>
• <code>/rates [город] [объем]</code> - расчет тарифа
• <code>/last_requests</code> - последние 5 заявок
• <code>/last_uploads</code> - последние 3 загрузки тарифов
• <code>/analytics</code> - аналитика и статистика
• <code>/info</code> - эта справка

📁 <b>Загрузка тарифов:</b>
Отправьте Excel файл с названием:
• "Комплексная ставка.xlsx" - для городских тарифов
• "До Новороссийска.xlsx" - для тарифов до СВХ

⚠️ <b>Важно:</b>
• Файлы должны соответствовать установленному формату
• При загрузке создается автоматический бэкап
• Все действия логируются

📊 <b>Аналитика включает:</b>
• Количество расчетов и заявок
• Популярные города и типы грузов
• Статистику незавершенных расчетов
• Средние показатели по периодам
"""
    
    await message.answer(help_text, parse_mode='HTML')

def register_handlers(dp):
    """Регистрация обработчиков"""
    dp.include_router(router) 