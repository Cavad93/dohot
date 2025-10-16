import logging
from aiogram import types, F, Router
from aiogram.filters import StateFilter 
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from datetime import datetime
import calendar
import sqlite3
import asyncio

logger = logging.getLogger(__name__)

from aiogram import Router
router = Router()

from database import Database
from calculations import FinancialCalculator
from bot import (
    DebtStates, CategoryStates, IncomeStates, ExpenseStates, 
    InvestmentStates, SavingsStates, CreditStates, BudgetStates,
    get_main_menu_keyboard, get_debt_menu_keyboard,
    get_income_expense_keyboard, get_investment_menu_keyboard,
    get_cancel_keyboard, get_credit_menu_keyboard, get_budget_menu_keyboard
)

db = Database()
# ==================== ОБРАБОТЧИКИ ДОЛГОВ ====================

async def handle_add_debt(message: types.Message, state: FSMContext):
    """Начало добавления долга"""
    await message.answer(
        "➕ Добавление нового долга\n\n"
        "Введите имя человека:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(DebtStates.waiting_person_name)


async def process_debt_person_name(message: types.Message, state: FSMContext):
    """Обработка имени человека для долга"""
    if message.text == "❌ Отмена":
        await cancel_handler(message, state)
        return
    
    await state.update_data(person_name=message.text)
    await message.answer("Введите сумму долга (в рублях):")
    await state.set_state(DebtStates.waiting_amount)


async def process_debt_amount(message: types.Message, state: FSMContext):
    """Обработка суммы долга"""
    try:
        amount = float(message.text.replace(",", "."))
        await state.update_data(amount=amount)
        
        keyboard = [
            [KeyboardButton(text="Я взял в долг")],
            [KeyboardButton(text="Я дал в долг")],
            [KeyboardButton(text="❌ Отмена")]
        ]
        markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        
        await message.answer(
            "Выберите тип долга:",
            reply_markup=markup
        )
        await state.set_state(DebtStates.waiting_type)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 5000 или 5000.50")


async def process_debt_type(message: types.Message, state: FSMContext):
    """Обработка типа долга"""
    if message.text == "❌ Отмена":
        await cancel_handler(message, state)
        return
    
    if message.text == "Я взял в долг":
        debt_type = "taken"
    elif message.text == "Я дал в долг":
        debt_type = "given"
    else:
        await message.answer("Пожалуйста, выберите один из вариантов с помощью кнопок")
        return
    
    await state.update_data(debt_type=debt_type)
    await message.answer(
        "Введите описание (необязательно) или отправьте '0' чтобы пропустить:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(DebtStates.waiting_description)


async def process_debt_description(message: types.Message, state: FSMContext):
    """Обработка описания долга и завершение добавления"""
    data = await state.get_data()
    
    description = None if message.text == "0" else message.text
    
    # Добавляем долг в базу
    db.add_debt(
        user_id=message.from_user.id,
        person_name=data['person_name'],
        amount=data['amount'],
        debt_type=data['debt_type'],
        description=description
    )
    
    await state.clear()
    
    debt_type_text = "взяли у" if data['debt_type'] == 'taken' else "дали"
    
    await message.answer(
        f"✅ Долг успешно добавлен!\n\n"
        f"👤 Вы {debt_type_text} {data['person_name']}\n"
        f"💰 Сумма: {data['amount']:,.2f} руб.\n"
        f"📝 Описание: {description or 'не указано'}",
        reply_markup=get_debt_menu_keyboard()
    )


async def show_user_debts(message: types.Message):
    """Показ списка долгов пользователя"""
    all_debts = db.get_user_debts(message.from_user.id, unpaid_only=False)
    
    if not all_debts:
        await message.answer(
            "У вас пока нет добавленных долгов.\n"
            "Используйте кнопку '➕ Добавить долг'",
            reply_markup=get_debt_menu_keyboard()
        )
        return
    
    active_debts = [d for d in all_debts if not d['is_paid']]
    paid_debts = [d for d in all_debts if d['is_paid']]
    
    text = "📋 Ваши долги:\n\n"
    
    if active_debts:
        text += "🔴 АКТИВНЫЕ:\n\n"
        for i, debt in enumerate(active_debts, 1):
            debt_type_text = "Взял у" if debt['debt_type'] == 'taken' else "Дал"
            text += f"{i}. {debt_type_text} {debt['person_name']}\n"
            text += f"   💰 Сумма: {debt['amount']:,.2f} руб.\n"
            text += f"   📅 Дата: {debt['date']}\n"
            if debt['description']:
                text += f"   📝 {debt['description']}\n"
            text += "\n"
    
    if paid_debts:
        text += "✅ ПОГАШЕННЫЕ:\n\n"
        for i, debt in enumerate(paid_debts, 1):
            debt_type_text = "Взял у" if debt['debt_type'] == 'taken' else "Дал"
            text += f"{i}. {debt_type_text} {debt['person_name']}: {debt['amount']:,.2f} руб.\n"
    
    await message.answer(text, reply_markup=get_debt_menu_keyboard())


async def handle_pay_debt(message: types.Message, state: FSMContext):
    """Начало процесса погашения долга"""
    debts = db.get_user_debts(message.from_user.id, unpaid_only=True)
    
    if not debts:
        await message.answer(
            "У вас нет активных долгов",
            reply_markup=get_debt_menu_keyboard()
        )
        return
    
    keyboard = []
    for debt in debts:
        debt_type_text = "Взял у" if debt['debt_type'] == 'taken' else "Дал"
        keyboard.append([InlineKeyboardButton(
            text=f"{debt_type_text} {debt['person_name']} ({debt['amount']:.2f} ₽)",
            callback_data=f"pay_debt_{debt['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    await message.answer(
        "Выберите долг для погашения:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(DebtStates.selecting_debt_for_payment)


async def process_debt_payment_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка погашения долга"""
    if callback.data == "cancel":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer(
            "❌ Отменено",
            reply_markup=get_debt_menu_keyboard()
        )
        return
    
    debt_id = int(callback.data.split("_")[2])
    
    # Помечаем долг как погашенный
    db.mark_debt_paid(debt_id)
    
    await callback.message.delete()
    await state.clear()
    
    await callback.message.answer(
        "✅ Долг успешно погашен!",
        reply_markup=get_debt_menu_keyboard()
    )


# ==================== ОБРАБОТЧИКИ КАТЕГОРИЙ ====================

async def handle_add_category(message: types.Message, state: FSMContext, cat_type: str):
    """Начало добавления категории"""
    type_text = "дохода" if cat_type == "income" else "расхода"
    await state.update_data(cat_type=cat_type)
    await message.answer(
        f"➕ Добавление категории {type_text}\n\n"
        f"Введите название категории:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CategoryStates.waiting_name)

# Обёртки под кнопки меню
async def start_add_income_category(message: types.Message, state: FSMContext):
    return await handle_add_category(message, state, "income")

async def start_add_expense_category(message: types.Message, state: FSMContext):
    return await handle_add_category(message, state, "expense")

async def show_user_expenses(message: types.Message):
    """Показ последних расходов пользователя"""
    user_id = message.from_user.id
    expenses = db.get_user_expenses(user_id=user_id)

    if not expenses:
        await message.answer("Пока расходов нет.", reply_markup=get_income_expense_keyboard(income=False))
        return

    # подтянем имена категорий
    cats = {c["id"]: c["name"] for c in db.get_user_categories(user_id, cat_type="expense")}
    lines = []
    for row in expenses[:10]:  # покажем последние 10
        dt = row.get("date") or row.get("created_at")
        amount = row["amount"]
        cat_name = cats.get(row.get("category_id"), "Без категории")
        desc = row.get("description") or ""
        lines.append(f"• {dt} — {amount:,.2f} ₽ — {cat_name}{' — '+desc if desc else ''}")

    text = "📋 Мои расходы (последние):\n\n" + "\n".join(lines)
    await message.answer(text, reply_markup=get_income_expense_keyboard(income=False))


async def process_category_name(message: types.Message, state: FSMContext):
    """Обработка названия категории"""
    if message.text == "❌ Отмена":
        await cancel_handler(message, state)
        return
    
    data = await state.get_data()
    
    # Добавляем категорию в базу
    db.add_category(
        user_id=message.from_user.id,
        name=message.text,
        cat_type=data['cat_type']
    )
    
    await state.clear()
    
    type_text = "дохода" if data['cat_type'] == "income" else "расхода"
    
    await message.answer(
        f"✅ Категория {type_text} '{message.text}' успешно добавлена!",
        reply_markup=get_main_menu_keyboard()
    )


# ==================== ОБРАБОТЧИКИ ДОХОДОВ ====================

async def handle_add_income(message: types.Message, state: FSMContext):
    """Начало добавления дохода"""
    await message.answer(
        "➕ Добавление дохода\n\n"
        "Введите сумму дохода (в рублях):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(IncomeStates.waiting_amount)


async def process_income_amount(message: types.Message, state: FSMContext):
    """Обработка суммы дохода"""
    try:
        amount = float(message.text.replace(",", "."))
        await state.update_data(amount=amount)
        
        # Получаем категории доходов
        categories = db.get_user_categories(message.from_user.id, cat_type="income")
        
        if not categories:
            await message.answer(
                "У вас нет категорий доходов. Создайте категорию или отправьте '0' чтобы добавить доход без категории:"
            )
            await state.set_state(IncomeStates.waiting_description)
            return
        
        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(
                text=cat['name'],
                callback_data=f"income_cat_{cat['id']}"
            )])
        keyboard.append([InlineKeyboardButton(text="Без категории", callback_data="income_cat_0")])
        keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
        
        await message.answer(
            "Выберите категорию дохода:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await state.set_state(IncomeStates.selecting_category)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 50000 или 50000.50")


async def process_income_category(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора категории дохода"""
    if callback.data == "cancel":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer(
            "❌ Отменено",
            reply_markup=get_income_expense_keyboard(income=True)
        )
        return
    
    category_id = int(callback.data.split("_")[2])
    category_id = None if category_id == 0 else category_id
    
    await state.update_data(category_id=category_id)
    await callback.message.delete()
    await callback.message.answer(
        "Введите описание (необязательно) или отправьте '0' чтобы пропустить:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(IncomeStates.waiting_description)


async def process_income_description(message: types.Message, state: FSMContext):
    """Обработка описания дохода и завершение добавления"""
    data = await state.get_data()
    
    description = None if message.text == "0" else message.text
    
    # Добавляем доход в базу
    db.add_income(
        user_id=message.from_user.id,
        amount=data['amount'],
        category_id=data.get('category_id'),
        description=description
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ Доход успешно добавлен!\n\n"
        f"💰 Сумма: {data['amount']:,.2f} руб.\n"
        f"📝 Описание: {description or 'не указано'}",
        reply_markup=get_income_expense_keyboard(income=True)
    )


# ==================== ОБРАБОТЧИКИ РАСХОДОВ ====================

async def handle_add_expense(message: types.Message, state: FSMContext):
    """Начало добавления расхода"""
    await message.answer(
        "➕ Добавление расхода\n\n"
        "Введите сумму расхода (в рублях):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ExpenseStates.waiting_amount)


async def process_expense_amount(message: types.Message, state: FSMContext):
    """Обработка суммы расхода"""
    try:
        amount = float(message.text.replace(",", "."))
        await state.update_data(amount=amount)
        
        # Получаем категории расходов
        categories = db.get_user_categories(message.from_user.id, cat_type="expense")
        
        if not categories:
            await message.answer(
                "У вас нет категорий расходов. Создайте категорию или отправьте '0' чтобы добавить расход без категории:"
            )
            await state.set_state(ExpenseStates.waiting_description)
            return
        
        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(
                text=cat['name'],
                callback_data=f"expense_cat_{cat['id']}"
            )])
        keyboard.append([InlineKeyboardButton(text="Без категории", callback_data="expense_cat_0")])
        keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
        
        await message.answer(
            "Выберите категорию расхода:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await state.set_state(ExpenseStates.selecting_category)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 5000 или 5000.50")


async def process_expense_category(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора категории расхода"""
    if callback.data == "cancel":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer(
            "❌ Отменено",
            reply_markup=get_income_expense_keyboard(income=False)
        )
        return
    
    category_id = int(callback.data.split("_")[2])
    category_id = None if category_id == 0 else category_id
    
    await state.update_data(category_id=category_id)
    await callback.message.delete()
    await callback.message.answer(
        "Введите описание (необязательно) или отправьте '0' чтобы пропустить:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ExpenseStates.waiting_description)


async def process_expense_description(message: types.Message, state: FSMContext):
    """Обработка описания расхода и завершение добавления"""
    from datetime import date
    
    data = await state.get_data()
    
    description = None if message.text == "0" else message.text
    expense_date = date.today().isoformat()
    
    # Добавляем расход в базу
    db.add_expense(
        user_id=message.from_user.id,
        amount=data['amount'],
        category_id=data.get('category_id'),
        description=description,
        expense_date=expense_date
    )
    
    # Проверяем соответствие бюджету
    budget_warning = await check_expense_budget_warning(
        message.from_user.id,
        data.get('category_id'),
        data['amount'],
        expense_date
    )
    
    await state.clear()
    
    response_text = f"✅ Расход успешно добавлен!\n\n"
    response_text += f"💸 Сумма: {data['amount']:,.2f} руб.\n"
    response_text += f"📝 Описание: {description or 'не указано'}"
    response_text += budget_warning
    
    await message.answer(
        response_text,
        reply_markup=get_income_expense_keyboard(income=False)
    )


async def check_expense_budget_warning(user_id: int, category_id: int, 
                                       amount: float, expense_date: str) -> str:
    """Проверяет расход против бюджета и формирует предупреждение"""
    
    check_result = db.check_expense_against_budget(user_id, category_id, amount, expense_date)
    
    if not check_result['has_budget']:
        return ""
    
    # Получаем название категории
    all_cats = db.get_user_categories(user_id)
    cat_name = next((c['name'] for c in all_cats if c['id'] == category_id), "Неизвестная категория")
    
    warning = f"\n\n📊 СТАТУС БЮДЖЕТА\n"
    warning += f"Категория: {cat_name}\n\n"
    
    if not check_result['category_in_budget']:
        warning += f"⚠️ ВНИМАНИЕ! Эта категория не была запланирована в бюджете на этот месяц!\n\n"
        warning += "Рекомендуется добавить эту категорию в бюджет для лучшего контроля расходов."
        return warning
    
    # Категория есть в бюджете
    planned = check_result['planned']
    spent_after = check_result['spent_after']
    percent = check_result['percent_used']
    
    warning += f"Запланировано: {planned:,.2f} руб.\n"
    warning += f"Потрачено: {spent_after:,.2f} руб.\n"
    warning += f"Использовано: {percent:.1f}%\n\n"
    
    if check_result['over_budget']:
        warning += f"🚨 ПРЕВЫШЕН БЮДЖЕТ на {spent_after - planned:,.2f} руб.!"
    elif percent >= 90:
        warning += f"⚠️ ВНИМАНИЕ! Осталось только {100 - percent:.1f}% бюджета по этой категории!"
    elif percent >= 75:
        warning += f"⚡ Израсходовано {percent:.1f}% бюджета. Будьте внимательны!"
    elif percent >= 50:
        warning += f"✅ Израсходовано {percent:.1f}% бюджета."
    else:
        warning += f"✅ Бюджет под контролем. Использовано {percent:.1f}%."
    
    return warning

# ==================== ОБРАБОТЧИКИ ИНВЕСТИЦИЙ ====================

async def handle_add_investment(message: types.Message, state: FSMContext):
    """Начало добавления инвестиции"""
    await message.answer(
        "➕ Добавление инвестиции\n\n"
        "Введите название актива:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(InvestmentStates.waiting_asset_name)


async def process_investment_asset_name(message: types.Message, state: FSMContext):
    """Обработка названия актива"""
    if message.text == "❌ Отмена":
        await cancel_handler(message, state)
        return
    
    await state.update_data(asset_name=message.text)
    await message.answer("Введите сумму вложенных средств (в рублях):")
    await state.set_state(InvestmentStates.waiting_invested_amount)


async def process_investment_amount(message: types.Message, state: FSMContext):
    """Обработка суммы инвестиции"""
    try:
        invested_amount = float(message.text.replace(",", "."))
        data = await state.get_data()
        
        # Добавляем инвестицию в базу
        db.add_investment(
            user_id=message.from_user.id,
            asset_name=data['asset_name'],
            invested_amount=invested_amount
        )
        
        await state.clear()
        
        await message.answer(
            f"✅ Инвестиция успешно добавлена!\n\n"
            f"📊 Актив: {data['asset_name']}\n"
            f"💰 Вложено: {invested_amount:,.2f} руб.\n"
            f"💹 Текущая стоимость: {invested_amount:,.2f} руб.",
            reply_markup=get_investment_menu_keyboard()
        )
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 100000 или 100000.50")


async def show_user_investments(message: types.Message):
    """Показ списка инвестиций пользователя"""
    investments = db.get_user_investments(message.from_user.id)
    
    if not investments:
        await message.answer(
            "У вас пока нет добавленных инвестиций.\n"
            "Используйте кнопку '➕ Добавить инвестицию'",
            reply_markup=get_investment_menu_keyboard()
        )
        return
    
    text = "📊 Ваши инвестиции:\n\n"
    total_invested = 0
    total_current = 0
    
    for i, inv in enumerate(investments, 1):
        profit = inv['current_value'] - inv['invested_amount']
        profit_pct = (profit / inv['invested_amount'] * 100) if inv['invested_amount'] > 0 else 0
        
        profit_emoji = "📈" if profit >= 0 else "📉"
        
        text += f"{i}. {inv['asset_name']}\n"
        text += f"   💰 Вложено: {inv['invested_amount']:,.2f} руб.\n"
        text += f"   💹 Текущая: {inv['current_value']:,.2f} руб.\n"
        text += f"   {profit_emoji} Прибыль: {profit:,.2f} руб. ({profit_pct:+.2f}%)\n"
        text += f"   📅 Обновлено: {inv['last_updated']}\n\n"
        
        total_invested += inv['invested_amount']
        total_current += inv['current_value']
    
    total_profit = total_current - total_invested
    total_profit_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
    
    text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"ИТОГО:\n"
    text += f"Вложено: {total_invested:,.2f} руб.\n"
    text += f"Текущая стоимость: {total_current:,.2f} руб.\n"
    text += f"Общая прибыль: {total_profit:,.2f} руб. ({total_profit_pct:+.2f}%)"
    
    await message.answer(text, reply_markup=get_investment_menu_keyboard())


async def handle_update_investment_value(message: types.Message, state: FSMContext):
    """Начало обновления стоимости инвестиции"""
    investments = db.get_user_investments(message.from_user.id)
    
    if not investments:
        await message.answer(
            "У вас нет инвестиций для обновления",
            reply_markup=get_investment_menu_keyboard()
        )
        return
    
    keyboard = []
    for inv in investments:
        keyboard.append([InlineKeyboardButton(
            text=f"{inv['asset_name']} ({inv['current_value']:.2f} ₽)",
            callback_data=f"update_inv_{inv['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    await message.answer(
        "Выберите инвестицию для обновления стоимости:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(InvestmentStates.selecting_investment)


async def process_investment_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора инвестиции для обновления"""
    if callback.data == "cancel":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer(
            "❌ Отменено",
            reply_markup=get_investment_menu_keyboard()
        )
        return
    
    investment_id = int(callback.data.split("_")[2])
    await state.update_data(investment_id=investment_id)
    
    await callback.message.delete()
    await callback.message.answer(
        "Введите новую текущую стоимость актива (в рублях):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(InvestmentStates.waiting_new_value)


async def process_investment_new_value(message: types.Message, state: FSMContext):
    """Обработка новой стоимости инвестиции"""
    if message.text == "❌ Отмена":
        await cancel_handler(message, state)
        return
    
    try:
        new_value = float(message.text.replace(",", "."))
        data = await state.get_data()
        
        # Обновляем стоимость
        db.update_investment_value(data['investment_id'], new_value)
        
        await state.clear()
        
        await message.answer(
            f"✅ Стоимость инвестиции успешно обновлена!\n\n"
            f"💹 Новая стоимость: {new_value:,.2f} руб.",
            reply_markup=get_investment_menu_keyboard()
        )
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 120000 или 120000.50")


# ==================== ОБРАБОТЧИКИ СБЕРЕЖЕНИЙ ====================

async def process_savings_amount(message: types.Message, state: FSMContext):
    """Обработка суммы сбережений"""
    if message.text == "❌ Отмена":
        await cancel_handler(message, state)
        return
    
    try:
        amount = float(message.text.replace(",", "."))
        
        # Добавляем сбережения в базу
        db.add_savings(
            user_id=message.from_user.id,
            amount=amount
        )
        
        await state.clear()
        
        await message.answer(
            f"✅ Сумма сбережений обновлена!\n\n"
            f"🏦 Текущие сбережения: {amount:,.2f} руб.",
            reply_markup=get_main_menu_keyboard()
        )
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 250000 или 250000.50")


# ==================== ДОСРОЧНОЕ ПОГАШЕНИЕ КРЕДИТОВ ====================

async def handle_early_payment(message: types.Message, state: FSMContext):
    """Начало процесса досрочного погашения"""
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
            text=f"{credit['display_name']} ({credit['remaining_debt']:.2f} ₽)",
            callback_data=f"early_credit_{credit['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    await message.answer(
        "Выберите кредит для досрочного погашения:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(CreditStates.selecting_credit_for_early)


async def process_early_credit_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора кредита для досрочного погашения"""
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
    await state.update_data(credit_id=credit_id)
    
    await callback.message.delete()
    await callback.message.answer(
        f"Досрочное погашение кредита:\n"
        f"🏦 {credit['display_name']}\n"
        f"💰 Остаток долга: {credit['remaining_debt']:,.2f} руб.\n\n"
        f"Введите сумму досрочного платежа:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CreditStates.entering_early_amount)


async def process_early_payment_amount(message: types.Message, state: FSMContext):
    """Обработка суммы досрочного платежа"""
    if message.text == "❌ Отмена":
        await cancel_handler(message, state)
        return
    
    try:
        amount = float(message.text.replace(",", "."))
        data = await state.get_data()
        credit = db.get_credit_by_id(data['credit_id'])
        
        if amount > credit['remaining_debt']:
            await message.answer(
                f"❌ Сумма платежа превышает остаток долга ({credit['remaining_debt']:,.2f} руб.)!\n"
                f"Введите сумму не более остатка долга:"
            )
            return
        
        await state.update_data(early_amount=amount)
        
        # Проверяем возможности досрочного погашения
        keyboard = []
        
        if amount >= credit['remaining_debt']:
            # Полное погашение
            keyboard.append([InlineKeyboardButton(
                text="✅ Полное погашение",
                callback_data="early_type_full"
            )])
        else:
            # Частичное погашение
            if credit['has_early_partial_period']:
                keyboard.append([InlineKeyboardButton(
                    text="📅 С сокращением срока",
                    callback_data="early_type_reduce_period"
                )])
            if credit['has_early_partial_payment']:
                keyboard.append([InlineKeyboardButton(
                    text="💰 С сокращением платежа",
                    callback_data="early_type_reduce_payment"
                )])
        
        keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
        
        if len(keyboard) == 1:
            await message.answer(
                "❌ Этот кредит не поддерживает досрочное погашение.\n"
                "Настройте возможности кредита через меню 'Настроить возможности кредита'",
                reply_markup=get_credit_menu_keyboard()
            )
            await state.clear()
            return
        
        await message.answer(
            "Выберите тип досрочного погашения:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await state.set_state(CreditStates.selecting_early_type)
        
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 50000 или 50000.50")


async def process_early_payment_type(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа досрочного погашения"""
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
    early_amount = data['early_amount']
    early_type = callback.data.split("_")[-1]
    
    if early_type == "full":
        payment_type = "early_full"
    elif early_type == "period":
        payment_type = "early_partial_period"
    else:
        payment_type = "early_partial_payment"
    
    # Рассчитываем новые параметры
    credit = db.get_credit_by_id(credit_id)
    
    if payment_type == "early_full":
        db.add_credit_payment(credit_id, credit['remaining_debt'], payment_type)
        result_text = f"🎉 Кредит полностью погашен!\n\n🏦 {credit['display_name']}"
    else:
        calculation = FinancialCalculator.calculate_effective_rate_with_early_payment(
            credit, early_amount, 
            'reduce_period' if payment_type == 'early_partial_period' else 'reduce_payment'
        )
        
        db.add_credit_payment(credit_id, early_amount, payment_type)
        
        if payment_type == 'early_partial_period':
            result_text = (
                f"✅ Досрочный платёж принят!\n\n"
                f"🏦 {credit['display_name']}\n"
                f"💰 Внесено: {early_amount:,.2f} руб.\n"
                f"📊 Новый остаток: {calculation['new_debt']:,.2f} руб.\n"
                f"📅 Сокращение срока: {calculation['saved_months']} мес.\n"
                f"💵 Платёж остался: {calculation['new_payment']:,.2f} руб.\n"
                f"💰 Экономия: {calculation['saved_amount']:,.2f} руб."
            )
        else:
            result_text = (
                f"✅ Досрочный платёж принят!\n\n"
                f"🏦 {credit['display_name']}\n"
                f"💰 Внесено: {early_amount:,.2f} руб.\n"
                f"📊 Новый остаток: {calculation['new_debt']:,.2f} руб.\n"
                f"💵 Новый платёж: {calculation['new_payment']:,.2f} руб.\n"
                f"💰 Экономия за срок: {calculation['saved_amount']:,.2f} руб."
            )
    
    await callback.message.delete()
    await state.clear()
    await callback.message.answer(result_text, reply_markup=get_credit_menu_keyboard())


# ==================== НАСТРОЙКА ВОЗМОЖНОСТЕЙ КРЕДИТА ====================

async def handle_credit_capabilities(message: types.Message, state: FSMContext):
    """Начало настройки возможностей кредита"""
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
            text=credit['display_name'],
            callback_data=f"cap_credit_{credit['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    await message.answer(
        "Выберите кредит для настройки возможностей:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(CreditStates.selecting_credit_for_capabilities)


async def process_capabilities_credit_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора кредита для настройки возможностей"""
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
    await state.update_data(credit_id=credit_id)
    
    keyboard = [
        [InlineKeyboardButton(
            text=f"{'✅' if credit['has_early_full'] else '❌'} Полное досрочное погашение",
            callback_data=f"toggle_full"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if credit['has_early_partial_period'] else '❌'} Частичное с сокращением срока",
            callback_data=f"toggle_period"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if credit['has_early_partial_payment'] else '❌'} Частичное с сокращением платежа",
            callback_data=f"toggle_payment"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if credit['has_holidays'] else '❌'} Кредитные каникулы",
            callback_data=f"toggle_holidays"
        )],
        [InlineKeyboardButton(text="✅ Готово", callback_data="cap_done")]
    ]
    
    await callback.message.edit_text(
        f"Настройка возможностей кредита:\n"
        f"🏦 {credit['display_name']}\n\n"
        f"Нажмите на кнопку чтобы переключить возможность:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(CreditStates.updating_capabilities)


async def process_capability_toggle(callback: types.CallbackQuery, state: FSMContext):
    """Обработка переключения возможностей кредита"""
    if callback.data == "cap_done":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer(
            "✅ Настройки сохранены!",
            reply_markup=get_credit_menu_keyboard()
        )
        return
    
    data = await state.get_data()
    credit_id = data['credit_id']
    credit = db.get_credit_by_id(credit_id)
    
    toggle_type = callback.data.split("_")[1]
    
    if toggle_type == "full":
        db.update_credit_capabilities(credit_id, has_early_full=not credit['has_early_full'])
    elif toggle_type == "period":
        db.update_credit_capabilities(credit_id, has_early_partial_period=not credit['has_early_partial_period'])
    elif toggle_type == "payment":
        db.update_credit_capabilities(credit_id, has_early_partial_payment=not credit['has_early_partial_payment'])
    elif toggle_type == "holidays":
        db.update_credit_capabilities(credit_id, has_holidays=not credit['has_holidays'])
    
    # Обновляем сообщение
    credit = db.get_credit_by_id(credit_id)
    
    keyboard = [
        [InlineKeyboardButton(
            text=f"{'✅' if credit['has_early_full'] else '❌'} Полное досрочное погашение",
            callback_data=f"toggle_full"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if credit['has_early_partial_period'] else '❌'} Частичное с сокращением срока",
            callback_data=f"toggle_period"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if credit['has_early_partial_payment'] else '❌'} Частичное с сокращением платежа",
            callback_data=f"toggle_payment"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if credit['has_holidays'] else '❌'} Кредитные каникулы",
            callback_data=f"toggle_holidays"
        )],
        [InlineKeyboardButton(text="✅ Готово", callback_data="cap_done")]
    ]
    
    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


async def cancel_handler(message: types.Message, state: FSMContext):
    """Обработчик отмены операции"""
    await state.clear()
    await message.answer(
        "❌ Операция отменена",
        reply_markup=get_main_menu_keyboard()
    )

# ==================== ОБРАБОТЧИКИ БЮДЖЕТА ====================

async def handle_create_budget(message: types.Message, state: FSMContext):
    """Начало создания бюджета"""
    from datetime import date
    from dateutil.relativedelta import relativedelta
    
    current_date = date.today()
    months = []
    
    # Предлагаем выбрать один из следующих 12 месяцев
    for i in range(12):
        target_date = current_date + relativedelta(months=i)
        months.append({
            'month': target_date.month,
            'year': target_date.year,
            'name': target_date.strftime('%B %Y')
        })
    
    keyboard = []
    for month_data in months[:6]:  # Показываем первые 6
        keyboard.append([InlineKeyboardButton(
            text=month_data['name'],
            callback_data=f"budget_month_{month_data['month']}_{month_data['year']}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="➡️ Ещё месяцы", callback_data="budget_more_months")])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    await message.answer(
        "Выберите месяц для планирования бюджета:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(BudgetStates.selecting_month)


async def process_budget_month_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора месяца для бюджета"""
    if callback.data == "cancel":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer(
            "❌ Отменено",
            reply_markup=get_budget_menu_keyboard()
        )
        return
    
    if callback.data == "budget_more_months":
        # Показываем следующие 6 месяцев
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        current_date = date.today()
        months = []
        
        for i in range(6, 12):
            target_date = current_date + relativedelta(months=i)
            months.append({
                'month': target_date.month,
                'year': target_date.year,
                'name': target_date.strftime('%B %Y')
            })
        
        keyboard = []
        for month_data in months:
            keyboard.append([InlineKeyboardButton(
                text=month_data['name'],
                callback_data=f"budget_month_{month_data['month']}_{month_data['year']}"
            )])
        
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="budget_back_months")])
        keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
        
        await callback.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        return
    
    parts = callback.data.split("_")
    month = int(parts[2])
    year = int(parts[3])
    
    await state.update_data(month=month, year=year)
    
    # Получаем расходы по кредитам на этот месяц
    credits = db.get_user_credits(callback.from_user.id)
    credit_expenses = FinancialCalculator.calculate_monthly_credit_expenses(credits, month, year)
    
    await state.update_data(credit_expenses=credit_expenses['total'])
    
    # Проверяем, есть ли уже бюджет
    existing_budget = db.get_budget(callback.from_user.id, month, year)
    
    info_text = f"📅 Планирование бюджета на {calendar.month_name[month]} {year}\n\n"
    
    if existing_budget:
        info_text += "⚠️ На этот месяц уже есть бюджет. Вы можете его обновить.\n\n"
    
    info_text += f"💳 Расходы по кредитам: {credit_expenses['total']:,.2f} руб.\n"
    
    if credit_expenses['credits']:
        info_text += "\nКредиты в этом месяце:\n"
        for credit in credit_expenses['credits']:
            info_text += f"  • {credit['display_name']}: {credit['monthly_payment']:,.2f} руб.\n"
    
    info_text += "\nВведите планируемый доход за месяц (в рублях):"
    
    await callback.message.delete()
    await callback.message.answer(info_text, reply_markup=get_cancel_keyboard())
    await state.set_state(BudgetStates.waiting_planned_income)


async def process_planned_income(message: types.Message, state: FSMContext):
    """Обработка планируемого дохода"""
    if message.text == "❌ Отмена":
        await cancel_handler(message, state)
        return
    
    try:
        planned_income = float(message.text.replace(",", "."))
        await state.update_data(planned_income=planned_income)
        
        await message.answer(
            "Введите планируемые расходы (без учета кредитов) в рублях:\n\n"
            "Например, на продукты, транспорт, развлечения и т.д.",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(BudgetStates.waiting_planned_expenses)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 75000")


async def process_planned_income(message: types.Message, state: FSMContext):
    """Обработка выбора категорий доходов"""
    if message.text == "❌ Отмена":
        await cancel_handler(message, state)
        return
    
    data = await state.get_data()
    
    # Получаем категории доходов пользователя
    income_categories = db.get_user_categories(message.from_user.id, cat_type="income")
    
    if not income_categories:
        await message.answer(
            "У вас нет категорий доходов. Сначала создайте их в разделе '⚙️ Категории'",
            reply_markup=get_budget_menu_keyboard()
        )
        await state.clear()
        return
    
    # Получаем предложения на основе истории
    suggestions = db.suggest_budget_categories(message.from_user.id, lookback_months=3)
    
    await state.update_data(income_categories_dict={}, income_suggestions=suggestions['income'])
    
    # Показываем список категорий для добавления
    await show_income_category_selection(message, state, income_categories, suggestions['income'])


async def show_income_category_selection(message: types.Message, state: FSMContext, 
                                        categories: list, suggestions: dict):
    """Показывает категории доходов для планирования"""
    data = await state.get_data()
    added_cats = data.get('income_categories_dict', {})
    
    keyboard = []
    
    text = "💰 Планирование доходов\n\n"
    text += "Выберите категорию дохода для добавления в бюджет:\n\n"
    
    for cat in categories:
        cat_id = cat['id']
        cat_name = cat['name']
        
        # Показываем уже добавленные категории
        if str(cat_id) in added_cats:
            amount = added_cats[str(cat_id)]
            text += f"✅ {cat_name}: {amount:,.2f} руб.\n"
        else:
            # Показываем предложение если есть
            if cat_id in suggestions:
                suggested = suggestions[cat_id]
                button_text = f"➕ {cat_name} (предл.: {suggested:,.0f} руб.)"
            else:
                button_text = f"➕ {cat_name}"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"budget_add_income_{cat_id}"
            )])
    
    if added_cats:
        total = sum(added_cats.values())
        text += f"\n💵 Итого доходов: {total:,.2f} руб.\n\n"
    
    keyboard.append([InlineKeyboardButton(
        text="✅ Далее к расходам" if added_cats else "⏭ Пропустить доходы",
        callback_data="budget_income_done"
    )])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(BudgetStates.selecting_income_categories)


async def process_income_category_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора категории дохода"""
    if callback.data == "cancel":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer("❌ Отменено", reply_markup=get_budget_menu_keyboard())
        return
    
    if callback.data == "budget_income_done":
        # Переходим к расходам
        await callback.message.delete()
        
        expense_categories = db.get_user_categories(callback.from_user.id, cat_type="expense")
        
        if not expense_categories:
            await callback.message.answer(
                "У вас нет категорий расходов. Сначала создайте их в разделе '⚙️ Категории'",
                reply_markup=get_budget_menu_keyboard()
            )
            await state.clear()
            return
        
        data = await state.get_data()
        suggestions = db.suggest_budget_categories(callback.from_user.id, lookback_months=3)
        await state.update_data(expense_categories_dict={}, expense_suggestions=suggestions['expense'])
        
        await show_expense_category_selection(callback.message, state, expense_categories, suggestions['expense'])
        return
    
    # Обработка добавления категории
    category_id = int(callback.data.split("_")[-1])
    
    await state.update_data(selected_income_category=category_id)
    
    # Проверяем есть ли предложение
    data = await state.get_data()
    suggestions = data.get('income_suggestions', {})
    
    prompt_text = "Введите планируемую сумму дохода (в рублях):"
    
    if category_id in suggestions:
        suggested = suggestions[category_id]
        prompt_text = f"Введите планируемую сумму дохода (в рублях):\n\n💡 Предложение на основе истории: {suggested:,.2f} руб."
    
    await callback.message.edit_text(
        prompt_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ])
    )
    await state.set_state(BudgetStates.waiting_income_category_amount)


async def process_income_category_amount(message: types.Message, state: FSMContext):
    """Обработка суммы для категории дохода"""
    try:
        amount = float(message.text.replace(",", "."))
        
        data = await state.get_data()
        category_id = data['selected_income_category']
        
        # Добавляем в словарь категорий
        income_cats = data.get('income_categories_dict', {})
        income_cats[str(category_id)] = amount
        
        await state.update_data(income_categories_dict=income_cats)
        
        # Показываем снова список категорий
        income_categories = db.get_user_categories(message.from_user.id, cat_type="income")
        suggestions = data.get('income_suggestions', {})
        
        await show_income_category_selection(message, state, income_categories, suggestions)
        
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 75000")


async def show_expense_category_selection(message: types.Message, state: FSMContext,
                                         categories: list, suggestions: dict):
    """Показывает категории расходов для планирования"""
    data = await state.get_data()
    added_cats = data.get('expense_categories_dict', {})
    
    keyboard = []
    
    text = "🛒 Планирование расходов\n\n"
    text += "Выберите категорию расхода для добавления в бюджет:\n\n"
    
    for cat in categories:
        cat_id = cat['id']
        cat_name = cat['name']
        
        # Показываем уже добавленные категории
        if str(cat_id) in added_cats:
            amount = added_cats[str(cat_id)]
            text += f"✅ {cat_name}: {amount:,.2f} руб.\n"
        else:
            # Показываем предложение если есть
            if cat_id in suggestions:
                suggested = suggestions[cat_id]
                button_text = f"➕ {cat_name} (предл.: {suggested:,.0f} руб.)"
            else:
                button_text = f"➕ {cat_name}"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"budget_add_expense_{cat_id}"
            )])
    
    if added_cats:
        total = sum(added_cats.values())
        text += f"\n💳 Итого расходов: {total:,.2f} руб.\n\n"
    
    data_income = data.get('income_categories_dict', {})
    if data_income:
        total_income = sum(data_income.values())
        total_expense = sum(added_cats.values()) if added_cats else 0
        credit_exp = data.get('credit_expenses', 0)
        balance = total_income - total_expense - credit_exp
        balance_emoji = "✅" if balance >= 0 else "⚠️"
        
        text += f"{balance_emoji} Остаток: {balance:,.2f} руб.\n\n"
    
    keyboard.append([InlineKeyboardButton(
        text="✅ Завершить создание бюджета" if added_cats else "⏭ Пропустить расходы",
        callback_data="budget_expense_done"
    )])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(BudgetStates.selecting_expense_categories)


async def process_expense_category_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора категории расхода"""
    if callback.data == "cancel":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer("❌ Отменено", reply_markup=get_budget_menu_keyboard())
        return
    
    if callback.data == "budget_expense_done":
        # Завершаем создание бюджета
        await callback.message.delete()
        await finalize_budget_creation(callback.message, state, callback.from_user.id)
        return
    
    # Обработка добавления категории
    category_id = int(callback.data.split("_")[-1])
    
    await state.update_data(selected_expense_category=category_id)
    
    # Проверяем есть ли предложение
    data = await state.get_data()
    suggestions = data.get('expense_suggestions', {})
    
    prompt_text = "Введите планируемую сумму расхода (в рублях):"
    
    if category_id in suggestions:
        suggested = suggestions[category_id]
        prompt_text = f"Введите планируемую сумму расхода (в рублях):\n\n💡 Предложение на основе истории: {suggested:,.2f} руб."
    
    await callback.message.edit_text(
        prompt_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ])
    )
    await state.set_state(BudgetStates.waiting_expense_category_amount)


async def process_expense_category_amount(message: types.Message, state: FSMContext):
    """Обработка суммы для категории расхода"""
    try:
        amount = float(message.text.replace(",", "."))
        
        data = await state.get_data()
        category_id = data['selected_expense_category']
        
        # Добавляем в словарь категорий
        expense_cats = data.get('expense_categories_dict', {})
        expense_cats[str(category_id)] = amount
        
        await state.update_data(expense_categories_dict=expense_cats)
        
        # Показываем снова список категорий
        expense_categories = db.get_user_categories(message.from_user.id, cat_type="expense")
        suggestions = data.get('expense_suggestions', {})
        
        await show_expense_category_selection(message, state, expense_categories, suggestions)
        
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 15000")


async def finalize_budget_creation(message: types.Message, state: FSMContext, user_id: int):
    """Завершение создания бюджета"""
    data = await state.get_data()
    
    income_cats = data.get('income_categories_dict', {})
    expense_cats = data.get('expense_categories_dict', {})
    
    income_cats_int = {int(k): v for k, v in income_cats.items()}
    expense_cats_int = {int(k): v for k, v in expense_cats.items()}
    
    credit_expenses_total = db.get_credit_expenses_for_budget(user_id)
    
    budget_id = db.create_or_update_budget(
        user_id=user_id,
        month=data['month'],
        year=data['year'],
        income_categories=income_cats_int,
        expense_categories=expense_cats_int,
        credit_expenses=credit_expenses_total
    )
    
    # Формируем отчет
    total_income = sum(income_cats.values())
    total_expenses = sum(expense_cats.values())
    credit_exp = data.get('credit_expenses', 0)
    total_all_expenses = total_expenses + credit_exp
    balance = total_income - total_all_expenses
    balance_emoji = "✅" if balance >= 0 else "❌"
    
    # Получаем названия категорий
    all_cats = db.get_user_categories(user_id)
    cat_names = {c['id']: c['name'] for c in all_cats}
    
    result_text = f"✅ Бюджет на {calendar.month_name[data['month']]} {data['year']} создан!\n\n"
    
    if income_cats:
        result_text += "💰 Доходы:\n"
        for cat_id, amount in income_cats.items():
            cat_name = cat_names.get(int(cat_id), "Неизвестно")
            result_text += f"  • {cat_name}: {amount:,.2f} руб.\n"
        result_text += f"  📊 ИТОГО доходов: {total_income:,.2f} руб.\n\n"
    
    if expense_cats or credit_exp > 0:
        result_text += "🛒 Расходы:\n"
        for cat_id, amount in expense_cats.items():
            cat_name = cat_names.get(int(cat_id), "Неизвестно")
            result_text += f"  • {cat_name}: {amount:,.2f} руб.\n"
        if credit_exp > 0:
            result_text += f"  • Кредиты: {credit_exp:,.2f} руб.\n"
        result_text += f"  📊 ИТОГО расходов: {total_all_expenses:,.2f} руб.\n\n"
    
    result_text += f"{balance_emoji} Баланс: {balance:,.2f} руб."
    
    if balance < 0:
        result_text += "\n\n⚠️ Внимание! Расходы превышают доходы. Рекомендуется пересмотреть бюджет."
    
    await state.clear()
    await message.answer(result_text, reply_markup=get_budget_menu_keyboard())


# ==================== АНАЛИТИКА ====================

async def show_analytics_menu(message: types.Message):
    """Показать меню аналитики"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Подробный отчёт")],
            [KeyboardButton(text="📈 Все графики"), KeyboardButton(text="💹 График баланса")],
            [KeyboardButton(text="🥧 Диаграмма расходов"), KeyboardButton(text="📉 График кредитов")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "📊 РАСШИРЕННАЯ АНАЛИТИКА\n\n"
        "Выберите тип отчёта:\n"
        "• Подробный отчёт - полный текстовый анализ\n"
        "• Все графики - комплект из 6+ графиков\n"
        "• График баланса - динамика доходов/расходов\n"
        "• Диаграмма расходов - топ категорий\n"
        "• График кредитов - план погашения",
        reply_markup=keyboard
    )


async def generate_detailed_analytics(message: types.Message):
    """Генерирует детальный аналитический отчёт"""
    from analytics import FinancialAnalytics
    from database import Database
    
    await message.answer("⏳ Анализирую ваши финансы... Это займёт несколько секунд.")
    
    try:
        db = Database()
        analytics = FinancialAnalytics(db)
        
        # Генерируем отчёт
        report = analytics.generate_comprehensive_report(message.from_user.id, period_days=30)
        
        # Разбиваем на части если слишком длинный
        max_length = 4000
        if len(report) > max_length:
            parts = []
            current_part = ""
            
            for line in report.split('\n'):
                if len(current_part) + len(line) + 1 > max_length:
                    parts.append(current_part)
                    current_part = line + '\n'
                else:
                    current_part += line + '\n'
            
            if current_part:
                parts.append(current_part)
            
            # Отправляем по частям
            for i, part in enumerate(parts):
                await message.answer(part)
                if i < len(parts) - 1:
                    await asyncio.sleep(0.5)  # Небольшая задержка между сообщениями
        else:
            await message.answer(report)
        
        await message.answer(
            "✅ Анализ завершён!\n\n"
            "💡 Для получения графиков используйте кнопки меню аналитики.",
            reply_markup=get_analytics_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        await message.answer(
            "❌ Произошла ошибка при генерации отчёта.\n"
            "Попробуйте позже или обратитесь к администратору."
        )


async def generate_all_charts(message: types.Message):
    """Генерирует все графики"""
    from visualization import ChartGenerator
    from database import Database
    
    await message.answer("📊 Создаю графики... Подождите немного.")
    
    try:
        db = Database()
        chart_gen = ChartGenerator()
        
        charts = chart_gen.generate_full_financial_dashboard(message.from_user.id, db)
        
        if charts:
            await message.answer(f"✅ Создано {len(charts)} графиков!")
            
            for i, chart_path in enumerate(charts, 1):
                photo = types.FSInputFile(chart_path)
                await message.answer_photo(
                    photo=photo,
                    caption=f"График {i} из {len(charts)}"
                )
                await asyncio.sleep(0.3)  # Задержка между отправками
            
            await message.answer(
                "📊 Все графики отправлены!",
                reply_markup=get_analytics_keyboard()
            )
        else:
            await message.answer(
                "⚠️ Недостаточно данных для создания графиков.\n"
                "Добавьте доходы, расходы и другую финансовую информацию."
            )
            
    except Exception as e:
        logger.error(f"Error generating charts: {e}")
        await message.answer("❌ Ошибка при создании графиков.")


def get_analytics_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура меню аналитики"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Подробный отчёт")],
            [KeyboardButton(text="📈 Все графики"), KeyboardButton(text="💹 График баланса")],
            [KeyboardButton(text="🥧 Диаграмма расходов"), KeyboardButton(text="📉 График кредитов")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )


async def show_user_budgets(message: types.Message):
    """Показ списка бюджетов пользователя"""
    budgets = db.get_user_budgets(message.from_user.id)
    
    if not budgets:
        await message.answer(
            "У вас пока нет созданных бюджетов.\n"
            "Используйте кнопку '➕ Создать бюджет'",
            reply_markup=get_budget_menu_keyboard()
        )
        return
    
    text = "📋 Ваши бюджеты:\n\n"
    
    for i, budget in enumerate(budgets, 1):
        total_expenses = budget['planned_expenses'] + budget['credit_expenses']
        balance = budget['planned_income'] - total_expenses
        balance_emoji = "✅" if balance >= 0 else "❌"
        
        text += f"{i}. {calendar.month_name[budget['month']]} {budget['year']}\n"
        text += f"   💰 Доход: {budget['planned_income']:,.0f} руб.\n"
        text += f"   🛒 Расход: {total_expenses:,.0f} руб.\n"
        text += f"   {balance_emoji} Баланс: {balance:,.0f} руб.\n\n"
    
    keyboard = []
    for budget in budgets[:10]:
        month_name = calendar.month_name[budget['month']]
        keyboard.append([InlineKeyboardButton(
            text=f"📊 {month_name} {budget['year']}",
            callback_data=f"view_budget_{budget['id']}"
        )])
    
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


async def show_budget_forecast(message: types.Message):
    """Показ прогноза бюджета на 6 месяцев"""
    forecast = FinancialCalculator.generate_budget_forecast(
        message.from_user.id, db, months_ahead=6
    )
    
    text = "📊 Прогноз бюджета на 6 месяцев\n\n"
    
    for period in forecast:
        status = "✅" if period['has_budget'] else "➖"
        balance_emoji = "✅" if period['balance'] >= 0 else "❌"
        
        text += f"{status} {period['month_name']}\n"
        
        if period['has_budget']:
            text += f"   💰 Доход: {period['planned_income']:,.2f} руб.\n"
            text += f"   📊 Расходы: {period['total_expenses']:,.2f} руб.\n"
            text += f"     ├─ Планируемые: {period['planned_expenses']:,.2f} руб.\n"
            text += f"     └─ Кредиты: {period['credit_expenses']:,.2f} руб.\n"
            text += f"   {balance_emoji} Баланс: {period['balance']:,.2f} руб.\n"
        else:
            text += f"   💳 Кредиты: {period['credit_expenses']:,.2f} руб.\n"
            if period['credit_details']:
                for credit in period['credit_details']:
                    text += f"     • {credit['display_name']}: {credit['monthly_payment']:,.2f} руб.\n"
            text += f"   ⚠️ Бюджет не создан\n"
        
        text += "\n"
    
    await message.answer(text, reply_markup=get_budget_menu_keyboard())


async def view_budget_details(callback: types.CallbackQuery):
    """Подробный просмотр бюджета с детализацией по категориям"""
    budget_id = int(callback.data.split("_")[2])
    
    conn = sqlite3.connect('financial_bot.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM budget_plans WHERE id = ?", (budget_id,))
    budget = cursor.fetchone()
    conn.close()
    
    if not budget:
        await callback.answer("Бюджет не найден", show_alert=True)
        return
    
    budget = dict(budget)
    user_id = budget['user_id']
    
    # Получаем категории с именами
    import json
    income_cats = json.loads(budget['income_categories']) if budget.get('income_categories') else {}
    expense_cats = json.loads(budget['expense_categories']) if budget.get('expense_categories') else {}
    
    all_cats = db.get_user_categories(user_id)
    cat_names = {c['id']: c['name'] for c in all_cats}
    
    total_expenses = budget['planned_expenses'] + budget['credit_expenses']
    balance = budget['planned_income'] - total_expenses
    balance_emoji = "✅" if balance >= 0 else "❌"
    
    text = f"📊 Бюджет на {calendar.month_name[budget['month']]} {budget['year']}\n\n"
    
    # Детализация доходов
    if income_cats:
        text += "💰 Доходы:\n"
        for cat_id_str, amount in income_cats.items():
            cat_name = cat_names.get(int(cat_id_str), "Неизвестно")
            text += f"  • {cat_name}: {amount:,.2f} руб.\n"
        text += f"  📊 ИТОГО: {budget['planned_income']:,.2f} руб.\n\n"
    else:
        text += f"💰 Доходы: {budget['planned_income']:,.2f} руб.\n\n"
    
    # Детализация расходов
    text += "🛒 Расходы:\n"
    if expense_cats:
        for cat_id_str, amount in expense_cats.items():
            cat_name = cat_names.get(int(cat_id_str), "Неизвестно")
            text += f"  • {cat_name}: {amount:,.2f} руб.\n"
    if budget['credit_expenses'] > 0:
        text += f"  • Кредиты: {budget['credit_expenses']:,.2f} руб.\n"
    text += f"  📊 ИТОГО: {total_expenses:,.2f} руб.\n\n"
    
    text += f"{balance_emoji} Баланс: {balance:,.2f} руб."
    
    if budget.get('notes'):
        text += f"\n\n📝 Примечания: {budget['notes']}"
    
    keyboard = [
        [InlineKeyboardButton(text="✏️ Редактировать категорию", callback_data=f"edit_budget_cat_{budget_id}")],
        [InlineKeyboardButton(text="🗑 Удалить бюджет", callback_data=f"delete_budget_{budget_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_budgets")]
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


async def edit_budget_callback(callback: types.CallbackQuery, state: FSMContext):
    """Начало редактирования бюджета"""
    budget_id = int(callback.data.split("_")[2])
    
    conn = db.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM budget_plans WHERE id = ?", (budget_id,))
    budget = cursor.fetchone()
    conn.close()
    
    if not budget:
        await callback.answer("Бюджет не найден", show_alert=True)
        return
    
    budget = dict(budget)
    await state.update_data(
        budget_id=budget_id,
        month=budget['month'],
        year=budget['year'],
        credit_expenses=budget['credit_expenses']
    )
    
    await callback.message.delete()
    await callback.message.answer(
        f"✏️ Редактирование бюджета на {calendar.month_name[budget['month']]} {budget['year']}\n\n"
        f"Текущий доход: {budget['planned_income']:,.2f} руб.\n\n"
        f"Введите новый планируемый доход (или 0 чтобы оставить текущий):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(BudgetStates.waiting_planned_income)


async def delete_budget_callback(callback: types.CallbackQuery):
    """Удаление бюджета"""
    budget_id = int(callback.data.split("_")[2])
    
    keyboard = [
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{budget_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ]
    
    await callback.message.edit_text(
        "⚠️ Вы уверены, что хотите удалить этот бюджет?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


async def confirm_delete_budget(callback: types.CallbackQuery):
    """Подтверждение удаления бюджета"""
    if callback.data == "cancel":
        await callback.message.delete()
        return
    
    budget_id = int(callback.data.split("_")[2])
    
    if db.delete_budget(budget_id):
        await callback.message.edit_text("✅ Бюджет успешно удален!")
        await asyncio.sleep(2)
        await callback.message.delete()
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)


# Обёртки для кнопок меню бюджета
async def start_create_budget(message: types.Message, state: FSMContext):
    """Обёртка для создания бюджета через кнопку меню"""
    return await handle_create_budget(message, state)


async def start_show_budgets(message: types.Message):
    """Обёртка для показа бюджетов через кнопку меню"""
    return await show_user_budgets(message)


async def start_budget_forecast(message: types.Message):
    """Обёртка для прогноза бюджета через кнопку меню"""
    return await show_budget_forecast(message)

from utils import NumberFormatter  # импорт добавлен

# удалить последний доход
async def handle_delete_last_income(message: types.Message):
    user_id = message.from_user.id
    last = db.get_last_income(user_id)
    if not last:
        await message.answer("У вас ещё нет доходов.")
        return
    ok = db.delete_income(user_id, last['id'])
    if ok:
        await message.answer(
            f"✅ Удалён доход ID {last['id']} на сумму {NumberFormatter.format_money(last['amount'])} от {last['date']}"
        )
    else:
        await message.answer("❌ Не удалось удалить: запись не найдена или не ваша.")

# удалить последний расход
async def handle_delete_last_expense(message: types.Message):
    user_id = message.from_user.id
    last = db.get_last_expense(user_id)
    if not last:
        await message.answer("У вас ещё нет расходов.")
        return
    ok = db.delete_expense(user_id, last['id'])
    if ok:
        await message.answer(
            f"✅ Удалён расход ID {last['id']} на сумму {NumberFormatter.format_money(last['amount'])} от {last['date']}"
        )
    else:
        await message.answer("❌ Не удалось удалить: запись не найдена или не ваша.")

# удалить доход по ID (попросит ID и покажет последние 10 записей)
async def handle_delete_income_by_id(message: types.Message, state: FSMContext):
    recents = db.get_user_incomes(message.from_user.id)[:10]
    if recents:
        lines = ["Последние доходы:"]
        for r in recents:
            lines.append(
                f"ID {r['id']}: {NumberFormatter.format_money(r['amount'])} — {r['date']} — {r['description'] or '—'}"
            )
        await message.answer("\n".join(lines))
    await message.answer("Введите ID дохода для удаления:")
    await state.set_state(IncomeStates.waiting_delete_id)

# удалить расход по ID (попросит ID и покажет последние 10 записей)
async def handle_delete_expense_by_id(message: types.Message, state: FSMContext):
    recents = db.get_user_expenses(message.from_user.id)[:10]
    if recents:
        lines = ["Последние расходы:"]
        for r in recents:
            lines.append(
                f"ID {r['id']}: {NumberFormatter.format_money(r['amount'])} — {r['date']} — {r['description'] or '—'}"
            )
        await message.answer("\n".join(lines))
    await message.answer("Введите ID расхода для удаления:")
    await state.set_state(ExpenseStates.waiting_delete_id)

# обработка ввода ID для удаления дохода
@router.message(StateFilter(IncomeStates.waiting_delete_id))
async def process_delete_income_id(message: types.Message, state: FSMContext):
    try:
        income_id = int(message.text)
    except ValueError:
        await message.answer("Введите целое число ID.")
        return
    ok = db.delete_income(message.from_user.id, income_id)
    await state.clear()
    await message.answer("✅ Доход удалён." if ok else "❌ Не удалось удалить: запись не найдена или не ваша.")

# обработка ввода ID для удаления расхода
@router.message(StateFilter(ExpenseStates.waiting_delete_id))
async def process_delete_expense_id(message: types.Message, state: FSMContext):
    try:
        expense_id = int(message.text)
    except ValueError:
        await message.answer("Введите целое число ID.")
        return
    ok = db.delete_expense(message.from_user.id, expense_id)
    await state.clear()
    await message.answer("✅ Расход удалён." if ok else "❌ Не удалось удалить: запись не найдена или не ваша.")

async def edit_budget_category_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало редактирования отдельной категории бюджета"""
    budget_id = int(callback.data.split("_")[-1])
    
    conn = sqlite3.connect('financial_bot.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM budget_plans WHERE id = ?", (budget_id,))
    budget = cursor.fetchone()
    conn.close()
    
    if not budget:
        await callback.answer("Бюджет не найден", show_alert=True)
        return
    
    budget = dict(budget)
    user_id = budget['user_id']
    
    import json
    income_cats = json.loads(budget['income_categories']) if budget.get('income_categories') else {}
    expense_cats = json.loads(budget['expense_categories']) if budget.get('expense_categories') else {}
    
    all_cats = db.get_user_categories(user_id)
    cat_names = {c['id']: c['name'] for c in all_cats}
    
    keyboard = []
    
    text = "Выберите категорию для редактирования:\n\n💰 Доходы:\n"
    
    for cat_id_str, amount in income_cats.items():
        cat_id = int(cat_id_str)
        cat_name = cat_names.get(cat_id, "Неизвестно")
        text += f"  • {cat_name}: {amount:,.2f} руб.\n"
        keyboard.append([InlineKeyboardButton(
            text=f"✏️ {cat_name} ({amount:,.0f} руб.)",
            callback_data=f"editcat_income_{budget_id}_{cat_id}"
        )])
    
    text += "\n🛒 Расходы:\n"
    
    for cat_id_str, amount in expense_cats.items():
        cat_id = int(cat_id_str)
        cat_name = cat_names.get(cat_id, "Неизвестно")
        text += f"  • {cat_name}: {amount:,.2f} руб.\n"
        keyboard.append([InlineKeyboardButton(
            text=f"✏️ {cat_name} ({amount:,.0f} руб.)",
            callback_data=f"editcat_expense_{budget_id}_{cat_id}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"view_budget_{budget_id}")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


async def edit_specific_category(callback: types.CallbackQuery, state: FSMContext):
    """Редактирование конкретной категории"""
    parts = callback.data.split("_")
    cat_type = parts[1]
    budget_id = int(parts[2])
    category_id = int(parts[3])
    
    # Получаем название категории
    all_cats = db.get_user_categories(callback.from_user.id)
    cat_name = next((c['name'] for c in all_cats if c['id'] == category_id), "Неизвестная")
    
    await state.update_data(
        edit_budget_id=budget_id,
        edit_category_id=category_id,
        edit_category_type=cat_type
    )
    
    await callback.message.edit_text(
        f"Редактирование категории: {cat_name}\n\nВведите новую сумму (в рублях):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_budget_{budget_id}")]
        ])
    )
    
    await state.set_state(BudgetStates.waiting_edited_category_amount)


async def process_edited_category_amount(message: types.Message, state: FSMContext):
    """Обработка новой суммы для категории"""
    try:
        new_amount = float(message.text.replace(",", "."))
        
        data = await state.get_data()
        budget_id = data['edit_budget_id']
        category_id = data['edit_category_id']
        cat_type = data['edit_category_type']
        
        # Обновляем категорию
        success = db.update_budget_category(budget_id, cat_type, category_id, new_amount)
        
        if success:
            await message.answer(
                f"✅ Сумма категории обновлена: {new_amount:,.2f} руб.",
                reply_markup=get_budget_menu_keyboard()
            )
        else:
            await message.answer(
                "❌ Ошибка при обновлении",
                reply_markup=get_budget_menu_keyboard()
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 50000")
