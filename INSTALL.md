# 📦 Инструкции по установке DoHot

## Способ 1: Обычная установка (рекомендуется)

### Требования
- Python 3.10+ 
- pip

### Установка

```bash
# 1. Клонируйте или скачайте проект
git clone <repository-url>
cd dohot

# 2. (Опционально) Создайте виртуальное окружение
python -m venv venv

# Активируйте виртуальное окружение:
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Создайте конфигурацию
cp .env.example .env

# 5. Отредактируйте .env и добавьте BOT_TOKEN
nano .env  # или любой другой текстовый редактор

# 6. Запустите бота
python main.py
```

### Запуск как сервис (Linux)

Создайте файл `/etc/systemd/system/dohot.service`:

```ini
[Unit]
Description=DoHot Telegram Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/dohot
Environment="PATH=/path/to/dohot/venv/bin"
ExecStart=/path/to/dohot/venv/bin/python /path/to/dohot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Затем:

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable dohot

# Запустите сервис
sudo systemctl start dohot

# Проверьте статус
sudo systemctl status dohot

# Просмотр логов
sudo journalctl -u dohot -f
```

## Способ 2: Установка через Docker

### Требования
- Docker
- Docker Compose

### Установка

```bash
# 1. Клонируйте или скачайте проект
git clone <repository-url>
cd dohot

# 2. Создайте конфигурацию
cp .env.example .env

# 3. Отредактируйте .env и добавьте BOT_TOKEN
nano .env

# 4. Создайте директории для данных
mkdir -p data charts

# 5. Соберите и запустите контейнер
docker-compose up -d

# 6. Проверьте логи
docker-compose logs -f

# Остановить бота
docker-compose down

# Перезапустить бота
docker-compose restart
```

### Обновление Docker версии

```bash
# Остановите контейнер
docker-compose down

# Обновите код
git pull

# Пересоберите образ
docker-compose build

# Запустите снова
docker-compose up -d
```

## Способ 3: Установка на VPS/Cloud сервер

### Подготовка сервера (Ubuntu/Debian)

```bash
# Обновите систему
sudo apt update
sudo apt upgrade -y

# Установите Python и pip
sudo apt install python3 python3-pip python3-venv git -y

# Клонируйте проект
cd /opt
sudo git clone <repository-url> dohot
cd dohot

# Создайте виртуальное окружение
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt

# Создайте конфигурацию
sudo cp .env.example .env
sudo nano .env  # добавьте BOT_TOKEN

# Измените владельца (замените username на ваше имя пользователя)
sudo chown -R username:username /opt/dohot

# Настройте systemd сервис (см. выше)
```

### Настройка автозапуска через screen (альтернатива)

```bash
# Установите screen
sudo apt install screen -y

# Создайте screen сессию
screen -S dohot

# Запустите бота
cd /opt/dohot
source venv/bin/activate
python main.py

# Отключитесь от screen (Ctrl+A, затем D)

# Подключиться обратно:
screen -r dohot
```

## Способ 4: Установка на Raspberry Pi

```bash
# Установите зависимости
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y

# Клонируйте проект
cd ~
git clone <repository-url> dohot
cd dohot

# Установите зависимости
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройте .env
cp .env.example .env
nano .env

# Запустите
python main.py

# Для автозапуска добавьте в crontab:
crontab -e

# Добавьте строку:
@reboot cd /home/pi/dohot && /home/pi/dohot/venv/bin/python /home/pi/dohot/main.py &
```

## Способ 5: Установка на Windows

### С использованием виртуального окружения

```cmd
:: 1. Установите Python с python.org (3.10+)

:: 2. Откройте PowerShell или CMD
cd C:\Users\YourName\Downloads\dohot

:: 3. Создайте виртуальное окружение
python -m venv venv

:: 4. Активируйте его
venv\Scripts\activate

:: 5. Установите зависимости
pip install -r requirements.txt

:: 6. Создайте .env
copy .env.example .env
notepad .env

:: 7. Запустите бота
python main.py
```

### Запуск как Windows Service

Используйте [NSSM](https://nssm.cc/):

```cmd
:: Скачайте NSSM

:: Установите сервис
nssm install DoHot C:\Path\To\Python\python.exe C:\Path\To\dohot\main.py

:: Настройте рабочую директорию
nssm set DoHot AppDirectory C:\Path\To\dohot

:: Запустите сервис
nssm start DoHot

:: Управление сервисом
nssm stop DoHot
nssm restart DoHot
nssm remove DoHot
```

## Проверка установки

После установки любым способом, проверьте:

1. **Бот запущен**: вы видите лог `INFO - Бот готов к работе!`
2. **База данных создана**: файл `dohot.db` существует
3. **Бот отвечает**: отправьте `/start` боту в Telegram

## Решение проблем

### Ошибка: "No module named 'aiogram'"

```bash
# Убедитесь что активировано виртуальное окружение
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate      # Windows

# Переустановите зависимости
pip install -r requirements.txt
```

### Ошибка: "BOT_TOKEN не найден"

1. Проверьте что файл `.env` создан
2. Проверьте что в `.env` есть строка `BOT_TOKEN=...`
3. Проверьте что токен правильный (от @BotFather)

### Бот не отвечает

1. Проверьте что `main.py` запущен
2. Проверьте логи на ошибки
3. Проверьте интернет соединение
4. Убедитесь что токен валидный

### Графики не создаются

```bash
# Установите matplotlib
pip install matplotlib==3.8.2

# Создайте директорию вручную
mkdir charts
```

## Резервное копирование

### Что нужно сохранять:

1. **База данных**: `dohot.db` - все ваши данные
2. **Конфигурация**: `.env` - ваши настройки
3. **Графики** (опционально): `charts/` - сгенерированные графики

### Автоматический бэкап (Linux)

Создайте скрипт `/opt/dohot/backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/path/to/backups"

mkdir -p $BACKUP_DIR
cp /opt/dohot/dohot.db $BACKUP_DIR/dohot_$DATE.db

# Удалить старые бэкапы (старше 30 дней)
find $BACKUP_DIR -name "dohot_*.db" -mtime +30 -delete
```

Добавьте в crontab:

```bash
crontab -e

# Бэкап каждый день в 3:00
0 3 * * * /opt/dohot/backup.sh
```

## Обновление

### Обычная установка:

```bash
cd dohot
git pull
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Docker:

```bash
cd dohot
docker-compose down
git pull
docker-compose build
docker-compose up -d
```

---

**Готово! Выберите удобный для вас способ установки и наслаждайтесь использованием DoHot! 🚀**
