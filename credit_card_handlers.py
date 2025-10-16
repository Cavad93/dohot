"""
Обработчики для работы с кредитными картами
"""

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import CreditCardStates, get_credit_card_menu_keyboard, get_cancel_keyboard, get_main_menu_keyboard
from credit_cards import CreditCardManager
from database import Database

db = Database()
card_manager = CreditCardManager()


async def handle_credit_cards_menu(message: types.Message):
    """Обработка входа в меню кредитных карт"""
    await message.answer(
        "💳 Кредитные карты\n\n"
        "Управление кредитными картами:\n"
        "• Добавляйте карты с лимитом\n"
        "• Пополняйте с учётом процентов\n"
        "• Отслеживайте минимальные платежи\n"
        "• Контролируйте задолженность",
        reply_markup=get_credit_card_menu_keyboard()
    )


async def handle_add_credit_card(message: types.Message, state: FSMContext):
    """Начало добавления кредитной карты"""
    await message.answer(
        "Добавление кредитной карты\n\n"
        "Введите название карты (например: Momentum, All Airlines):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CreditCardStates.waiting_card_name)


async def process_card_name(message: types.Message, state: FSMContext):
    """Обработка названия карты"""
    if message.text == "❌ Отмена":
        await cancel_credit_card_handler(message, state)
        return
    
    await state.update_data(card_name=message.text)
    await message.answer("Введите название банка:")
    await state.set_state(CreditCardStates.waiting_bank_name)


async def process_card_bank_name(message: types.Message, state: FSMContext):
    """Обработка названия банка"""
    if message.text == "❌ Отмена":
        await cancel_credit_card_handler(message, state)
        return
    
    await state.update_data(bank_name=message.text)
    await message.answer("Введите кредитный лимит (в рублях):")
    await state.set_state(CreditCardStates.waiting_credit_limit)


async def process_card_credit_limit(message: types.Message, state: FSMContext):
    """Обработка кредитного лимита"""
    if message.text == "❌ Отмена":
        await cancel_credit_card_handler(message, state)
        return
    
    try:
        credit_limit = float(message.text.replace(",", "."))
        await state.update_data(credit_limit=credit_limit)
        await message.answer("Введите годовую процентную ставку (например: 19.9):")
        await state.set_state(CreditCardStates.waiting_interest_rate)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 100000")


async def process_card_interest_rate(message: types.Message, state: FSMContext):
    """Обработка процентной ставки"""
    if message.text == "❌ Отмена":
        await cancel_credit_card_handler(message, state)
        return
    
    try:
        interest_rate = float(message.text.replace(",", "."))
        await state.update_data(interest_rate=interest_rate)
        await message.answer(
            "Введите процент минимального платежа от задолженности\n"
            "(обычно 5-10%, по умолчанию 5%):"
        )
        await state.set_state(CreditCardStates.waiting_minimum_payment_percent)
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 19.9")


async def process_card_minimum_payment_percent(message: types.Message, state: FSMContext):
    """Обработка процента минимального платежа и завершение добавления карты"""
    if message.text == "❌ Отмена":
        await cancel_credit_card_handler(message, state)
        return
    
    try:
        minimum_payment_percent = float(message.text.replace(",", "."))
        data = await state.get_data()
        
        card_id = card_manager.add_credit_card(
            user_id=message.from_user.id,
            card_name=data['card_name'],
            bank_name=data['bank_name'],
            credit_limit=data['credit_limit'],
            interest_rate=data['interest_rate'],
            minimum_payment_percent=minimum_payment_percent
        )
        
        await state.clear()
        
        await message.answer(
            f"✅ Кредитная карта успешно добавлена!\n\n"
            f"💳 Карта: {data['card_name']}\n"
            f"🏦 Банк: {data['bank_name']}\n"
            f"💰 Лимит: {data['credit_limit']:,.2f} руб.\n"
            f"📈 Ставка: {data['interest_rate']}% годовых\n"
            f"📊 Минимальный платёж: {minimum_payment_percent}% от задолженности",
            reply_markup=get_credit_card_menu_keyboard()
        )
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 5")


async def show_user_credit_cards(message: types.Message):
    """Показать список кредитных карт пользователя"""
    cards = card_manager.get_user_credit_cards(message.from_user.id)
    
    if not cards:
        await message.answer(
            "У вас пока нет добавленных кредитных карт.\n"
            "Используйте кнопку '➕ Добавить карту'",
            reply_markup=get_credit_card_menu_keyboard()
        )
        return
    
    text = "💳 Ваши кредитные карты:\n\n"
    
    for i, card in enumerate(cards, 1):
        used_credit = card['credit_limit'] - card['current_balance']
        usage_percent = (used_credit / card['credit_limit']) * 100
        minimum_payment = card_manager.calculate_minimum_payment(card['id'])
        
        status_emoji = "🟢" if used_credit == 0 else "🟡" if usage_percent < 50 else "🔴"
        
        text += f"{i}. {status_emoji} {card['bank_name']} - {card['card_name']}\n"
        text += f"   Лимит: {card['credit_limit']:,.0f} руб.\n"
        text += f"   Доступно: {card['current_balance']:,.0f} руб.\n"
        text += f"   Задолженность: {used_credit:,.0f} руб. ({usage_percent:.1f}%)\n"
        
        if used_credit > 0:
            text += f"   Минимальный платёж: {minimum_payment:,.2f} руб.\n"
        
        text += f"   Ставка: {card['interest_rate']}%\n\n"
    
    total_limit = sum(c['credit_limit'] for c in cards)
    total_available = sum(c['current_balance'] for c in cards)
    total_used = total_limit - total_available
    total_minimum = sum(card_manager.calculate_minimum_payment(c['id']) for c in cards)
    
    text += f"📊 ИТОГО:\n"
    text += f"Общий лимит: {total_limit:,.0f} руб.\n"
    text += f"Доступно: {total_available:,.0f} руб.\n"
    text += f"Задолженность: {total_used:,.0f} руб.\n"
    
    if total_minimum > 0:
        text += f"Минимальный платёж: {total_minimum:,.2f} руб."
    
    await message.answer(text, reply_markup=get_credit_card_menu_keyboard())


async def handle_add_money_to_card(message: types.Message, state: FSMContext):
    """Начало пополнения кредитной карты"""
    cards = card_manager.get_user_credit_cards(message.from_user.id)
    
    if not cards:
        await message.answer(
            "У вас нет активных кредитных карт",
            reply_markup=get_credit_card_menu_keyboard()
        )
        return
    
    keyboard = []
    for card in cards:
        used_credit = card['credit_limit'] - card['current_balance']
        if used_credit > 0:
            keyboard.append([InlineKeyboardButton(
                text=f"{card['bank_name']} - {card['card_name']} (долг: {used_credit:,.0f} ₽)",
                callback_data=f"repay_card_{card['id']}"
            )])
    
    if not keyboard:
        await message.answer(
            "Все ваши кредитные карты не имеют задолженности!",
            reply_markup=get_credit_card_menu_keyboard()
        )
        return
    
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    await message.answer(
        "Выберите карту для пополнения:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(CreditCardStates.selecting_card_for_transaction)


async def process_card_selection_for_repayment(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора карты для пополнения"""
    if callback.data == "cancel":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer(
            "❌ Отменено",
            reply_markup=get_credit_card_menu_keyboard()
        )
        return
    
    card_id = int(callback.data.split("_")[2])
    card = card_manager.get_card_by_id(card_id)
    await state.update_data(card_id=card_id)
    
    used_credit = card['credit_limit'] - card['current_balance']
    minimum_payment = card_manager.calculate_minimum_payment(card_id)
    
    await callback.message.delete()
    await callback.message.answer(
        f"Пополнение карты:\n"
        f"💳 {card['bank_name']} - {card['card_name']}\n"
        f"💰 Задолженность: {used_credit:,.2f} руб.\n"
        f"📊 Минимальный платёж: {minimum_payment:,.2f} руб.\n"
        f"📈 Ставка: {card['interest_rate']}% годовых\n\n"
        f"⚠️ Внимание! Часть вашего платежа пойдёт на погашение процентов.\n\n"
        f"Введите сумму пополнения:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CreditCardStates.waiting_transaction_amount)


async def process_card_repayment_amount(message: types.Message, state: FSMContext):
    """Обработка суммы пополнения"""
    if message.text == "❌ Отмена":
        await cancel_credit_card_handler(message, state)
        return
    
    try:
        amount = float(message.text.replace(",", "."))
        data = await state.get_data()
        card_id = data['card_id']
        
        result = card_manager.add_money_to_card(card_id, amount)
        
        await state.clear()
        
        response = f"✅ Карта успешно пополнена!\n\n"
        response += f"💰 Внесено: {result['amount_added']:,.2f} руб.\n"
        response += f"📉 Проценты списаны: {result['interest_charged']:,.2f} руб.\n"
        response += f"💳 Погашено задолженности: {result['effective_repayment']:,.2f} руб.\n\n"
        response += f"📊 Баланс карты:\n"
        response += f"   Было: {result['balance_before']:,.2f} руб.\n"
        response += f"   Стало: {result['balance_after']:,.2f} руб.\n\n"
        response += f"✨ Доступно для использования: {result['available_credit']:,.2f} руб.\n"
        
        if result['used_credit'] > 0:
            response += f"⚠️ Осталось погасить: {result['used_credit']:,.2f} руб."
        else:
            response += f"🎉 Задолженность полностью погашена!"
        
        await message.answer(response, reply_markup=get_credit_card_menu_keyboard())
        
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 5000")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=get_credit_card_menu_keyboard())
        await state.clear()


async def handle_spend_from_card(message: types.Message, state: FSMContext):
    """Начало процесса траты с кредитной карты"""
    cards = card_manager.get_user_credit_cards(message.from_user.id)
    
    if not cards:
        await message.answer(
            "У вас нет активных кредитных карт",
            reply_markup=get_credit_card_menu_keyboard()
        )
        return
    
    keyboard = []
    for card in cards:
        if card['current_balance'] > 0:
            keyboard.append([InlineKeyboardButton(
                text=f"{card['bank_name']} - {card['card_name']} (доступно: {card['current_balance']:,.0f} ₽)",
                callback_data=f"spend_card_{card['id']}"
            )])
    
    if not keyboard:
        await message.answer(
            "На всех ваших кредитных картах исчерпан лимит!",
            reply_markup=get_credit_card_menu_keyboard()
        )
        return
    
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    await message.answer(
        "Выберите карту для покупки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(CreditCardStates.selecting_card_for_spending)


async def process_card_selection_for_spending(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора карты для траты"""
    if callback.data == "cancel":
        await callback.message.delete()
        await state.clear()
        await callback.message.answer(
            "❌ Отменено",
            reply_markup=get_credit_card_menu_keyboard()
        )
        return
    
    card_id = int(callback.data.split("_")[2])
    card = card_manager.get_card_by_id(card_id)
    await state.update_data(card_id=card_id)
    
    await callback.message.delete()
    await callback.message.answer(
        f"Покупка с карты:\n"
        f"💳 {card['bank_name']} - {card['card_name']}\n"
        f"💰 Доступно: {card['current_balance']:,.2f} руб.\n\n"
        f"Введите сумму покупки:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CreditCardStates.waiting_spending_amount)


async def process_card_spending_amount(message: types.Message, state: FSMContext):
    """Обработка суммы траты"""
    if message.text == "❌ Отмена":
        await cancel_credit_card_handler(message, state)
        return
    
    try:
        amount = float(message.text.replace(",", "."))
        data = await state.get_data()
        card_id = data['card_id']
        
        result = card_manager.spend_from_card(card_id, amount)
        
        await state.clear()
        
        response = f"✅ Покупка совершена!\n\n"
        response += f"💳 Потрачено: {result['amount_spent']:,.2f} руб.\n\n"
        response += f"📊 Баланс карты:\n"
        response += f"   Было: {result['balance_before']:,.2f} руб.\n"
        response += f"   Стало: {result['balance_after']:,.2f} руб.\n\n"
        response += f"✨ Доступно для использования: {result['available_credit']:,.2f} руб.\n"
        response += f"⚠️ Задолженность: {result['used_credit']:,.2f} руб."
        
        await message.answer(response, reply_markup=get_credit_card_menu_keyboard())
        
    except ValueError:
        await message.answer("❌ Неверный формат! Введите число, например: 1500")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=get_credit_card_menu_keyboard())
        await state.clear()


async def show_card_transactions(message: types.Message):
    """Показать историю операций по картам"""
    cards = card_manager.get_user_credit_cards(message.from_user.id)
    
    if not cards:
        await message.answer(
            "У вас нет кредитных карт",
            reply_markup=get_credit_card_menu_keyboard()
        )
        return
    
    text = "📊 История операций по кредитным картам:\n\n"
    
    for card in cards:
        transactions = card_manager.get_card_transactions(card['id'], limit=10)
        
        if transactions:
            text += f"💳 {card['bank_name']} - {card['card_name']}\n"
            
            for trans in transactions[:5]:
                date_str = trans['transaction_date']
                trans_type = "💰 Пополнение" if trans['transaction_type'] == 'repayment' else "🛒 Покупка"
                
                text += f"   {trans_type} {date_str}\n"
                text += f"   Сумма: {trans['amount']:,.2f} руб.\n"
                
                if trans['interest_charged'] > 0:
                    text += f"   Проценты: {trans['interest_charged']:,.2f} руб.\n"
                
                text += f"   Баланс: {trans['balance_after']:,.2f} руб.\n\n"
    
    if not any(card_manager.get_card_transactions(c['id'], limit=1) for c in cards):
        text += "Пока нет операций по картам."
    
    await message.answer(text, reply_markup=get_credit_card_menu_keyboard())


async def cancel_credit_card_handler(message: types.Message, state: FSMContext):
    """Отмена операции с кредитной картой"""
    await state.clear()
    await message.answer(
        "❌ Операция отменена",
        reply_markup=get_credit_card_menu_keyboard()
    )