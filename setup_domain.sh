#!/bin/bash

# RZD Bot - Настройка домена и SSL
# Этот скрипт настраивает домен и SSL сертификат для продакшена

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

# Проверка прав
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт должен запускаться от имени root"
        print_warning "Используйте: sudo ./setup_domain.sh"
        exit 1
    fi
}

# Получение домена
get_domain() {
    echo
    print_status "Настройка домена и SSL сертификата"
    echo
    echo "Для настройки SSL сертификата нужен домен, указывающий на этот сервер."
    echo "Убедитесь, что:"
    echo "1. У вас есть домен (например: mybot.example.com)"
    echo "2. DNS запись A указывает на IP этого сервера"
    echo "3. Порты 80 и 443 открыты в файрволе"
    echo
    
    read -p "Введите ваш домен (например: mybot.example.com): " DOMAIN
    
    if [[ -z "$DOMAIN" ]]; then
        print_error "Домен не может быть пустым!"
        exit 1
    fi
    
    # Проверяем, что домен указывает на сервер
    print_status "Проверка DNS записи..."
    
    SERVER_IP=$(curl -s ifconfig.me)
    DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)
    
    if [[ "$SERVER_IP" != "$DOMAIN_IP" ]]; then
        print_warning "DNS запись может быть не настроена!"
        echo "IP сервера: $SERVER_IP"
        echo "IP домена: $DOMAIN_IP"
        echo
        read -p "Продолжить настройку? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "DNS запись настроена корректно"
    fi
}

# Обновление конфигурации Nginx
update_nginx_config() {
    print_status "Обновление конфигурации Nginx..."
    
    # Создаем новую конфигурацию с доменом
    cat > /etc/nginx/sites-available/rzd-bot << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /webhook {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /health {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location / {
        return 200 'RZD Bot is running on $DOMAIN!';
        add_header Content-Type text/plain;
    }
}
EOF

    # Проверяем конфигурацию
    nginx -t
    
    # Перезапускаем Nginx
    systemctl restart nginx
    
    print_success "Конфигурация Nginx обновлена"
}

# Получение SSL сертификата
get_ssl_certificate() {
    print_status "Получение SSL сертификата от Let's Encrypt..."
    
    # Устанавливаем Certbot если не установлен
    if ! command -v certbot &> /dev/null; then
        apt update
        apt install -y certbot python3-certbot-nginx
    fi
    
    # Получаем сертификат
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    
    print_success "SSL сертификат получен"
}

# Обновление конфигурации бота
update_bot_config() {
    print_status "Обновление конфигурации бота..."
    
    # Обновляем .env файл
    sed -i "s|TELEGRAM_WEBHOOK_URL=.*|TELEGRAM_WEBHOOK_URL=https://$DOMAIN/webhook|" /home/rzdbot/rzd-bot/.env
    
    print_success "Конфигурация бота обновлена"
}

# Настройка автообновления сертификата
setup_cert_renewal() {
    print_status "Настройка автообновления SSL сертификата..."
    
    # Создаем cron задачу для автообновления
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
    
    print_success "Автообновление SSL сертификата настроено"
}

# Настройка веб-хука
setup_webhook() {
    print_status "Настройка Telegram веб-хука..."
    
    # Получаем токен бота из .env
    BOT_TOKEN=$(grep "TELEGRAM_BOT_TOKEN=" /home/rzdbot/rzd-bot/.env | cut -d'=' -f2)
    
    if [[ -z "$BOT_TOKEN" ]]; then
        print_error "Токен бота не найден в .env файле!"
        return 1
    fi
    
    # Устанавливаем веб-хук
    WEBHOOK_URL="https://$DOMAIN/webhook"
    
    print_status "Устанавливаем веб-хук: $WEBHOOK_URL"
    
    curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
         -H "Content-Type: application/json" \
         -d "{\"url\": \"$WEBHOOK_URL\"}"
    
    print_success "Веб-хук настроен"
}

# Проверка настройки
verify_setup() {
    print_status "Проверка настройки..."
    
    # Проверяем SSL сертификат
    if openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
        print_success "SSL сертификат работает"
    else
        print_warning "SSL сертификат может быть не настроен"
    fi
    
    # Проверяем веб-хук
    BOT_TOKEN=$(grep "TELEGRAM_BOT_TOKEN=" /home/rzdbot/rzd-bot/.env | cut -d'=' -f2)
    if [[ -n "$BOT_TOKEN" ]]; then
        WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo")
        if echo "$WEBHOOK_INFO" | grep -q "$DOMAIN"; then
            print_success "Веб-хук настроен корректно"
        else
            print_warning "Веб-хук может быть не настроен"
        fi
    fi
}

# Показ финальной информации
show_final_info() {
    echo
    print_success "🎉 Домен и SSL настроены успешно!"
    echo
    echo "🌐 Информация о домене:"
    echo "• Домен: $DOMAIN"
    echo "• HTTPS: https://$DOMAIN"
    echo "• Webhook: https://$DOMAIN/webhook"
    echo "• Health check: https://$DOMAIN/health"
    echo
    echo "🔒 SSL сертификат:"
    echo "• Автообновление: настроено"
    echo "• Срок действия: 90 дней"
    echo "• Проверка: openssl s_client -connect $DOMAIN:443"
    echo
    echo "📱 Telegram бот:"
    echo "• Веб-хук настроен автоматически"
    echo "• Найдите бота в Telegram и отправьте /start"
    echo
    echo "🔧 Управление:"
    echo "• Обновление сертификата: certbot renew"
    echo "• Проверка статуса: systemctl status nginx"
    echo "• Логи Nginx: journalctl -u nginx -f"
    echo
    print_warning "⚠️  Не забудьте обновить DNS записи если изменили домен!"
}

# Основная функция
main() {
    echo "🌐 RZD Bot - Настройка домена и SSL"
    echo "===================================="
    echo
    
    check_permissions
    get_domain
    update_nginx_config
    get_ssl_certificate
    update_bot_config
    setup_cert_renewal
    setup_webhook
    verify_setup
    show_final_info
}

# Запуск
main "$@"

