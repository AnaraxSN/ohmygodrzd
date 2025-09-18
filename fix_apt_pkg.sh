#!/bin/bash

# Скрипт для исправления проблем с apt_pkg
# Используйте этот скрипт, если возникают ошибки с ModuleNotFoundError: No module named 'apt_pkg'

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

# Проверка прав root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Скрипт запущен от имени root"
        ROOT_MODE=true
    else
        print_status "Скрипт запущен от обычного пользователя"
        ROOT_MODE=false
    fi
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
        
        # Устанавливаем дополнительные пакеты
        apt install -y software-properties-common
    else
        # Переустанавливаем python3-apt
        sudo apt install --reinstall -y python3-apt
        
        # Обновляем кэш apt
        sudo apt update
        
        # Устанавливаем дополнительные пакеты
        sudo apt install -y software-properties-common
    fi
    
    print_success "Проблемы с apt_pkg исправлены"
}

# Проверка работы add-apt-repository
test_add_apt_repository() {
    print_status "Тестирование add-apt-repository..."
    
    if [[ "$ROOT_MODE" == "true" ]]; then
        if add-apt-repository --help > /dev/null 2>&1; then
            print_success "add-apt-repository работает корректно"
        else
            print_error "add-apt-repository не работает"
            return 1
        fi
    else
        if sudo add-apt-repository --help > /dev/null 2>&1; then
            print_success "add-apt-repository работает корректно"
        else
            print_error "add-apt-repository не работает"
            return 1
        fi
    fi
}

# Основная функция
main() {
    print_header "Исправление проблем с apt_pkg"
    
    check_root
    fix_apt_pkg
    test_add_apt_repository
    
    print_success "Все проблемы исправлены!"
    echo
    echo "Теперь вы можете запустить основной скрипт установки:"
    echo "./install.sh"
}

# Запуск
main "$@"
