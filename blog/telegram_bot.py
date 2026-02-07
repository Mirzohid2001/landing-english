"""
Утилита для отправки сообщений в Telegram бот
"""
import requests
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(message: str, chat_id: str = None) -> bool:
    """
    Отправляет сообщение в Telegram бот
    
    Args:
        message: Текст сообщения
        chat_id: ID чата (если не указан, используется из настроек)
    
    Returns:
        bool: True если успешно, False если ошибка
    """
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен в settings.py")
        print("❌ TELEGRAM_BOT_TOKEN не настроен в settings.py")
        return False
    
    if not chat_id:
        chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
    
    if not chat_id:
        logger.error("TELEGRAM_CHAT_ID не настроен в settings.py")
        print("❌ TELEGRAM_CHAT_ID не настроен в settings.py")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    
    try:
        logger.info(f"Отправка сообщения в Telegram. Chat ID: {chat_id}")
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get('ok'):
            logger.info("Сообщение успешно отправлено в Telegram")
            print("✅ Сообщение успешно отправлено в Telegram")
            return True
        else:
            error_description = result.get('description', 'Unknown error')
            logger.error(f"Ошибка Telegram API: {error_description}")
            print(f"❌ Ошибка Telegram API: {error_description}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("Таймаут при отправке сообщения в Telegram")
        print("❌ Таймаут при отправке сообщения в Telegram")
        return False
    except requests.exceptions.HTTPError as e:
        error_text = ""
        try:
            error_data = e.response.json()
            error_text = error_data.get('description', str(e))
        except:
            error_text = str(e)
        logger.error(f"HTTP ошибка при отправке в Telegram: {error_text}")
        print(f"❌ HTTP ошибка при отправке в Telegram: {error_text}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
        print(f"❌ Ошибка при отправке сообщения в Telegram: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        print(f"❌ Неожиданная ошибка: {e}")
        return False


def format_contact_message(contact_request) -> str:
    """
    Форматирует сообщение для контактной формы
    
    Args:
        contact_request: Объект ContactRequest
    
    Returns:
        str: Отформатированное сообщение
    """
    # Экранируем HTML символы для безопасности
    def escape_html(text):
        if text:
            return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return ''
    
    message = f"""━━━━━━━━━━━━━━━━━━━━
🔔 <b>НОВАЯ ЗАЯВКА С КОНТАКТНОЙ ФОРМЫ</b>
━━━━━━━━━━━━━━━━━━━━

👤 <b>Имя:</b>
   {escape_html(contact_request.name)}

📞 <b>Телефон:</b>
   <code>{escape_html(contact_request.phone)}</code>

📧 <b>Email:</b>
   <code>{escape_html(contact_request.email)}</code>

💬 <b>Сообщение:</b>
   {escape_html(contact_request.message)}

━━━━━━━━━━━━━━━━━━━━
⏰ <i>{contact_request.created_at.strftime('%d.%m.%Y в %H:%M')}</i>
━━━━━━━━━━━━━━━━━━━━"""
    return message.strip()


def format_course_application_message(application) -> str:
    """
    Форматирует сообщение для заявки на курс
    
    Args:
        application: Объект CourseApplication
    
    Returns:
        str: Отформатированное сообщение
    """
    # Экранируем HTML символы для безопасности
    def escape_html(text):
        if text:
            return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return ''
    
    # Получаем уровень курса
    level_emoji = {
        'beginner': '🟢',
        'elementary': '🟡',
        'intermediate': '🟠',
        'upper-intermediate': '🔵',
        'advanced': '🔴'
    }
    level_emoji_icon = level_emoji.get(application.course.level, '📚')
    
    message = f"""━━━━━━━━━━━━━━━━━━━━
🎓 <b>НОВАЯ ЗАЯВКА НА КУРС</b>
━━━━━━━━━━━━━━━━━━━━

👤 <b>Имя:</b>
   {escape_html(application.name)}

📞 <b>Телефон:</b>
   <code>{escape_html(application.phone)}</code>

📧 <b>Email:</b>
   <code>{escape_html(application.email)}</code>

━━━━━━━━━━━━━━━━━━━━
{level_emoji_icon} <b>Курс:</b>
   {escape_html(application.course.title)}

💰 <b>Стоимость:</b> ${application.course.price}
⏱ <b>Длительность:</b> {application.course.duration}
━━━━━━━━━━━━━━━━━━━━"""
    
    if application.message:
        message += f"""
💬 <b>Дополнительное сообщение:</b>
   {escape_html(application.message)}

━━━━━━━━━━━━━━━━━━━━"""
    
    message += f"""
⏰ <i>{application.created_at.strftime('%d.%m.%Y в %H:%M')}</i>
━━━━━━━━━━━━━━━━━━━━"""
    
    return message.strip()

