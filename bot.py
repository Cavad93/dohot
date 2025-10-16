import asyncio
import logging
from datetime import datetime, date
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import Database
from calculations import FinancialCalculator
from visualization import ChartGenerator

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
db = Database()
scheduler = AsyncIOScheduler()
chart_gen = ChartGenerator()


# ==================== СОСТОЯНИЯ FSM ====================

class CreditStates(StatesGroup):
    waiting_bank_name = State()
    waiting_monthly_payment = State()
    waiting_total_months = State()
    waiting_interest_rate = State()
    waiting_remaining_debt = State()
    waiting_start_date = State()
    
    selecting_credit = State()
    entering_payment_amount = State()
    
    selecting_credit_for_early = State()
    entering_early_amount = State()
    selecting_early_type = State()
    
    selecting_credit_for_capabilities = State()
    selecting_capability = State()


class CreditCardStates(StatesGroup):
    waiting_card_name = State()
    waiting_bank_name = State()
    waiting_credit_limit = State()
    waiting_interest_rate = State()
    waiting_minimum_payment_percent = State()
    
    selecting_card_for_transaction = State()
    waiting_transaction_amount = State()
    waiting_transaction_notes = State()
    
    selecting_card_for_spending = State()
    waiting_spending_amount = State()
    waiting_spending_notes = State()


class DebtStates(StatesGroup):
    waiting_person_name = State()
    waiting_amount = State()
    waiting_type = State()
    waiting_description = State()
    
    # Для погашения долга
    selecting_debt_for_payment = State()


class CategoryStates(StatesGroup):
    waiting_name = State()
    waiting_type = State()


class IncomeStates(StatesGroup):
    waiting_amount = State()
    selecting_category = State()
    waiting_description = State()
    waiting_delete_id = State()

class ExpenseStates(StatesGroup):
    waiting_amount = State()
    selecting_category = State()
    waiting_description = State()
    waiting_delete_id = State()



class InvestmentStates(StatesGroup):
    waiting_asset_name = State()
    waiting_invested_amount = State()
    
    # Для обновления стоимости
    selecting_investment = State()
    waiting_new_value = State()


class SavingsStates(StatesGroup):
    waiting_amount = State()


class BudgetStates(StatesGroup):
    selecting_month = State()
    waiting_planned_income = State()
    waiting_planned_expenses = State()
    editing_credit_expenses = State()
    waiting_custom_expense_name = State()
    waiting_custom_expense_amount = State()
    waiting_notes = State()
    viewing_budget = State()
    selecting_budget_to_edit = State()
    
    # Новые состояния для работы с категориями
    selecting_income_categories = State()
    waiting_income_category_amount = State()
    selecting_expense_categories = State()
    waiting_expense_category_amount = State()
    editing_single_category = State()
    waiting_edited_category_amount = State()


# ==================== КЛАВИАТУРЫ ====================

def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton(text="💳 Кредиты"), KeyboardButton(text="💸 Долги")],
        [KeyboardButton(text="💰 Доходы"), KeyboardButton(text="🛒 Расходы")],
        [KeyboardButton(text="📊 Инвестиции"), KeyboardButton(text="🏦 Сбережения")],
        [KeyboardButton(text="📅 Бюджет"), KeyboardButton(text="📋 Отчёт")],
        [KeyboardButton(text="📈 График капитала"), KeyboardButton(text="⚙️ Категории")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_credit_menu_keyboard():
    keyboard = [
        [KeyboardButton(text="➕ Добавить кредит")],
        [KeyboardButton(text="📋 Мои кредиты"), KeyboardButton(text="💳 Внести платёж")],
        [KeyboardButton(text="💡 Рекомендации"), KeyboardButton(text="⚙️ Возможности кредитов")],
        [KeyboardButton(text="💰 Досрочное погашение")],
        [KeyboardButton(text="💳 Кредитные карты")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_credit_card_menu_keyboard():
    keyboard = [
        [KeyboardButton(text="➕ Добавить карту")],
        [KeyboardButton(text="📋 Мои карты")],
        [KeyboardButton(text="💰 Пополнить карту"), KeyboardButton(text="🛒 Потратить")],
        [KeyboardButton(text="📊 История операций")],
        [KeyboardButton(text="◀️ К кредитам"), KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_debt_menu_keyboard():
    keyboard = [
        [KeyboardButton(text="➕ Добавить долг")],
        [KeyboardButton(text="📋 Мои долги")],
        [KeyboardButton(text="✅ Погасить долг")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_income_expense_keyboard(income: bool = True):
    text = "доход" if income else "расход"
    plural = "доходы" if income else "расходы"
    keyboard = [
        [KeyboardButton(text=f"➕ Добавить {text}")],
        [KeyboardButton(text=f"📋 Мои {plural}")],
        [KeyboardButton(text=f"🗑 Удалить последний {text}")],
        [KeyboardButton(text=f"🗑 Удалить {text} по ID")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)



def get_investment_menu_keyboard():
    keyboard = [
        [KeyboardButton(text="➕ Добавить инвестицию")],
        [KeyboardButton(text="📋 Мои инвестиции")],
        [KeyboardButton(text="💹 Обновить стоимость")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_cancel_keyboard():
    keyboard = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_budget_menu_keyboard():
    keyboard = [
        [KeyboardButton(text="➕ Создать бюджет")],
        [KeyboardButton(text="📋 Мои бюджеты")],
        [KeyboardButton(text="📊 Прогноз на 6 месяцев")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
# ==================== ОБРАБОТЧИКИ КОМАНД ====================

async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    
    user = message.from_user
    db.add_user(user.id, user.username, user.first_name)
    
    await message.answer(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я помогу тебе вести домашнюю бухгалтерию:\n"
        "• Учёт кредитов и их погашение\n"
        "• Учёт долгов (взятых и выданных)\n"
        "• Учёт доходов и расходов\n"
        "• Учёт инвестиций\n"
        "• Учёт сбережений\n"
        "• Финансовая аналитика и отчёты\n"
        "• Рекомендации по досрочному погашению\n\n"
        "Выбери нужный раздел из меню ниже:",
        reply_markup=get_main_menu_keyboard()
    )


async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    await message.answer(
        "📖 Справка по боту DoHot\n\n"
        "💳 КРЕДИТЫ:\n"
        "• Добавление кредита с полными данными\n"
        "• Автоматические напоминания о платежах\n"
        "• Досрочное погашение (полное/частичное)\n"
        "• Кредитные каникулы\n"
        "• Рекомендации по оптимальному погашению\n\n"
        
        "💸 ДОЛГИ:\n"
        "• Учёт долгов взятых/выданных\n"
        "• Без процентов\n"
        "• Отслеживание статуса\n\n"
        
        "💰 ДОХОДЫ И РАСХОДЫ:\n"
        "• Учёт по категориям\n"
        "• Детальная аналитика\n\n"
        
        "📊 ИНВЕСТИЦИИ:\n"
        "• Учёт активов\n"
        "• Ручное обновление стоимости\n\n"
        
        "📈 АНАЛИТИКА:\n"
        "• График чистого капитала\n"
        "• Подробные финансовые отчёты\n"
        "• Рекомендации по оптимизации\n\n"
        
        "Все данные сохраняются в базе данных!"
    )


# ==================== ОБРАБОТЧИКИ МЕНЮ ====================

async def handle_main_menu(message: types.Message, state: FSMContext):
    """Обработчик кнопок главного меню"""
    await state.clear()
    
    if message.text == "💳 Кредиты":
        await message.answer(
            "💳 Управление кредитами\n\n"
            "Здесь вы можете:\n"
            "• Добавить новый кредит\n"
            "• Посмотреть список кредитов\n"
            "• Внести очередной платёж\n"
            "• Сделать досрочное погашение\n"
            "• Получить рекомендации\n"
            "• Настроить возможности кредита",
            reply_markup=get_credit_menu_keyboard()
        )
    
    elif message.text == "💸 Долги":
        await message.answer(
            "💸 Управление долгами\n\n"
            "Учёт долгов без процентов:\n"
            "• Взятых у людей\n"
            "• Выданных людям",
            reply_markup=get_debt_menu_keyboard()
        )
    
    elif message.text == "💰 Доходы":
        await message.answer(
            "💰 Управление доходами",
            reply_markup=get_income_expense_keyboard(income=True)
        )
    
    elif message.text == "🛒 Расходы":
        await message.answer(
            "🛒 Управление расходами",
            reply_markup=get_income_expense_keyboard(income=False)
        )
    
    elif message.text == "📊 Инвестиции":
        await message.answer(
            "📊 Управление инвестициями",
            reply_markup=get_investment_menu_keyboard()
        )
    
    elif message.text == "🏦 Сбережения":
        await message.answer(
            "🏦 Укажите текущую сумму сбережений:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(SavingsStates.waiting_amount)
    
    elif message.text == "📈 График капитала":
        await show_capital_chart(message)
    
    elif message.text == "📋 Отчёт":
        await show_financial_report(message)
    
    elif message.text == "📅 Бюджет":
        await message.answer(
            "📅 Планирование бюджета\n\n"
            "Здесь вы можете:\n"
            "• Создать бюджет на месяц\n"
            "• Посмотреть существующие бюджеты\n"
            "• Увидеть прогноз с учетом кредитов",
            reply_markup=get_budget_menu_keyboard()
        )
    
    elif message.text == "⚙️ Категории":
        await show_categories_menu(message)
    elif message.text == "🗑 Удалить последний доход":
        await handlers.handle_delete_last_income(message)
    elif message.text == "🗑 Удалить доход по ID":
        await handlers.handle_delete_income_by_id(message, state)
    elif message.text == "🗑 Удалить последний расход":
        await handlers.handle_delete_last_expense(message)
    elif message.text == "🗑 Удалить расход по ID":
        await handlers.handle_delete_expense_by_id(message, state)


# ==================== ОБРАБОТЧИКИ КРЕДИТОВ ====================

async def handle_add_credit(message: types.Message, state: FSMContext):
    """Начало добавления кредита"""
    await message.answer(
        "➕ Добавление нового кредита\n\n"
        "Введите название банка:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CreditStates.waiting_bank_name)


async def process_bank_name(message: types.Message, state: FSMContext):
    """Обработка названия банка"""
    if message.text == "❌ Отмена":
        await cancel_handler(message, state)
        return
    
    await state.update_data(bank_name=message.text)
    await message.answer("Введите ежемесячный платёж (в рублях):")
    await state.set_state(CreditStates.waiting_monthly_payment)


async def process_monthly_payment(message: types.Message, state: FSMContext):
    """Обработка ежемесячного платежа"""
    try:
        monthly_payment = float(message.text.replace(",", "."))
        await state.update_data(monthly_payment=monthly_payment)
        await message.answer("Введите срок кредита (в месяцах):")
        await state.set_state(CreditStates.waiting_total_months)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 15000 или 15000.50")


async def process_total_months(message: types.Message, state: FSMContext):
    """Обработка срока кредита"""
    try:
        total_months = int(message.text)
        await state.update_data(total_months=total_months)
        await message.answer("Введите процентную ставку (в процентах годовых):")
        await state.set_state(CreditStates.waiting_interest_rate)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите целое число, например: 36")


async def process_interest_rate(message: types.Message, state: FSMContext):
    """Обработка процентной ставки"""
    try:
        interest_rate = float(message.text.replace(",", "."))
        await state.update_data(interest_rate=interest_rate)
        await message.answer("Введите текущий остаток долга (в рублях):")
        await state.set_state(CreditStates.waiting_remaining_debt)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 12.5")


async def process_remaining_debt(message: types.Message, state: FSMContext):
    """Обработка остатка долга"""
    try:
        remaining_debt = float(message.text.replace(",", "."))
        await state.update_data(remaining_debt=remaining_debt)
        await message.answer(
            "Введите дату начала кредита в формате ДД.ММ.ГГГГ\n"
            "или отправьте '0' чтобы использовать сегодняшнюю дату:"
        )
        await state.set_state(CreditStates.waiting_start_date)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 500000")


async def process_start_date(message: types.Message, state: FSMContext):
    """Обработка даты начала и завершение добавления кредита"""
    data = await state.get_data()
    
    if message.text == "0":
        start_date = date.today().isoformat()
    else:
        try:
            start_date = datetime.strptime(message.text, "%d.%m.%Y").date().isoformat()
        except ValueError:
            await message.answer("❌ Неверный формат даты! Используйте ДД.ММ.ГГГГ, например: 15.01.2024")
            return
    
    # Добавляем кредит в базу
    credit_id = db.add_credit(
        user_id=message.from_user.id,
        bank_name=data['bank_name'],
        monthly_payment=data['monthly_payment'],
        total_months=data['total_months'],
        interest_rate=data['interest_rate'],
        remaining_debt=data['remaining_debt'],
        start_date=start_date
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ Кредит успешно добавлен!\n\n"
        f"🏦 Банк: {data['bank_name']}\n"
        f"💵 Ежемесячный платёж: {data['monthly_payment']:,.2f} руб.\n"
        f"📅 Срок: {data['total_months']} мес.\n"
        f"📈 Ставка: {data['interest_rate']}%\n"
        f"💰 Остаток долга: {data['remaining_debt']:,.2f} руб.",
        reply_markup=get_credit_menu_keyboard()
    )


async def show_user_credits(message: types.Message):
    """Показ списка кредитов пользователя"""
    credits = db.get_user_credits(message.from_user.id)
    
    if not credits:
        await message.answer(
            "У вас пока нет добавленных кредитов.\n"
            "Используйте кнопку '➕ Добавить кредит'",
            reply_markup=get_credit_menu_keyboard()
        )
        return
    
    text = "📋 Ваши кредиты:\n\n"
    
    for i, credit in enumerate(credits, 1):
        remaining = FinancialCalculator.calculate_remaining_months(credit)
        next_payment = FinancialCalculator.calculate_next_payment_date(credit)
        
        text += f"{i}. {credit['display_name']}\n"
        text += f"   💰 Остаток: {credit['remaining_debt']:,.2f} руб.\n"
        text += f"   💵 Платёж: {credit['monthly_payment']:,.2f} руб.\n"
        text += f"   📈 Ставка: {credit['interest_rate']}%\n"
        text += f"   ⏱ Осталось: {remaining} мес.\n"
        text += f"   📅 Следующий платёж: {next_payment.strftime('%d.%m.%Y')}\n\n"
    
    await message.answer(text, reply_markup=get_credit_menu_keyboard())


async def handle_credit_payment(message: types.Message, state: FSMContext):
    """Начало процесса внесения платежа"""
    credits = db.get_user_credits(message.from_user.id)
    
    if not credits:
        await message.answer(
            "У вас нет активных кредитов",
            reply_markup=get_credit_menu_keyboard()
        )
        return
    
    keyboard = []
    for credit in credits:
        keyboard.append([InlineKeyboardButton(
            text=f"{credit['display_name']} ({credit['monthly_payment']:.2f} руб.)",
            callback_data=f"pay_credit_{credit['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    await message.answer(
        "Выберите кредит для внесения платежа:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(CreditStates.selecting_credit_for_payment)


async def process_credit_payment_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора кредита для платежа"""
    if callback.data == "cancel":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer(
            "❌ Отменено",
            reply_markup=get_credit_menu_keyboard()
        )
        return
    
    credit_id = int(callback.data.split("_")[2])
    credit = db.get_credit_by_id(credit_id)
    
    keyboard = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_pay_{credit_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ]
    
    await callback.message.edit_text(
        f"Внесение платежа по кредиту:\n"
        f"🏦 {credit['display_name']}\n"
        f"💵 Сумма платежа: {credit['monthly_payment']:,.2f} руб.\n\n"
        f"Подтвердите операцию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.update_data(credit_id=credit_id)
    await state.set_state(CreditStates.confirming_payment)


async def confirm_credit_payment(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение и проведение платежа"""
    if callback.data == "cancel":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer(
            "❌ Отменено",
            reply_markup=get_credit_menu_keyboard()
        )
        return
    
    data = await state.get_data()
    credit_id = data['credit_id']
    credit = db.get_credit_by_id(credit_id)
    
    # Вносим платёж
    db.add_credit_payment(
        credit_id=credit_id,
        amount=credit['monthly_payment'],
        payment_type='regular'
    )
    
    # Получаем обновлённые данные
    credit = db.get_credit_by_id(credit_id)
    remaining = FinancialCalculator.calculate_remaining_months(credit)
    
    await callback.message.delete()
    await state.clear()
    
    if credit['is_active']:
        await callback.message.answer(
            f"✅ Платёж успешно внесён!\n\n"
            f"🏦 {credit['display_name']}\n"
            f"💰 Новый остаток долга: {credit['remaining_debt']:,.2f} руб.\n"
            f"⏱ Осталось месяцев: {remaining}",
            reply_markup=get_credit_menu_keyboard()
        )
    else:
        await callback.message.answer(
            f"🎉 Поздравляем! Кредит полностью погашен!\n\n"
            f"🏦 {credit['display_name']}\n"
            f"Вы закрыли этот кредит!",
            reply_markup=get_credit_menu_keyboard()
        )


async def show_credit_recommendations(message: types.Message):
    """Показ рекомендаций по досрочному погашению"""
    credits = db.get_user_credits(message.from_user.id)
    
    if not credits:
        await message.answer(
            "У вас нет активных кредитов",
            reply_markup=get_credit_menu_keyboard()
        )
        return
    
    recommendation = FinancialCalculator.recommend_early_payment_strategy(credits)
    
    await message.answer(
        f"🎯 Рекомендации по досрочному погашению\n\n"
        f"{recommendation['explanation']}\n\n"
        f"{recommendation['payment_type_explanation']}",
        reply_markup=get_credit_menu_keyboard()
    )


# ==================== ОТЧЁТЫ И ГРАФИКИ ====================

async def show_capital_chart(message: types.Message):
    """Генерация и отправка графика капитала"""
    user_id = message.from_user.id
    
    credits = db.get_user_credits(user_id)
    debts = db.get_user_debts(user_id)
    investments = db.get_user_investments(user_id)
    savings_data = db.get_latest_savings(user_id)
    
    savings = savings_data['amount'] if savings_data else 0
    
    net_worth = FinancialCalculator.calculate_net_worth(savings, credits, debts, investments)
    
    # Генерируем график
    chart_path = chart_gen.generate_capital_chart(net_worth)
    
    if chart_path:
        photo = types.FSInputFile(chart_path)
        await message.answer_photo(
            photo=photo,
            caption=f"📈 График вашего капитала\n\n"
                   f"Чистый капитал: {net_worth['net_worth']:,.2f} руб.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(
            "❌ Ошибка при создании графика",
            reply_markup=get_main_menu_keyboard()
        )


async def show_financial_report(message: types.Message):
    """Генерация и отправка подробного финансового отчёта"""
    report = FinancialCalculator.generate_financial_report(message.from_user.id, db)
    
    # Разбиваем отчёт на части если он слишком длинный
    max_length = 4000
    if len(report) > max_length:
        parts = [report[i:i+max_length] for i in range(0, len(report), max_length)]
        for part in parts:
            await message.answer(part)
    else:
        await message.answer(report)
    
    await message.answer(
        "Готово!",
        reply_markup=get_main_menu_keyboard()
    )


# ==================== НАПОМИНАНИЯ ====================

async def check_payment_reminders(bot: Bot):
    """Проверка и отправка напоминаний о платежах"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Получаем все активные кредиты
    cursor.execute("""
        SELECT c.*, u.user_id 
        FROM credits c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.is_active = 1
    """)
    
    columns = [description[0] for description in cursor.description]
    credits = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    today = date.today()
    
    for credit in credits:
        next_payment = FinancialCalculator.calculate_next_payment_date(credit)
        
        # Отправляем напоминание в день платежа
        if next_payment == today:
            try:
                await bot.send_message(
                    credit['user_id'],
                    f"🔔 Напоминание о платеже!\n\n"
                    f"Сегодня день платежа по кредиту:\n"
                    f"🏦 {credit['display_name']}\n"
                    f"💵 Сумма: {credit['monthly_payment']:,.2f} руб.\n\n"
                    f"Не забудьте внести платёж и отметить его в боте!"
                )
            except Exception as e:
                logger.error(f"Error sending reminder to user {credit['user_id']}: {e}")


# ==================== ВСПОМОГАТЕЛЬНЫЕ ОБРАБОТЧИКИ ====================

async def cancel_handler(message: types.Message, state: FSMContext):
    """Обработчик отмены операции"""
    await state.clear()
    await message.answer(
        "❌ Операция отменена",
        reply_markup=get_main_menu_keyboard()
    )


def get_categories_menu_keyboard():
    keyboard = [
        [KeyboardButton(text="➕ Категория дохода")],
        [KeyboardButton(text="➕ Категория расхода")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

async def show_categories_menu(message: types.Message):
    """Показ меню категорий"""
    await message.answer(
        "⚙️ Управление категориями\n\n"
        "Выберите, что добавить:",
        reply_markup=get_categories_menu_keyboard()
    )
