#!/usr/bin/env python3
"""
Главный файл для запуска Telegram-бота мониторинга билетов РЖД
"""

import asyncio
import sys
import os
from loguru import logger

# Добавляем путь к src в sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.bot import main
from src.config import settings


def setup_logging():
    """Настройка логирования"""
    logger.remove()  # Удаляем стандартный обработчик
    
    # Добавляем обработчик для консоли
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Добавляем обработчик для файла
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )


def main_sync():
    """Синхронная функция запуска"""
    try:
        logger.info("Запуск Telegram-бота мониторинга билетов РЖД")
        logger.info(f"Токен бота: {settings.telegram_bot_token[:10]}...")
        logger.info(f"База данных: {settings.database_url}")
        logger.info(f"Интервал проверки: {settings.check_interval_minutes} минут")
        
        # Запускаем бота
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_logging()
    main_sync()

