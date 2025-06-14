"""
Обработчики callback'ов для аналитики
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from config import is_admin
from utils.logger import bot_logger
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.startswith("analytics_"))
async def handle_analytics_callback(callback: CallbackQuery):
    """Обработка callback'ов аналитики"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступно только сотрудникам компании.", show_alert=True)
        return
    
    try:
        period = callback.data.split("_")[1]  # analytics_weekly -> weekly
        
        if period == "incomplete":
            # Статистика незавершенных расчетов
            stats = bot_logger.get_incomplete_calculations_stats()
            
            response = "📊 <b>Незавершенные расчеты</b>\n\n"
            
            for period_name, period_data in stats.items():
                period_display = {
                    "weekly": "📅 За неделю",
                    "monthly": "📅 За месяц", 
                    "quarterly": "📅 За 3 месяца",
                    "all_time": "📅 За все время"
                }.get(period_name, period_name)
                
                total = period_data.get("total", 0)
                by_step = period_data.get("by_step", {})
                
                response += f"{period_display}: <b>{total}</b>\n"
                
                if by_step:
                    for step, count in by_step.items():
                        step_display = {
                            "volume_weight": "📦 Ввод объема/веса",
                            "city_selection": "🏙 Выбор города",
                            "rate_calculation": "💰 Расчет ставки",
                            "contact_collection": "📞 Сбор контактов"
                        }.get(step, step)
                        response += f"  • {step_display}: {count}\n"
                
                response += "\n"
            
        else:
            # Обычная аналитика
            analytics = bot_logger.get_analytics(period)
            
            period_display = {
                "weekly": "📅 За неделю",
                "monthly": "📅 За месяц",
                "quarterly": "📅 За 3 месяца", 
                "all_time": "📅 За все время"
            }.get(period, period)
            
            response = f"📊 <b>Аналитика {period_display}</b>\n\n"
            
            # Основные показатели
            total_calculations = analytics.get("total_calculations", 0)
            total_requests = analytics.get("total_requests", 0)
            avg_volume = analytics.get("average_volume", 0)
            
            response += f"🔢 <b>Основные показатели:</b>\n"
            response += f"• Расчетов: {total_calculations}\n"
            response += f"• Заявок: {total_requests}\n"
            response += f"• Средний объем: {avg_volume:.1f} м³\n\n"
            
            # Популярные города
            popular_cities = analytics.get("popular_cities", {})
            if popular_cities:
                response += f"🏙 <b>Популярные города:</b>\n"
                sorted_cities = sorted(popular_cities.items(), key=lambda x: x[1], reverse=True)
                for city, count in sorted_cities[:5]:
                    response += f"• {city}: {count}\n"
                response += "\n"
            
            # Типы грузов
            cargo_types = analytics.get("cargo_types", {})
            if cargo_types:
                response += f"📦 <b>Типы грузов:</b>\n"
                sorted_cargo = sorted(cargo_types.items(), key=lambda x: x[1], reverse=True)
                for cargo, count in sorted_cargo[:5]:
                    response += f"• {cargo}: {count}\n"
                response += "\n"
            
            if not analytics:
                response += "📭 Данных за этот период пока нет"
        
        await callback.message.edit_text(response, parse_mode='HTML')
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка обработки аналитики: {e}")
        await callback.answer("❌ Ошибка при получении аналитики", show_alert=True)

def register_handlers(dp):
    """Регистрация обработчиков"""
    dp.include_router(router) 