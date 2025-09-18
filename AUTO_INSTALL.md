# 🚀 Автоматическая установка RZD Bot

Этот набор скриптов позволяет полностью автоматизировать установку и настройку RZD Bot на сервере Ubuntu. Пользователю нужно только ввести токен бота и запустить Docker.

## 📋 Доступные скрипты

### 1. `install.sh` - Полная автоматическая установка
**Полностью автоматизированная установка всех компонентов системы.**

```bash
# Скачайте и запустите скрипт
wget https://raw.githubusercontent.com/yourusername/rzd-bot/main/install.sh
chmod +x install.sh
./install.sh

# Или запустите от имени root
sudo ./install.sh
```

**Что делает скрипт:**
- ✅ Обновляет систему Ubuntu
- ✅ Устанавливает Python 3.11, PostgreSQL, Redis, Docker
- ✅ Создает пользователя `rzdbot`
- ✅ Клонирует проект из GitHub
- ✅ Настраивает виртуальное окружение
- ✅ Запрашивает токен бота у пользователя
- ✅ Создает конфигурацию `.env`
- ✅ Настраивает базу данных
- ✅ Создает systemd сервисы
- ✅ Настраивает Nginx
- ✅ Настраивает файрвол
- ✅ Создает скрипты управления
- ✅ Запускает все сервисы

**Требования:**
- Ubuntu 20.04+ (проверяется автоматически)
- Интернет соединение
- Токен бота от @BotFather

### 2. `quick_start.sh` - Быстрый запуск с Docker
**Запускает бота только с Docker, без systemd сервисов.**

```bash
# Убедитесь, что у вас есть файл .env с токеном
chmod +x quick_start.sh
./quick_start.sh
```

**Что делает скрипт:**
- ✅ Проверяет наличие Docker
- ✅ Проверяет файл `.env` с токеном
- ✅ Останавливает существующие контейнеры
- ✅ Запускает Docker Compose
- ✅ Проверяет статус контейнеров

**Требования:**
- Docker и Docker Compose установлены
- Файл `.env` с токеном бота

### 3. `create_env.sh` - Создание конфигурации
**Простой скрипт для создания файла `.env` с токеном бота.**

```bash
chmod +x create_env.sh
./create_env.sh
```

**Что делает скрипт:**
- ✅ Запрашивает токен бота
- ✅ Опционально запрашивает домен для веб-хука
- ✅ Создает файл `.env` с правильными настройками
- ✅ Показывает следующие шаги

### 4. `setup_domain.sh` - Настройка домена и SSL
**Настраивает домен и SSL сертификат для продакшена.**

```bash
sudo chmod +x setup_domain.sh
sudo ./setup_domain.sh
```

**Что делает скрипт:**
- ✅ Проверяет DNS записи домена
- ✅ Обновляет конфигурацию Nginx
- ✅ Получает SSL сертификат от Let's Encrypt
- ✅ Настраивает автообновление сертификата
- ✅ Устанавливает Telegram веб-хук

**Требования:**
- Права root (sudo)
- Домен, указывающий на сервер
- Открытые порты 80 и 443

## 🎯 Сценарии использования

### Сценарий 1: Полная установка с нуля
```bash
# 1. Скачиваем и запускаем полную установку
wget https://raw.githubusercontent.com/yourusername/rzd-bot/main/install.sh
chmod +x install.sh

# Запуск от обычного пользователя (будет запрашивать sudo)
./install.sh

# ИЛИ запуск от root (без запроса sudo)
sudo ./install.sh

# 2. Вводим токен бота когда запросит
# 3. Ждем завершения установки
# 4. Бот автоматически запускается
```

### Сценарий 2: Быстрый запуск с Docker
```bash
# 1. Создаем конфигурацию
./create_env.sh

# 2. Запускаем с Docker
./quick_start.sh

# 3. Бот работает в контейнерах
```

### Сценарий 3: Настройка для продакшена
```bash
# 1. Полная установка (от root или обычного пользователя)
sudo ./install.sh
# или
./install.sh

# 2. Настройка домена и SSL (требует root)
sudo ./setup_domain.sh

# 3. Бот работает с HTTPS и веб-хуками
```

## 📱 Получение токена бота

1. **Откройте Telegram** и найдите @BotFather
2. **Отправьте команду** `/newbot`
3. **Введите имя бота** (например: "My RZD Bot")
4. **Введите username бота** (например: "my_rzd_bot")
5. **Скопируйте токен** (формат: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

## 🔧 Управление после установки

### Systemd сервисы (после install.sh)
```bash
# Статус сервисов (от root или с sudo)
systemctl status rzd-bot rzd-celery-worker rzd-celery-beat
# или
sudo systemctl status rzd-bot rzd-celery-worker rzd-celery-beat

# Логи (от root или с sudo)
journalctl -u rzd-bot -f
journalctl -u rzd-celery-worker -f
journalctl -u rzd-celery-beat -f
# или
sudo journalctl -u rzd-bot -f
sudo journalctl -u rzd-celery-worker -f
sudo journalctl -u rzd-celery-beat -f

# Перезапуск (от root или с sudo)
systemctl restart rzd-bot
# или
sudo systemctl restart rzd-bot
```

### Docker контейнеры (после quick_start.sh)
```bash
# Статус контейнеров
docker-compose ps

# Логи
docker-compose logs -f
docker-compose logs -f bot
docker-compose logs -f celery-worker

# Остановка
docker-compose down

# Перезапуск
docker-compose restart
```

### Скрипты управления (создаются автоматически)
```bash
# Мониторинг системы
/home/rzdbot/monitor.sh

# Обновление бота
/home/rzdbot/update_bot.sh

# Запуск с Docker
/home/rzdbot/start_docker.sh

# Остановка Docker
/home/rzdbot/stop_docker.sh
```

## 🌐 Веб-интерфейс

После установки бот доступен по адресам:

- **HTTP**: `http://your-server-ip`
- **HTTPS** (после setup_domain.sh): `https://your-domain.com`
- **Webhook**: `https://your-domain.com/webhook`
- **Health check**: `https://your-domain.com/health`

## 📊 Мониторинг

### Проверка статуса
```bash
# Общий статус
/home/rzdbot/monitor.sh

# Статус сервисов (от root или с sudo)
systemctl status rzd-bot rzd-celery-worker rzd-celery-beat
# или
sudo systemctl status rzd-bot rzd-celery-worker rzd-celery-beat

# Статус Docker
docker-compose ps
```

### Логи
```bash
# Логи бота
tail -f /home/rzdbot/rzd-bot/logs/bot.log

# Логи systemd (от root или с sudo)
journalctl -u rzd-bot -f
# или
sudo journalctl -u rzd-bot -f

# Логи Docker
docker-compose logs -f bot
```

### База данных
```bash
# Подключение к PostgreSQL
sudo -u postgres psql rzd_bot

# Проверка таблиц
sudo -u postgres psql -c "SELECT count(*) FROM users;" rzd_bot
sudo -u postgres psql -c "SELECT count(*) FROM subscriptions WHERE is_active = true;" rzd_bot
```

## 🔒 Безопасность

### Настройки по умолчанию
- ✅ Файрвол настроен (только SSH, HTTP, HTTPS)
- ✅ Пользователь бота изолирован
- ✅ База данных защищена паролем
- ✅ Логи ротируются
- ✅ SSL сертификат автообновляется

### Дополнительные меры
```bash
# Смена пароля базы данных
sudo -u postgres psql -c "ALTER USER rzd_user PASSWORD 'new_strong_password';"

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Проверка файрвола
sudo ufw status
```

## 🛠️ Устранение неполадок

### Ошибка "ModuleNotFoundError: No module named 'apt_pkg'"
```bash
# Запустите скрипт исправления
./fix_apt_pkg.sh

# Или исправьте вручную
sudo apt install --reinstall python3-apt
sudo apt update
```

### Бот не отвечает
```bash
# Проверяем токен
grep TELEGRAM_BOT_TOKEN /home/rzdbot/rzd-bot/.env

# Проверяем логи
tail -f /home/rzdbot/rzd-bot/logs/bot.log

# Проверяем статус (от root или с sudo)
systemctl status rzd-bot
# или
sudo systemctl status rzd-bot
```

### Ошибки базы данных
```bash
# Проверяем PostgreSQL (от root или с sudo)
systemctl status postgresql
# или
sudo systemctl status postgresql

# Проверяем подключение
sudo -u postgres psql -c "SELECT version();"

# Проверяем права
sudo -u postgres psql -c "SELECT usename FROM pg_user WHERE usename = 'rzd_user';"
```

### Проблемы с Docker
```bash
# Проверяем Docker
docker --version
docker-compose --version

# Проверяем контейнеры
docker-compose ps

# Перезапускаем
docker-compose down
docker-compose up -d --build
```

## 📞 Поддержка

### Полезные команды
```bash
# Полная диагностика
/home/rzdbot/monitor.sh

# Обновление бота
/home/rzdbot/update_bot.sh

# Проверка конфигурации (от root или с sudo)
nginx -t
# или
sudo nginx -t

# Проверка SSL
openssl s_client -connect your-domain.com:443
```

### Логи и файлы
- **Логи бота**: `/home/rzdbot/rzd-bot/logs/bot.log`
- **Конфигурация**: `/home/rzdbot/rzd-bot/.env`
- **Конфигурация Nginx**: `/etc/nginx/sites-available/rzd-bot`
- **Systemd сервисы**: `/etc/systemd/system/rzd-*.service`

---

**🎉 После выполнения любого из сценариев ваш RZD Bot будет полностью настроен и готов к работе!**
