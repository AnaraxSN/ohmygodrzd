import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict
from loguru import logger

from src.config import settings
from src.database import engine
from src.models import Subscription, FoundTicket, User
from src.scraper import RZDScraper
from telegram import Bot
from telegram.error import TelegramError


class MonitoringService:
    def __init__(self):
        self.scraper = RZDScraper()
        self.bot = Bot(token=settings.telegram_bot_token)
        self.is_running = False
    
    async def start_monitoring(self):
        """Запуск сервиса мониторинга"""
        self.is_running = True
        logger.info("Сервис мониторинга запущен")
        
        while self.is_running:
            try:
                await self.check_all_subscriptions()
                await asyncio.sleep(settings.check_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Ошибка в сервисе мониторинга: {e}")
                await asyncio.sleep(60)  # Ждем минуту перед повтором
    
    async def stop_monitoring(self):
        """Остановка сервиса мониторинга"""
        self.is_running = False
        logger.info("Сервис мониторинга остановлен")
    
    async def check_all_subscriptions(self):
        """Проверка всех активных подписок"""
        with Session(engine) as db:
            # Получаем все активные подписки, которые нужно проверить
            subscriptions = db.query(Subscription).filter(
                Subscription.is_active == True
            ).all()
            
            logger.info(f"Проверка {len(subscriptions)} подписок")
            
            for subscription in subscriptions:
                try:
                    await self.check_subscription(subscription, db)
                except Exception as e:
                    logger.error(f"Ошибка проверки подписки {subscription.id}: {e}")
                    continue
    
    async def check_subscription(self, subscription: Subscription, db: Session):
        """Проверка конкретной подписки"""
        try:
            # Проверяем, нужно ли проверять эту подписку сейчас
            if subscription.last_checked:
                time_since_last_check = datetime.now() - subscription.last_checked
                if time_since_last_check.total_seconds() < subscription.check_frequency * 60:
                    return  # Еще рано проверять
            
            logger.info(f"Проверка подписки {subscription.id}: {subscription.departure_station} -> {subscription.arrival_station}")
            
            # Ищем билеты
            trains = self.scraper.search_tickets(
                departure_station=subscription.departure_station,
                arrival_station=subscription.arrival_station,
                departure_date=subscription.departure_date,
                train_number=subscription.train_number
            )
            
            # Обновляем время последней проверки
            subscription.last_checked = datetime.now()
            db.commit()
            
            # Обрабатываем найденные поезда
            for train in trains:
                await self.process_found_train(train, subscription, db)
                
        except Exception as e:
            logger.error(f"Ошибка при проверке подписки {subscription.id}: {e}")
    
    async def process_found_train(self, train: Dict, subscription: Subscription, db: Session):
        """Обработка найденного поезда"""
        try:
            # Проверяем, соответствует ли поезд критериям подписки
            if not self.train_matches_subscription(train, subscription):
                return
            
            # Проверяем, есть ли доступные места нужного типа
            available_seats = train.get('available_seats', {})
            if not self.has_matching_seats(available_seats, subscription.seat_type):
                return
            
            # Проверяем, не уведомляли ли мы уже об этом поезде
            existing_ticket = db.query(FoundTicket).filter(
                FoundTicket.subscription_id == subscription.id,
                FoundTicket.train_number == train.get('train_number'),
                FoundTicket.departure_time == train.get('departure_time'),
                FoundTicket.is_notified == True
            ).first()
            
            if existing_ticket:
                return  # Уже уведомляли
            
            # Создаем запись о найденном билете
            found_ticket = FoundTicket(
                subscription_id=subscription.id,
                train_number=train.get('train_number'),
                departure_time=train.get('departure_time'),
                arrival_time=train.get('arrival_time'),
                available_seats=available_seats,
                prices=train.get('prices', {})
            )
            
            db.add(found_ticket)
            db.commit()
            
            # Отправляем уведомление
            await self.send_notification(subscription, train, found_ticket.id)
            
            # Отмечаем как уведомленное
            found_ticket.is_notified = True
            db.commit()
            
            logger.info(f"Найден билет для подписки {subscription.id}: {train.get('train_number')}")
            
        except Exception as e:
            logger.error(f"Ошибка обработки найденного поезда: {e}")
    
    def train_matches_subscription(self, train: Dict, subscription: Subscription) -> bool:
        """Проверка соответствия поезда критериям подписки"""
        # Если указан конкретный номер поезда, проверяем его
        if subscription.train_number:
            return train.get('train_number') == subscription.train_number
        
        return True  # Если номер поезда не указан, подходит любой
    
    def has_matching_seats(self, available_seats: Dict, seat_type: str) -> bool:
        """Проверка наличия мест нужного типа"""
        if not seat_type or seat_type == 'любой':
            return len(available_seats) > 0
        
        # Проверяем наличие мест указанного типа
        for seat_type_name, seat_info in available_seats.items():
            if seat_type.lower() in seat_type_name.lower():
                count = seat_info.get('count', '0')
                if isinstance(count, str):
                    count = ''.join(filter(str.isdigit, count))
                    count = int(count) if count else 0
                return count > 0
        
        return False
    
    async def send_notification(self, subscription: Subscription, train: Dict, ticket_id: int):
        """Отправка уведомления пользователю"""
        try:
            user = subscription.user
            
            # Формируем сообщение
            message = self.format_notification_message(subscription, train, ticket_id)
            
            # Отправляем уведомление
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Уведомление отправлено пользователю {user.telegram_id}")
            
        except TelegramError as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке уведомления: {e}")
    
    def format_notification_message(self, subscription: Subscription, train: Dict, ticket_id: int) -> str:
        """Форматирование сообщения уведомления"""
        train_number = train.get('train_number', 'Неизвестно')
        departure_time = train.get('departure_time', 'Неизвестно')
        arrival_time = train.get('arrival_time', 'Неизвестно')
        available_seats = train.get('available_seats', {})
        prices = train.get('prices', {})
        
        message = f"""
🎫 <b>НАЙДЕНЫ БИЛЕТЫ!</b>

🚂 <b>Поезд:</b> {train_number}
📍 <b>Маршрут:</b> {subscription.departure_station} → {subscription.arrival_station}
📅 <b>Дата:</b> {subscription.departure_date.strftime('%d.%m.%Y')}
🕐 <b>Отправление:</b> {departure_time}
🕐 <b>Прибытие:</b> {arrival_time}

💺 <b>Доступные места:</b>
"""
        
        # Добавляем информацию о доступных местах
        for seat_type, seat_info in available_seats.items():
            count = seat_info.get('count', '0')
            price = seat_info.get('price', '0')
            message += f"• {seat_type.title()}: {count} мест от {price}₽\n"
        
        # Добавляем ссылку на покупку (примерная)
        rzd_url = f"https://pass.rzd.ru/tickets/public/ru?layerName=search&ticketSearch[departureStation]={subscription.departure_station}&ticketSearch[arrivalStation]={subscription.arrival_station}&ticketSearch[departureDate]={subscription.departure_date.strftime('%d.%m.%Y')}"
        
        message += f"""
🔗 <a href="{rzd_url}">Купить билет</a>

📋 Подписка: #{subscription.id} ({subscription.departure_station} → {subscription.arrival_station})
        """
        
        return message.strip()
    
    async def get_statistics(self) -> Dict:
        """Получение статистики мониторинга"""
        with Session(engine) as db:
            total_subscriptions = db.query(Subscription).filter(Subscription.is_active == True).count()
            total_found_tickets = db.query(FoundTicket).count()
            total_notifications = db.query(FoundTicket).filter(FoundTicket.is_notified == True).count()
            
            return {
                'active_subscriptions': total_subscriptions,
                'found_tickets': total_found_tickets,
                'sent_notifications': total_notifications
            }

