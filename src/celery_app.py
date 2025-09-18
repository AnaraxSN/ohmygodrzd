from celery import Celery
from src.config import settings

# Создаем экземпляр Celery
celery_app = Celery(
    'rzd_bot',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['src.tasks']
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,  # 25 минут
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Периодические задачи
celery_app.conf.beat_schedule = {
    'check-subscriptions': {
        'task': 'src.tasks.check_all_subscriptions',
        'schedule': settings.check_interval_minutes * 60.0,  # в секундах
    },
    'cleanup-old-tickets': {
        'task': 'src.tasks.cleanup_old_tickets',
        'schedule': 24 * 60 * 60.0,  # раз в день
    },
    'update-stations': {
        'task': 'src.tasks.update_stations_list',
        'schedule': 7 * 24 * 60 * 60.0,  # раз в неделю
    },
}

if __name__ == '__main__':
    celery_app.start()

