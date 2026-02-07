import re
from django import template

register = template.Library()


@register.filter
def youtube_id(url):
    """Извлекает YouTube video ID из различных форматов URL"""
    if not url:
        return None
    
    # Убираем пробелы
    url = url.strip()
    
    if not url:
        return None
    
    # Паттерны для разных форматов YouTube URL
    # Приоритет: сначала проверяем короткие ссылки, потом полные
    patterns = [
        r'youtu\.be\/([a-zA-Z0-9_-]{11})',  # Короткие ссылки youtu.be
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',  # Embed ссылки
        r'youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',  # Обычные ссылки с v=
        r'youtube\.com\/watch\?.*[&?]v=([a-zA-Z0-9_-]{11})',  # Ссылки с дополнительными параметрами
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            # Проверяем, что ID валидный (11 символов)
            if len(video_id) == 11:
                return video_id
    
    return None


@register.filter
def vimeo_id(url):
    """Извлекает Vimeo video ID из URL"""
    if not url:
        return None
    
    pattern = r'vimeo\.com\/(?:video\/)?(\d+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    
    return None


@register.filter
def is_not_empty(value):
    """Проверяет, не является ли значение пустым"""
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip()
        # Проверяем, что это не пустая строка и не только пробелы
        return len(stripped) > 0 and stripped.lower() != 'none' and stripped.lower() != 'null'
    return bool(value)

