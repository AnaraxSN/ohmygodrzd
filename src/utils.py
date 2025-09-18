from datetime import datetime, date
from typing import Optional, List, Dict
import re


def validate_date(date_string: str) -> Optional[date]:
    """
    Валидация даты в формате ДД.ММ.ГГГГ
    """
    try:
        return datetime.strptime(date_string, '%d.%m.%Y').date()
    except ValueError:
        return None


def validate_train_number(train_number: str) -> bool:
    """
    Валидация номера поезда
    """
    # Простая валидация: номер должен содержать цифры и буквы
    pattern = r'^[0-9]{3}[А-Я]{1}$'
    return bool(re.match(pattern, train_number.upper()))


def format_station_name(station_code: str, station_name: str) -> str:
    """
    Форматирование названия станции для отображения
    """
    return f"{station_name} ({station_code})"


def format_price(price: str) -> str:
    """
    Форматирование цены для отображения
    """
    # Извлекаем только цифры
    digits = re.findall(r'\d+', price)
    if digits:
        return f"{digits[0]}₽"
    return "0₽"


def format_time(time_string: str) -> str:
    """
    Форматирование времени для отображения
    """
    if not time_string:
        return "Неизвестно"
    
    # Пытаемся извлечь время в формате ЧЧ:ММ
    time_match = re.search(r'\d{1,2}:\d{2}', time_string)
    if time_match:
        return time_match.group()
    
    return time_string


def get_seat_type_emoji(seat_type: str) -> str:
    """
    Получение эмодзи для типа места
    """
    emoji_map = {
        'плацкарт': '💺',
        'купе': '🚪',
        'св': '🛏',
        'сидячие': '🪑',
        'люкс': '👑',
        'любой': '🔍'
    }
    
    return emoji_map.get(seat_type.lower(), '💺')


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Обрезание текста до указанной длины
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def parse_station_code(station_input: str) -> str:
    """
    Извлечение кода станции из ввода пользователя
    """
    # Если ввод содержит код в скобках, извлекаем его
    code_match = re.search(r'\(([^)]+)\)', station_input)
    if code_match:
        return code_match.group(1).upper()
    
    # Если ввод похож на код (3-4 символа), возвращаем как есть
    if len(station_input) <= 4 and station_input.isupper():
        return station_input
    
    # Иначе возвращаем весь ввод
    return station_input


def is_valid_station_code(code: str) -> bool:
    """
    Проверка валидности кода станции
    """
    # Код станции должен быть 3-4 символа, буквы и цифры
    pattern = r'^[А-Я0-9]{3,4}$'
    return bool(re.match(pattern, code.upper()))


def format_subscription_summary(subscription_data: Dict) -> str:
    """
    Форматирование сводки подписки
    """
    summary = f"🚂 {subscription_data['departure_station_name']} → {subscription_data['arrival_station_name']}\n"
    summary += f"📅 {subscription_data['departure_date'].strftime('%d.%m.%Y')}\n"
    
    if subscription_data.get('train_number'):
        summary += f"🚆 Поезд: {subscription_data['train_number']}\n"
    
    if subscription_data.get('seat_type'):
        emoji = get_seat_type_emoji(subscription_data['seat_type'])
        summary += f"{emoji} Тип места: {subscription_data['seat_type']}\n"
    
    return summary.strip()


def get_time_range_emoji(time_range: str) -> str:
    """
    Получение эмодзи для временного диапазона
    """
    emoji_map = {
        'утро': '🌅',
        'день': '☀️',
        'вечер': '🌆',
        'ночь': '🌙',
        'любое': '⏰'
    }
    
    return emoji_map.get(time_range.lower(), '⏰')


def calculate_next_check_time(check_frequency_minutes: int) -> datetime:
    """
    Расчет времени следующей проверки
    """
    return datetime.now() + timedelta(minutes=check_frequency_minutes)


def format_duration(start_time: str, end_time: str) -> str:
    """
    Форматирование продолжительности поездки
    """
    try:
        start = datetime.strptime(start_time, '%H:%M')
        end = datetime.strptime(end_time, '%H:%M')
        
        # Если время прибытия меньше времени отправления, значит поездка на следующий день
        if end < start:
            end = end.replace(day=end.day + 1)
        
        duration = end - start
        hours = duration.total_seconds() // 3600
        minutes = (duration.total_seconds() % 3600) // 60
        
        if hours > 0:
            return f"{int(hours)}ч {int(minutes)}м"
        else:
            return f"{int(minutes)}м"
            
    except ValueError:
        return "Неизвестно"


def sanitize_input(text: str) -> str:
    """
    Очистка пользовательского ввода от потенциально опасных символов
    """
    # Удаляем HTML теги и специальные символы
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\w\s\-\.\(\)]', '', text)
    return text.strip()


def format_notification_time() -> str:
    """
    Форматирование времени для уведомлений
    """
    now = datetime.now()
    return now.strftime('%d.%m.%Y %H:%M')


def is_working_hours() -> bool:
    """
    Проверка, находится ли текущее время в рабочих часах
    """
    now = datetime.now()
    return 8 <= now.hour <= 22


def get_subscription_status_emoji(is_active: bool, last_checked: Optional[datetime]) -> str:
    """
    Получение эмодзи статуса подписки
    """
    if not is_active:
        return "❌"
    
    if not last_checked:
        return "⏳"
    
    # Проверяем, когда была последняя проверка
    time_since_check = datetime.now() - last_checked
    
    if time_since_check.total_seconds() < 300:  # Менее 5 минут
        return "🟢"
    elif time_since_check.total_seconds() < 1800:  # Менее 30 минут
        return "🟡"
    else:
        return "🔴"

