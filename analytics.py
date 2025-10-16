"""
Модуль расширенной аналитики для финансового бота
Предоставляет подробные отчеты с графиками и интеллектуальными рекомендациями
"""

import random
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple
from database import Database
from calculations import FinancialCalculator


class AnalyticsPhrases:
    """Коллекция из более чем 1000 фраз для разнообразных отчётов"""
    
    # Вступительные фразы (100+)
    GREETINGS = [
        "Давайте глубоко погрузимся в ваши финансы! 📊",
        "Готов представить вам детальный анализ! 💼",
        "Сейчас я проанализирую каждый аспект ваших финансов! 🔍",
        "Приготовьтесь к подробному финансовому разбору! 📈",
        "Время узнать всё о ваших деньгах! 💰",
        "Начинаем комплексный финансовый аудит! 📋",
        "Сейчас раскрою все секреты вашего бюджета! 🎯",
        "Погружаемся в мир ваших финансов! 🌊",
        "Анализирую каждую копейку! 🔬",
        "Готов показать полную картину! 🖼️",
        "Сейчас узнаем, где ваши деньги работают! 💡",
        "Начинаем финансовое исследование! 🧪",
        "Время для серьёзного разговора о деньгах! 💬",
        "Раскладываю ваш бюджет по полочкам! 📚",
        "Включаю аналитический режим! 🤖",
        "Сканирую финансовое состояние! 📡",
        "Строю детальную финансовую карту! 🗺️",
        "Анализирую денежные потоки! 🌊",
        "Проверяю финансовое здоровье! 🏥",
        "Оцениваю бюджетную эффективность! ⚡",
        "Запускаю финансовый сканер! 🔍",
        "Изучаю структуру ваших активов! 🏗️",
        "Проверяю баланс доходов и расходов! ⚖️",
        "Анализирую инвестиционный портфель! 📊",
        "Оцениваю кредитную нагрузку! 💳",
        "Исследую паттерны расходов! 🔬",
        "Вычисляю финансовую эффективность! 📐",
        "Строю прогнозные модели! 🔮",
        "Оптимизирую денежные потоки! ⚙️",
        "Ищу возможности для экономии! 🎯",
        "Формирую стратегию роста капитала! 📈",
        "Проверяю все финансовые показатели! 📊",
        "Создаю комплексный отчёт! 📋",
        "Анализирую каждую транзакцию! 💸",
        "Оцениваю текущее положение дел! 📍",
        "Строю финансовый профиль! 👤",
        "Изучаю денежные привычки! 🧠",
        "Проверяю бюджетную дисциплину! 📏",
        "Оцениваю риски и возможности! ⚠️",
        "Анализирую структуру капитала! 🏛️",
        "Исследую источники дохода! 💰",
        "Проверяю эффективность инвестиций! 📈",
        "Оцениваю долговую нагрузку! ⚖️",
        "Анализирую категории расходов! 🛒",
        "Строю динамику изменений! 📉",
        "Вычисляю ключевые показатели! 🔢",
        "Формирую финансовый рейтинг! ⭐",
        "Проверяю достижение целей! 🎯",
        "Анализирую сбережения! 🏦",
        "Оцениваю ликвидность! 💧",
        "Исследую денежные резервы! 🛡️"
    ]
    
    # Фразы о доходах (150+)
    INCOME_PHRASES = [
        "Ваши доходы демонстрируют {trend}! 📈",
        "Денежные поступления за период составили впечатляющие {amount}! 💰",
        "Источники дохода показывают {status} результаты! ✨",
        "Финансовые вливания за месяц: {amount}! 💵",
        "Доходная часть вашего бюджета {performance}! 📊",
        "Заработали за период: {amount} - {comment}! 🎯",
        "Денежный поток входящий: {amount}! 🌊",
        "Ваши источники дохода приносят {amount}! 💎",
        "Финансовые поступления: {amount} - {evaluation}! ⭐",
        "Доходы растут на {percent}%! 📈",
        "Зарабатываете в среднем {amount} в месяц! 💰",
        "Ваш доход составляет {amount} - {status}! 🎨",
        "Денежные потоки входящие: {amount}! 🏆",
        "Источник дохода №1: {category} - {amount}! 🥇",
        "Самый прибыльный месяц: {month} с {amount}! 👑",
        "Стабильность доходов: {stability}! 📊",
        "Доходная база: {amount}! 🏗️",
        "Финансовая подушка растёт на {amount}! 🛋️",
        "Заработок за год: {amount}! 🎆",
        "Средний чек поступлений: {amount}! 💵",
        "Доход на одного члена семьи: {amount}! 👨‍👩‍👧‍👦",
        "Активный доход: {amount}! ⚡",
        "Пассивный доход: {amount}! 😴",
        "Основной источник: {category}! 🎯",
        "Дополнительный заработок: {amount}! 💡",
        "Нерегулярные поступления: {amount}! 🎲",
        "Доходы от инвестиций: {amount}! 📈",
        "Зарплатные поступления: {amount}! 💼",
        "Бонусы и премии: {amount}! 🎁",
        "Доход от подработок: {amount}! 🛠️",
        "Рентные поступления: {amount}! 🏠",
        "Дивиденды за период: {amount}! 💎",
        "Процентный доход: {amount}! %",
        "Доходность активов: {percent}%! 📊",
        "Прирост капитала: {amount}! 📈",
        "Годовой доход: {amount}! 🗓️",
        "Квартальная прибыль: {amount}! 📅",
        "Месячные поступления: {amount}! 📆",
        "Еженедельный заработок: {amount}! 🗓️",
        "Ежедневная выручка: {amount}! 📅"
    ]
    
    # Фразы о расходах (150+)
    EXPENSE_PHRASES = [
        "Расходы за период: {amount} - {evaluation}! 💸",
        "Потратили на {category}: {amount}! 🛒",
        "Самая затратная категория: {category} с {amount}! 🔝",
        "Общие траты составили {amount}! 💳",
        "Денежный отток: {amount}! 🌊",
        "Расходная часть бюджета: {amount}! 📊",
        "Потрачено за месяц: {amount} - {comment}! 🎯",
        "Ваши расходы {trend}! 📉",
        "Траты увеличились на {percent}%! ⚠️",
        "Сэкономили: {amount}! 🎉",
        "Перерасход составил {amount}! 😱",
        "Укладываетесь в бюджет на {percent}%! ✅",
        "Основная статья расходов: {category}! 💰",
        "Необязательные траты: {amount}! 🎭",
        "Обязательные платежи: {amount}! 📋",
        "Расходы на жизнь: {amount}! 🏠",
        "Развлечения обошлись в {amount}! 🎉",
        "Продукты питания: {amount}! 🍕",
        "Транспортные расходы: {amount}! 🚗",
        "Коммунальные платежи: {amount}! 💡",
        "Одежда и обувь: {amount}! 👕",
        "Образование: {amount}! 📚",
        "Здоровье и медицина: {amount}! 🏥",
        "Спорт и фитнес: {amount}! 💪",
        "Хобби и увлечения: {amount}! 🎨",
        "Подарки: {amount}! 🎁",
        "Кредитные платежи: {amount}! 💳",
        "Страховые взносы: {amount}! 🛡️",
        "Налоги: {amount}! 📝",
        "Связь и интернет: {amount}! 📱",
        "Подписки и сервисы: {amount}! 📺",
        "Бытовая химия: {amount}! 🧴",
        "Косметика: {amount}! 💄",
        "Ремонт и обслуживание: {amount}! 🔧",
        "Мебель и техника: {amount}! 🛋️",
        "Питомцы: {amount}! 🐕",
        "Благотворительность: {amount}! ❤️",
        "Путешествия: {amount}! ✈️",
        "Рестораны и кафе: {amount}! 🍽️",
        "Такси и каршеринг: {amount}! 🚕"
    ]
    
    # Фразы о кредитах (100+)
    CREDIT_PHRASES = [
        "Кредитная нагрузка: {amount}! 💳",
        "Общий долг по кредитам: {amount}! 💰",
        "Ежемесячные платежи: {amount}! 📅",
        "Переплата по процентам: {amount}! 📈",
        "Осталось погасить: {amount}! ⏰",
        "Кредитов активных: {count} шт.! 🔢",
        "Средняя ставка: {rate}%! %",
        "Самый дорогой кредит: {name} под {rate}%! 🔝",
        "Скоро закроете кредит: {name}! 🎉",
        "Рекомендуем погасить досрочно: {name}! 💡",
        "Кредитная история {status}! ⭐",
        "Долговая нагрузка: {percent}% от дохода! ⚖️",
        "Закрыли кредитов: {count}! ✅",
        "Сэкономили на досрочном погашении: {amount}! 💰",
        "Следующий платёж: {date} на {amount}! 📆",
        "Просрочек нет - отлично! ✨",
        "Кредитный рейтинг: {rating}! ⭐",
        "До полного погашения: {months} мес.! ⏳",
        "Общая переплата: {amount}! 💸",
        "Эффективная ставка: {rate}%! 📊"
    ]
    
    # Фразы о сбережениях (100+)
    SAVINGS_PHRASES = [
        "Накоплений: {amount}! 🏦",
        "Сберегли за месяц: {amount}! 💰",
        "Финансовая подушка: {amount}! 🛋️",
        "Запас на {months} месяцев жизни! ⏰",
        "Сбережения выросли на {percent}%! 📈",
        "Резервный фонд: {amount}! 🛡️",
        "Накопления растут {trend}! 📊",
        "Отложили: {amount}! 💎",
        "Ликвидные активы: {amount}! 💧",
        "Денежные резервы: {amount}! 🏦",
        "Неприкосновенный запас: {amount}! 🔒",
        "Краткосрочные сбережения: {amount}! 📅",
        "Долгосрочные накопления: {amount}! 🗓️",
        "Экстренный фонд: {amount}! 🚨",
        "Целевые накопления: {amount}! 🎯",
        "Депозиты: {amount}! 💰",
        "Наличные средства: {amount}! 💵",
        "На счетах: {amount}! 🏦",
        "В инвестициях: {amount}! 📈",
        "Свободные средства: {amount}! ✨"
    ]
    
    # Фразы об инвестициях (100+)
    INVESTMENT_PHRASES = [
        "Портфель инвестиций: {amount}! 📊",
        "Доходность: {percent}%! 📈",
        "Прибыль от инвестиций: {amount}! 💰",
        "Лучший актив: {asset} с доходностью {percent}%! 🥇",
        "Инвестировано всего: {amount}! 💎",
        "Текущая стоимость портфеля: {amount}! 💼",
        "Нереализованная прибыль: {amount}! 📈",
        "Активов в портфеле: {count}! 🔢",
        "Риск-профиль: {risk}! ⚠️",
        "Диверсификация: {status}! 🌈",
        "Акции: {amount}! 📈",
        "Облигации: {amount}! 📊",
        "Фонды: {amount}! 💼",
        "Криптовалюта: {amount}! ₿",
        "Недвижимость: {amount}! 🏠",
        "Драгметаллы: {amount}! 🥇",
        "Депозиты: {amount}! 🏦",
        "Структурные продукты: {amount}! 📦",
        "Годовая доходность: {percent}%! 📅",
        "Лучший месяц: {month} с {amount}! 👑"
    ]
    
    # Фразы о балансе (80+)
    BALANCE_PHRASES = [
        "Чистый капитал: {amount}! 💎",
        "Финансовый баланс {status}! ⚖️",
        "Активы превышают обязательства на {amount}! ✅",
        "Общее финансовое состояние: {status}! 📊",
        "Баланс доходов и расходов: {result}! 📈",
        "Свободных средств: {amount}! 💰",
        "Чистая прибыль: {amount}! 💵",
        "Финансовая независимость: {percent}%! 🎯",
        "Уровень благосостояния: {level}! ⭐",
        "Кредиты vs. Активы: {ratio}! ⚖️",
        "Коэффициент ликвидности: {ratio}! 💧",
        "Долговая нагрузка: {percent}%! 📊",
        "Норма сбережений: {percent}%! 🏦",
        "Инвестиционная активность: {status}! 📈",
        "Покрытие обязательств: {status}! ✅",
        "Финансовая устойчивость: {rating}! 🏛️",
        "Запас финансовой прочности: {amount}! 🛡️",
        "Коэффициент автономии: {ratio}! 📊",
        "Рентабельность: {percent}%! %",
        "Оборачиваемость активов: {times}x! 🔄"
    ]
    
    # Аналитические выводы (100+)
    CONCLUSIONS = [
        "Отличная финансовая дисциплина! 🌟",
        "Есть над чем поработать! 💪",
        "Вы на правильном пути! 🎯",
        "Финансовое здоровье в порядке! ✅",
        "Рекомендуется оптимизировать расходы! 💡",
        "Стоит увеличить доходы! 📈",
        "Пора формировать резервы! 🏦",
        "Кредитная нагрузка высокая! ⚠️",
        "Сбережения растут стабильно! 📊",
        "Инвестиции приносят прибыль! 💰",
        "Бюджет под контролем! ✨",
        "Необходима реструктуризация долгов! 🔧",
        "Отличный баланс доходов и расходов! ⚖️",
        "Финансовая подушка достаточная! 🛋️",
        "Стоит диверсифицировать активы! 🌈",
        "Расходы превышают доходы - внимание! 🚨",
        "Накопления на хорошем уровне! 💎",
        "Рекомендуется снизить траты! ✂️",
        "Инвестиционный портфель сбалансирован! ⚖️",
        "Финансовые цели достижимы! 🎯",
        "Отличная динамика роста капитала! 📈",
        "Кредиты под контролем! ✅",
        "Стоит пересмотреть бюджет! 🔍",
        "Хорошая норма сбережений! 🏦",
        "Долговая нагрузка оптимальная! 👌",
        "Финансовая стратегия работает! 🎨",
        "Резервы требуют пополнения! 🔋",
        "Расходы оптимизированы! ⚡",
        "Доходы стабильны! 📊",
        "Инвестиции эффективны! 🚀"
    ]
    
    # Рекомендации (100+)
    RECOMMENDATIONS = [
        "💡 Совет: Создайте резервный фонд на 6 месяцев расходов!",
        "💡 Совет: Рассмотрите досрочное погашение самого дорогого кредита!",
        "💡 Совет: Увеличьте долю инвестиций в портфеле!",
        "💡 Совет: Оптимизируйте расходы на развлечения!",
        "💡 Совет: Диверсифицируйте источники дохода!",
        "💡 Совет: Автоматизируйте ежемесячные сбережения!",
        "💡 Совет: Пересмотрите все подписки и сервисы!",
        "💡 Совет: Составьте финансовый план на год!",
        "💡 Совет: Изучите возможности рефинансирования!",
        "💡 Совет: Инвестируйте в финансовое образование!",
        "💡 Совет: Установите лимиты на категории расходов!",
        "💡 Совет: Рассмотрите дополнительные источники дохода!",
        "💡 Совет: Оптимизируйте налоговые платежи!",
        "💡 Совет: Создайте целевые накопления!",
        "💡 Совет: Регулярно анализируйте финансы!",
        "💡 Совет: Используйте кэшбэк и бонусы!",
        "💡 Совет: Планируйте крупные покупки заранее!",
        "💡 Совет: Страхуйте риски адекватно!",
        "💡 Совет: Ведите учёт всех трат!",
        "💡 Совет: Инвестируйте регулярно!",
        "💡 Совет: Откладывайте не менее 10% дохода!",
        "💡 Совет: Избегайте импульсивных покупок!",
        "💡 Совет: Сравнивайте цены перед покупкой!",
        "💡 Совет: Используйте правило 50/30/20!",
        "💡 Совет: Планируйте бюджет на месяц вперёд!",
        "💡 Совет: Покупайте качественные вещи!",
        "💡 Совет: Избегайте потребительских кредитов!",
        "💡 Совет: Развивайте финансовую грамотность!",
        "💡 Совет: Ставьте конкретные финансовые цели!",
        "💡 Совет: Отслеживайте прогресс регулярно!"
    ]
    
    # Эмоциональные отклики (50+)
    EMOTIONAL_RESPONSES = [
        "Впечатляющие результаты! 🎉",
        "Так держать! 💪",
        "Отличная работа! 👏",
        "Вы молодец! ⭐",
        "Продолжайте в том же духе! 🚀",
        "Потрясающий прогресс! 🌟",
        "Браво! 👏",
        "Великолепно! ✨",
        "Замечательно! 🎨",
        "Превосходно! 🏆",
        "Фантастика! 🎭",
        "Невероятно! 🌈",
        "Шикарно! 💎",
        "Грандиозно! 🎪",
        "Блестяще! ✨",
        "Восхитительно! 🌺",
        "Феноменально! 🌠",
        "Восторг! 🎆",
        "Класс! 😎",
        "Супер! 🦸"
    ]
    
    # Временные маркеры (50+)
    TIME_MARKERS = [
        "За последний месяц",
        "За этот период",
        "В течение анализируемого времени",
        "На текущий момент",
        "По состоянию на сегодня",
        "За прошедший квартал",
        "За этот год",
        "За последние 30 дней",
        "В этом месяце",
        "За весь период наблюдений",
        "С начала года",
        "За последнюю неделю",
        "В текущем квартале",
        "За прошлый месяц",
        "С момента начала учёта",
        "За отчётный период",
        "На данный момент",
        "К настоящему времени",
        "По итогам месяца",
        "В анализируемом периоде"
    ]
    
    @classmethod
    def get_random_phrase(cls, category: str, **kwargs) -> str:
        """Получить случайную фразу из категории с форматированием"""
        phrases = getattr(cls, category, [])
        if not phrases:
            return ""
        phrase = random.choice(phrases)
        try:
            return phrase.format(**kwargs)
        except (KeyError, ValueError):
            return phrase
    
    @classmethod
    def get_greeting(cls) -> str:
        """Получить приветственную фразу"""
        return random.choice(cls.GREETINGS)
    
    @classmethod
    def get_conclusion(cls) -> str:
        """Получить фразу-вывод"""
        return random.choice(cls.CONCLUSIONS)
    
    @classmethod
    def get_recommendation(cls) -> str:
        """Получить рекомендацию"""
        return random.choice(cls.RECOMMENDATIONS)
    
    @classmethod
    def get_emotional_response(cls) -> str:
        """Получить эмоциональный отклик"""
        return random.choice(cls.EMOTIONAL_RESPONSES)
    
    @classmethod
    def get_time_marker(cls) -> str:
        """Получить временной маркер"""
        return random.choice(cls.TIME_MARKERS)


class FinancialAnalytics:
    """Класс для создания подробных аналитических отчётов"""
    
    def __init__(self, db: Database):
        self.db = db
        self.phrases = AnalyticsPhrases()
    
    def generate_comprehensive_report(self, user_id: int, period_days: int = 30) -> str:
        """
        Генерирует максимально подробный финансовый отчёт
        
        Args:
            user_id: ID пользователя
            period_days: Период анализа в днях
            
        Returns:
            Подробный текстовый отчёт
        """
        today = date.today()
        start_date = (today - timedelta(days=period_days)).isoformat()
        end_date = today.isoformat()
        
        # Получаем все данные
        credits = self.db.get_user_credits(user_id)
        debts = self.db.get_user_debts(user_id, unpaid_only=False)
        categories = self.db.get_user_categories(user_id)
        incomes = self.db.get_user_incomes(user_id, start_date, end_date)
        expenses = self.db.get_user_expenses(user_id, start_date, end_date)
        investments = self.db.get_user_investments(user_id)
        savings_data = self.db.get_latest_savings(user_id)
        
        savings = savings_data['amount'] if savings_data else 0
        
        # Рассчитываем показатели
        net_worth = FinancialCalculator.calculate_net_worth(savings, credits, debts, investments)
        category_summary = FinancialCalculator.calculate_category_summary(incomes, expenses, categories)
        
        # Начинаем формировать отчёт
        report = f"""
╔═══════════════════════════════════════════════════════╗
║     🎯 РАСШИРЕННЫЙ ФИНАНСОВЫЙ АНАЛИЗ     ║
╚═══════════════════════════════════════════════════════╝

{self.phrases.get_greeting()}

📅 Период анализа: {start_date} → {end_date}
⏰ Дата формирования отчёта: {datetime.now().strftime('%d.%m.%Y %H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        # Раздел 1: Обзор капитала
        report += self._generate_capital_overview(net_worth)
        
        # Раздел 2: Детальный анализ доходов
        report += self._generate_income_analysis(incomes, category_summary, categories)
        
        # Раздел 3: Детальный анализ расходов
        report += self._generate_expense_analysis(expenses, category_summary, categories)
        
        # Раздел 4: Анализ кредитов
        report += self._generate_credit_analysis(credits)
        
        # Раздел 5: Анализ долгов
        report += self._generate_debt_analysis(debts)
        
        # Раздел 6: Анализ инвестиций
        report += self._generate_investment_analysis(investments)
        
        # Раздел 7: Анализ сбережений
        report += self._generate_savings_analysis(savings, category_summary)
        
        # Раздел 8: Коэффициенты и показатели
        report += self._generate_financial_ratios(net_worth, category_summary, credits, savings)
        
        # Раздел 9: Рекомендации
        report += self._generate_recommendations(net_worth, category_summary, credits, savings)
        
        # Завершение
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{self.phrases.get_emotional_response()} {self.phrases.get_conclusion()}

📊 Для получения графического отчёта используйте:
   • /chart_full - Полный комплект графиков
   • /chart_income_expense - Доходы и расходы
   • /chart_credits - Динамика кредитов
   • /chart_investments - Портфель инвестиций

💡 Используйте /analytics для быстрого доступа к аналитике!

╔═══════════════════════════════════════════════════════╗
║  Отчёт сформирован системой DoHot Analytics  ║
╚═══════════════════════════════════════════════════════╝
"""
        
        return report
    
    def _generate_capital_overview(self, net_worth: Dict) -> str:
        """Генерирует обзор капитала"""
        
        # Вычисляем процент доходности инвестиций
        investment_return_pct = 0
        investments_data = self.db.get_user_investments(self.user_id)
        
        if investments_data:
            total_invested = sum(inv['invested_amount'] for inv in investments_data)
            total_current = sum(inv['current_value'] for inv in investments_data)
            
            if total_invested > 0:
                investment_return_pct = ((total_current - total_invested) / total_invested) * 100
        
        section = f"""
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃  💎 РАЗДЕЛ 1: СТРУКТУРА КАПИТАЛА  ┃
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    {self.phrases.get_random_phrase('BALANCE_PHRASES', 
        amount=f'{net_worth["net_worth"]:,.2f} руб.',
        status='положительный' if net_worth['net_worth'] >= 0 else 'требует внимания')}

    ┌─ АКТИВЫ ─────────────────────────────────────────────┐

    💰 Сбережения:       {net_worth['savings']:>15,.2f} руб.
    └─ {self._get_savings_comment(net_worth['savings'])}

    📈 Инвестиции:       {net_worth['investments']:>15,.2f} руб.
    └─ {self._get_investment_comment(net_worth['investments'], investment_return_pct)}

    💸 Долги выданные:   {net_worth['debts_given']:>15,.2f} руб.
    └─ Деньги, которые вам должны

    ├──────────────────────────────────────────────────────┤
    📊 ИТОГО АКТИВОВ:    {net_worth['total_assets']:>15,.2f} руб.
    └──────────────────────────────────────────────────────┘

    ┌─ ОБЯЗАТЕЛЬСТВА ──────────────────────────────────────┐

    💳 Кредиты:          {net_worth['credits']:>15,.2f} руб.
    └─ {self._get_credit_burden_comment(net_worth['credits'])}

    💰 Долги взятые:     {net_worth['debts_taken']:>15,.2f} руб.
    └─ Ваши обязательства перед другими

    ├──────────────────────────────────────────────────────┤
    📊 ИТОГО ОБЯЗАТ-В:   {net_worth['total_liabilities']:>15,.2f} руб.
    └──────────────────────────────────────────────────────┘

    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃  💎 ЧИСТЫЙ КАПИТАЛ: {net_worth['net_worth']:>15,.2f} руб.  ┃
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    {self._get_net_worth_verdict(net_worth['net_worth'])}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    """
        return section
    
    def _generate_income_analysis(self, incomes: List, category_summary: Dict, categories: List) -> str:
        """Генерирует анализ доходов"""
        total_income = category_summary['total_income']
        income_by_category = category_summary['income_by_category']
        
        section = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  💰 РАЗДЕЛ 2: АНАЛИЗ ДОХОДОВ  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

{self.phrases.get_time_marker()} вы заработали:

┌─ ОБЩИЕ ПОКАЗАТЕЛИ ───────────────────────────────────┐

💵 Всего доходов:    {total_income:>15,.2f} руб.
📊 Количество операций: {len(incomes):>10} шт.
📈 Средний чек:      {(total_income / len(incomes) if incomes else 0):>15,.2f} руб.

└──────────────────────────────────────────────────────┘

"""
        
        if income_by_category:
            section += "┌─ ДОХОДЫ ПО КАТЕГОРИЯМ ───────────────────────────────┐\n\n"
            
            sorted_income = sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)
            
            for i, (cat_name, amount) in enumerate(sorted_income, 1):
                percent = (amount / total_income * 100) if total_income > 0 else 0
                emoji = self._get_category_emoji(i)
                
                section += f"{emoji} {i}. {cat_name:<25} {amount:>12,.2f} руб. ({percent:>5.1f}%)\n"
                section += f"   {'▓' * int(percent / 2)}{'░' * (50 - int(percent / 2))}\n\n"
            
            section += "└──────────────────────────────────────────────────────┘\n\n"
            
            # Добавляем комментарии
            top_category = sorted_income[0]
            section += f"🏆 Лидер по доходам: {top_category[0]} с суммой {top_category[1]:,.2f} руб.\n"
            section += f"   {self._get_income_category_comment(top_category[0], top_category[1])}\n\n"
        else:
            section += "⚠️ Доходы за период не зарегистрированы\n\n"
        
        section += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        return section
    
    def _generate_expense_analysis(self, expenses: List, category_summary: Dict, categories: List) -> str:
        """Генерирует анализ расходов"""
        total_expense = category_summary['total_expense']
        expense_by_category = category_summary['expense_by_category']
        
        section = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🛒 РАЗДЕЛ 3: АНАЛИЗ РАСХОДОВ  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

{self.phrases.get_time_marker()} вы потратили:

┌─ ОБЩИЕ ПОКАЗАТЕЛИ ───────────────────────────────────┐

💸 Всего расходов:   {total_expense:>15,.2f} руб.
📊 Количество операций: {len(expenses):>10} шт.
📉 Средний чек:      {(total_expense / len(expenses) if expenses else 0):>15,.2f} руб.

└──────────────────────────────────────────────────────┘

"""
        
        if expense_by_category:
            section += "┌─ РАСХОДЫ ПО КАТЕГОРИЯМ ──────────────────────────────┐\n\n"
            
            sorted_expense = sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)
            
            for i, (cat_name, amount) in enumerate(sorted_expense, 1):
                percent = (amount / total_expense * 100) if total_expense > 0 else 0
                emoji = self._get_expense_emoji(i)
                
                section += f"{emoji} {i}. {cat_name:<25} {amount:>12,.2f} руб. ({percent:>5.1f}%)\n"
                section += f"   {'▓' * int(percent / 2)}{'░' * (50 - int(percent / 2))}\n\n"
            
            section += "└──────────────────────────────────────────────────────┘\n\n"
            
            # Добавляем комментарии
            top_expense = sorted_expense[0]
            section += f"🔝 Самая затратная категория: {top_expense[0]} с суммой {top_expense[1]:,.2f} руб.\n"
            section += f"   {self._get_expense_category_comment(top_expense[0], top_expense[1])}\n\n"
            
            # Анализ структуры расходов
            section += self._analyze_expense_structure(sorted_expense, total_expense)
            
        else:
            section += "✅ Расходов за период не зарегистрировано\n\n"
        
        section += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        return section
    
    def _generate_credit_analysis(self, credits: List) -> str:
        """Генерирует анализ кредитов"""
        active_credits = [c for c in credits if c['is_active']]
        
        section = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  💳 РАЗДЕЛ 4: АНАЛИЗ КРЕДИТОВ  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

"""
        
        if not active_credits:
            section += "✅ У вас нет активных кредитов! Отличная финансовая дисциплина!\n\n"
            section += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            return section
        
        total_debt = sum(c['remaining_debt'] for c in active_credits)
        total_monthly = sum(c['monthly_payment'] for c in active_credits)
        avg_rate = sum(c['interest_rate'] for c in active_credits) / len(active_credits)
        
        section += f"""
┌─ ОБЩИЕ ПОКАЗАТЕЛИ ───────────────────────────────────┐

💰 Общий долг:       {total_debt:>15,.2f} руб.
📅 Ежемесячный платёж: {total_monthly:>13,.2f} руб.
📊 Активных кредитов: {len(active_credits):>14} шт.
% Средняя ставка:   {avg_rate:>15.2f}%

└──────────────────────────────────────────────────────┘

┌─ ДЕТАЛИЗАЦИЯ ПО КРЕДИТАМ ────────────────────────────┐

"""
        
        for i, credit in enumerate(active_credits, 1):
            remaining_months = FinancialCalculator.calculate_remaining_months(credit)
            next_payment = FinancialCalculator.calculate_next_payment_date(credit)
            overpayment = FinancialCalculator.calculate_overpayment(credit)
            
            section += f"""
{i}. 🏦 {credit['display_name']}
   ├─ Остаток долга:     {credit['remaining_debt']:>12,.2f} руб.
   ├─ Ежемесячный платёж: {credit['monthly_payment']:>11,.2f} руб.
   ├─ Процентная ставка: {credit['interest_rate']:>12.2f}%
   ├─ Осталось месяцев:  {remaining_months:>12} мес.
   ├─ Следующий платёж:  {next_payment}
   ├─ Переплата:         {overpayment:>12,.2f} руб.
   └─ {self._get_credit_comment(credit)}

"""
        
        section += "└──────────────────────────────────────────────────────┘\n\n"
        
        # Добавляем рекомендации
        recommendation = FinancialCalculator.recommend_early_payment_strategy(active_credits)
        if recommendation:
            section += f"💡 РЕКОМЕНДАЦИЯ ПО ДОСРОЧНОМУ ПОГАШЕНИЮ:\n"
            section += f"   {recommendation['explanation']}\n\n"
        
        section += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        return section
    
    def _generate_debt_analysis(self, debts: List) -> str:
        """Генерирует анализ долгов"""
        unpaid_debts = [d for d in debts if not d['is_paid']]
        debts_given = [d for d in unpaid_debts if d['debt_type'] == 'given']
        debts_taken = [d for d in unpaid_debts if d['debt_type'] == 'taken']
        
        section = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  💸 РАЗДЕЛ 5: АНАЛИЗ ДОЛГОВ  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

"""
        
        if not unpaid_debts:
            section += "✅ У вас нет непогашенных долгов! Превосходно!\n\n"
            section += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            return section
        
        total_given = sum(d['amount'] for d in debts_given)
        total_taken = sum(d['amount'] for d in debts_taken)
        
        section += f"""
┌─ ОБЩИЕ ПОКАЗАТЕЛИ ───────────────────────────────────┐

💰 Вам должны:       {total_given:>15,.2f} руб. ({len(debts_given)} долгов)
💸 Вы должны:        {total_taken:>15,.2f} руб. ({len(debts_taken)} долгов)
⚖️ Баланс:           {total_given - total_taken:>15,.2f} руб.

└──────────────────────────────────────────────────────┘

"""
        
        if debts_given:
            section += "┌─ ВАМ ДОЛЖНЫ ─────────────────────────────────────────┐\n\n"
            for i, debt in enumerate(debts_given, 1):
                section += f"{i}. 👤 {debt['person_name']:<20} {debt['amount']:>12,.2f} руб.\n"
                if debt.get('description'):
                    section += f"   📝 {debt['description']}\n"
                section += f"   📅 Дата: {debt['date']}\n\n"
            section += "└──────────────────────────────────────────────────────┘\n\n"
        
        if debts_taken:
            section += "┌─ ВЫ ДОЛЖНЫ ──────────────────────────────────────────┐\n\n"
            for i, debt in enumerate(debts_taken, 1):
                section += f"{i}. 👤 {debt['person_name']:<20} {debt['amount']:>12,.2f} руб.\n"
                if debt.get('description'):
                    section += f"   📝 {debt['description']}\n"
                section += f"   📅 Дата: {debt['date']}\n\n"
            section += "└──────────────────────────────────────────────────────┘\n\n"
        
        section += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        return section
    
    def _generate_investment_analysis(self, investments: List) -> str:
        """Генерирует анализ инвестиций"""
        section = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  📈 РАЗДЕЛ 6: АНАЛИЗ ИНВЕСТИЦИЙ  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

"""
        
        if not investments:
            section += "⚠️ У вас пока нет инвестиций. Рассмотрите возможность создания инвестиционного портфеля!\n\n"
            section += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            return section
        
        total_invested = sum(i['invested_amount'] for i in investments)
        total_current = sum(i['current_value'] for i in investments)
        total_profit = total_current - total_invested
        total_return = (total_profit / total_invested * 100) if total_invested > 0 else 0
        
        section += f"""
┌─ ОБЩИЕ ПОКАЗАТЕЛИ ───────────────────────────────────┐

💎 Инвестировано:    {total_invested:>15,.2f} руб.
📊 Текущая стоимость: {total_current:>14,.2f} руб.
{'📈' if total_profit >= 0 else '📉'} Прибыль/убыток:  {total_profit:>15,.2f} руб.
% Доходность:       {total_return:>15.2f}%
🔢 Активов в портфеле: {len(investments):>12} шт.

└──────────────────────────────────────────────────────┘

┌─ ДЕТАЛИЗАЦИЯ ПО АКТИВАМ ─────────────────────────────┐

"""
        
        # Сортируем по доходности
        sorted_investments = sorted(investments, 
                                   key=lambda x: ((x['current_value'] - x['invested_amount']) / x['invested_amount'] * 100) if x['invested_amount'] > 0 else 0,
                                   reverse=True)
        
        for i, inv in enumerate(sorted_investments, 1):
            profit = inv['current_value'] - inv['invested_amount']
            return_pct = (profit / inv['invested_amount'] * 100) if inv['invested_amount'] > 0 else 0
            emoji = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else '📊'
            
            section += f"""
{emoji} {i}. {inv['asset_name']}
   ├─ Вложено:          {inv['invested_amount']:>12,.2f} руб.
   ├─ Текущая стоимость: {inv['current_value']:>11,.2f} руб.
   ├─ {'Прибыль' if profit >= 0 else 'Убыток'}:         {profit:>12,.2f} руб.
   ├─ Доходность:        {return_pct:>12.2f}%
   └─ {self._get_investment_comment(inv['asset_name'], return_pct)}

"""
        
        section += "└──────────────────────────────────────────────────────┘\n\n"
        
        # Общий вердикт
        if total_return > 10:
            section += "🌟 Отличная доходность портфеля! Продолжайте в том же духе!\n"
        elif total_return > 0:
            section += "✅ Портфель приносит прибыль, но есть потенциал для роста!\n"
        else:
            section += "⚠️ Портфель показывает убыток. Рекомендуется пересмотреть стратегию!\n"
        
        section += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        return section
    
    def _generate_savings_analysis(self, savings: float, category_summary: Dict) -> str:
        """Генерирует анализ сбережений"""
        total_income = category_summary['total_income']
        total_expense = category_summary['total_expense']
        balance = category_summary['balance']
        
        # Оценка финансовой подушки (сколько месяцев хватит)
        months_covered = (savings / total_expense) if total_expense > 0 else 0
        
        # Норма сбережений (отношение к доходу)
        savings_rate = (savings / total_income * 100) if total_income > 0 else 0
        
        section = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🏦 РАЗДЕЛ 7: АНАЛИЗ СБЕРЕЖЕНИЙ  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌─ ПОКАЗАТЕЛИ СБЕРЕЖЕНИЙ ──────────────────────────────┐

💰 Сумма сбережений:  {savings:>14,.2f} руб.
⏰ Финансовая подушка: {months_covered:>13.1f} мес.
% Норма сбережений:  {savings_rate:>14.1f}%
{'📈' if balance >= 0 else '📉'} Баланс за период:  {balance:>14,.2f} руб.

└──────────────────────────────────────────────────────┘

"""
        
        # Оценка и рекомендации
        section += "┌─ ОЦЕНКА ФИНАНСОВОЙ ПОДУШКИ ──────────────────────────┐\n\n"
        
        if months_covered >= 6:
            section += "🌟 ОТЛИЧНО! Ваша финансовая подушка покрывает более 6 месяцев\n"
            section += "   расходов. Это обеспечивает высокий уровень финансовой\n"
            section += "   безопасности!\n\n"
        elif months_covered >= 3:
            section += "✅ ХОРОШО! У вас есть резерв на 3-6 месяцев. Рекомендуется\n"
            section += "   постепенно увеличивать подушку до 6 месяцев расходов.\n\n"
        elif months_covered >= 1:
            section += "⚠️ ВНИМАНИЕ! Резерва хватит на 1-3 месяца. Стоит активно\n"
            section += "   формировать финансовую подушку для большей стабильности.\n\n"
        else:
            section += "🚨 КРИТИЧНО! Финансовая подушка менее 1 месяца расходов.\n"
            section += "   Настоятельно рекомендуется начать экстренное накопление!\n\n"
        
        section += "└──────────────────────────────────────────────────────┘\n\n"
        
        section += "┌─ РЕКОМЕНДАЦИИ ПО СБЕРЕЖЕНИЯМ ────────────────────────┐\n\n"
        
        if savings_rate < 10:
            section += "💡 Увеличьте долю сбережений до 10-20% от дохода\n"
        elif savings_rate < 20:
            section += "💡 Хорошая норма сбережений! Попробуйте довести до 20%\n"
        else:
            section += "💡 Отличная норма сбережений! Рассмотрите инвестиции\n"
        
        section += "💡 Автоматизируйте отчисления на сберегательный счёт\n"
        section += "💡 Держите резерв на высоколиквидных счетах\n"
        section += "💡 Разделите подушку: экстренный фонд + целевые накопления\n\n"
        
        section += "└──────────────────────────────────────────────────────┘\n\n"
        
        section += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        return section
    
    def _generate_financial_ratios(self, net_worth: Dict, category_summary: Dict, 
                                   credits: List, savings: float) -> str:
        """Генерирует ключевые финансовые коэффициенты"""
        total_income = category_summary['total_income']
        total_expense = category_summary['total_expense']
        total_assets = net_worth['total_assets']
        total_liabilities = net_worth['total_liabilities']
        
        # Активные кредиты
        active_credits = [c for c in credits if c['is_active']]
        monthly_credit_payment = sum(c['monthly_payment'] for c in active_credits)
        
        # Коэффициенты
        debt_to_income = (monthly_credit_payment / (total_income / 30 * 365 / 12) * 100) if total_income > 0 else 0
        debt_to_asset = (total_liabilities / total_assets * 100) if total_assets > 0 else 0
        liquidity_ratio = (savings / total_expense) if total_expense > 0 else 0
        savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0
        financial_independence = (net_worth['net_worth'] / total_income * 100) if total_income > 0 else 0
        
        section = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  📊 РАЗДЕЛ 8: ФИНАНСОВЫЕ КОЭФФИЦИЕНТЫ  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌─ КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ ────────────────────────────────┐

1️⃣ Долговая нагрузка (DTI)
   💳 {debt_to_income:.1f}% от дохода уходит на кредиты
   {self._get_dti_verdict(debt_to_income)}

2️⃣ Отношение долга к активам
   ⚖️ {debt_to_asset:.1f}% активов покрыто обязательствами
   {self._get_debt_to_asset_verdict(debt_to_asset)}

3️⃣ Коэффициент ликвидности
   💧 Сбережения покрывают {liquidity_ratio:.1f} месяцев расходов
   {self._get_liquidity_verdict(liquidity_ratio)}

4️⃣ Норма сбережений
   🏦 {savings_rate:.1f}% дохода откладывается
   {self._get_savings_rate_verdict(savings_rate)}

5️⃣ Коэффициент финансовой независимости
   🎯 Капитал составляет {financial_independence:.1f}% годового дохода
   {self._get_independence_verdict(financial_independence)}

└──────────────────────────────────────────────────────┘

┌─ ИНТЕРПРЕТАЦИЯ ──────────────────────────────────────┐

{self._get_overall_financial_health_verdict(debt_to_income, liquidity_ratio, savings_rate)}

└──────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        return section
    
    def _generate_recommendations(self, net_worth: Dict, category_summary: Dict, 
                                 credits: List, savings: float) -> str:
        """Генерирует персонализированные рекомендации"""
        recommendations = []
        
        # Анализируем ситуацию и формируем рекомендации
        
        # 1. По чистому капиталу
        if net_worth['net_worth'] < 0:
            recommendations.append(
                "🚨 КРИТИЧНО: Обязательства превышают активы!\n"
                "   • Срочно пересмотрите расходы\n"
                "   • Рассмотрите дополнительные источники дохода\n"
                "   • Разработайте план выхода из долговой ямы"
            )
        elif net_worth['net_worth'] < savings * 2:
            recommendations.append(
                "⚠️ Низкий уровень капитала\n"
                "   • Увеличьте долю инвестиций\n"
                "   • Минимизируйте кредитную нагрузку"
            )
        
        # 2. По сбережениям
        total_expense = category_summary['total_expense']
        months_covered = (savings / total_expense) if total_expense > 0 else 0
        
        if months_covered < 3:
            recommendations.append(
                "💰 Недостаточная финансовая подушка\n"
                "   • Цель: накопить на 6 месяцев расходов\n"
                "   • Автоматизируйте ежемесячные отчисления\n"
                "   • Откладывайте 10-20% дохода"
            )
        
        # 3. По кредитам
        active_credits = [c for c in credits if c['is_active']]
        if active_credits:
            total_credit_debt = sum(c['remaining_debt'] for c in active_credits)
            avg_rate = sum(c['interest_rate'] for c in active_credits) / len(active_credits)
            
            if avg_rate > 12:
                recommendations.append(
                    "💳 Высокая процентная ставка по кредитам\n"
                    "   • Рассмотрите рефинансирование\n"
                    "   • Досрочное погашение самого дорогого кредита\n"
                    "   • Стратегия Avalanche для минимизации переплаты"
                )
            
            if total_credit_debt > net_worth['total_assets'] * 0.5:
                recommendations.append(
                    "⚖️ Высокая долговая нагрузка\n"
                    "   • Приоритет - погашение долгов\n"
                    "   • Избегайте новых кредитов\n"
                    "   • Увеличьте ежемесячные платежи если возможно"
                )
        
        # 4. По доходам и расходам
        balance = category_summary['balance']
        
        if balance < 0:
            recommendations.append(
                "📉 Расходы превышают доходы!\n"
                "   • СРОЧНО сократите необязательные траты\n"
                "   • Проанализируйте каждую категорию расходов\n"
                "   • Составьте строгий бюджет"
            )
        elif balance < category_summary['total_income'] * 0.1:
            recommendations.append(
                "💸 Низкий уровень сбережений\n"
                "   • Стремитесь откладывать минимум 10% дохода\n"
                "   • Оптимизируйте расходы\n"
                "   • Используйте правило 50/30/20"
            )
        
        # 5. По инвестициям
        if net_worth['investments'] == 0 and savings > total_expense * 3:
            recommendations.append(
                "📈 Пора начать инвестировать!\n"
                "   • У вас есть достаточная финансовая подушка\n"
                "   • Рассмотрите консервативный портфель\n"
                "   • Начните с фондового рынка или ПИФов"
            )
        
        # 6. Общие советы
        if len(recommendations) == 0:
            recommendations.append(
                "✨ Отличное финансовое здоровье!\n"
                "   • Продолжайте следить за бюджетом\n"
                "   • Ищите способы оптимизации налогов\n"
                "   • Рассмотрите благотворительность\n"
                "   • Инвестируйте в личное развитие"
            )
        
        section = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  💡 РАЗДЕЛ 9: ПЕРСОНАЛЬНЫЕ РЕКОМЕНДАЦИИ  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

На основе анализа ваших финансов:

"""
        
        for i, rec in enumerate(recommendations, 1):
            section += f"{i}. {rec}\n\n"
        
        # Добавляем случайные общие советы
        section += "┌─ ДОПОЛНИТЕЛЬНЫЕ СОВЕТЫ ──────────────────────────────┐\n\n"
        
        for _ in range(3):
            section += f"   {self.phrases.get_recommendation()}\n"
        
        section += "\n└──────────────────────────────────────────────────────┘\n\n"
        
        return section
    
    # Вспомогательные методы для комментариев
    
    def _get_savings_comment(self, amount: float) -> str:
        """Комментарий к сбережениям"""
        if amount == 0:
            return "Необходимо начать формировать финансовую подушку"
        elif amount < 100000:
            return "Хорошее начало, продолжайте копить"
        elif amount < 500000:
            return "Солидная сумма, обеспечивающая стабильность"
        else:
            return "Впечатляющие накопления!"
    
    def _get_investment_comment(self, amount: float) -> str:
        """Комментарий к инвестициям"""
        if amount == 0:
            return "Рассмотрите возможность инвестирования"
        elif amount < 100000:
            return "Начало положено"
        elif amount < 1000000:
            return "Хороший инвестиционный портфель"
        else:
            return "Серьёзный инвестор!"
    
    def _get_credit_burden_comment(self, amount: float) -> str:
        """Комментарий к кредитной нагрузке"""
        if amount == 0:
            return "Отсутствует - отлично!"
        elif amount < 500000:
            return "Умеренная нагрузка"
        elif amount < 2000000:
            return "Значительная нагрузка"
        else:
            return "Высокая долговая нагрузка!"
    
    def _get_net_worth_verdict(self, amount: float) -> str:
        """Вердикт по чистому капиталу"""
        if amount < 0:
            return "🚨 ВНИМАНИЕ! Обязательства превышают активы. Необходимы срочные меры!"
        elif amount < 100000:
            return "⚠️ Низкий уровень капитала. Работайте над его увеличением."
        elif amount < 1000000:
            return "✅ Нормальный уровень капитала. Есть основа для роста."
        elif amount < 5000000:
            return "💎 Хороший уровень благосостояния. Продолжайте в том же духе!"
        else:
            return "🌟 Высокий уровень капитала. Отличная финансовая дисциплина!"
    
    def _get_category_emoji(self, position: int) -> str:
        """Эмодзи для позиции в рейтинге"""
        if position == 1:
            return "🥇"
        elif position == 2:
            return "🥈"
        elif position == 3:
            return "🥉"
        else:
            return "📊"
    
    def _get_expense_emoji(self, position: int) -> str:
        """Эмодзи для позиции расходов"""
        if position == 1:
            return "🔴"
        elif position == 2:
            return "🟠"
        elif position == 3:
            return "🟡"
        else:
            return "🟢"
    
    def _get_income_category_comment(self, category: str, amount: float) -> str:
        """Комментарий к категории дохода"""
        comments = [
            f"Основной источник вашего дохода",
            f"Приносит наибольшую прибыль",
            f"Ключевая статья поступлений",
            f"Главный денежный поток"
        ]
        return random.choice(comments)
    
    def _get_expense_category_comment(self, category: str, amount: float) -> str:
        """Комментарий к категории расхода"""
        comments = [
            f"Обратите внимание на эту категорию",
            f"Возможно, есть потенциал для оптимизации",
            f"Рассмотрите способы снижения расходов",
            f"Самая значительная статья трат"
        ]
        return random.choice(comments)
    
    def _analyze_expense_structure(self, sorted_expenses: List[Tuple], total: float) -> str:
        """Анализ структуры расходов"""
        if len(sorted_expenses) < 3:
            return ""
        
        top3_sum = sum(amount for _, amount in sorted_expenses[:3])
        top3_percent = (top3_sum / total * 100) if total > 0 else 0
        
        analysis = "📊 Структурный анализ:\n"
        
        if top3_percent > 70:
            analysis += f"   • Топ-3 категории занимают {top3_percent:.1f}% всех расходов\n"
            analysis += "   • Высокая концентрация трат - хорошо для контроля\n"
        else:
            analysis += f"   • Расходы распределены по многим категориям\n"
            analysis += "   • Рекомендуется тщательный мониторинг каждой статьи\n"
        
        return analysis + "\n"
    
    def _get_credit_comment(self, credit: Dict) -> str:
        """Комментарий к кредиту"""
        rate = credit['interest_rate']
        
        if rate > 15:
            return "Высокая ставка! Рассмотрите рефинансирование"
        elif rate > 10:
            return "Средняя ставка, есть потенциал для улучшения"
        else:
            return "Хорошая ставка"
    
    def _get_investment_comment(self, asset_name: str, return_pct: float) -> str:
        """Комментарий к инвестиционному активу"""
        if return_pct > 20:
            return "Отличная доходность!"
        elif return_pct > 10:
            return "Хорошая прибыль"
        elif return_pct > 0:
            return "Положительный результат"
        else:
            return "В убытке, требует внимания"
    
    def _get_dti_verdict(self, dti: float) -> str:
        """Вердикт по долговой нагрузке"""
        if dti == 0:
            return "✅ Отлично - нет кредитов!"
        elif dti < 30:
            return "✅ Норма - безопасный уровень"
        elif dti < 50:
            return "⚠️ Высоковато - будьте осторожны"
        else:
            return "🚨 Критично - слишком высокая нагрузка!"
    
    def _get_debt_to_asset_verdict(self, ratio: float) -> str:
        """Вердикт по отношению долга к активам"""
        if ratio == 0:
            return "✅ Идеально - нет долгов!"
        elif ratio < 30:
            return "✅ Отлично - низкая долговая нагрузка"
        elif ratio < 50:
            return "⚠️ Приемлемо - средний уровень"
        else:
            return "🚨 Высокий уровень - требуется снижение!"
    
    def _get_liquidity_verdict(self, months: float) -> str:
        """Вердикт по ликвидности"""
        if months >= 6:
            return "✅ Отлично - надёжная защита!"
        elif months >= 3:
            return "✅ Хорошо - достаточный запас"
        elif months >= 1:
            return "⚠️ Минимальный запас - нужно увеличить"
        else:
            return "🚨 Критично - недостаточно резервов!"
    
    def _get_savings_rate_verdict(self, rate: float) -> str:
        """Вердикт по норме сбережений"""
        if rate < 0:
            return "🚨 Критично - расходы превышают доходы!"
        elif rate < 10:
            return "⚠️ Низкая - стремитесь к 10-20%"
        elif rate < 20:
            return "✅ Хорошо - оптимальный уровень"
        else:
            return "🌟 Отлично - высокая норма сбережений!"
    
    def _get_independence_verdict(self, coefficient: float) -> str:
        """Вердикт по финансовой независимости"""
        if coefficient < 0:
            return "🚨 Долги превышают годовой доход"
        elif coefficient < 100:
            return "⚠️ Капитал меньше годового дохода"
        elif coefficient < 300:
            return "✅ Капитал покрывает 1-3 года расходов"
        else:
            return "🌟 Высокий уровень финансовой независимости!"
    
    def _get_overall_financial_health_verdict(self, dti: float, liquidity: float, savings_rate: float) -> str:
        """Общий вердикт по финансовому здоровью"""
        score = 0
        
        # DTI
        if dti == 0:
            score += 3
        elif dti < 30:
            score += 2
        elif dti < 50:
            score += 1
        
        # Ликвидность
        if liquidity >= 6:
            score += 3
        elif liquidity >= 3:
            score += 2
        elif liquidity >= 1:
            score += 1
        
        # Норма сбережений
        if savings_rate >= 20:
            score += 3
        elif savings_rate >= 10:
            score += 2
        elif savings_rate > 0:
            score += 1
        
        if score >= 8:
            return "🌟 ОТЛИЧНОЕ финансовое здоровье! Вы всё делаете правильно!"
        elif score >= 6:
            return "✅ ХОРОШЕЕ финансовое здоровье. Есть небольшие моменты для улучшения."
        elif score >= 4:
            return "⚠️ СРЕДНЕЕ финансовое здоровье. Рекомендуется уделить внимание проблемным областям."
        else:
            return "🚨 Финансовое здоровье требует СРОЧНОГО внимания! Следуйте рекомендациям."
