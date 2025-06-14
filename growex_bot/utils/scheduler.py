"""
Планировщик задач для уведомлений о сроках тарифов
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional
from .tariffs import tariff_manager
from config import TARIFF_WARNING_DAYS, MANAGER_CHAT_ID

logger = logging.getLogger(__name__)

class TariffScheduler:
    """Планировщик для проверки сроков действия тарифов"""
    
    def __init__(self, bot=None):
        self.bot = bot
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_notification_date = {}  # Для отслеживания последних уведомлений
        
    def start(self, bot):
        """Запуск планировщика"""
        self.bot = bot
        if not self.running:
            self.running = True
            
            # Планируем проверку каждый день в 10:00
            schedule.every().day.at("10:00").do(self._check_tariff_expiry)
            
            # Запускаем в отдельном потоке
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            
            logger.info("Планировщик тарифов запущен")
    
    def stop(self):
        """Остановка планировщика"""
        self.running = False
        schedule.clear()
        logger.info("Планировщик тарифов остановлен")
    
    def _run_scheduler(self):
        """Основной цикл планировщика"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")
                time.sleep(300)  # При ошибке ждем 5 минут
    
    def _check_tariff_expiry(self):
        """Проверка сроков действия тарифов"""
        try:
            if not self.bot:
                return
            
            expiry_info = tariff_manager.check_tariff_expiry()
            today = datetime.now().date()
            
            # Проверяем комплексные тарифы
            composite_info = expiry_info.get("composite", {})
            if composite_info.get("valid_until"):
                days_left = composite_info.get("days_left", 0)
                
                if days_left <= TARIFF_WARNING_DAYS and days_left >= 0:
                    notification_key = f"composite_{today}"
                    if notification_key not in self.last_notification_date:
                        self._send_expiry_notification("комплексных тарифов", days_left, composite_info.get("valid_until"))
                        self.last_notification_date[notification_key] = today
                
                elif days_left < 0:
                    # Тарифы истекли
                    notification_key = f"composite_expired_{today}"
                    if notification_key not in self.last_notification_date:
                        self._send_expired_notification("комплексных тарифов", abs(days_left))
                        self.last_notification_date[notification_key] = today
            
            # Проверяем тарифы до Новороссийска
            novorossiysk_info = expiry_info.get("novorossiysk", {})
            if novorossiysk_info.get("valid_until"):
                days_left = novorossiysk_info.get("days_left", 0)
                
                if days_left <= TARIFF_WARNING_DAYS and days_left >= 0:
                    notification_key = f"novorossiysk_{today}"
                    if notification_key not in self.last_notification_date:
                        self._send_expiry_notification("тарифов до Новороссийска", days_left, novorossiysk_info.get("valid_until"))
                        self.last_notification_date[notification_key] = today
                
                elif days_left < 0:
                    # Тарифы истекли
                    notification_key = f"novorossiysk_expired_{today}"
                    if notification_key not in self.last_notification_date:
                        self._send_expired_notification("тарифов до Новороссийска", abs(days_left))
                        self.last_notification_date[notification_key] = today
            
            # Очищаем старые записи уведомлений (старше 30 дней)
            self._cleanup_notification_history()
            
        except Exception as e:
            logger.error(f"Ошибка проверки сроков тарифов: {e}")
    
    def _send_expiry_notification(self, tariff_type: str, days_left: int, valid_until: str):
        """Отправка уведомления о приближении срока действия"""
        try:
            if days_left == 0:
                message = f"⚠️ <b>ВНИМАНИЕ!</b>\n\n" \
                         f"Срок действия {tariff_type} истекает СЕГОДНЯ!\n" \
                         f"Действуют до: {valid_until}\n\n" \
                         f"Необходимо срочно загрузить новые тарифы."
            else:
                message = f"⚠️ <b>Напоминание о тарифах</b>\n\n" \
                         f"Срок действия {tariff_type} истекает через {days_left} дн.\n" \
                         f"Действуют до: {valid_until}\n\n" \
                         f"Не забудьте загрузить новые тарифы."
            
            # Отправляем уведомление администратору
            self.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Отправлено уведомление о сроке {tariff_type}: {days_left} дней")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о сроке тарифов: {e}")
    
    def _send_expired_notification(self, tariff_type: str, days_expired: int):
        """Отправка уведомления об истекших тарифах"""
        try:
            message = f"🚨 <b>КРИТИЧЕСКОЕ УВЕДОМЛЕНИЕ!</b>\n\n" \
                     f"Срок действия {tariff_type} истек {days_expired} дн. назад!\n\n" \
                     f"Бот может работать некорректно. Необходимо СРОЧНО загрузить новые тарифы."
            
            # Отправляем критическое уведомление
            self.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
            
            logger.warning(f"Отправлено критическое уведомление: {tariff_type} истекли {days_expired} дней назад")
            
        except Exception as e:
            logger.error(f"Ошибка отправки критического уведомления: {e}")
    
    def _cleanup_notification_history(self):
        """Очистка истории уведомлений"""
        try:
            thirty_days_ago = datetime.now().date() - timedelta(days=30)
            
            # Удаляем старые записи
            keys_to_remove = []
            for key, date in self.last_notification_date.items():
                if date < thirty_days_ago:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.last_notification_date[key]
                
        except Exception as e:
            logger.error(f"Ошибка очистки истории уведомлений: {e}")
    
    def force_check(self):
        """Принудительная проверка тарифов (для тестирования)"""
        self._check_tariff_expiry()

# Глобальный экземпляр планировщика
tariff_scheduler = TariffScheduler() 