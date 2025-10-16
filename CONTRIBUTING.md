# 🤝 Внесение вклада в DoHot

Спасибо за интерес к проекту DoHot! Мы рады любому вкладу.

## 📋 Содержание

- [Как помочь](#как-помочь)
- [Процесс разработки](#процесс-разработки)
- [Стиль кода](#стиль-кода)
- [Тестирование](#тестирование)
- [Коммиты](#коммиты)
- [Pull Requests](#pull-requests)

## 🎯 Как помочь

### Сообщения об ошибках

Если вы нашли ошибку:

1. Проверьте, не создан ли уже Issue по этой проблеме
2. Создайте новый Issue с подробным описанием:
   - Версия Python
   - Версия aiogram
   - Шаги для воспроизведения
   - Ожидаемое поведение
   - Фактическое поведение
   - Логи ошибок

### Предложения по улучшению

Есть идея? Создайте Issue с тегом `enhancement`:

- Опишите проблему, которую решает предложение
- Объясните предлагаемое решение
- Приведите примеры использования
- Укажите альтернативные решения, если есть

### Исправления и новые функции

1. Fork репозитория
2. Создайте ветку для вашей функции (`git checkout -b feature/amazing-feature`)
3. Внесите изменения
4. Commit изменений (`git commit -m 'Add amazing feature'`)
5. Push в ветку (`git push origin feature/amazing-feature`)
6. Откройте Pull Request

## 🔧 Процесс разработки

### Настройка окружения

```bash
# Клонируйте ваш fork
git clone https://github.com/your-username/dohot.git
cd dohot

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r requirements.txt

# Создайте .env
cp .env.example .env
# Добавьте ваш BOT_TOKEN для тестирования
```

### Структура проекта

```
dohot/
├── main.py              # Точка входа
├── bot.py               # Основной бот
├── handlers.py          # Обработчики
├── database.py          # БД
├── calculations.py      # Расчёты
├── visualization.py     # Графики
├── utils.py             # Утилиты
├── config.py            # Конфигурация
├── logger_config.py     # Логирование
├── backup.py            # Резервное копирование
├── migrations.py        # Миграции
└── export_data.py       # Экспорт данных
```

### Запуск для разработки

```bash
# Запуск с подробным логированием
python main.py

# Или через Makefile
make dev
```

## 📝 Стиль кода

### Python Style Guide

Мы следуем [PEP 8](https://www.python.org/dev/peps/pep-0008/):

```python
# ✅ Правильно
def calculate_payment(amount: float, rate: float) -> float:
    """
    Рассчитать платёж
    
    Args:
        amount: Сумма кредита
        rate: Процентная ставка
        
    Returns:
        Размер платежа
    """
    return amount * rate


# ❌ Неправильно
def calc(a,r):
    return a*r
```

### Форматирование

- Используйте 4 пробела для отступов
- Максимальная длина строки: 100 символов
- Используйте f-strings для форматирования строк
- Добавляйте docstrings для функций и классов

### Импорты

```python
# Стандартная библиотека
import os
import sys
from datetime import datetime

# Сторонние библиотеки
from aiogram import Bot, Dispatcher
from aiogram.types import Message

# Локальные модули
from database import Database
from calculations import FinancialCalculator
```

### Именование

```python
# Классы: PascalCase
class FinancialCalculator:
    pass

# Функции и переменные: snake_case
def calculate_credit_payment():
    monthly_rate = 0.05
    return monthly_rate

# Константы: UPPER_CASE
MAX_CREDIT_TERM = 360
DEFAULT_RATE = 10.0

# Приватные методы: _leading_underscore
def _internal_method():
    pass
```

## 🧪 Тестирование

### Написание тестов

Создайте тесты в директории `tests/`:

```python
# tests/test_calculations.py
import pytest
from calculations import FinancialCalculator


def test_calculate_remaining_months():
    credit = {
        'total_months': 36,
        'current_month': 12
    }
    result = FinancialCalculator.calculate_remaining_months(credit)
    assert result == 24


def test_calculate_overpayment():
    # Ваш тест
    pass
```

### Запуск тестов

```bash
# Установите pytest
pip install pytest pytest-cov

# Запустите тесты
pytest tests/

# С покрытием кода
pytest --cov=. tests/
```

## 📦 Коммиты

### Формат коммитов

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Типы:**
- `feat`: Новая функция
- `fix`: Исправление ошибки
- `docs`: Документация
- `style`: Форматирование
- `refactor`: Рефакторинг
- `test`: Тесты
- `chore`: Обслуживание

**Примеры:**

```bash
feat(credits): добавить поддержку кредитных каникул

Реализована функция добавления периодов кредитных каникул.
Добавлена таблица credit_holidays в БД.

Closes #123
```

```bash
fix(database): исправить ошибку при создании резервной копии

Исправлена ошибка SQLite при попытке создать backup
во время активной транзакции.
```

```bash
docs(readme): обновить инструкции по установке

Добавлены примеры для Windows и macOS.
```

## 🔀 Pull Requests

### Чеклист перед созданием PR

- [ ] Код соответствует стилю проекта
- [ ] Добавлены тесты для новой функциональности
- [ ] Все тесты проходят
- [ ] Обновлена документация (если нужно)
- [ ] Коммиты следуют конвенции
- [ ] PR описывает изменения

### Шаблон PR

```markdown
## Описание
Краткое описание изменений.

## Тип изменений
- [ ] Исправление ошибки (fix)
- [ ] Новая функция (feature)
- [ ] Изменение с ломающими изменениями (breaking change)
- [ ] Документация

## Как протестировано
Опишите как вы тестировали изменения.

## Чеклист
- [ ] Код следует стилю проекта
- [ ] Я протестировал изменения
- [ ] Обновлена документация
- [ ] Нет конфликтов с main

## Скриншоты (если применимо)
```

### Процесс ревью

1. Создайте PR с описанием изменений
2. Дождитесь автоматических проверок
3. Ответьте на комментарии ревьюеров
4. Внесите необходимые изменения
5. После апрува PR будет смержен

## 🎨 Разработка новых функций

### Добавление нового обработчика

1. Определите FSM состояния в `bot.py`:

```python
class NewFeatureStates(StatesGroup):
    waiting_input = State()
    confirming = State()
```

2. Создайте обработчики в `handlers.py`:

```python
async def handle_new_feature(message: types.Message, state: FSMContext):
    """Начало новой функции"""
    await message.answer("Введите данные:")
    await state.set_state(NewFeatureStates.waiting_input)


async def process_input(message: types.Message, state: FSMContext):
    """Обработка ввода"""
    data = await state.get_data()
    # Логика
    await state.clear()
```

3. Зарегистрируйте в `main.py`:

```python
dp.message.register(handle_new_feature, F.text == "Кнопка")
dp.message.register(process_input, NewFeatureStates.waiting_input)
```

### Добавление таблицы в БД

1. Создайте миграцию в `migrations.py`:

```python
class Migration00X_NewTable(Migration):
    def __init__(self):
        super().__init__(X, "Add new_table")
    
    def up(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS new_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                data TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.commit()
    
    def down(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS new_table")
        conn.commit()
```

2. Добавьте методы в `database.py`:

```python
def add_new_data(self, user_id: int, data: str) -> int:
    conn = self.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO new_table (user_id, data)
        VALUES (?, ?)
    """, (user_id, data))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id
```

3. Примените миграцию:

```bash
python migrations.py --migrate
```

## 🐛 Отладка

### Логирование

Используйте логгер:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Запуск с отладкой

```bash
# Подробное логирование
python main.py --log-level DEBUG

# Просмотр логов
tail -f logs/dohot.log
```

## 📚 Документация

### Docstrings

Используйте Google Style:

```python
def function(arg1: int, arg2: str) -> bool:
    """
    Краткое описание функции.
    
    Более подробное описание, если необходимо.
    
    Args:
        arg1: Описание первого аргумента
        arg2: Описание второго аргумента
        
    Returns:
        Описание возвращаемого значения
        
    Raises:
        ValueError: Когда arg1 отрицательный
        
    Example:
        >>> function(5, "test")
        True
    """
    if arg1 < 0:
        raise ValueError("arg1 must be positive")
    return True
```

### Обновление документации

При добавлении функции обновите:
- `README.md` - если это основная функция
- `USAGE.md` - примеры использования
- `INSTALL.md` - если меняется установка
- Docstrings в коде

## ❓ Вопросы

Есть вопросы? Создайте Issue с тегом `question` или напишите в:
- Issues: для обсуждения проблем и предложений
- Discussions: для общих вопросов

## 📜 Лицензия

Внося вклад в проект, вы соглашаетесь с тем, что ваш код будет лицензирован под MIT License.

## 🎉 Благодарности

Спасибо всем, кто вносит вклад в DoHot! Ваша помощь делает проект лучше.

---

**Помните:** Любой вклад ценен - от исправления опечатки до реализации новой функции! 💪
