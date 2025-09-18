#!/bin/bash

# RZD Bot - Создание файла конфигурации
# Простой скрипт для создания .env файла с токеном бота

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка существующего .env файла
check_existing_env() {
    if [[ -f ".env" ]]; then
        print_warning "Файл .env уже существует!"
        echo "Текущее содержимое:"
        echo "=================="
        cat .env
        echo "=================="
        echo
        read -p "Перезаписать файл? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Отменено пользователем"
            exit 0
        fi
    fi
}

# Получение токена бота
get_bot_token() {
    echo
    print_status "Настройка конфигурации RZD Bot"
    echo
    echo "Для работы бота нужен токен от @BotFather в Telegram:"
    echo "1. Найдите @BotFather в Telegram"
    echo "2. Отправьте команду /newbot"
    echo "3. Следуйте инструкциям для создания бота"
    echo "4. Скопируйте полученный токен"
    echo
    
    read -p "Введите токен бота: " BOT_TOKEN
    
    if [[ -z "$BOT_TOKEN" ]]; then
        print_error "Токен бота не может быть пустым!"
        exit 1
    fi
    
    # Простая валидация токена
    if [[ ! "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
        print_warning "Токен выглядит некорректно!"
        print_warning "Формат должен быть: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Получение домена (опционально)
get_domain() {
    echo
    read -p "Введите домен для веб-хука (опционально, можно пропустить): " DOMAIN
    
    if [[ -n "$DOMAIN" ]]; then
        WEBHOOK_URL="https://$DOMAIN/webhook"
        print_status "Веб-хук будет настроен на: $WEBHOOK_URL"
    else
        WEBHOOK_URL=""
        print_status "Веб-хук не настроен (будет использоваться polling)"
    fi
}

# Создание .env файла
create_env_file() {
    print_status "Создание файла .env..."
    
    cat > .env << EOF
# Telegram Bot
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_WEBHOOK_URL=$WEBHOOK_URL

# Database
DATABASE_URL=postgresql://rzd_user:rzd_secure_password_2024@localhost:5432/rzd_bot
REDIS_URL=redis://localhost:6379/0

# RZD Settings
RZD_BASE_URL=https://pass.rzd.ru
SCRAPING_DELAY=5
MAX_CONCURRENT_REQUESTS=3

# Monitoring
CHECK_INTERVAL_MINUTES=10
MAX_SUBSCRIPTIONS_PER_USER=5

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
EOF

    print_success "Файл .env создан"
}

# Показ информации
show_info() {
    echo
    print_success "🎉 Конфигурация создана!"
    echo
    echo "📋 Созданный файл .env:"
    echo "========================"
    cat .env
    echo "========================"
    echo
    echo "🚀 Следующие шаги:"
    echo "1. Запустите бота: ./quick_start.sh"
    echo "2. Или используйте Docker: docker-compose up -d"
    echo "3. Найдите бота в Telegram и отправьте /start"
    echo
    if [[ -n "$DOMAIN" ]]; then
        echo "🌐 Для настройки SSL сертификата:"
        echo "sudo ./setup_domain.sh"
    fi
    echo
    print_warning "⚠️  Не делитесь токеном бота с другими!"
}

# Основная функция
main() {
    echo "⚙️ RZD Bot - Создание конфигурации"
    echo "=================================="
    echo
    
    check_existing_env
    get_bot_token
    get_domain
    create_env_file
    show_info
}

# Запуск
main "$@"

