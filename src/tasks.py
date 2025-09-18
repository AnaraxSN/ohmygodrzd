from celery import current_task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from loguru import logger

from src.celery_app import celery_app
from src.database import engine
from src.models import Subscription, FoundTicket, Station
from src.scraper import RZDScraper
from src.monitoring import MonitoringService


@celery_app.task(bind=True)
def check_all_subscriptions(self):
    """
    Проверка всех активных подписок
    """
    try:
        logger.info("Начало проверки всех подписок")
        
        with Session(engine) as db:
            # Получаем все активные подписки
            subscriptions = db.query(Subscription).filter(
                Subscription.is_active == True
            ).all()
            
            logger.info(f"Найдено {len(subscriptions)} активных подписок")
            
            monitoring = MonitoringService()
            
            for i, subscription in enumerate(subscriptions):
                try:
                    # Обновляем прогресс задачи
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': i + 1, 'total': len(subscriptions)}
                    )
                    
                    # Проверяем подписку
                    await monitoring.check_subscription(subscription, db)
                    
                except Exception as e:
                    logger.error(f"Ошибка проверки подписки {subscription.id}: {e}")
                    continue
            
            logger.info("Проверка всех подписок завершена")
            return {'status': 'completed', 'checked': len(subscriptions)}
            
    except Exception as e:
        logger.error(f"Ошибка в задаче проверки подписок: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task
def cleanup_old_tickets():
    """
    Очистка старых найденных билетов (старше 7 дней)
    """
    try:
        logger.info("Начало очистки старых билетов")
        
        with Session(engine) as db:
            cutoff_date = datetime.now() - timedelta(days=7)
            
            old_tickets = db.query(FoundTicket).filter(
                FoundTicket.found_at < cutoff_date
            ).all()
            
            count = len(old_tickets)
            
            for ticket in old_tickets:
                db.delete(ticket)
            
            db.commit()
            
            logger.info(f"Удалено {count} старых билетов")
            return {'status': 'completed', 'deleted': count}
            
    except Exception as e:
        logger.error(f"Ошибка очистки старых билетов: {e}")
        raise


@celery_app.task
def update_stations_list():
    """
    Обновление списка станций РЖД
    """
    try:
        logger.info("Начало обновления списка станций")
        
        scraper = RZDScraper()
        
        # Получаем список популярных станций
        popular_stations = [
            'Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург',
            'Казань', 'Нижний Новгород', 'Челябинск', 'Самара',
            'Омск', 'Ростов-на-Дону', 'Уфа', 'Красноярск',
            'Воронеж', 'Пермь', 'Волгоград', 'Владивосток'
        ]
        
        with Session(engine) as db:
            updated_count = 0
            
            for station_name in popular_stations:
                try:
                    stations = scraper.get_stations(station_name)
                    
                    for station_data in stations:
                        existing_station = db.query(Station).filter(
                            Station.code == station_data['code']
                        ).first()
                        
                        if not existing_station:
                            new_station = Station(
                                code=station_data['code'],
                                name=station_data['name'],
                                region=station_data.get('region', '')
                            )
                            db.add(new_station)
                            updated_count += 1
                        
                except Exception as e:
                    logger.warning(f"Ошибка обновления станции {station_name}: {e}")
                    continue
            
            db.commit()
            
            logger.info(f"Обновлено {updated_count} станций")
            return {'status': 'completed', 'updated': updated_count}
            
    except Exception as e:
        logger.error(f"Ошибка обновления списка станций: {e}")
        raise


@celery_app.task
def send_notification_task(user_id: int, message: str):
    """
    Отправка уведомления пользователю
    """
    try:
        from telegram import Bot
        from src.config import settings
        
        bot = Bot(token=settings.telegram_bot_token)
        
        bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
        
        logger.info(f"Уведомление отправлено пользователю {user_id}")
        return {'status': 'sent', 'user_id': user_id}
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
        raise


@celery_app.task
def check_specific_subscription(subscription_id: int):
    """
    Проверка конкретной подписки
    """
    try:
        logger.info(f"Проверка подписки {subscription_id}")
        
        with Session(engine) as db:
            subscription = db.query(Subscription).filter(
                Subscription.id == subscription_id,
                Subscription.is_active == True
            ).first()
            
            if not subscription:
                logger.warning(f"Подписка {subscription_id} не найдена или неактивна")
                return {'status': 'not_found'}
            
            monitoring = MonitoringService()
            await monitoring.check_subscription(subscription, db)
            
            logger.info(f"Подписка {subscription_id} проверена")
            return {'status': 'checked', 'subscription_id': subscription_id}
            
    except Exception as e:
        logger.error(f"Ошибка проверки подписки {subscription_id}: {e}")
        raise


@celery_app.task
def get_monitoring_statistics():
    """
    Получение статистики мониторинга
    """
    try:
        with Session(engine) as db:
            total_subscriptions = db.query(Subscription).filter(
                Subscription.is_active == True
            ).count()
            
            total_found_tickets = db.query(FoundTicket).count()
            
            total_notifications = db.query(FoundTicket).filter(
                FoundTicket.is_notified == True
            ).count()
            
            recent_tickets = db.query(FoundTicket).filter(
                FoundTicket.found_at >= datetime.now() - timedelta(hours=24)
            ).count()
            
            return {
                'active_subscriptions': total_subscriptions,
                'total_found_tickets': total_found_tickets,
                'total_notifications': total_notifications,
                'recent_tickets_24h': recent_tickets,
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise

