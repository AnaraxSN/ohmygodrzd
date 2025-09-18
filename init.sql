-- Инициализация базы данных для RZD Bot

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON subscriptions(is_active);
CREATE INDEX IF NOT EXISTS idx_subscriptions_last_checked ON subscriptions(last_checked);
CREATE INDEX IF NOT EXISTS idx_found_tickets_subscription_id ON found_tickets(subscription_id);
CREATE INDEX IF NOT EXISTS idx_found_tickets_found_at ON found_tickets(found_at);

-- Вставка популярных станций РЖД
INSERT INTO stations (code, name, region) VALUES
('МСК', 'Москва', 'Московская область'),
('СПБ', 'Санкт-Петербург', 'Ленинградская область'),
('НСК', 'Новосибирск', 'Новосибирская область'),
('ЕКБ', 'Екатеринбург', 'Свердловская область'),
('КЗН', 'Казань', 'Республика Татарстан'),
('ННГ', 'Нижний Новгород', 'Нижегородская область'),
('ЧЛБ', 'Челябинск', 'Челябинская область'),
('СМР', 'Самара', 'Самарская область'),
('ОМС', 'Омск', 'Омская область'),
('РНД', 'Ростов-на-Дону', 'Ростовская область'),
('УФА', 'Уфа', 'Республика Башкортостан'),
('КРС', 'Красноярск', 'Красноярский край'),
('ВРН', 'Воронеж', 'Воронежская область'),
('ПРМ', 'Пермь', 'Пермский край'),
('ВЛГ', 'Волгоград', 'Волгоградская область'),
('ВЛД', 'Владивосток', 'Приморский край')
ON CONFLICT (code) DO NOTHING;

