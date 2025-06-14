import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ExcelParser:
    """Класс для парсинга Excel файлов с тарифами"""
    
    def __init__(self):
        self.composite_file_name = "Комплексная ставка.xlsx"
        self.novorossiysk_file_name = "До Новороссийска.xlsx"
    
    def parse_composite_rates(self, file_path: str) -> Dict[str, Any]:
        """Парсинг файла с комплексными ставками"""
        try:
            # Читаем файл с правильным заголовком
            df = pd.read_excel(file_path, header=1)
            
            # Получаем дату действия тарифов из последней колонки
            valid_until = None
            for col in df.columns:
                if isinstance(col, datetime):
                    valid_until = col.strftime("%Y-%m-%d")
                    break
            
            # Удаляем колонки с датами и пустые
            df = df.loc[:, ~df.columns.str.contains('Unnamed')]
            df = df.dropna(subset=[df.columns[0]])  # Удаляем строки без названия города
            
            rates = {}
            
            for index, row in df.iterrows():
                city = row.iloc[0]  # Первая колонка - название города
                if pd.isna(city) or city == "в USD":
                    continue
                
                city_rates = {}
                # Парсим ставки по объемам
                for i, col in enumerate(df.columns[1:], 1):
                    if "М3" in str(col):
                        volume = self._extract_volume_from_column(str(col))
                        if volume and not pd.isna(row.iloc[i]):
                            city_rates[str(volume)] = float(row.iloc[i])
                
                if city_rates:
                    rates[city] = city_rates
            
            return {
                "valid_until": valid_until,
                "currency": "USD",
                "rates": rates,
                "last_update": datetime.now().isoformat(),
                "filename": os.path.basename(file_path)
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга комплексных ставок: {e}")
            raise ValueError(f"Ошибка обработки файла: {str(e)}")
    
    def parse_novorossiysk_rates(self, file_path: str) -> Dict[str, Any]:
        """Парсинг файла со ставками до Новороссийска"""
        try:
            # Читаем файл с правильным заголовком
            df = pd.read_excel(file_path, header=1)
            
            # Получаем дату действия тарифов
            valid_until = None
            for col in df.columns:
                if isinstance(col, datetime):
                    valid_until = col.strftime("%Y-%m-%d")
                    break
            
            rates = {}
            
            # Берем первую строку с данными
            if len(df) > 0:
                row = df.iloc[0]
                for i, col in enumerate(df.columns):
                    if "М3" in str(col) and not pd.isna(row.iloc[i]):
                        volume = self._extract_volume_from_column(str(col))
                        if volume:
                            rates[str(volume)] = float(row.iloc[i])
            
            return {
                "valid_until": valid_until,
                "currency": "USD",
                "rates": {"default": rates},
                "last_update": datetime.now().isoformat(),
                "filename": os.path.basename(file_path)
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ставок до Новороссийска: {e}")
            raise ValueError(f"Ошибка обработки файла: {str(e)}")
    
    def _extract_volume_from_column(self, column_name: str) -> Optional[int]:
        """Извлекает объем из названия колонки"""
        try:
            # Ищем число перед "М3"
            import re
            match = re.search(r'(\d+)\s*М3', column_name)
            if match:
                return int(match.group(1))
        except:
            pass
        return None
    
    def validate_excel_file(self, file_path: str, expected_type: str) -> Tuple[bool, str]:
        """Валидация Excel файла"""
        try:
            if not os.path.exists(file_path):
                return False, "Файл не найден"
            
            if not file_path.endswith('.xlsx'):
                return False, "Неподдерживаемый формат файла. Требуется .xlsx"
            
            # Проверяем, можно ли открыть файл
            df = pd.read_excel(file_path)
            
            if expected_type == "composite":
                # Проверяем структуру файла комплексных ставок
                if len(df.columns) < 10:
                    return False, "Недостаточно колонок в файле комплексных ставок"
                
                # Проверяем наличие городов
                df_with_header = pd.read_excel(file_path, header=1)
                if len(df_with_header) < 5:
                    return False, "Недостаточно городов в файле"
                    
            elif expected_type == "novorossiysk":
                # Проверяем структуру файла до Новороссийска
                df_with_header = pd.read_excel(file_path, header=1)
                if len(df_with_header.columns) < 10:
                    return False, "Недостаточно колонок в файле ставок до Новороссийска"
            
            return True, "Файл прошел валидацию"
            
        except Exception as e:
            return False, f"Ошибка валидации файла: {str(e)}"
    
    def get_file_type_by_name(self, filename: str) -> Optional[str]:
        """Определяет тип файла по названию"""
        if self.composite_file_name.lower() in filename.lower():
            return "composite"
        elif self.novorossiysk_file_name.lower() in filename.lower():
            return "novorossiysk"
        return None 