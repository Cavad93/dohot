from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from datetime import datetime

from database import Database
from calculations import FinancialCalculator
from bot import (
    DebtStates, CategoryStates, IncomeStates, ExpenseStates, 
    InvestmentStates, SavingsStates, CreditStates,
    get_main_menu_keyboard, get_debt_menu_keyboard,
    get_income_expense_keyboard, get_investment_menu_keyboard,
    get_cancel_keyboard, get_credit_menu_keyboard
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
    data = await state.get_data()
    
    description = None if message.text == "0" else message.text
    
    # Добавляем расход в базу
    db.add_expense(
        user_id=message.from_user.id,
        amount=data['amount'],
        category_id=data.get('category_id'),
        description=description
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ Расход успешно добавлен!\n\n"
        f"💰 Сумма: {data['amount']:,.2f} руб.\n"
        f"📝 Описание: {description or 'не указано'}",
        reply_markup=get_income_expense_keyboard(income=False)
    )


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
