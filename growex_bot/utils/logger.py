"""
Система логирования и аналитики для Telegram бота
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from logging.handlers import RotatingFileHandler
import threading

class BotLogger:
    """Система логирования и аналитики бота"""
    
    def __init__(self):
        self.data_dir = "data"
        self.logs_dir = os.path.join(self.data_dir, "logs")
        self.analytics_file = os.path.join(self.data_dir, "analytics.json")
        self.requests_log_file = os.path.join(self.data_dir, "requests_log.json")
        self.uploads_log_file = os.path.join(self.data_dir, "last_uploads.json")
        self.incomplete_calculations_file = os.path.join(self.data_dir, "incomplete_calculations.json")
        
        # Создаем директории
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Настраиваем логирование
        self._setup_logging()
        
        # Блокировка для потокобезопасности
        self._lock = threading.Lock()
    
    def _setup_logging(self):
        """Настройка системы логирования"""
        # Основной лог файл
        main_log_file = os.path.join(self.logs_dir, "bot.log")
        
        # Настраиваем ротацию логов (максимум 10MB, 5 файлов)
        handler = RotatingFileHandler(
            main_log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Формат логов
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Настраиваем корневой логгер
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        # Консольный вывод
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    def log_calculation(self, user_id: int, username: str, calculation_data: Dict[str, Any], 
                       step: str = "completed", calculation_id: str = None):
        """Логирование расчета"""
        try:
            with self._lock:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "username": username,
                    "calculation_id": calculation_id or f"CALC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id}",
                    "step": step,
                    "data": calculation_data
                }
                
                # Обновляем аналитику
                self._update_analytics("calculation", log_entry)
                
                # Если расчет не завершен, логируем в отдельный файл
                if step != "completed":
                    self._log_incomplete_calculation(log_entry)
                
                logging.info(f"Расчет пользователя {user_id} ({username}): {step}")
                
        except Exception as e:
            logging.error(f"Ошибка логирования расчета: {e}")
    
    def log_request(self, user_id: int, username: str, request_data: Dict[str, Any], 
                   request_id: str = None):
        """Логирование заявки"""
        try:
            with self._lock:
                request_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "username": username,
                    "request_id": request_id or f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id}",
                    "data": request_data
                }
                
                # Сохраняем в лог заявок
                self._save_request_log(request_entry)
                
                # Обновляем аналитику
                self._update_analytics("request", request_entry)
                
                logging.info(f"Заявка от пользователя {user_id} ({username}): {request_data.get('city', 'N/A')}")
                
        except Exception as e:
            logging.error(f"Ошибка логирования заявки: {e}")
    
    def log_upload(self, user_id: int, username: str, upload_data: Dict[str, Any]):
        """Логирование загрузки тарифов"""
        try:
            with self._lock:
                upload_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "username": username,
                    "data": upload_data
                }
                
                # Сохраняем в лог загрузок (последние 3)
                self._save_upload_log(upload_entry)
                
                logging.info(f"Загрузка тарифов пользователем {user_id} ({username}): {upload_data.get('filename', 'N/A')}")
                
        except Exception as e:
            logging.error(f"Ошибка логирования загрузки: {e}")
    
    def log_suspicious_activity(self, user_id: int, username: str, activity_type: str, details: Dict[str, Any]):
        """Логирование подозрительной активности"""
        try:
            with self._lock:
                activity_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "username": username,
                    "activity_type": activity_type,
                    "details": details
                }
                
                # Сохраняем в отдельный файл безопасности
                security_log_file = os.path.join(self.logs_dir, "security.log")
                with open(security_log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(activity_entry, ensure_ascii=False) + '\n')
                
                logging.warning(f"Подозрительная активность пользователя {user_id} ({username}): {activity_type}")
                
        except Exception as e:
            logging.error(f"Ошибка логирования подозрительной активности: {e}")
    
    def _save_request_log(self, request_entry: Dict[str, Any]):
        """Сохранение лога заявок (последние 100)"""
        try:
            requests = []
            if os.path.exists(self.requests_log_file):
                with open(self.requests_log_file, 'r', encoding='utf-8') as f:
                    requests = json.load(f)
            
            requests.append(request_entry)
            
            # Оставляем только последние 100 заявок
            if len(requests) > 100:
                requests = requests[-100:]
            
            with open(self.requests_log_file, 'w', encoding='utf-8') as f:
                json.dump(requests, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"Ошибка сохранения лога заявок: {e}")
    
    def _save_upload_log(self, upload_entry: Dict[str, Any]):
        """Сохранение лога загрузок (последние 3)"""
        try:
            uploads = []
            if os.path.exists(self.uploads_log_file):
                with open(self.uploads_log_file, 'r', encoding='utf-8') as f:
                    uploads = json.load(f)
            
            uploads.append(upload_entry)
            
            # Оставляем только последние 3 загрузки
            if len(uploads) > 3:
                uploads = uploads[-3:]
            
            with open(self.uploads_log_file, 'w', encoding='utf-8') as f:
                json.dump(uploads, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"Ошибка сохранения лога загрузок: {e}")
    
    def _log_incomplete_calculation(self, log_entry: Dict[str, Any]):
        """Логирование незавершенных расчетов"""
        try:
            incomplete = {}
            if os.path.exists(self.incomplete_calculations_file):
                with open(self.incomplete_calculations_file, 'r', encoding='utf-8') as f:
                    incomplete = json.load(f)
            
            # Инициализируем структуру если её нет
            if "calculations" not in incomplete:
                incomplete["calculations"] = []
            
            incomplete["calculations"].append(log_entry)
            
            # Оставляем только записи за последние 3 месяца
            three_months_ago = datetime.now() - timedelta(days=90)
            incomplete["calculations"] = [
                calc for calc in incomplete["calculations"]
                if datetime.fromisoformat(calc["timestamp"]) > three_months_ago
            ]
            
            with open(self.incomplete_calculations_file, 'w', encoding='utf-8') as f:
                json.dump(incomplete, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"Ошибка логирования незавершенного расчета: {e}")
    
    def _update_analytics(self, event_type: str, event_data: Dict[str, Any]):
        """Обновление аналитики"""
        try:
            analytics = self._load_analytics()
            
            # Обновляем счетчики по периодам
            for period in ["weekly", "monthly", "quarterly", "all_time"]:
                period_data = analytics.get(period, {})
                
                if event_type == "calculation":
                    period_data["total_calculations"] = period_data.get("total_calculations", 0) + 1
                    
                    # Популярные города
                    city = event_data.get("data", {}).get("city", "Неизвестно")
                    popular_cities = period_data.get("popular_cities", {})
                    popular_cities[city] = popular_cities.get(city, 0) + 1
                    period_data["popular_cities"] = popular_cities
                    
                    # Средний объем
                    volume = event_data.get("data", {}).get("volume", 0)
                    if volume:
                        total_volume = period_data.get("total_volume", 0) + volume
                        calc_count = period_data.get("total_calculations", 1)
                        period_data["total_volume"] = total_volume
                        period_data["average_volume"] = total_volume / calc_count
                
                elif event_type == "request":
                    period_data["total_requests"] = period_data.get("total_requests", 0) + 1
                    
                    # Типы грузов
                    cargo_type = event_data.get("data", {}).get("cargo_description", "Неизвестно")
                    cargo_types = period_data.get("cargo_types", {})
                    cargo_types[cargo_type] = cargo_types.get(cargo_type, 0) + 1
                    period_data["cargo_types"] = cargo_types
                
                analytics[period] = period_data
            
            # Сохраняем аналитику
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(analytics, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"Ошибка обновления аналитики: {e}")
    
    def _load_analytics(self) -> Dict[str, Any]:
        """Загрузка аналитики"""
        try:
            if os.path.exists(self.analytics_file):
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Ошибка загрузки аналитики: {e}")
        
        # Возвращаем пустую структуру
        return {
            "weekly": {},
            "monthly": {},
            "quarterly": {},
            "all_time": {}
        }
    
    def get_analytics(self, period: str = "all_time") -> Dict[str, Any]:
        """Получение аналитики за период"""
        analytics = self._load_analytics()
        return analytics.get(period, {})
    
    def get_incomplete_calculations_stats(self) -> Dict[str, Any]:
        """Получение статистики незавершенных расчетов"""
        try:
            if not os.path.exists(self.incomplete_calculations_file):
                return {"weekly": {}, "monthly": {}, "quarterly": {}, "all_time": {}}
            
            with open(self.incomplete_calculations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            calculations = data.get("calculations", [])
            now = datetime.now()
            
            stats = {
                "weekly": {"total": 0, "by_step": {}},
                "monthly": {"total": 0, "by_step": {}},
                "quarterly": {"total": 0, "by_step": {}},
                "all_time": {"total": 0, "by_step": {}}
            }
            
            for calc in calculations:
                calc_time = datetime.fromisoformat(calc["timestamp"])
                step = calc.get("step", "unknown")
                
                # Определяем период
                days_diff = (now - calc_time).days
                
                if days_diff <= 7:
                    stats["weekly"]["total"] += 1
                    stats["weekly"]["by_step"][step] = stats["weekly"]["by_step"].get(step, 0) + 1
                
                if days_diff <= 30:
                    stats["monthly"]["total"] += 1
                    stats["monthly"]["by_step"][step] = stats["monthly"]["by_step"].get(step, 0) + 1
                
                if days_diff <= 90:
                    stats["quarterly"]["total"] += 1
                    stats["quarterly"]["by_step"][step] = stats["quarterly"]["by_step"].get(step, 0) + 1
                
                stats["all_time"]["total"] += 1
                stats["all_time"]["by_step"][step] = stats["all_time"]["by_step"].get(step, 0) + 1
            
            return stats
            
        except Exception as e:
            logging.error(f"Ошибка получения статистики незавершенных расчетов: {e}")
            return {"weekly": {}, "monthly": {}, "quarterly": {}, "all_time": {}}
    
    def get_last_requests(self, count: int = 5) -> List[Dict[str, Any]]:
        """Получение последних заявок"""
        try:
            if not os.path.exists(self.requests_log_file):
                return []
            
            with open(self.requests_log_file, 'r', encoding='utf-8') as f:
                requests = json.load(f)
            
            return requests[-count:] if len(requests) >= count else requests
            
        except Exception as e:
            logging.error(f"Ошибка получения последних заявок: {e}")
            return []
    
    def get_last_uploads(self, count: int = 3) -> List[Dict[str, Any]]:
        """Получение последних загрузок"""
        try:
            if not os.path.exists(self.uploads_log_file):
                return []
            
            with open(self.uploads_log_file, 'r', encoding='utf-8') as f:
                uploads = json.load(f)
            
            return uploads[-count:] if len(uploads) >= count else uploads
            
        except Exception as e:
            logging.error(f"Ошибка получения последних загрузок: {e}")
            return []

# Глобальный экземпляр логгера
bot_logger = BotLogger()
