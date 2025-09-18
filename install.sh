#!/bin/bash

# RZD Bot - Автоматический скрипт установки
# Автор: RZD Bot Team
# Версия: 1.0

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
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

# Проверка прав root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Скрипт запущен от имени root"
        print_status "Будет создан пользователь rzdbot для безопасности"
        ROOT_MODE=true
    else
        print_status "Скрипт запущен от обычного пользователя"
        print_status "Будет запрашиваться sudo при необходимости"
        ROOT_MODE=false
    fi
}

# Проверка операционной системы
check_os() {
    if [[ ! -f /etc/os-release ]]; then
        print_error "Не удалось определить операционную систему"
        exit 1
    fi
    
    . /etc/os-release
    
    if [[ "$ID" != "ubuntu" ]]; then
        print_warning "Этот скрипт предназначен для Ubuntu. Текущая ОС: $ID"
        read -p "Продолжить установку? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_success "Обнаружена операционная система: $PRETTY_NAME"
}

# Обновление системы
update_system() {
    print_status "Обновление системы..."
    if [[ "$ROOT_MODE" == "true" ]]; then
        apt update && apt upgrade -y
    else
        sudo apt update && sudo apt upgrade -y
    fi
    print_success "Система обновлена"
}

# Исправление проблем с apt_pkg
fix_apt_pkg() {
    print_status "Проверка и исправление проблем с apt_pkg..."
    
    # Проверяем, есть ли проблемы с apt_pkg
    if python3 -c "import apt_pkg" 2>/dev/null; then
        print_success "apt_pkg работает корректно"
        return 0
    fi
    
    print_warning "Обнаружены проблемы с apt_pkg, исправляем..."
    
    if [[ "$ROOT_MODE" == "true" ]]; then
        # Переустанавливаем python3-apt
        apt install --reinstall -y python3-apt
        
        # Обновляем кэш apt
        apt update
    else
        # Переустанавливаем python3-apt
        sudo apt install --reinstall -y python3-apt
        
        # Обновляем кэш apt
        sudo apt update
    fi
    
    print_success "Проблемы с apt_pkg исправлены"
}

# Установка необходимых пакетов
install_packages() {
    print_status "Установка необходимых пакетов..."
    
    if [[ "$ROOT_MODE" == "true" ]]; then
        apt install -y \
            curl \
            wget \
            git \
            vim \
            htop \
            tree \
            unzip \
            software-properties-common \
            python3-apt \
            build-essential \
            libssl-dev \
            libffi-dev \
            python3-dev \
            libpq-dev \
            pkg-config \
            ufw \
            nginx \
            certbot \
            python3-certbot-nginx
    else
        sudo apt install -y \
            curl \
            wget \
            git \
            vim \
            htop \
            tree \
            unzip \
            software-properties-common \
            python3-apt \
            build-essential \
            libssl-dev \
            libffi-dev \
            python3-dev \
            libpq-dev \
            pkg-config \
            ufw \
            nginx \
            certbot \
            python3-certbot-nginx
    fi
    
    print_success "Пакеты установлены"
}

# Установка Python 3.11
install_python() {
    print_status "Установка Python 3.11..."
    
    # Проверяем, есть ли уже Python 3.11
    if command -v python3.11 &> /dev/null; then
        print_warning "Python 3.11 уже установлен"
        return 0
    fi
    
    # Сначала пытаемся установить из стандартных репозиториев
    print_status "Попытка установки Python 3.11 из стандартных репозиториев..."
    if [[ "$ROOT_MODE" == "true" ]]; then
        apt update
        apt install -y python3.11 python3.11-venv python3.11-dev python3-pip python3-apt
    else
        sudo apt update
        sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip python3-apt
    fi
    
    # Проверяем, установился ли Python 3.11
    if command -v python3.11 &> /dev/null; then
        print_success "Python 3.11 установлен из стандартных репозиториев"
    else
        print_warning "Python 3.11 не найден в стандартных репозиториях, пробуем PPA..."
        
        # Устанавливаем необходимые пакеты для работы с PPA
        if [[ "$ROOT_MODE" == "true" ]]; then
            apt install -y software-properties-common python3-apt
        else
            sudo apt install -y software-properties-common python3-apt
        fi
        
        # Пытаемся добавить PPA
        if [[ "$ROOT_MODE" == "true" ]]; then
            add-apt-repository ppa:deadsnakes/ppa -y 2>/dev/null || {
                print_error "Не удалось добавить PPA deadsnakes"
                print_status "Пробуем установить доступную версию Python..."
                apt install -y python3 python3-venv python3-dev python3-pip
                return 0
            }
            apt update
            apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
        else
            sudo add-apt-repository ppa:deadsnakes/ppa -y 2>/dev/null || {
                print_error "Не удалось добавить PPA deadsnakes"
                print_status "Пробуем установить доступную версию Python..."
                sudo apt install -y python3 python3-venv python3-dev python3-pip
                return 0
            }
            sudo apt update
            sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
        fi
    fi
    
    # Создаем символическую ссылку
    if [[ "$ROOT_MODE" == "true" ]]; then
        ln -sf /usr/bin/python3.11 /usr/bin/python3 2>/dev/null || ln -sf /usr/bin/python3 /usr/bin/python3
    else
        sudo ln -sf /usr/bin/python3.11 /usr/bin/python3 2>/dev/null || sudo ln -sf /usr/bin/python3 /usr/bin/python3
    fi
    
    print_success "Python установлен"
}

# Установка PostgreSQL
install_postgresql() {
    print_status "Установка PostgreSQL..."
    
    if [[ "$ROOT_MODE" == "true" ]]; then
        apt install -y postgresql postgresql-contrib
        
        # Настройка PostgreSQL
        systemctl start postgresql
        systemctl enable postgresql
        
        # Создание пользователя и базы данных
        sudo -u postgres psql -c "CREATE USER rzd_user WITH PASSWORD 'rzd_secure_password_2024';" 2>/dev/null || true
        sudo -u postgres psql -c "CREATE DATABASE rzd_bot OWNER rzd_user;" 2>/dev/null || true
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE rzd_bot TO rzd_user;" 2>/dev/null || true
    else
        sudo apt install -y postgresql postgresql-contrib
        
        # Настройка PostgreSQL
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
        
        # Создание пользователя и базы данных
        sudo -u postgres psql -c "CREATE USER rzd_user WITH PASSWORD 'rzd_secure_password_2024';" 2>/dev/null || true
        sudo -u postgres psql -c "CREATE DATABASE rzd_bot OWNER rzd_user;" 2>/dev/null || true
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE rzd_bot TO rzd_user;" 2>/dev/null || true
    fi
    
    print_success "PostgreSQL установлен и настроен"
}

# Установка Redis
install_redis() {
    print_status "Установка Redis..."
    
    if [[ "$ROOT_MODE" == "true" ]]; then
        apt install -y redis-server
        
        # Настройка Redis
        sed -i 's/supervised no/supervised systemd/' /etc/redis/redis.conf
        sed -i 's/# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
        sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
        
        systemctl restart redis-server
        systemctl enable redis-server
    else
        sudo apt install -y redis-server
        
        # Настройка Redis
        sudo sed -i 's/supervised no/supervised systemd/' /etc/redis/redis.conf
        sudo sed -i 's/# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
        sudo sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
        
        sudo systemctl restart redis-server
        sudo systemctl enable redis-server
    fi
    
    print_success "Redis установлен и настроен"
}

# Установка Docker
install_docker() {
    print_status "Установка Docker..."
    
    if [[ "$ROOT_MODE" == "true" ]]; then
        # Удаляем старые версии Docker
        apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
        
        # Устанавливаем Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        
        # Добавляем пользователя rzdbot в группу docker
        usermod -aG docker rzdbot
        
        # Устанавливаем Docker Compose
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    else
        # Удаляем старые версии Docker
        sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
        
        # Устанавливаем Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm get-docker.sh
        
        # Добавляем пользователя в группу docker
        sudo usermod -aG docker $USER
        
        # Устанавливаем Docker Compose
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    print_success "Docker и Docker Compose установлены"
}

# Создание пользователя для бота
create_bot_user() {
    print_status "Создание пользователя для бота..."
    
    if ! id "rzdbot" &>/dev/null; then
        if [[ "$ROOT_MODE" == "true" ]]; then
            adduser --disabled-password --gecos "" rzdbot
            usermod -aG sudo rzdbot
            usermod -aG docker rzdbot
        else
            sudo adduser --disabled-password --gecos "" rzdbot
            sudo usermod -aG sudo rzdbot
            sudo usermod -aG docker rzdbot
        fi
        print_success "Пользователь rzdbot создан"
    else
        print_warning "Пользователь rzdbot уже существует"
        # Обновляем группы пользователя
        if [[ "$ROOT_MODE" == "true" ]]; then
            usermod -aG sudo rzdbot
            usermod -aG docker rzdbot
        else
            sudo usermod -aG sudo rzdbot
            sudo usermod -aG docker rzdbot
        fi
    fi
}

# Клонирование проекта
clone_project() {
    print_status "Клонирование проекта..."
    
    if [[ -d "/home/rzdbot/rzd-bot" ]]; then
        print_warning "Проект уже существует, обновляем..."
        if [[ "$ROOT_MODE" == "true" ]]; then
            sudo -u rzdbot bash -c "cd /home/rzdbot/rzd-bot && git pull origin main"
        else
            sudo -u rzdbot bash -c "cd /home/rzdbot/rzd-bot && git pull origin main"
        fi
    else
        if [[ "$ROOT_MODE" == "true" ]]; then
            sudo -u rzdbot bash -c "cd /home/rzdbot && git clone https://github.com/yourusername/rzd-bot.git"
        else
            sudo -u rzdbot bash -c "cd /home/rzdbot && git clone https://github.com/yourusername/rzd-bot.git"
        fi
    fi
    
    print_success "Проект клонирован"
}

# Настройка виртуального окружения
setup_venv() {
    print_status "Настройка виртуального окружения..."
    
    if [[ "$ROOT_MODE" == "true" ]]; then
        sudo -u rzdbot bash -c "
            cd /home/rzdbot/rzd-bot
            python3.11 -m venv venv
            source venv/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
        "
    else
        sudo -u rzdbot bash -c "
            cd /home/rzdbot/rzd-bot
            python3.11 -m venv venv
            source venv/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
        "
    fi
    
    print_success "Виртуальное окружение настроено"
}

# Настройка конфигурации
setup_config() {
    print_status "Настройка конфигурации..."
    
    # Запрашиваем токен бота
    echo
    print_warning "Для завершения установки нужен токен Telegram бота"
    echo "Получите токен у @BotFather в Telegram:"
    echo "1. Найдите @BotFather в Telegram"
    echo "2. Отправьте команду /newbot"
    echo "3. Следуйте инструкциям"
    echo "4. Скопируйте полученный токен"
    echo
    
    read -p "Введите токен бота: " BOT_TOKEN
    
    if [[ -z "$BOT_TOKEN" ]]; then
        print_error "Токен бота не может быть пустым!"
        exit 1
    fi
    
    # Создаем файл конфигурации
    if [[ "$ROOT_MODE" == "true" ]]; then
        sudo -u rzdbot bash -c "
            cd /home/rzdbot/rzd-bot
            cat > .env << EOF
# Telegram Bot
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/webhook

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
LOG_FILE=/home/rzdbot/rzd-bot/logs/bot.log
EOF
        "
    else
        sudo -u rzdbot bash -c "
            cd /home/rzdbot/rzd-bot
            cat > .env << EOF
# Telegram Bot
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/webhook

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
LOG_FILE=/home/rzdbot/rzd-bot/logs/bot.log
EOF
        "
    fi
    
    print_success "Конфигурация создана"
}

# Настройка базы данных
setup_database() {
    print_status "Настройка базы данных..."
    
    if [[ "$ROOT_MODE" == "true" ]]; then
        sudo -u rzdbot bash -c "
            cd /home/rzdbot/rzd-bot
            mkdir -p logs
            source venv/bin/activate
            python run.py migrate
        "
    else
        sudo -u rzdbot bash -c "
            cd /home/rzdbot/rzd-bot
            mkdir -p logs
            source venv/bin/activate
            python run.py migrate
        "
    fi
    
    print_success "База данных настроена"
}

# Настройка systemd сервисов
setup_systemd() {
    print_status "Настройка systemd сервисов..."
    
    # Сервис бота
    sudo tee /etc/systemd/system/rzd-bot.service > /dev/null << EOF
[Unit]
Description=RZD Bot Telegram Bot
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=rzdbot
Group=rzdbot
WorkingDirectory=/home/rzdbot/rzd-bot
Environment=PATH=/home/rzdbot/rzd-bot/venv/bin
ExecStart=/home/rzdbot/rzd-bot/venv/bin/python run.py bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Сервис Celery worker
    sudo tee /etc/systemd/system/rzd-celery-worker.service > /dev/null << EOF
[Unit]
Description=RZD Bot Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=rzdbot
Group=rzdbot
WorkingDirectory=/home/rzdbot/rzd-bot
Environment=PATH=/home/rzdbot/rzd-bot/venv/bin
ExecStart=/home/rzdbot/rzd-bot/venv/bin/python run.py worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Сервис Celery beat
    sudo tee /etc/systemd/system/rzd-celery-beat.service > /dev/null << EOF
[Unit]
Description=RZD Bot Celery Beat
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=rzdbot
Group=rzdbot
WorkingDirectory=/home/rzdbot/rzd-bot
Environment=PATH=/home/rzdbot/rzd-bot/venv/bin
ExecStart=/home/rzdbot/rzd-bot/venv/bin/python run.py beat
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Перезагружаем systemd
    if [[ "$ROOT_MODE" == "true" ]]; then
        systemctl daemon-reload
        systemctl enable rzd-bot rzd-celery-worker rzd-celery-beat
    else
        sudo systemctl daemon-reload
        sudo systemctl enable rzd-bot rzd-celery-worker rzd-celery-beat
    fi
    
    print_success "Systemd сервисы настроены"
}

# Настройка Nginx
setup_nginx() {
    print_status "Настройка Nginx..."
    
    # Создаем конфигурацию Nginx
    sudo tee /etc/nginx/sites-available/rzd-bot > /dev/null << EOF
server {
    listen 80;
    server_name _;

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
        return 200 'RZD Bot is running!';
        add_header Content-Type text/plain;
    }
}
EOF

    # Активируем конфигурацию
    sudo ln -sf /etc/nginx/sites-available/rzd-bot /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Проверяем конфигурацию
    if [[ "$ROOT_MODE" == "true" ]]; then
        nginx -t
        
        # Перезапускаем Nginx
        systemctl restart nginx
        systemctl enable nginx
    else
        sudo nginx -t
        
        # Перезапускаем Nginx
        sudo systemctl restart nginx
        sudo systemctl enable nginx
    fi
    
    print_success "Nginx настроен"
}

# Настройка файрвола
setup_firewall() {
    print_status "Настройка файрвола..."
    
    if [[ "$ROOT_MODE" == "true" ]]; then
        ufw --force reset
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw --force enable
    else
        sudo ufw --force reset
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        sudo ufw allow ssh
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw --force enable
    fi
    
    print_success "Файрвол настроен"
}

# Создание скриптов управления
create_management_scripts() {
    print_status "Создание скриптов управления..."
    
    # Скрипт мониторинга
    if [[ "$ROOT_MODE" == "true" ]]; then
        sudo -u rzdbot bash -c "
            cat > /home/rzdbot/monitor.sh << 'EOF'
#!/bin/bash

echo \"=== RZD Bot Status ===\"
echo \"Bot Service:\"
systemctl is-active rzd-bot
echo \"Celery Worker:\"
systemctl is-active rzd-celery-worker
echo \"Celery Beat:\"
systemctl is-active rzd-celery-beat

echo -e \"\\n=== Database Status ===\"
sudo -u postgres psql -c \"SELECT count(*) FROM subscriptions WHERE is_active = true;\"

echo -e \"\\n=== Redis Status ===\"
redis-cli ping

echo -e \"\\n=== Disk Usage ===\"
df -h

echo -e \"\\n=== Memory Usage ===\"
free -h

echo -e \"\\n=== Recent Logs ===\"
tail -5 /home/rzdbot/rzd-bot/logs/bot.log
EOF
            chmod +x /home/rzdbot/monitor.sh
        "
    else
        sudo -u rzdbot bash -c "
            cat > /home/rzdbot/monitor.sh << 'EOF'
#!/bin/bash

echo \"=== RZD Bot Status ===\"
echo \"Bot Service:\"
systemctl is-active rzd-bot
echo \"Celery Worker:\"
systemctl is-active rzd-celery-worker
echo \"Celery Beat:\"
systemctl is-active rzd-celery-beat

echo -e \"\\n=== Database Status ===\"
sudo -u postgres psql -c \"SELECT count(*) FROM subscriptions WHERE is_active = true;\"

echo -e \"\\n=== Redis Status ===\"
redis-cli ping

echo -e \"\\n=== Disk Usage ===\"
df -h

echo -e \"\\n=== Memory Usage ===\"
free -h

echo -e \"\\n=== Recent Logs ===\"
tail -5 /home/rzdbot/rzd-bot/logs/bot.log
EOF
            chmod +x /home/rzdbot/monitor.sh
        "
    fi
    
    # Скрипт обновления
    if [[ "$ROOT_MODE" == "true" ]]; then
        sudo -u rzdbot bash -c "
            cat > /home/rzdbot/update_bot.sh << 'EOF'
#!/bin/bash

echo \"Stopping services...\"
sudo systemctl stop rzd-bot rzd-celery-worker rzd-celery-beat

echo \"Backing up database...\"
sudo -u postgres pg_dump rzd_bot > /home/rzdbot/backup_\$(date +%Y%m%d_%H%M%S).sql

echo \"Updating code...\"
cd /home/rzdbot/rzd-bot
git pull origin main

echo \"Updating dependencies...\"
source venv/bin/activate
pip install -r requirements.txt

echo \"Running migrations...\"
python run.py migrate

echo \"Starting services...\"
sudo systemctl start rzd-bot rzd-celery-worker rzd-celery-beat

echo \"Update completed!\"
EOF
            chmod +x /home/rzdbot/update_bot.sh
        "
    else
        sudo -u rzdbot bash -c "
            cat > /home/rzdbot/update_bot.sh << 'EOF'
#!/bin/bash

echo \"Stopping services...\"
sudo systemctl stop rzd-bot rzd-celery-worker rzd-celery-beat

echo \"Backing up database...\"
sudo -u postgres pg_dump rzd_bot > /home/rzdbot/backup_\$(date +%Y%m%d_%H%M%S).sql

echo \"Updating code...\"
cd /home/rzdbot/rzd-bot
git pull origin main

echo \"Updating dependencies...\"
source venv/bin/activate
pip install -r requirements.txt

echo \"Running migrations...\"
python run.py migrate

echo \"Starting services...\"
sudo systemctl start rzd-bot rzd-celery-worker rzd-celery-beat

echo \"Update completed!\"
EOF
            chmod +x /home/rzdbot/update_bot.sh
        "
    fi
    
    # Скрипт запуска Docker
    if [[ "$ROOT_MODE" == "true" ]]; then
        sudo -u rzdbot bash -c "
            cat > /home/rzdbot/start_docker.sh << 'EOF'
#!/bin/bash

echo \"Starting RZD Bot with Docker...\"
cd /home/rzdbot/rzd-bot

# Останавливаем systemd сервисы
sudo systemctl stop rzd-bot rzd-celery-worker rzd-celery-beat

# Запускаем Docker
docker-compose up -d --build

echo \"Docker containers started!\"
echo \"Check status with: docker-compose ps\"
echo \"View logs with: docker-compose logs -f\"
EOF
            chmod +x /home/rzdbot/start_docker.sh
        "
    else
        sudo -u rzdbot bash -c "
            cat > /home/rzdbot/start_docker.sh << 'EOF'
#!/bin/bash

echo \"Starting RZD Bot with Docker...\"
cd /home/rzdbot/rzd-bot

# Останавливаем systemd сервисы
sudo systemctl stop rzd-bot rzd-celery-worker rzd-celery-beat

# Запускаем Docker
docker-compose up -d --build

echo \"Docker containers started!\"
echo \"Check status with: docker-compose ps\"
echo \"View logs with: docker-compose logs -f\"
EOF
            chmod +x /home/rzdbot/start_docker.sh
        "
    fi
    
    # Скрипт остановки Docker
    if [[ "$ROOT_MODE" == "true" ]]; then
        sudo -u rzdbot bash -c "
            cat > /home/rzdbot/stop_docker.sh << 'EOF'
#!/bin/bash

echo \"Stopping RZD Bot Docker containers...\"
cd /home/rzdbot/rzd-bot

docker-compose down

echo \"Docker containers stopped!\"
echo \"Starting systemd services...\"
sudo systemctl start rzd-bot rzd-celery-worker rzd-celery-beat

echo \"Systemd services started!\"
EOF
            chmod +x /home/rzdbot/stop_docker.sh
        "
    else
        sudo -u rzdbot bash -c "
            cat > /home/rzdbot/stop_docker.sh << 'EOF'
#!/bin/bash

echo \"Stopping RZD Bot Docker containers...\"
cd /home/rzdbot/rzd-bot

docker-compose down

echo \"Docker containers stopped!\"
echo \"Starting systemd services...\"
sudo systemctl start rzd-bot rzd-celery-worker rzd-celery-beat

echo \"Systemd services started!\"
EOF
            chmod +x /home/rzdbot/stop_docker.sh
        "
    fi
    
    print_success "Скрипты управления созданы"
}

# Запуск сервисов
start_services() {
    print_status "Запуск сервисов..."
    
    if [[ "$ROOT_MODE" == "true" ]]; then
        systemctl start rzd-bot rzd-celery-worker rzd-celery-beat
        
        # Ждем запуска
        sleep 5
        
        # Проверяем статус
        if systemctl is-active --quiet rzd-bot && \
           systemctl is-active --quiet rzd-celery-worker && \
           systemctl is-active --quiet rzd-celery-beat; then
            print_success "Все сервисы запущены успешно"
        else
            print_warning "Некоторые сервисы могут не запуститься. Проверьте логи:"
            echo "journalctl -u rzd-bot -f"
            echo "journalctl -u rzd-celery-worker -f"
            echo "journalctl -u rzd-celery-beat -f"
        fi
    else
        sudo systemctl start rzd-bot rzd-celery-worker rzd-celery-beat
        
        # Ждем запуска
        sleep 5
        
        # Проверяем статус
        if systemctl is-active --quiet rzd-bot && \
           systemctl is-active --quiet rzd-celery-worker && \
           systemctl is-active --quiet rzd-celery-beat; then
            print_success "Все сервисы запущены успешно"
        else
            print_warning "Некоторые сервисы могут не запуститься. Проверьте логи:"
            echo "sudo journalctl -u rzd-bot -f"
            echo "sudo journalctl -u rzd-celery-worker -f"
            echo "sudo journalctl -u rzd-celery-beat -f"
        fi
    fi
}

# Финальная проверка
final_check() {
    print_status "Выполнение финальной проверки..."
    
    # Проверяем подключение к базе данных
    if sudo -u postgres psql -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "PostgreSQL работает"
    else
        print_error "PostgreSQL не работает"
    fi
    
    # Проверяем Redis
    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis работает"
    else
        print_error "Redis не работает"
    fi
    
    # Проверяем Nginx
    if systemctl is-active --quiet nginx; then
        print_success "Nginx работает"
    else
        print_error "Nginx не работает"
    fi
    
    # Проверяем сервисы бота
    if systemctl is-active --quiet rzd-bot; then
        print_success "RZD Bot работает"
    else
        print_error "RZD Bot не работает"
    fi
}

# Вывод информации о завершении
show_completion_info() {
    echo
    print_success "🎉 Установка завершена успешно!"
    echo
    echo "📋 Информация о системе:"
    echo "• Пользователь бота: rzdbot"
    echo "• Директория проекта: /home/rzdbot/rzd-bot"
    echo "• База данных: PostgreSQL (rzd_bot)"
    echo "• Кэш: Redis"
    echo "• Веб-сервер: Nginx"
    echo
    echo "🚀 Управление ботом:"
    if [[ "$ROOT_MODE" == "true" ]]; then
        echo "• Статус: systemctl status rzd-bot"
        echo "• Логи: journalctl -u rzd-bot -f"
    else
        echo "• Статус: sudo systemctl status rzd-bot"
        echo "• Логи: sudo journalctl -u rzd-bot -f"
    fi
    echo "• Мониторинг: /home/rzdbot/monitor.sh"
    echo "• Обновление: /home/rzdbot/update_bot.sh"
    echo
    echo "🐳 Запуск с Docker:"
    echo "• Запуск: /home/rzdbot/start_docker.sh"
    echo "• Остановка: /home/rzdbot/stop_docker.sh"
    echo "• Статус: docker-compose ps"
    echo "• Логи: docker-compose logs -f"
    echo
    echo "🌐 Веб-интерфейс:"
    echo "• URL: http://$(curl -s ifconfig.me)"
    echo "• Webhook: http://$(curl -s ifconfig.me)/webhook"
    echo
    echo "📞 Поддержка:"
    echo "• Логи бота: /home/rzdbot/rzd-bot/logs/bot.log"
    echo "• Конфигурация: /home/rzdbot/rzd-bot/.env"
    echo
    print_warning "⚠️  Не забудьте настроить домен и SSL сертификат для продакшена!"
    echo
}

# Основная функция
main() {
    echo "🚂 RZD Bot - Автоматический установщик"
    echo "======================================"
    echo
    
    check_root
    check_os
    
    print_status "Начинаем установку RZD Bot..."
    echo
    
    update_system
    fix_apt_pkg
    install_packages
    install_python
    install_postgresql
    install_redis
    install_docker
    create_bot_user
    clone_project
    setup_venv
    setup_config
    setup_database
    setup_systemd
    setup_nginx
    setup_firewall
    create_management_scripts
    start_services
    final_check
    show_completion_info
}

# Запуск основной функции
main "$@"
