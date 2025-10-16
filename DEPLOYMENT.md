# 🚀 Руководство по развертыванию DoHot на production

Это руководство описывает полный процесс развертывания бота DoHot на production сервере.

## 📋 Содержание

1. [Требования](#требования)
2. [Подготовка сервера](#подготовка-сервера)
3. [Установка и настройка](#установка-и-настройка)
4. [Systemd сервис](#systemd-сервис)
5. [Мониторинг](#мониторинг)
6. [Резервное копирование](#резервное-копирование)
7. [Обновление](#обновление)
8. [Решение проблем](#решение-проблем)

---

## Требования

### Минимальные требования сервера

- **ОС:** Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM:** 512 MB (рекомендуется 1 GB)
- **Диск:** 2 GB свободного места
- **Python:** 3.10+
- **Интернет:** Постоянное соединение

### Рекомендуемая конфигурация

- **ОС:** Ubuntu 22.04 LTS
- **RAM:** 2 GB
- **Диск:** 10 GB (SSD)
- **Python:** 3.11
- **Swap:** 1 GB

---

## Подготовка сервера

### Шаг 1: Обновление системы

```bash
# Ubuntu/Debian
sudo apt update
sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git curl -y

# CentOS/RHEL
sudo yum update -y
sudo yum install python3 python3-pip git curl -y
```

### Шаг 2: Создание пользователя

```bash
# Создаем пользователя для бота
sudo useradd -m -s /bin/bash dohot
sudo passwd dohot  # Установите пароль

# Добавляем в sudoers (опционально)
sudo usermod -aG sudo dohot

# Переключаемся на пользователя
sudo su - dohot
```

### Шаг 3: Настройка firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw enable

# Firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

---

## Установка и настройка

### Шаг 1: Клонирование репозитория

```bash
cd /opt
sudo git clone https://github.com/your-repo/dohot.git
sudo chown -R dohot:dohot /opt/dohot
cd /opt/dohot
```

### Шаг 2: Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 3: Настройка конфигурации

```bash
# Создайте .env файл
cp .env.example .env

# Отредактируйте конфигурацию
nano .env
```

Добавьте в `.env`:

```env
# ОБЯЗАТЕЛЬНО
BOT_TOKEN=ваш_токен_от_BotFather

# Опционально
DB_PATH=/opt/dohot/data/dohot.db
CHARTS_DIR=/opt/dohot/charts
REMINDER_HOUR=9
REMINDER_MINUTE=0
```

### Шаг 4: Создание директорий

```bash
mkdir -p /opt/dohot/data
mkdir -p /opt/dohot/charts
mkdir -p /opt/dohot/backups
mkdir -p /opt/dohot/logs
mkdir -p /opt/dohot/exports

# Установка прав
chmod 755 /opt/dohot
chmod 700 /opt/dohot/data
chmod 700 /opt/dohot/backups
```

### Шаг 5: Тестовый запуск

```bash
# Активируйте venv если не активен
source /opt/dohot/venv/bin/activate

# Запустите бота
python /opt/dohot/main.py
```

Если бот запустился без ошибок - нажмите `Ctrl+C` и переходите к настройке systemd.

---

## Systemd сервис

### Шаг 1: Копирование service файла

```bash
sudo cp /opt/dohot/dohot.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/dohot.service
```

### Шаг 2: Редактирование service файла

```bash
sudo nano /etc/systemd/system/dohot.service
```

Убедитесь что пути правильные:

```ini
[Unit]
Description=DoHot Telegram Bot
After=network.target

[Service]
Type=simple
User=dohot
Group=dohot
WorkingDirectory=/opt/dohot
Environment="PATH=/opt/dohot/venv/bin"
ExecStart=/opt/dohot/venv/bin/python /opt/dohot/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Шаг 3: Запуск сервиса

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable dohot

# Запустите сервис
sudo systemctl start dohot

# Проверьте статус
sudo systemctl status dohot
```

### Шаг 4: Просмотр логов

```bash
# Все логи
sudo journalctl -u dohot -f

# Последние 100 строк
sudo journalctl -u dohot -n 100

# Логи за сегодня
sudo journalctl -u dohot --since today

# Только ошибки
sudo journalctl -u dohot -p err
```

### Управление сервисом

```bash
# Остановить
sudo systemctl stop dohot

# Перезапустить
sudo systemctl restart dohot

# Отключить автозапуск
sudo systemctl disable dohot

# Статус
sudo systemctl status dohot
```

---

## Мониторинг

### Настройка логирования

```bash
# Создайте конфигурацию logrotate
sudo nano /etc/logrotate.d/dohot
```

Добавьте:

```
/opt/dohot/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    create 0644 dohot dohot
}
```

### Мониторинг производительности

```bash
# Использование памяти
ps aux | grep "python.*main.py"

# Использование диска
du -sh /opt/dohot/*

# Размер базы данных
ls -lh /opt/dohot/data/dohot.db

# Статистика базы данных
cd /opt/dohot
source venv/bin/activate
python -c "from utils import DatabaseValidator; v = DatabaseValidator(); print(v.get_database_stats())"
```

### Алерты (опционально)

Создайте скрипт для проверки работы бота:

```bash
nano /opt/dohot/check_bot.sh
```

```bash
#!/bin/bash
if ! systemctl is-active --quiet dohot; then
    echo "DoHot bot is down!" | mail -s "DoHot Alert" admin@example.com
    sudo systemctl restart dohot
fi
```

Добавьте в crontab:

```bash
crontab -e
*/5 * * * * /opt/dohot/check_bot.sh
```

---

## Резервное копирование

### Автоматические бэкапы

```bash
# Создайте скрипт бэкапа
nano /opt/dohot/backup_cron.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/dohot/backups"
DB_FILE="/opt/dohot/data/dohot.db"

# Создаём бэкап
cp $DB_FILE $BACKUP_DIR/dohot_$DATE.db

# Удаляем старые (старше 30 дней)
find $BACKUP_DIR -name "dohot_*.db" -mtime +30 -delete

# Логируем
echo "Backup created: dohot_$DATE.db" >> $BACKUP_DIR/backup.log
```

Сделайте исполняемым:

```bash
chmod +x /opt/dohot/backup_cron.sh
```

Добавьте в crontab:

```bash
crontab -e

# Бэкап каждый день в 3:00
0 3 * * * /opt/dohot/backup_cron.sh
```

### Ручной бэкап

```bash
cd /opt/dohot
source venv/bin/activate
python backup.py
```

### Восстановление

```bash
cd /opt/dohot
source venv/bin/activate

# Остановите бота
sudo systemctl stop dohot

# Восстановите из бэкапа
python backup.py --restore backups/dohot_20251016_030000.db

# Запустите бота
sudo systemctl start dohot
```

---

## Обновление

### Стандартное обновление

```bash
cd /opt/dohot

# Остановите бота
sudo systemctl stop dohot

# Создайте бэкап
source venv/bin/activate
python backup.py

# Обновите код
git pull

# Обновите зависимости
source venv/bin/activate
pip install -r requirements.txt

# Примените миграции
python migrations.py --migrate

# Запустите бота
sudo systemctl start dohot

# Проверьте статус
sudo systemctl status dohot
```

### Откат после неудачного обновления

```bash
# Остановите бота
sudo systemctl stop dohot

# Откатите код
git reset --hard HEAD~1

# Восстановите базу
source venv/bin/activate
python backup.py --restore backups/latest_backup.db

# Запустите
sudo systemctl start dohot
```

---

## Решение проблем

### Бот не запускается

**Проверьте логи:**

```bash
sudo journalctl -u dohot -n 50
```

**Типичные проблемы:**

1. **"BOT_TOKEN не найден"**
   ```bash
   # Проверьте .env
   cat /opt/dohot/.env
   # Убедитесь что токен правильный
   ```

2. **"Permission denied"**
   ```bash
   # Проверьте права
   ls -la /opt/dohot/
   # Установите правильные права
   sudo chown -R dohot:dohot /opt/dohot
   ```

3. **"Module not found"**
   ```bash
   # Переустановите зависимости
   cd /opt/dohot
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Бот перестал отвечать

```bash
# Проверьте статус
sudo systemctl status dohot

# Перезапустите
sudo systemctl restart dohot

# Проверьте интернет
ping -c 3 api.telegram.org

# Проверьте использование памяти
free -h
```

### База данных повреждена

```bash
# Проверьте целостность
cd /opt/dohot
source venv/bin/activate
python backup.py --check

# Если повреждена - восстановите
sudo systemctl stop dohot
python backup.py --restore backups/latest_good_backup.db
sudo systemctl start dohot
```

### Диск заполнен

```bash
# Проверьте место
df -h

# Очистите старые логи
sudo journalctl --vacuum-time=7d

# Удалите старые бэкапы
find /opt/dohot/backups -name "*.db" -mtime +30 -delete

# Очистите графики
rm -rf /opt/dohot/charts/*
```

---

## Чеклист развертывания

- [ ] Сервер настроен и обновлен
- [ ] Создан пользователь `dohot`
- [ ] Установлены зависимости
- [ ] Клонирован репозиторий в `/opt/dohot`
- [ ] Создано виртуальное окружение
- [ ] Настроен `.env` с токеном
- [ ] Созданы необходимые директории
- [ ] Установлены правильные права доступа
- [ ] Протестирован ручной запуск
- [ ] Настроен systemd сервис
- [ ] Бот запущен и работает
- [ ] Настроено автоматическое резервное копирование
- [ ] Настроен logrotate
- [ ] Проверены логи на ошибки
- [ ] Протестированы основные функции бота
- [ ] Создана документация для команды

---

## Безопасность

### Рекомендации

1. **Ограничьте доступ к серверу:**
   ```bash
   # Используйте SSH ключи вместо паролей
   # Отключите root login
   # Используйте нестандартный SSH порт
   ```

2. **Защитите .env файл:**
   ```bash
   chmod 600 /opt/dohot/.env
   ```

3. **Регулярно обновляйте систему:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Мониторьте логи:**
   ```bash
   # Установите fail2ban
   sudo apt install fail2ban
   ```

5. **Используйте HTTPS для webhook (если применимо)**

---

## Контакты и поддержка

- **Документация:** README.md, INSTALL.md, USAGE.md
- **Issues:** GitHub Issues
- **Логи:** `/opt/dohot/logs/` и `journalctl -u dohot`

---

**Готово! Ваш DoHot бот развернут и готов к работе! 🎉**
