"""
Модуль для расчета стоимости доставки грузов из Турции на основе Excel тарифов
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
import logging
from .excel_parser import ExcelParser

logger = logging.getLogger(__name__)

class TariffManager:
    """Менеджер тарифов для расчета стоимости доставки"""
    
    def __init__(self):
        self.data_dir = "data"
        self.composite_file = os.path.join(self.data_dir, "composite_rates.json")
        self.novorossiysk_file = os.path.join(self.data_dir, "novorossiysk_rates.json")
        self.excel_parser = ExcelParser()
        
        # Создаем директорию если её нет
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Инициализируем тарифы из Excel файлов если JSON файлы не существуют
        self._initialize_tariffs()
    
    def _initialize_tariffs(self):
        """Инициализация тарифов из Excel файлов"""
        try:
            # Проверяем существование JSON файлов
            if not os.path.exists(self.composite_file):
                composite_excel = "tabs_excel/Комплексная ставка.xlsx"
                if os.path.exists(composite_excel):
                    self.update_composite_rates(composite_excel)
            
            if not os.path.exists(self.novorossiysk_file):
                novorossiysk_excel = "tabs_excel/До Новороссийска.xlsx"
                if os.path.exists(novorossiysk_excel):
                    self.update_novorossiysk_rates(novorossiysk_excel)
                    
        except Exception as e:
            logger.error(f"Ошибка инициализации тарифов: {e}")
    
    def update_composite_rates(self, excel_file_path: str) -> Dict[str, Any]:
        """Обновление комплексных тарифов из Excel файла"""
        try:
            # Валидация файла
            is_valid, error_msg = self.excel_parser.validate_excel_file(excel_file_path, "composite")
            if not is_valid:
                raise ValueError(error_msg)
            
            # Создаем бэкап старого файла
            self._create_backup(self.composite_file)
            
            # Парсим новые тарифы
            new_rates = self.excel_parser.parse_composite_rates(excel_file_path)
            
            # Сохраняем в JSON
            with open(self.composite_file, 'w', encoding='utf-8') as f:
                json.dump(new_rates, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Комплексные тарифы обновлены из файла {excel_file_path}")
            return new_rates
            
        except Exception as e:
            logger.error(f"Ошибка обновления комплексных тарифов: {e}")
            raise
    
    def update_novorossiysk_rates(self, excel_file_path: str) -> Dict[str, Any]:
        """Обновление тарифов до Новороссийска из Excel файла"""
        try:
            # Валидация файла
            is_valid, error_msg = self.excel_parser.validate_excel_file(excel_file_path, "novorossiysk")
            if not is_valid:
                raise ValueError(error_msg)
            
            # Создаем бэкап старого файла
            self._create_backup(self.novorossiysk_file)
            
            # Парсим новые тарифы
            new_rates = self.excel_parser.parse_novorossiysk_rates(excel_file_path)
            
            # Сохраняем в JSON
            with open(self.novorossiysk_file, 'w', encoding='utf-8') as f:
                json.dump(new_rates, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Тарифы до Новороссийска обновлены из файла {excel_file_path}")
            return new_rates
            
        except Exception as e:
            logger.error(f"Ошибка обновления тарифов до Новороссийска: {e}")
            raise
    
    def _create_backup(self, file_path: str):
        """Создание бэкапа файла"""
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                import shutil
                shutil.copy2(file_path, backup_path)
                logger.info(f"Создан бэкап: {backup_path}")
            except Exception as e:
                logger.warning(f"Не удалось создать бэкап: {e}")
    
    def get_composite_rates(self) -> Dict[str, Any]:
        """Получение комплексных тарифов"""
        try:
            with open(self.composite_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Файл комплексных тарифов не найден")
            return {"rates": {}, "valid_until": None}
        except Exception as e:
            logger.error(f"Ошибка загрузки комплексных тарифов: {e}")
            return {"rates": {}, "valid_until": None}
    
    def get_novorossiysk_rates(self) -> Dict[str, Any]:
        """Получение тарифов до Новороссийска"""
        try:
            with open(self.novorossiysk_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Файл тарифов до Новороссийска не найден")
            return {"rates": {"default": {}}, "valid_until": None}
        except Exception as e:
            logger.error(f"Ошибка загрузки тарифов до Новороссийска: {e}")
            return {"rates": {"default": {}}, "valid_until": None}
    
    def get_available_cities(self) -> List[str]:
        """Получение списка доступных городов"""
        composite_rates = self.get_composite_rates()
        return list(composite_rates.get("rates", {}).keys())
    
    def calculate_rate(self, volume: int, weight: int, city: str) -> Tuple[float, str, Dict[str, Any]]:
        """
        Расчет ставки доставки
        
        Args:
            volume: Объем в м³
            weight: Вес в кг
            city: Город доставки
            
        Returns:
            Tuple[rate, calculation_type, details]
            rate: Стоимость в USD
            calculation_type: "composite" или "novorossiysk"
            details: Дополнительная информация о расчете
        """
        try:
            # Получаем тарифы
            composite_rates = self.get_composite_rates()
            novorossiysk_rates = self.get_novorossiysk_rates()
            
            # Проверяем, есть ли город в комплексных тарифах
            city_rates = composite_rates.get("rates", {}).get(city)
            
            if city_rates:
                # Расчет по комплексным тарифам
                rate = self._calculate_by_volume_weight(city_rates, volume, weight)
                return rate, "composite", {
                    "city": city,
                    "volume": volume,
                    "weight": weight,
                    "valid_until": composite_rates.get("valid_until"),
                    "currency": "USD"
                }
            else:
                # Расчет до Новороссийска
                default_rates = novorossiysk_rates.get("rates", {}).get("default", {})
                rate = self._calculate_by_volume_weight(default_rates, volume, weight)
                return rate, "novorossiysk", {
                    "city": "СВХ Новороссийск",
                    "original_city": city,
                    "volume": volume,
                    "weight": weight,
                    "valid_until": novorossiysk_rates.get("valid_until"),
                    "currency": "USD",
                    "note": "Доставка до СВХ Новороссийск. Дальнейшая доставка рассчитывается отдельно."
                }
                
        except Exception as e:
            logger.error(f"Ошибка расчета ставки: {e}")
            raise ValueError(f"Ошибка расчета: {str(e)}")
    
    def _calculate_by_volume_weight(self, rates: Dict[str, float], volume: int, weight: int) -> float:
        """
        Расчет ставки по объему и весу
        
        Args:
            rates: Словарь тарифов по объемам
            volume: Объем в м³
            weight: Вес в кг
            
        Returns:
            Стоимость в USD
        """
        if not rates:
            raise ValueError("Тарифы не найдены")
        
        # Находим подходящий тариф по объему
        volume_str = str(volume)
        
        if volume_str in rates:
            return rates[volume_str]
        
        # Если точного объема нет, ищем ближайший больший
        available_volumes = [int(v) for v in rates.keys() if v.isdigit()]
        available_volumes.sort()
        
        for vol in available_volumes:
            if vol >= volume:
                return rates[str(vol)]
        
        # Если объем больше максимального, берем максимальный тариф
        if available_volumes:
            max_volume = max(available_volumes)
            return rates[str(max_volume)]
        
        raise ValueError("Не удалось найти подходящий тариф")
    
    def check_tariff_expiry(self) -> Dict[str, Any]:
        """Проверка срока действия тарифов"""
        result = {
            "composite": {"expired": False, "days_left": None, "valid_until": None},
            "novorossiysk": {"expired": False, "days_left": None, "valid_until": None}
        }
        
        try:
            # Проверяем комплексные тарифы
            composite_rates = self.get_composite_rates()
            if composite_rates.get("valid_until"):
                valid_until = datetime.strptime(composite_rates["valid_until"], "%Y-%m-%d")
                days_left = (valid_until - datetime.now()).days
                result["composite"] = {
                    "expired": days_left < 0,
                    "days_left": days_left,
                    "valid_until": composite_rates["valid_until"]
                }
            
            # Проверяем тарифы до Новороссийска
            novorossiysk_rates = self.get_novorossiysk_rates()
            if novorossiysk_rates.get("valid_until"):
                valid_until = datetime.strptime(novorossiysk_rates["valid_until"], "%Y-%m-%d")
                days_left = (valid_until - datetime.now()).days
                result["novorossiysk"] = {
                    "expired": days_left < 0,
                    "days_left": days_left,
                    "valid_until": novorossiysk_rates["valid_until"]
                }
                
        except Exception as e:
            logger.error(f"Ошибка проверки срока действия тарифов: {e}")
        
        return result

# Глобальный экземпляр менеджера тарифов
tariff_manager = TariffManager()

# Функции для обратной совместимости
def calculate_cost(volume: int = None, weight: int = None, city: str = "Москва") -> Tuple[float, str, Dict[str, Any]]:
    """Расчет стоимости доставки (обертка для совместимости)"""
    if not volume and not weight:
        raise ValueError("Необходимо указать объем или вес груза")
    
    volume = volume or 1
    weight = weight or 100
    
    return tariff_manager.calculate_rate(volume, weight, city)

def get_available_cities() -> List[str]:
    """Получение списка доступных городов"""
    return tariff_manager.get_available_cities()

def check_tariff_expiry() -> Dict[str, Any]:
    """Проверка срока действия тарифов"""
    return tariff_manager.check_tariff_expiry()
