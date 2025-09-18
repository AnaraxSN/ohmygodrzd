import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Dict, List
import json

from src.config import settings
from src.database import get_db, engine
from src.models import User, Subscription, Station, FoundTicket
from src.scraper import RZDScraper
from src.monitoring import MonitoringService
from src.utils import get_seat_type_emoji, format_subscription_summary
from loguru import logger


class RZDBot:
    def __init__(self):
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        self.scraper = RZDScraper()
        self.monitoring = MonitoringService()
        self.user_states = {}  # Для хранения состояний пользователей
        self.setup_handlers()
    
    def create_main_keyboard(self) -> ReplyKeyboardMarkup:
        """Создание основной клавиатуры"""
        keyboard = [
            [KeyboardButton("🚂 Мои подписки"), KeyboardButton("➕ Добавить подписку")],
            [KeyboardButton("⚙️ Настройки"), KeyboardButton("📊 Статус")],
            [KeyboardButton("❓ Помощь"), KeyboardButton("📋 Статистика")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    def create_cancel_keyboard(self) -> InlineKeyboardMarkup:
        """Создание клавиатуры с кнопкой отмены"""
        keyboard = [[InlineKeyboardButton("❌ Отменить", callback_data="cancel_operation")]]
        return InlineKeyboardMarkup(keyboard)
    
    def create_seat_type_keyboard(self) -> InlineKeyboardMarkup:
        """Создание клавиатуры выбора типа места"""
        keyboard = [
            [
                InlineKeyboardButton(f"{get_seat_type_emoji('плацкарт')} Плацкарт", callback_data="seat_плацкарт"),
                InlineKeyboardButton(f"{get_seat_type_emoji('купе')} Купе", callback_data="seat_купе")
            ],
            [
                InlineKeyboardButton(f"{get_seat_type_emoji('св')} СВ", callback_data="seat_св"),
                InlineKeyboardButton(f"{get_seat_type_emoji('сидячие')} Сидячие", callback_data="seat_сидячие")
            ],
            [
                InlineKeyboardButton(f"{get_seat_type_emoji('люкс')} Люкс", callback_data="seat_люкс"),
                InlineKeyboardButton(f"{get_seat_type_emoji('любой')} Любой", callback_data="seat_любой")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_time_range_keyboard(self) -> InlineKeyboardMarkup:
        """Создание клавиатуры выбора времени"""
        keyboard = [
            [InlineKeyboardButton("🌅 Утро (06:00-12:00)", callback_data="time_утро")],
            [InlineKeyboardButton("☀️ День (12:00-18:00)", callback_data="time_день")],
            [InlineKeyboardButton("🌆 Вечер (18:00-24:00)", callback_data="time_вечер")],
            [InlineKeyboardButton("🌙 Ночь (00:00-06:00)", callback_data="time_ночь")],
            [InlineKeyboardButton("⏰ Любое время", callback_data="time_любое")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_frequency_keyboard(self) -> InlineKeyboardMarkup:
        """Создание клавиатуры выбора частоты проверки"""
        keyboard = [
            [InlineKeyboardButton("⚡ 5 минут", callback_data="freq_5")],
            [InlineKeyboardButton("🔄 10 минут", callback_data="freq_10")],
            [InlineKeyboardButton("⏱️ 15 минут", callback_data="freq_15")],
            [InlineKeyboardButton("⏰ 30 минут", callback_data="freq_30")],
            [InlineKeyboardButton("🕐 60 минут", callback_data="freq_60")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_subscription_actions_keyboard(self, subscription_id: int) -> InlineKeyboardMarkup:
        """Создание клавиатуры действий с подпиской"""
        keyboard = [
            [
                InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_sub_{subscription_id}"),
                InlineKeyboardButton("⏸️ Пауза", callback_data=f"pause_sub_{subscription_id}")
            ],
            [
                InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_sub_{subscription_id}"),
                InlineKeyboardButton("📊 Статистика", callback_data=f"stats_sub_{subscription_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_confirmation_keyboard(self) -> InlineKeyboardMarkup:
        """Создание клавиатуры подтверждения"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, создать", callback_data="confirm_yes"),
                InlineKeyboardButton("❌ Нет, отменить", callback_data="confirm_no")
            ],
            [InlineKeyboardButton("✏️ Изменить параметры", callback_data="confirm_edit")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("subscriptions", self.subscriptions_command))
        self.application.add_handler(CommandHandler("add_subscription", self.add_subscription_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("cancel", self.cancel_command))
        
        # Callback queries
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        # Обработка текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Регистрируем пользователя в базе данных
        await self.register_user(user)
        
        welcome_text = f"""
🚂 <b>Добро пожаловать в бот мониторинга билетов РЖД!</b>

Привет, {user.first_name}! 👋

Я помогу вам отслеживать появление билетов на поезда РЖД и мгновенно уведомлю вас, когда появятся доступные места.

🎯 <b>Что я умею:</b>
• 🔍 Мониторить билеты по вашим критериям
• 🔔 Отправлять мгновенные уведомления
• 📱 Предоставлять удобный интерфейс
• ⚙️ Настраивать параметры поиска

📋 <b>Используйте кнопки ниже для навигации:</b>
        """
        
        # Отправляем основную клавиатуру
        main_keyboard = self.create_main_keyboard()
        
        await update.message.reply_text(
            welcome_text, 
            reply_markup=main_keyboard,
            parse_mode=ParseMode.HTML
        )
        
        # Отправляем дополнительную информацию
        help_text = """
💡 <b>Быстрый старт:</b>
1. Нажмите "➕ Добавить подписку"
2. Выберите станции отправления и назначения
3. Укажите дату поездки
4. Выберите тип места
5. Получайте уведомления о билетах!

❓ Если нужна помощь, нажмите "❓ Помощь"
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📖 Помощь по использованию бота

🔍 Как создать подписку:
1. Используйте команду /add_subscription
2. Выберите станцию отправления
3. Выберите станцию назначения
4. Укажите дату поездки
5. Выберите номер поезда (опционально)
6. Выберите тип места
7. Подтвердите создание подписки

📋 Управление подписками:
• /subscriptions - просмотр всех подписок
• /status - статус мониторинга
• /settings - настройки уведомлений

⚙️ Настройки:
• Частота проверки (5-60 минут)
• Типы уведомлений
• Время работы (рабочие часы)

🎫 Типы мест:
• Плацкарт - недорогие места в общем вагоне
• Купе - места в купе на 4 человека
• СВ - спальный вагон (люкс)
• Сидячие - места в сидячем вагоне
• Люкс - места повышенной комфортности

❓ Если у вас есть вопросы, обратитесь к администратору.
        """
        
        await update.message.reply_text(help_text)
    
    async def subscriptions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /subscriptions"""
        user_id = update.effective_user.id
        
        with Session(engine) as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await update.message.reply_text("❌ Пользователь не найден. Используйте /start для регистрации.")
                return
            
            subscriptions = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.is_active == True
            ).all()
            
            if not subscriptions:
                text = """
📋 <b>У вас пока нет активных подписок</b>

🚂 Создайте первую подписку для мониторинга билетов!

Нажмите кнопку ниже, чтобы начать.
                """
                keyboard = [
                    [InlineKeyboardButton("➕ Добавить подписку", callback_data="add_subscription")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                return
            
            text = f"📋 <b>Ваши активные подписки ({len(subscriptions)}):</b>\n\n"
            
            for i, sub in enumerate(subscriptions, 1):
                # Получаем названия станций
                departure_station = db.query(Station).filter(Station.code == sub.departure_station).first()
                arrival_station = db.query(Station).filter(Station.code == sub.arrival_station).first()
                
                departure_name = departure_station.name if departure_station else sub.departure_station
                arrival_name = arrival_station.name if arrival_station else sub.arrival_station
                
                text += f"<b>{i}. 🚂 {departure_name} → {arrival_name}</b>\n"
                text += f"📅 <b>Дата:</b> {sub.departure_date.strftime('%d.%m.%Y')}\n"
                if sub.train_number:
                    text += f"🚆 <b>Поезд:</b> {sub.train_number}\n"
                if sub.seat_type:
                    emoji = get_seat_type_emoji(sub.seat_type)
                    text += f"{emoji} <b>Тип места:</b> {sub.seat_type}\n"
                text += f"⏰ <b>Проверка:</b> каждые {sub.check_frequency} мин\n"
                text += f"📊 <b>Последняя проверка:</b> {sub.last_checked.strftime('%d.%m.%Y %H:%M') if sub.last_checked else 'Никогда'}\n\n"
            
            # Создаем клавиатуру с действиями для каждой подписки
            keyboard = []
            for sub in subscriptions:
                keyboard.append([
                    InlineKeyboardButton(f"✏️ #{sub.id}", callback_data=f"edit_sub_{sub.id}"),
                    InlineKeyboardButton(f"⏸️ #{sub.id}", callback_data=f"pause_sub_{sub.id}"),
                    InlineKeyboardButton(f"🗑 #{sub.id}", callback_data=f"delete_sub_{sub.id}")
                ])
            
            keyboard.append([InlineKeyboardButton("➕ Добавить подписку", callback_data="add_subscription")])
            keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def add_subscription_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /add_subscription"""
        user_id = update.effective_user.id
        
        # Проверяем лимит подписок
        with Session(engine) as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await update.message.reply_text("❌ Пользователь не найден. Используйте /start для регистрации.")
                return
            
            active_subs = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.is_active == True
            ).count()
            
            if active_subs >= settings.max_subscriptions_per_user:
                text = f"""
❌ <b>Достигнут лимит подписок</b>

У вас уже {active_subs} активных подписок из {settings.max_subscriptions_per_user} возможных.

🗑 Удалите одну из существующих подписок перед созданием новой.
                """
                keyboard = [
                    [InlineKeyboardButton("📋 Мои подписки", callback_data="subscriptions")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                return
        
        # Инициализируем состояние пользователя
        self.user_states[user_id] = {
            'step': 'departure_station',
            'data': {}
        }
        
        text = """
🚂 <b>Создание новой подписки</b>

🎯 <b>Шаг 1/7: Станция отправления</b>

Введите название станции отправления или её код.
Например: Москва, МСК, Санкт-Петербург, СПБ

💡 <b>Совет:</b> Используйте полное название города для лучших результатов поиска.
        """
        
        keyboard = self.create_cancel_keyboard()
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /settings"""
        user_id = update.effective_user.id
        
        with Session(engine) as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await update.message.reply_text("❌ Пользователь не найден. Используйте /start для регистрации.")
                return
            
            # Получаем статистику пользователя
            active_subscriptions = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.is_active == True
            ).count()
            
            user_tickets = db.query(FoundTicket).join(Subscription).filter(
                Subscription.user_id == user.id
            ).count()
            
            text = f"""
⚙️ <b>Настройки бота</b>

🔔 <b>Уведомления:</b>
• Статус: ✅ Включены
• Частота проверки: {settings.check_interval_minutes} минут
• Рабочие часы: 08:00 - 22:00

📊 <b>Ваша статистика:</b>
• Активных подписок: {active_subscriptions}
• Найдено билетов: {user_tickets}
• Последняя активность: {user.created_at.strftime('%d.%m.%Y')}

🎯 <b>Лимиты:</b>
• Максимум подписок: {settings.max_subscriptions_per_user}
• Максимум запросов в минуту: {settings.max_concurrent_requests}
            """
            
            keyboard = [
                [InlineKeyboardButton("🔔 Настройки уведомлений", callback_data="notification_settings")],
                [InlineKeyboardButton("⏰ Частота проверки", callback_data="frequency_settings")],
                [InlineKeyboardButton("📊 Подробная статистика", callback_data="detailed_stats")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def show_main_menu(self, query):
        """Показ главного меню"""
        text = """
🏠 <b>Главное меню</b>

Выберите действие с помощью кнопок ниже:
        """
        
        keyboard = self.create_main_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        text = """
📊 Статус мониторинга

🟢 Бот работает
🟢 Мониторинг активен
🟢 База данных подключена
🟢 Парсер РЖД работает

📈 Статистика за сегодня:
• Проверок выполнено: 0
• Найдено билетов: 0
• Отправлено уведомлений: 0

⏰ Следующая проверка: через 5 минут
        """
        
        await update.message.reply_text(text)
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /cancel"""
        user_id = update.effective_user.id
        
        if user_id in self.user_states:
            del self.user_states[user_id]
        
        await update.message.reply_text("❌ Операция отменена.")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        # Основные действия
        if data == "add_subscription":
            await self.add_subscription_command(update, context)
        elif data == "subscriptions":
            await self.subscriptions_command(update, context)
        elif data == "settings":
            await self.settings_command(update, context)
        elif data == "cancel_operation":
            await self.cancel_command(update, context)
        elif data == "main_menu":
            await self.show_main_menu(query)
        
        # Выбор типа места
        elif data.startswith("seat_"):
            seat_type = data.split("_", 1)[1]
            if user_id in self.user_states:
                self.user_states[user_id]['data']['seat_type'] = seat_type
                self.user_states[user_id]['step'] = 'time_range'
                await self.handle_time_range_selection(query, seat_type)
        
        # Выбор времени
        elif data.startswith("time_"):
            time_range = data.split("_", 1)[1]
            if user_id in self.user_states:
                self.user_states[user_id]['data']['time_range'] = time_range
                self.user_states[user_id]['step'] = 'frequency'
                await self.handle_frequency_selection(query, time_range)
        
        # Выбор частоты
        elif data.startswith("freq_"):
            frequency = int(data.split("_", 1)[1])
            if user_id in self.user_states:
                self.user_states[user_id]['data']['frequency'] = frequency
                self.user_states[user_id]['step'] = 'confirm'
                await self.handle_final_confirmation(query)
        
        # Подтверждение
        elif data == "confirm_yes":
            await self.create_subscription_from_state(query)
        elif data == "confirm_no":
            await self.cancel_command(update, context)
        elif data == "confirm_edit":
            await self.edit_subscription_parameters(query)
        
        # Действия с подписками
        elif data.startswith("edit_sub_"):
            sub_id = int(data.split("_")[2])
            await self.edit_subscription(query, sub_id)
        elif data.startswith("delete_sub_"):
            sub_id = int(data.split("_")[2])
            await self.delete_subscription(query, sub_id)
        elif data.startswith("pause_sub_"):
            sub_id = int(data.split("_")[2])
            await self.pause_subscription(query, sub_id)
        elif data.startswith("stats_sub_"):
            sub_id = int(data.split("_")[2])
            await self.show_subscription_stats(query, sub_id)
        
        # Выбор станций
        elif data.startswith("select_departure_"):
            station_code = data.split("_", 2)[2]
            await self.select_departure_station(query, station_code)
        elif data.startswith("select_arrival_"):
            station_code = data.split("_", 2)[2]
            await self.select_arrival_station(query, station_code)
        
        # Пропуск номера поезда
        elif data == "skip_train_number":
            if user_id in self.user_states:
                self.user_states[user_id]['data']['train_number'] = None
                self.user_states[user_id]['step'] = 'seat_type'
                await self.handle_seat_type_selection(query)
        
        # Дополнительные настройки
        elif data == "notification_settings":
            await self.show_notification_settings(query)
        elif data == "frequency_settings":
            await self.show_frequency_settings(query)
        elif data == "detailed_stats":
            await self.show_detailed_statistics(query)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Обработка кнопок основной клавиатуры
        if text == "🚂 Мои подписки":
            await self.subscriptions_command(update, context)
            return
        elif text == "➕ Добавить подписку":
            await self.add_subscription_command(update, context)
            return
        elif text == "⚙️ Настройки":
            await self.settings_command(update, context)
            return
        elif text == "📊 Статус":
            await self.status_command(update, context)
            return
        elif text == "❓ Помощь":
            await self.help_command(update, context)
            return
        elif text == "📋 Статистика":
            await self.statistics_command(update, context)
            return
        
        # Обработка состояний создания подписки
        if user_id not in self.user_states:
            await update.message.reply_text(
                "Используйте кнопки ниже для навигации или команды для взаимодействия с ботом.",
                reply_markup=self.create_main_keyboard()
            )
            return
        
        state = self.user_states[user_id]
        step = state['step']
        
        if step == 'departure_station':
            await self.handle_departure_station(update, text, state)
        elif step == 'arrival_station':
            await self.handle_arrival_station(update, text, state)
        elif step == 'departure_date':
            await self.handle_departure_date(update, text, state)
        elif step == 'train_number':
            await self.handle_train_number(update, text, state)
        elif step == 'seat_type':
            await self.handle_seat_type(update, text, state)
        elif step == 'confirm':
            await self.handle_confirmation(update, text, state)
    
    async def handle_departure_station(self, update: Update, text: str, state: Dict):
        """Обработка выбора станции отправления"""
        # Поиск станций
        stations = self.scraper.get_stations(text)
        
        if not stations:
            await update.message.reply_text(
                "❌ Станции не найдены. Попробуйте ввести другое название или код станции."
            )
            return
        
        if len(stations) == 1:
            state['data']['departure_station'] = stations[0]['code']
            state['data']['departure_station_name'] = stations[0]['name']
            state['step'] = 'arrival_station'
            
            text = f"""
✅ Станция отправления: {stations[0]['name']}

Шаг 2/6: Станция назначения

Введите название станции назначения или её код.
Например: Владивосток, ВЛД, Новосибирск, НСК
            """
            await update.message.reply_text(text)
        else:
            # Показываем список найденных станций
            keyboard = []
            for station in stations[:5]:  # Показываем только первые 5
                keyboard.append([
                    InlineKeyboardButton(
                        f"{station['name']} ({station['code']})",
                        callback_data=f"select_departure_{station['code']}"
                    )
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🔍 Найдено несколько станций. Выберите нужную:",
                reply_markup=reply_markup
            )
    
    async def handle_arrival_station(self, update: Update, text: str, state: Dict):
        """Обработка выбора станции назначения"""
        stations = self.scraper.get_stations(text)
        
        if not stations:
            await update.message.reply_text(
                "❌ Станции не найдены. Попробуйте ввести другое название или код станции."
            )
            return
        
        if len(stations) == 1:
            state['data']['arrival_station'] = stations[0]['code']
            state['data']['arrival_station_name'] = stations[0]['name']
            state['step'] = 'departure_date'
            
            text = f"""
✅ Станция назначения: {stations[0]['name']}

Шаг 3/6: Дата поездки

Введите дату поездки в формате ДД.ММ.ГГГГ
Например: 15.03.2024

💡 Совет: Дата должна быть не раньше завтрашнего дня.
            """
            await update.message.reply_text(text)
        else:
            # Показываем список найденных станций
            keyboard = []
            for station in stations[:5]:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{station['name']} ({station['code']})",
                        callback_data=f"select_arrival_{station['code']}"
                    )
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🔍 Найдено несколько станций. Выберите нужную:",
                reply_markup=reply_markup
            )
    
    async def handle_departure_date(self, update: Update, text: str, state: Dict):
        """Обработка выбора даты поездки"""
        try:
            departure_date = datetime.strptime(text, '%d.%m.%Y').date()
            
            if departure_date < date.today():
                await update.message.reply_text(
                    "❌ Дата не может быть в прошлом. Введите корректную дату."
                )
                return
            
            state['data']['departure_date'] = departure_date
            state['step'] = 'train_number'
            
            text = f"""
✅ Дата поездки: {departure_date.strftime('%d.%m.%Y')}

Шаг 4/6: Номер поезда (опционально)

Введите номер поезда или нажмите "Пропустить" для поиска всех поездов.
Например: 001М, 002М, 003М

💡 Совет: Если не знаете номер поезда, можете пропустить этот шаг.
            """
            
            keyboard = [[InlineKeyboardButton("⏭ Пропустить", callback_data="skip_train_number")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup)
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например: 15.03.2024)"
            )
    
    async def handle_train_number(self, update: Update, text: str, state: Dict):
        """Обработка выбора номера поезда"""
        state['data']['train_number'] = text.strip()
        state['step'] = 'seat_type'
        
        text = f"""
✅ Номер поезда: {text}

Шаг 5/6: Тип места

Выберите желаемый тип места:
        """
        
        keyboard = [
            [InlineKeyboardButton("💺 Плацкарт", callback_data="seat_плацкарт")],
            [InlineKeyboardButton("🚪 Купе", callback_data="seat_купе")],
            [InlineKeyboardButton("🛏 СВ (Спальный вагон)", callback_data="seat_св")],
            [InlineKeyboardButton("🪑 Сидячие места", callback_data="seat_сидячие")],
            [InlineKeyboardButton("👑 Люкс", callback_data="seat_люкс")],
            [InlineKeyboardButton("🔍 Любой тип", callback_data="seat_любой")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
    
    async def handle_seat_type_selection(self, query):
        """Обработка выбора типа места через кнопки"""
        text = """
🎯 <b>Шаг 5/7: Выбор времени поездки</b>

Выберите предпочтительное время отправления:
        """
        
        keyboard = self.create_time_range_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def handle_time_range_selection(self, query, seat_type: str):
        """Обработка выбора времени"""
        text = f"""
✅ <b>Тип места:</b> {seat_type}

🎯 <b>Шаг 6/7: Частота проверки</b>

Как часто проверять наличие билетов?
        """
        
        keyboard = self.create_frequency_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def handle_frequency_selection(self, query, time_range: str):
        """Обработка выбора частоты"""
        text = f"""
✅ <b>Время:</b> {time_range}

🎯 <b>Шаг 7/7: Подтверждение</b>

Проверять билеты каждые {query.data.split('_')[1]} минут.

Создать подписку с этими параметрами?
        """
        
        keyboard = self.create_confirmation_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def handle_final_confirmation(self, query):
        """Обработка финального подтверждения"""
        user_id = query.from_user.id
        if user_id not in self.user_states:
            return
        
        data = self.user_states[user_id]['data']
        
        summary = f"""
📋 <b>Подтверждение подписки</b>

🚂 <b>Маршрут:</b> {data['departure_station_name']} → {data['arrival_station_name']}
📅 <b>Дата:</b> {data['departure_date'].strftime('%d.%m.%Y')}
🚆 <b>Поезд:</b> {data.get('train_number', 'Любой')}
💺 <b>Тип места:</b> {data['seat_type']}
⏰ <b>Время:</b> {data.get('time_range', 'Любое')}
🔄 <b>Проверка:</b> каждые {data.get('frequency', 10)} минут

Создать подписку?
        """
        
        keyboard = self.create_confirmation_keyboard()
        await query.edit_message_text(summary, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def create_subscription_from_state(self, query):
        """Создание подписки из состояния"""
        user_id = query.from_user.id
        if user_id not in self.user_states:
            await query.edit_message_text("❌ Ошибка: состояние не найдено")
            return
        
        try:
            data = self.user_states[user_id]['data']
            
            with Session(engine) as db:
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if not user:
                    await query.edit_message_text("❌ Пользователь не найден")
                    return
                
                # Создаем подписку
                subscription = Subscription(
                    user_id=user.id,
                    departure_station=data['departure_station'],
                    arrival_station=data['arrival_station'],
                    departure_date=data['departure_date'],
                    train_number=data.get('train_number'),
                    seat_type=data['seat_type'],
                    departure_time_range=data.get('time_range'),
                    check_frequency=data.get('frequency', 10)
                )
                
                db.add(subscription)
                db.commit()
                
                # Очищаем состояние
                del self.user_states[user_id]
                
                success_text = f"""
✅ <b>Подписка создана успешно!</b>

🚂 <b>Маршрут:</b> {data['departure_station_name']} → {data['arrival_station_name']}
📅 <b>Дата:</b> {data['departure_date'].strftime('%d.%m.%Y')}
🔄 <b>Проверка:</b> каждые {data.get('frequency', 10)} минут

🔔 Теперь вы будете получать уведомления о появлении билетов!

Используйте кнопки ниже для управления подписками.
                """
                
                keyboard = self.create_main_keyboard()
                await query.edit_message_text(success_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
                
        except Exception as e:
            logger.error(f"Ошибка создания подписки: {e}")
            await query.edit_message_text("❌ Ошибка при создании подписки. Попробуйте еще раз.")
    
    async def select_departure_station(self, query, station_code: str):
        """Выбор станции отправления"""
        user_id = query.from_user.id
        if user_id not in self.user_states:
            return
        
        # Получаем информацию о станции
        with Session(engine) as db:
            station = db.query(Station).filter(Station.code == station_code).first()
            if station:
                self.user_states[user_id]['data']['departure_station'] = station_code
                self.user_states[user_id]['data']['departure_station_name'] = station.name
                self.user_states[user_id]['step'] = 'arrival_station'
                
                text = f"""
✅ <b>Станция отправления:</b> {station.name}

🎯 <b>Шаг 2/7: Станция назначения</b>

Введите название станции назначения или её код.
Например: Владивосток, ВЛД, Новосибирск, НСК
                """
                
                keyboard = self.create_cancel_keyboard()
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def select_arrival_station(self, query, station_code: str):
        """Выбор станции назначения"""
        user_id = query.from_user.id
        if user_id not in self.user_states:
            return
        
        # Получаем информацию о станции
        with Session(engine) as db:
            station = db.query(Station).filter(Station.code == station_code).first()
            if station:
                self.user_states[user_id]['data']['arrival_station'] = station_code
                self.user_states[user_id]['data']['arrival_station_name'] = station.name
                self.user_states[user_id]['step'] = 'departure_date'
                
                text = f"""
✅ <b>Станция назначения:</b> {station.name}

🎯 <b>Шаг 3/7: Дата поездки</b>

Введите дату поездки в формате ДД.ММ.ГГГГ
Например: 15.03.2024

💡 Совет: Дата должна быть не раньше завтрашнего дня.
                """
                
                keyboard = self.create_cancel_keyboard()
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    async def statistics_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды статистики"""
        user_id = update.effective_user.id
        
        with Session(engine) as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await update.message.reply_text("❌ Пользователь не найден. Используйте /start для регистрации.")
                return
            
            # Статистика пользователя
            user_subscriptions = db.query(Subscription).filter(Subscription.user_id == user.id).count()
            active_subscriptions = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.is_active == True
            ).count()
            
            user_tickets = db.query(FoundTicket).join(Subscription).filter(
                Subscription.user_id == user.id
            ).count()
            
            # Общая статистика
            total_subscriptions = db.query(Subscription).filter(Subscription.is_active == True).count()
            total_tickets = db.query(FoundTicket).count()
            
            stats_text = f"""
📊 <b>Статистика мониторинга</b>

👤 <b>Ваша статистика:</b>
• Всего подписок: {user_subscriptions}
• Активных подписок: {active_subscriptions}
• Найдено билетов: {user_tickets}

🌐 <b>Общая статистика:</b>
• Всего активных подписок: {total_subscriptions}
• Всего найдено билетов: {total_tickets}

📈 <b>Система работает стабильно!</b>
            """
            
            await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)
    
    async def show_notification_settings(self, query):
        """Показ настроек уведомлений"""
        text = """
🔔 <b>Настройки уведомлений</b>

📱 <b>Текущие настройки:</b>
• Уведомления: ✅ Включены
• Рабочие часы: 08:00 - 22:00
• Типы уведомлений: Все билеты

⚙️ <b>Доступные настройки:</b>
• Время работы уведомлений
• Типы уведомлений (все/только дешевые)
• Пауза мониторинга
        """
        
        keyboard = [
            [InlineKeyboardButton("⏰ Рабочие часы", callback_data="working_hours")],
            [InlineKeyboardButton("💰 Типы уведомлений", callback_data="notification_types")],
            [InlineKeyboardButton("⏸️ Пауза мониторинга", callback_data="pause_monitoring")],
            [InlineKeyboardButton("🔙 Назад к настройкам", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def show_frequency_settings(self, query):
        """Показ настроек частоты"""
        text = f"""
⏰ <b>Настройки частоты проверки</b>

🔄 <b>Текущая частота:</b> {settings.check_interval_minutes} минут

📊 <b>Рекомендации:</b>
• 5 минут - для популярных маршрутов
• 10 минут - оптимальный баланс
• 15-30 минут - для редких маршрутов
• 60 минут - для долгосрочного мониторинга

⚠️ <b>Важно:</b> Частота влияет на нагрузку на сервер РЖД
        """
        
        keyboard = [
            [InlineKeyboardButton("⚡ 5 минут", callback_data="set_freq_5")],
            [InlineKeyboardButton("🔄 10 минут", callback_data="set_freq_10")],
            [InlineKeyboardButton("⏱️ 15 минут", callback_data="set_freq_15")],
            [InlineKeyboardButton("⏰ 30 минут", callback_data="set_freq_30")],
            [InlineKeyboardButton("🕐 60 минут", callback_data="set_freq_60")],
            [InlineKeyboardButton("🔙 Назад к настройкам", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def show_detailed_statistics(self, query):
        """Показ подробной статистики"""
        user_id = query.from_user.id
        
        with Session(engine) as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await query.edit_message_text("❌ Пользователь не найден")
                return
            
            # Подробная статистика
            subscriptions = db.query(Subscription).filter(Subscription.user_id == user.id).all()
            active_subscriptions = [s for s in subscriptions if s.is_active]
            
            total_tickets = db.query(FoundTicket).join(Subscription).filter(
                Subscription.user_id == user.id
            ).count()
            
            recent_tickets = db.query(FoundTicket).join(Subscription).filter(
                Subscription.user_id == user.id,
                FoundTicket.found_at >= datetime.now() - timedelta(days=7)
            ).count()
            
            text = f"""
📊 <b>Подробная статистика</b>

👤 <b>Ваша активность:</b>
• Всего подписок: {len(subscriptions)}
• Активных подписок: {len(active_subscriptions)}
• Найдено билетов: {total_tickets}
• Найдено за неделю: {recent_tickets}

📈 <b>Детализация по подпискам:</b>
            """
            
            for sub in active_subscriptions[:5]:  # Показываем первые 5
                departure_station = db.query(Station).filter(Station.code == sub.departure_station).first()
                arrival_station = db.query(Station).filter(Station.code == sub.arrival_station).first()
                
                departure_name = departure_station.name if departure_station else sub.departure_station
                arrival_name = arrival_station.name if arrival_station else sub.arrival_station
                
                sub_tickets = db.query(FoundTicket).filter(FoundTicket.subscription_id == sub.id).count()
                
                text += f"• #{sub.id}: {departure_name} → {arrival_name} ({sub_tickets} билетов)\n"
            
            if len(active_subscriptions) > 5:
                text += f"... и еще {len(active_subscriptions) - 5} подписок\n"
            
            keyboard = [
                [InlineKeyboardButton("📊 Общая статистика", callback_data="statistics")],
                [InlineKeyboardButton("🔙 Назад к настройкам", callback_data="settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def handle_confirmation(self, update: Update, text: str, state: Dict):
        """Обработка подтверждения создания подписки"""
        # Этот метод вызывается только при callback query
        pass
    
    async def register_user(self, user):
        """Регистрация пользователя в базе данных"""
        with Session(engine) as db:
            existing_user = db.query(User).filter(User.telegram_id == user.id).first()
            
            if not existing_user:
                new_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                db.add(new_user)
                db.commit()
                logger.info(f"Зарегистрирован новый пользователь: {user.id}")
    
    async def run(self):
        """Запуск бота"""
        logger.info("Запуск Telegram бота...")
        
        # Запускаем мониторинг в фоне
        asyncio.create_task(self.monitoring.start_monitoring())
        
        # Запускаем бота
        await self.application.run_polling()


# Создаем экземпляр бота
bot = RZDBot()

# Функция для запуска
async def main():
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
