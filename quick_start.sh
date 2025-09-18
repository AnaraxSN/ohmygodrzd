#!/bin/bash

# RZD Bot - Быстрый запуск с Docker
# Этот скрипт запускает бота только с Docker, без systemd сервисов

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

# Проверка Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен!"
        print_warning "Запустите сначала install.sh для полной установки"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose не установлен!"
        print_warning "Запустите сначала install.sh для полной установки"
        exit 1
    fi
    
    print_success "Docker и Docker Compose найдены"
}

# Проверка токена бота
check_bot_token() {
    if [[ ! -f ".env" ]]; then
        print_error "Файл .env не найден!"
        print_warning "Создайте файл .env с токеном бота"
        echo
        echo "Пример содержимого .env:"
        echo "TELEGRAM_BOT_TOKEN=your_bot_token_here"
        echo "DATABASE_URL=postgresql://rzd_user:rzd_secure_password_2024@postgres:5432/rzd_bot"
        echo "REDIS_URL=redis://redis:6379/0"
        exit 1
    fi
    
    if ! grep -q "TELEGRAM_BOT_TOKEN=" .env; then
        print_error "Токен бота не найден в .env!"
        print_warning "Добавьте TELEGRAM_BOT_TOKEN=your_token в файл .env"
        exit 1
    fi
    
    print_success "Токен бота найден в .env"
}

# Остановка существующих контейнеров
stop_containers() {
    print_status "Остановка существующих контейнеров..."
    docker-compose down 2>/dev/null || true
    print_success "Контейнеры остановлены"
}

# Запуск контейнеров
start_containers() {
    print_status "Запуск RZD Bot с Docker..."
    
    # Собираем и запускаем контейнеры
    docker-compose up -d --build
    
    print_success "Контейнеры запущены!"
}

# Проверка статуса
check_status() {
    print_status "Проверка статуса контейнеров..."
    
    sleep 10  # Ждем запуска
    
    if docker-compose ps | grep -q "Up"; then
        print_success "Все контейнеры работают"
        
        echo
        echo "📊 Статус контейнеров:"
        docker-compose ps
        
        echo
        echo "📋 Полезные команды:"
        echo "• Просмотр логов: docker-compose logs -f"
        echo "• Логи бота: docker-compose logs -f bot"
        echo "• Логи worker: docker-compose logs -f celery-worker"
        echo "• Остановка: docker-compose down"
        echo "• Перезапуск: docker-compose restart"
        
    else
        print_error "Некоторые контейнеры не запустились"
        echo
        echo "Проверьте логи:"
        docker-compose logs
    fi
}

# Показ информации
show_info() {
    echo
    print_success "🎉 RZD Bot запущен с Docker!"
    echo
    echo "🌐 Веб-интерфейс:"
    echo "• Локально: http://localhost"
    echo "• Внешний IP: http://$(curl -s ifconfig.me 2>/dev/null || echo 'недоступен')"
    echo
    echo "📱 Telegram бот:"
    echo "• Найдите вашего бота в Telegram"
    echo "• Отправьте команду /start"
    echo
    echo "🔧 Управление:"
    echo "• Остановка: docker-compose down"
    echo "• Перезапуск: docker-compose restart"
    echo "• Логи: docker-compose logs -f"
    echo
    print_warning "⚠️  Для продакшена настройте домен и SSL сертификат"
}

# Основная функция
main() {
    echo "🚂 RZD Bot - Быстрый запуск с Docker"
    echo "====================================="
    echo
    
    check_docker
    check_bot_token
    stop_containers
    start_containers
    check_status
    show_info
}

# Запуск
main "$@"

