#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для печати с цветом
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

# Заголовок
clear
echo -e "${BLUE}"
echo "╔══════════════════════════════════════╗"
echo "║    DoHot Installation Script         ║"
echo "║  Telegram Bot для домашней бухгалтерии  ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# Проверка Python
print_info "Проверка Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 не найден!"
    echo "Установите Python 3.10+ и запустите скрипт снова"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION найден"

# Проверка pip
print_info "Проверка pip..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip не найден!"
    echo "Установите pip: sudo apt install python3-pip"
    exit 1
fi
print_success "pip найден"

# Создание виртуального окружения
print_info "Создание виртуального окружения..."
if [ -d "venv" ]; then
    print_warning "venv уже существует, пропускаем создание"
else
    python3 -m venv venv
    print_success "Виртуальное окружение создано"
fi

# Активация виртуального окружения
print_info "Активация виртуального окружения..."
source venv/bin/activate
print_success "Виртуальное окружение активировано"

# Обновление pip
print_info "Обновление pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "pip обновлён"

# Установка зависимостей
print_info "Установка зависимостей..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null 2>&1
    print_success "Зависимости установлены"
else
    print_error "requirements.txt не найден!"
    exit 1
fi

# Создание .env файла
print_info "Настройка конфигурации..."
if [ -f ".env" ]; then
    print_warning ".env уже существует"
    read -p "Перезаписать? (y/n): " overwrite
    if [ "$overwrite" == "y" ]; then
        cp .env.example .env
        print_success ".env создан"
    fi
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env создан"
    else
        print_error ".env.example не найден!"
        exit 1
    fi
fi

# Запрос токена
echo ""
print_info "Требуется токен Telegram бота"
echo "Получите его у @BotFather в Telegram"
echo ""
read -p "Введите BOT_TOKEN (или Enter чтобы пропустить): " bot_token

if [ ! -z "$bot_token" ]; then
    # Обновляем .env файл
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/BOT_TOKEN=.*/BOT_TOKEN=$bot_token/" .env
    else
        # Linux
        sed -i "s/BOT_TOKEN=.*/BOT_TOKEN=$bot_token/" .env
    fi
    print_success "Токен сохранён в .env"
else
    print_warning "Токен не указан, вам нужно добавить его вручную в .env"
fi

# Создание директорий
print_info "Создание рабочих директорий..."
mkdir -p data charts backups logs exports
print_success "Директории созданы"

# Инициализация базы данных
print_info "Инициализация базы данных..."
python3 -c "from database import Database; Database()" > /dev/null 2>&1
print_success "База данных инициализирована"

# Проверка миграций
print_info "Проверка миграций..."
python3 migrations.py --check > /dev/null 2>&1
print_success "Миграции проверены"

# Завершение
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Установка завершена успешно!     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""

# Инструкции
echo -e "${BLUE}📝 Следующие шаги:${NC}"
echo ""

if [ -z "$bot_token" ]; then
    echo "1. Отредактируйте .env и добавьте BOT_TOKEN:"
    echo -e "   ${YELLOW}nano .env${NC}"
    echo ""
fi

echo "2. Активируйте виртуальное окружение (если ещё не активно):"
echo -e "   ${YELLOW}source venv/bin/activate${NC}"
echo ""

echo "3. Запустите бота:"
echo -e "   ${YELLOW}python main.py${NC}"
echo ""

echo -e "${BLUE}📚 Дополнительно:${NC}"
echo ""
echo "• Быстрый старт:    cat QUICKSTART.md"
echo "• Полная установка: cat INSTALL.md"
echo "• Руководство:      cat USAGE.md"
echo "• Помощь:           python main.py --help"
echo ""

echo -e "${BLUE}🛠️  Полезные команды:${NC}"
echo ""
echo "• make run          - Запустить бота"
echo "• make backup       - Создать резервную копию"
echo "• make status       - Проверить статус"
echo "• make help         - Показать все команды"
echo ""

echo -e "${GREEN}Удачи с DoHot! 🚀${NC}"
