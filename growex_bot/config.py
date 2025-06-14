import os
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_CHAT_ID = int(os.getenv("MANAGER_CHAT_ID"))
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")  # Группа для отправки заявок

# Загрузка списка администраторов
def load_admins():
    try:
        with open("data/admins.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Создаем файл с администраторами по умолчанию
        default_admins = [MANAGER_CHAT_ID] if MANAGER_CHAT_ID else []
        save_admins(default_admins)
        return default_admins

def save_admins(admins_list):
    os.makedirs("data", exist_ok=True)
    with open("data/admins.json", "w", encoding="utf-8") as f:
        json.dump(admins_list, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id in load_admins()

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

if not MANAGER_CHAT_ID:
    raise ValueError("MANAGER_CHAT_ID не найден в переменных окружения")

# Настройки безопасности
MAX_REQUESTS_PER_MINUTE = 10
SPAM_THRESHOLD = 5  # количество запросов за минуту для блокировки

# Настройки уведомлений
TARIFF_WARNING_DAYS = 4  # за сколько дней предупреждать об истечении тарифов
