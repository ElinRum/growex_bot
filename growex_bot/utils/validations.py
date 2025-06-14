import re
from typing import Tuple, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Счетчик запросов для защиты от спама
request_counter = {}

def is_valid_email(email: str) -> bool:
    """
    Валидация email адреса
    
    Args:
        email: Email адрес для проверки
        
    Returns:
        True если email валидный, False в противном случае
    """
    if not email or len(email) > 254:
        return False
    
    # Улучшенная регулярка для email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(email_pattern, email.strip().lower()))

def is_valid_phone(phone: str) -> Tuple[bool, str]:
    """
    Валидация номера телефона с поддержкой различных форматов
    
    Args:
        phone: Номер телефона для проверки
        
    Returns:
        Кортеж (валиден ли, отформатированный номер)
    """
    if not phone:
        return False, ""
    
    # Удаляем все символы кроме цифр и +
    cleaned_phone = re.sub(r'[^\d+]', '', phone.strip())
    
    # Различные форматы российских номеров
    patterns = [
        # +7XXXXXXXXXX (11 цифр с +7)
        (r'^\+7(\d{10})$', '+7{}'),
        # 7XXXXXXXXXX (11 цифр с 7)
        (r'^7(\d{10})$', '+7{}'),
        # 8XXXXXXXXXX (11 цифр с 8)
        (r'^8(\d{10})$', '+7{}'),
        # 9XXXXXXXXX (10 цифр, начинается с 9)
        (r'^9(\d{9})$', '+79{}'),
    ]
    
    for pattern, format_str in patterns:
        match = re.match(pattern, cleaned_phone)
        if match:
            formatted_phone = format_str.format(match.group(1))
            return True, formatted_phone
    
    return False, ""

def format_phone_mask(phone: str) -> str:
    """
    Форматирование телефона с маской
    
    Args:
        phone: Номер телефона
        
    Returns:
        Отформатированный номер в виде +7 (XXX) XXX-XX-XX
    """
    is_valid, formatted = is_valid_phone(phone)
    if not is_valid:
        return phone
    
    # Извлекаем цифры после +7
    digits = formatted[2:]  # Убираем +7
    
    if len(digits) == 10:
        return f"+7 ({digits[:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:]}"
    
    return formatted

def validate_volume(volume_str: str) -> Tuple[bool, int]:
    """
    Валидация объема груза (только целые числа)
    
    Args:
        volume_str: Строка с объемом
        
    Returns:
        Кортеж (валиден ли, значение)
    """
    try:
        # Заменяем запятую на точку и пытаемся преобразовать
        volume_float = float(volume_str.replace(',', '.').strip())
        volume = int(volume_float)  # Округляем до целого
        
        if 1 <= volume <= 50:  # Разумные пределы для объема в м³
            return True, volume
        return False, 0
    except (ValueError, TypeError):
        return False, 0

def validate_weight(weight_str: str) -> Tuple[bool, int]:
    """
    Валидация веса груза (только целые числа)
    
    Args:
        weight_str: Строка с весом
        
    Returns:
        Кортеж (валиден ли, значение)
    """
    try:
        # Заменяем запятую на точку и пытаемся преобразовать
        weight_float = float(weight_str.replace(',', '.').strip())
        weight = int(weight_float)  # Округляем до целого
        
        if 1 <= weight <= 10000:  # Разумные пределы для веса в кг
            return True, weight
        return False, 0
    except (ValueError, TypeError):
        return False, 0

def validate_city(city: str) -> bool:
    """
    Валидация названия города
    
    Args:
        city: Название города
        
    Returns:
        True если название валидное
    """
    if not city or len(city.strip()) < 2:
        return False
    
    city = city.strip()
    
    # Проверяем длину
    if len(city) > 50:
        return False
    
    # Проверяем, что в названии есть буквы (русские или английские)
    if not re.search(r'[a-zA-Zа-яА-Я]', city):
        return False
    
    # Разрешенные символы: буквы, пробелы, дефисы, точки
    if not re.match(r'^[a-zA-Zа-яА-Я\s\-\.]+$', city):
        return False
    
    return True

def validate_name(name: str) -> bool:
    """
    Валидация имени пользователя
    
    Args:
        name: Имя пользователя
        
    Returns:
        True если имя валидное
    """
    if not name or len(name.strip()) < 2:
        return False
    
    name = name.strip()
    
    # Проверяем длину
    if len(name) > 100:
        return False
    
    # Проверяем, что имя содержит только буквы, пробелы и дефисы
    if not re.match(r'^[a-zA-Zа-яА-Я\s\-]+$', name):
        return False
    
    return True

def validate_cargo_description(description: str) -> bool:
    """
    Валидация описания груза
    
    Args:
        description: Описание груза
        
    Returns:
        True если описание валидное
    """
    if not description or len(description.strip()) < 2:
        return False
    
    description = description.strip()
    
    # Проверяем длину
    if len(description) > 200:
        return False
    
    # Разрешенные символы: буквы, цифры, пробелы и основные знаки препинания
    if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\.\,\-\(\)\/]+$', description):
        return False
    
    return True

def validate_inn(inn: str) -> bool:
    """
    Валидация ИНН (опционально)
    
    Args:
        inn: ИНН для проверки
        
    Returns:
        True если ИНН валидный или пустой
    """
    if not inn:
        return True  # ИНН не обязателен
    
    inn = inn.strip()
    
    # ИНН должен содержать только цифры
    if not inn.isdigit():
        return False
    
    # ИНН может быть 10 или 12 цифр
    if len(inn) not in [10, 12]:
        return False
    
    return True

def check_spam_protection(user_id: int, max_requests: int = 10, time_window: int = 60) -> Tuple[bool, int]:
    """
    Проверка защиты от спама
    
    Args:
        user_id: ID пользователя
        max_requests: Максимальное количество запросов
        time_window: Временное окно в секундах
        
    Returns:
        Кортеж (разрешен ли запрос, количество оставшихся запросов)
    """
    now = datetime.now()
    
    # Очищаем старые записи
    cleanup_old_requests(time_window)
    
    # Получаем историю запросов пользователя
    user_requests = request_counter.get(user_id, [])
    
    # Фильтруем запросы в текущем временном окне
    recent_requests = [
        req_time for req_time in user_requests
        if (now - req_time).total_seconds() <= time_window
    ]
    
    # Проверяем лимит
    if len(recent_requests) >= max_requests:
        return False, 0
    
    # Добавляем текущий запрос
    recent_requests.append(now)
    request_counter[user_id] = recent_requests
    
    remaining = max_requests - len(recent_requests)
    return True, remaining

def cleanup_old_requests(time_window: int = 60):
    """
    Очистка старых запросов из счетчика
    
    Args:
        time_window: Временное окно в секундах
    """
    now = datetime.now()
    
    for user_id in list(request_counter.keys()):
        user_requests = request_counter[user_id]
        
        # Фильтруем только недавние запросы
        recent_requests = [
            req_time for req_time in user_requests
            if (now - req_time).total_seconds() <= time_window
        ]
        
        if recent_requests:
            request_counter[user_id] = recent_requests
        else:
            del request_counter[user_id]

def validate_input_safety(text: str) -> bool:
    """
    Проверка безопасности ввода (защита от инъекций)
    
    Args:
        text: Текст для проверки
        
    Returns:
        True если текст безопасен
    """
    if not text:
        return True
    
    # Список подозрительных паттернов
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
        r'shell_exec',
        r'passthru',
        r'file_get_contents',
        r'fopen\s*\(',
        r'curl_exec',
        r'SELECT\s+.*FROM',
        r'INSERT\s+INTO',
        r'UPDATE\s+.*SET',
        r'DELETE\s+FROM',
        r'DROP\s+TABLE',
    ]
    
    text_lower = text.lower()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.warning(f"Обнаружен подозрительный ввод: {pattern}")
            return False
    
    return True

def get_validation_error_message(field: str, value: str) -> str:
    """
    Получение сообщения об ошибке валидации
    
    Args:
        field: Название поля
        value: Значение поля
        
    Returns:
        Сообщение об ошибке
    """
    error_messages = {
        "email": "❌ Неверный формат email. Пример: example@mail.ru",
        "phone": "❌ Неверный формат телефона. Поддерживаемые форматы:\n"
                "• +7 (XXX) XXX-XX-XX\n"
                "• 8 (XXX) XXX-XX-XX\n"
                "• 7XXXXXXXXXX\n"
                "• 9XXXXXXXXX",
        "volume": "❌ Объем должен быть числом от 1 до 50 м³",
        "weight": "❌ Вес должен быть числом от 1 до 10000 кг",
        "city": "❌ Название города должно содержать от 2 до 50 символов и состоять из букв",
        "name": "❌ Имя должно содержать от 2 до 100 символов и состоять из букв",
        "cargo": "❌ Описание груза должно содержать от 2 до 200 символов",
        "inn": "❌ ИНН должен содержать 10 или 12 цифр",
        "spam": "❌ Превышен лимит запросов. Попробуйте позже.",
        "safety": "❌ Обнаружены недопустимые символы в тексте."
    }
    
    return error_messages.get(field, f"❌ Ошибка валидации поля {field}")

def validate_all_contact_data(name: str, phone: str, email: str = "", inn: str = "") -> Dict[str, Any]:
    """
    Комплексная валидация контактных данных
    
    Args:
        name: Имя
        phone: Телефон
        email: Email (опционально)
        inn: ИНН (опционально)
        
    Returns:
        Словарь с результатами валидации
    """
    result = {
        "valid": True,
        "errors": [],
        "formatted_data": {}
    }
    
    # Проверка безопасности всех полей
    for field_name, field_value in [("name", name), ("phone", phone), ("email", email), ("inn", inn)]:
        if field_value and not validate_input_safety(field_value):
            result["valid"] = False
            result["errors"].append(get_validation_error_message("safety", field_value))
            return result
    
    # Валидация имени
    if not validate_name(name):
        result["valid"] = False
        result["errors"].append(get_validation_error_message("name", name))
    else:
        result["formatted_data"]["name"] = name.strip().title()
    
    # Валидация телефона
    phone_valid, formatted_phone = is_valid_phone(phone)
    if not phone_valid:
        result["valid"] = False
        result["errors"].append(get_validation_error_message("phone", phone))
    else:
        result["formatted_data"]["phone"] = formatted_phone
        result["formatted_data"]["phone_display"] = format_phone_mask(phone)
    
    # Валидация email (если указан)
    if email:
        if not is_valid_email(email):
            result["valid"] = False
            result["errors"].append(get_validation_error_message("email", email))
        else:
            result["formatted_data"]["email"] = email.strip().lower()
    
    # Валидация ИНН (если указан)
    if inn:
        if not validate_inn(inn):
            result["valid"] = False
            result["errors"].append(get_validation_error_message("inn", inn))
        else:
            result["formatted_data"]["inn"] = inn.strip()
    
    return result
