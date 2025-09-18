#!/usr/bin/env python3
"""
Скрипт для запуска различных компонентов системы
"""

import sys
import os
import argparse
from loguru import logger

# Добавляем путь к src в sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config import settings


def run_bot():
    """Запуск Telegram бота"""
    from src.bot import main
    import asyncio
    
    logger.info("Запуск Telegram бота...")
    asyncio.run(main())


def run_celery_worker():
    """Запуск Celery worker"""
    from src.celery_app import celery_app
    
    logger.info("Запуск Celery worker...")
    celery_app.worker_main(['worker', '--loglevel=info'])


def run_celery_beat():
    """Запуск Celery beat (планировщик)"""
    from src.celery_app import celery_app
    
    logger.info("Запуск Celery beat...")
    celery_app.start(['beat', '--loglevel=info'])


def run_migrations():
    """Запуск миграций базы данных"""
    import subprocess
    
    logger.info("Запуск миграций базы данных...")
    subprocess.run(['alembic', 'upgrade', 'head'])


def create_migration():
    """Создание новой миграции"""
    import subprocess
    
    logger.info("Создание новой миграции...")
    subprocess.run(['alembic', 'revision', '--autogenerate', '-m', 'Auto migration'])


def run_tests():
    """Запуск тестов"""
    import subprocess
    
    logger.info("Запуск тестов...")
    subprocess.run(['pytest', 'tests/', '-v'])


def main():
    parser = argparse.ArgumentParser(description='RZD Bot Management Script')
    parser.add_argument('command', choices=[
        'bot', 'worker', 'beat', 'migrate', 'create-migration', 'test'
    ], help='Команда для выполнения')
    
    args = parser.parse_args()
    
    # Настройка логирования
    logger.remove()
    logger.add(sys.stdout, level=settings.log_level)
    
    if args.command == 'bot':
        run_bot()
    elif args.command == 'worker':
        run_celery_worker()
    elif args.command == 'beat':
        run_celery_beat()
    elif args.command == 'migrate':
        run_migrations()
    elif args.command == 'create-migration':
        create_migration()
    elif args.command == 'test':
        run_tests()


if __name__ == "__main__":
    main()

