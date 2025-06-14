import json
import os

COUNTER_FILE = "data/counter.json"

def load_counters():
    """Загрузка счетчиков из файла"""
    if not os.path.exists(COUNTER_FILE):
        # Создаем директорию если её нет
        os.makedirs("data", exist_ok=True)
        # Создаем файл с начальными значениями
        default_data = {"calculations_total": 0, "calculations_with_contacts": 0}
        save_counters(default_data)
        return default_data
    
    try:
        with open(COUNTER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # Если файл поврежден, создаем новый
        default_data = {"calculations_total": 0, "calculations_with_contacts": 0}
        save_counters(default_data)
        return default_data

def save_counters(data):
    """Сохранение счетчиков в файл"""
    try:
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения счетчиков: {e}")

def increment_calculation():
    """Увеличение счетчика расчетов"""
    counters = load_counters()
    counters["calculations_total"] += 1
    save_counters(counters)
    return counters["calculations_total"]

def increment_lead():
    """Увеличение счетчика лидов (расчетов с контактами)"""
    counters = load_counters()
    counters["calculations_with_contacts"] += 1
    save_counters(counters)
    return counters["calculations_with_contacts"]

def get_statistics():
    """Получение статистики"""
    counters = load_counters()
    return {
        "total_calculations": counters["calculations_total"],
        "total_leads": counters["calculations_with_contacts"],
        "conversion_rate": round(
            (counters["calculations_with_contacts"] / max(counters["calculations_total"], 1)) * 100, 2
        )
    }
