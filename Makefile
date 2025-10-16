.PHONY: help install run stop backup restore clean test migrate check export docker-build docker-up docker-down docker-logs

# Цвета для вывода
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
BLUE   := $(shell tput -Txterm setaf 4)
RESET  := $(shell tput -Txterm sgr0)

help: ## Показать эту справку
	@echo '$(BLUE)Доступные команды для DoHot:$(RESET)'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ''

install: ## Установить зависимости
	@echo '$(BLUE)Установка зависимостей...$(RESET)'
	pip install -r requirements.txt
	@echo '$(GREEN)✓ Зависимости установлены$(RESET)'

venv: ## Создать виртуальное окружение
	@echo '$(BLUE)Создание виртуального окружения...$(RESET)'
	python3 -m venv venv
	@echo '$(GREEN)✓ Виртуальное окружение создано$(RESET)'
	@echo '$(YELLOW)Активируйте его: source venv/bin/activate$(RESET)'

setup: venv install ## Полная настройка проекта
	@echo '$(BLUE)Создание файла конфигурации...$(RESET)'
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo '$(GREEN)✓ Файл .env создан$(RESET)'; \
		echo '$(YELLOW)⚠ Не забудьте добавить BOT_TOKEN в .env$(RESET)'; \
	else \
		echo '$(YELLOW)⚠ Файл .env уже существует$(RESET)'; \
	fi
	@echo '$(GREEN)✓ Настройка завершена!$(RESET)'

run: ## Запустить бота
	@echo '$(BLUE)Запуск бота DoHot...$(RESET)'
	python main.py

dev: ## Запустить бота в режиме разработки с подробным логированием
	@echo '$(BLUE)Запуск в режиме разработки...$(RESET)'
	python main.py --log-level DEBUG

stop: ## Остановить бота (найти процесс и остановить)
	@echo '$(BLUE)Остановка бота...$(RESET)'
	@pkill -f "python main.py" || echo '$(YELLOW)Бот не запущен$(RESET)'

backup: ## Создать резервную копию базы данных
	@echo '$(BLUE)Создание резервной копии...$(RESET)'
	python backup.py
	@echo '$(GREEN)✓ Резервная копия создана$(RESET)'

backup-list: ## Показать список резервных копий
	@echo '$(BLUE)Список резервных копий:$(RESET)'
	python backup.py --list

restore: ## Восстановить из резервной копии (использование: make restore BACKUP=путь/к/файлу)
	@if [ -z "$(BACKUP)" ]; then \
		echo '$(YELLOW)Использование: make restore BACKUP=путь/к/файлу$(RESET)'; \
		python backup.py --list; \
	else \
		echo '$(BLUE)Восстановление из $(BACKUP)...$(RESET)'; \
		python backup.py --restore $(BACKUP); \
	fi

clean: ## Очистить временные файлы
	@echo '$(BLUE)Очистка временных файлов...$(RESET)'
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete 2>/dev/null || true
	@echo '$(GREEN)✓ Очистка завершена$(RESET)'

clean-all: clean ## Очистить всё (включая базу данных и графики)
	@echo '$(YELLOW)⚠ ВНИМАНИЕ: Будут удалены база данных и все графики!$(RESET)'
	@read -p "Продолжить? [y/N]: " confirm && [ "$$confirm" = "y" ]
	rm -f dohot.db
	rm -rf charts/
	rm -rf logs/
	@echo '$(GREEN)✓ Полная очистка завершена$(RESET)'

test: ## Запустить тесты (если есть)
	@echo '$(BLUE)Запуск тестов...$(RESET)'
	@if [ -d "tests" ]; then \
		python -m pytest tests/; \
	else \
		echo '$(YELLOW)Тесты не найдены$(RESET)'; \
	fi

migrate: ## Применить миграции базы данных
	@echo '$(BLUE)Применение миграций...$(RESET)'
	python migrations.py --migrate
	@echo '$(GREEN)✓ Миграции применены$(RESET)'

migrate-status: ## Показать статус миграций
	@echo '$(BLUE)Статус миграций:$(RESET)'
	python migrations.py --status

check: ## Проверить базу данных на целостность
	@echo '$(BLUE)Проверка базы данных...$(RESET)'
	python backup.py --check

export: ## Экспортировать данные (использование: make export USER=12345)
	@if [ -z "$(USER)" ]; then \
		echo '$(YELLOW)Использование: make export USER=user_id$(RESET)'; \
	else \
		echo '$(BLUE)Экспорт данных пользователя $(USER)...$(RESET)'; \
		python export_data.py --user $(USER) --format json; \
	fi

export-all: ## Экспортировать данные всех пользователей
	@echo '$(BLUE)Экспорт данных всех пользователей...$(RESET)'
	python export_data.py --all --format json

summary: ## Показать сводный отчёт
	@echo '$(BLUE)Генерация сводного отчёта...$(RESET)'
	python export_data.py --summary

docker-build: ## Собрать Docker образ
	@echo '$(BLUE)Сборка Docker образа...$(RESET)'
	docker-compose build
	@echo '$(GREEN)✓ Образ собран$(RESET)'

docker-up: ## Запустить бота в Docker
	@echo '$(BLUE)Запуск бота в Docker...$(RESET)'
	docker-compose up -d
	@echo '$(GREEN)✓ Бот запущен в фоне$(RESET)'
	@echo 'Для просмотра логов: make docker-logs'

docker-down: ## Остановить бота в Docker
	@echo '$(BLUE)Остановка бота в Docker...$(RESET)'
	docker-compose down
	@echo '$(GREEN)✓ Бот остановлен$(RESET)'

docker-logs: ## Показать логи Docker контейнера
	docker-compose logs -f

docker-restart: docker-down docker-up ## Перезапустить Docker контейнер

docker-clean: docker-down ## Очистить Docker ресурсы
	@echo '$(BLUE)Очистка Docker ресурсов...$(RESET)'
	docker-compose down -v
	docker system prune -f
	@echo '$(GREEN)✓ Очистка завершена$(RESET)'

logs: ## Показать логи бота
	@if [ -f logs/dohot.log ]; then \
		tail -f logs/dohot.log; \
	else \
		echo '$(YELLOW)Файл логов не найден$(RESET)'; \
	fi

logs-error: ## Показать логи ошибок
	@if [ -f logs/dohot_errors.log ]; then \
		tail -f logs/dohot_errors.log; \
	else \
		echo '$(YELLOW)Файл логов ошибок не найден$(RESET)'; \
	fi

stats: ## Показать статистику базы данных
	@echo '$(BLUE)Статистика базы данных:$(RESET)'
	@python -c "from database import Database; from utils import DatabaseValidator; \
	db = Database(); validator = DatabaseValidator(); \
	stats = validator.get_database_stats(); \
	print('📊 Размер БД:', f\"{stats.get('size_mb', 0):.2f} MB\"); \
	print('👥 Пользователей:', stats.get('total_users', 0)); \
	print('💳 Кредитов:', stats.get('credits_count', 0)); \
	print('💸 Долгов:', stats.get('debts_count', 0)); \
	print('💰 Доходов:', stats.get('incomes_count', 0)); \
	print('🛒 Расходов:', stats.get('expenses_count', 0)); \
	print('📊 Инвестиций:', stats.get('investments_count', 0))"

status: ## Показать статус бота
	@echo '$(BLUE)Статус бота:$(RESET)'
	@if pgrep -f "python main.py" > /dev/null; then \
		echo '$(GREEN)✓ Бот запущен$(RESET)'; \
		ps aux | grep "python main.py" | grep -v grep; \
	else \
		echo '$(YELLOW)○ Бот не запущен$(RESET)'; \
	fi

update: ## Обновить проект из git
	@echo '$(BLUE)Обновление проекта...$(RESET)'
	git pull
	pip install -r requirements.txt
	@echo '$(GREEN)✓ Проект обновлён$(RESET)'

docs: ## Открыть документацию
	@echo '$(BLUE)Документация DoHot$(RESET)'
	@echo ''
	@echo '📖 Основные файлы:'
	@echo '  - README.md        Основная документация'
	@echo '  - QUICKSTART.md    Быстрый старт'
	@echo '  - INSTALL.md       Инструкции по установке'
	@echo '  - USAGE.md         Подробное руководство'
	@echo ''

info: ## Показать информацию о проекте
	@echo '$(BLUE)╔══════════════════════════════════════╗$(RESET)'
	@echo '$(BLUE)║          DoHot - v1.0.0              ║$(RESET)'
	@echo '$(BLUE)║  Telegram бот для домашней бухгалтерии  ║$(RESET)'
	@echo '$(BLUE)╚══════════════════════════════════════╝$(RESET)'
	@echo ''
	@echo '📦 Модули:'
	@echo '  - database.py       База данных'
	@echo '  - bot.py            Telegram бот'
	@echo '  - calculations.py   Финансовые расчёты'
	@echo '  - visualization.py  Графики'
	@echo '  - handlers.py       Обработчики'
	@echo ''
	@echo '🛠️  Утилиты:'
	@echo '  - backup.py         Резервное копирование'
	@echo '  - migrations.py     Миграции БД'
	@echo '  - export_data.py    Экспорт данных'
	@echo '  - utils.py          Вспомогательные функции'
	@echo ''
	@echo 'Для справки: make help'
