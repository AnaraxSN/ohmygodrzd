# Руководство по развертыванию RZD Bot

## Быстрый старт

### 1. Подготовка окружения

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd rzd

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка конфигурации

```bash
# Скопируйте файл конфигурации
cp env_example.txt .env

# Отредактируйте .env файл
nano .env
```

Обязательно укажите:
- `TELEGRAM_BOT_TOKEN` - токен вашего бота от @BotFather
- `DATABASE_URL` - URL подключения к PostgreSQL
- `REDIS_URL` - URL подключения к Redis

### 3. Настройка базы данных

```bash
# Создайте базу данных PostgreSQL
createdb rzd_bot

# Запустите миграции
python run.py migrate
```

### 4. Запуск с Docker (рекомендуется)

```bash
# Запустите все сервисы
docker-compose up -d

# Проверьте статус
docker-compose ps

# Просмотр логов
docker-compose logs -f bot
```

### 5. Запуск без Docker

```bash
# Терминал 1: Запуск бота
python run.py bot

# Терминал 2: Запуск Celery worker
python run.py worker

# Терминал 3: Запуск Celery beat (планировщик)
python run.py beat
```

## Подробная настройка

### Получение токена бота

1. Найдите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в файл `.env`

### Настройка PostgreSQL

```sql
-- Создание пользователя и базы данных
CREATE USER rzd_user WITH PASSWORD 'rzd_password';
CREATE DATABASE rzd_bot OWNER rzd_user;
GRANT ALL PRIVILEGES ON DATABASE rzd_bot TO rzd_user;
```

### Настройка Redis

```bash
# Установка Redis (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

# Запуск Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Настройка веб-хуков (опционально)

Если вы хотите использовать веб-хуки вместо polling:

```bash
# Установите ngrok для тестирования
npm install -g ngrok

# Запустите туннель
ngrok http 8000

# Установите веб-хук
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-domain.com/webhook"}'
```

## Мониторинг и логирование

### Просмотр логов

```bash
# Docker
docker-compose logs -f bot
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat

# Без Docker
tail -f logs/bot.log
```

### Мониторинг базы данных

```sql
-- Статистика подписок
SELECT 
    COUNT(*) as total_subscriptions,
    COUNT(CASE WHEN is_active THEN 1 END) as active_subscriptions
FROM subscriptions;

-- Статистика найденных билетов
SELECT 
    DATE(found_at) as date,
    COUNT(*) as tickets_found
FROM found_tickets
GROUP BY DATE(found_at)
ORDER BY date DESC;
```

### Мониторинг Redis

```bash
# Подключение к Redis
redis-cli

# Просмотр очереди задач
KEYS celery-task-meta-*
LLEN celery

# Очистка очереди (осторожно!)
FLUSHDB
```

## Обновление и обслуживание

### Обновление кода

```bash
# Остановка сервисов
docker-compose down

# Обновление кода
git pull origin main

# Пересборка и запуск
docker-compose up -d --build
```

### Резервное копирование

```bash
# Создание бэкапа базы данных
pg_dump rzd_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
psql rzd_bot < backup_20240101_120000.sql
```

### Очистка старых данных

```bash
# Запуск задачи очистки
python -c "
from src.tasks import cleanup_old_tickets
cleanup_old_tickets.delay()
"
```

## Устранение неполадок

### Частые проблемы

1. **Бот не отвечает**
   - Проверьте токен бота
   - Убедитесь, что бот запущен
   - Проверьте логи на ошибки

2. **Ошибки подключения к базе данных**
   - Проверьте URL подключения
   - Убедитесь, что PostgreSQL запущен
   - Проверьте права доступа пользователя

3. **Парсинг РЖД не работает**
   - Проверьте интернет-соединение
   - Возможно, изменилась структура сайта РЖД
   - Проверьте логи парсера

4. **Celery задачи не выполняются**
   - Проверьте подключение к Redis
   - Убедитесь, что worker запущен
   - Проверьте очереди задач

### Логи и отладка

```bash
# Включение подробного логирования
export LOG_LEVEL=DEBUG

# Просмотр логов в реальном времени
tail -f logs/bot.log | grep ERROR

# Проверка статуса сервисов
docker-compose ps
systemctl status redis-server
systemctl status postgresql
```

## Безопасность

### Рекомендации

1. **Используйте сильные пароли** для базы данных
2. **Ограничьте доступ** к серверу по SSH
3. **Настройте файрвол** для защиты портов
4. **Регулярно обновляйте** зависимости
5. **Мониторьте логи** на подозрительную активность

### Переменные окружения

```bash
# Никогда не коммитьте .env файл!
echo ".env" >> .gitignore

# Используйте разные токены для тестирования и продакшена
TELEGRAM_BOT_TOKEN_TEST=your_test_token
TELEGRAM_BOT_TOKEN_PROD=your_production_token
```

## Масштабирование

### Горизонтальное масштабирование

```yaml
# docker-compose.override.yml
services:
  celery-worker:
    deploy:
      replicas: 3
  
  bot:
    deploy:
      replicas: 2
```

### Оптимизация производительности

1. **Увеличьте количество worker'ов** Celery
2. **Настройте connection pooling** для базы данных
3. **Используйте Redis Cluster** для высокой доступности
4. **Настройте мониторинг** с помощью Prometheus/Grafana

## Поддержка

При возникновении проблем:

1. Проверьте логи системы
2. Изучите документацию
3. Создайте issue в репозитории
4. Обратитесь к разработчику

---

**Важно**: Этот бот предназначен только для личного использования. Соблюдайте условия использования сайта РЖД и не злоупотребляйте частотой запросов.

