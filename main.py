import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from functools import partial 

from handlers import router 

from config import load_config
from database import Database
from bot import (
    cmd_start, cmd_help, handle_main_menu,
    handle_add_credit, show_user_credits, handle_credit_payment,
    show_credit_recommendations, show_capital_chart, show_financial_report,
    process_bank_name, process_monthly_payment, process_total_months,
    process_interest_rate, process_remaining_debt, process_start_date,
    process_credit_payment_callback, confirm_credit_payment,
    CreditStates, DebtStates, CategoryStates, IncomeStates,
    ExpenseStates, InvestmentStates, SavingsStates, BudgetStates,
    check_payment_reminders
)
from handlers import (
    handle_add_debt, process_debt_person_name, process_debt_amount,
    process_debt_type, process_debt_description, show_user_debts,
    handle_pay_debt, process_debt_payment_callback,
    handle_add_category, process_category_name,
    handle_add_income, process_income_amount, process_income_category,
    process_income_description,
    handle_add_expense, process_expense_amount, process_expense_category,
    process_expense_description,handle_delete_last_income, handle_delete_income_by_id,
    handle_delete_last_expense,handle_delete_expense_by_id,
    handle_add_investment, process_investment_asset_name,
    process_investment_amount, show_user_investments,
    handle_update_investment_value, process_investment_selection,
    process_investment_new_value,
    process_savings_amount,
    handle_early_payment, process_early_credit_selection,
    process_early_payment_amount, process_early_payment_type,
    handle_credit_capabilities, process_capabilities_credit_selection,
    process_capability_toggle, show_user_expenses,
    start_create_budget, start_show_budgets, start_budget_forecast,
    process_budget_month_selection,
    process_income_category_selection, process_income_category_amount,
    process_expense_category_selection, process_expense_category_amount,
    view_budget_details, edit_budget_category_start, edit_specific_category,
    process_edited_category_amount, delete_budget_callback,
    confirm_delete_budget, check_expense_budget_warning,
    cancel_handler
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def register_all_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков бота"""
    
    # ==================== КОМАНДЫ ====================
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    
    # ==================== ГЛАВНОЕ МЕНЮ ====================
    # ==================== ГЛАВНОЕ МЕНЮ ====================
    dp.message.register(
        handle_main_menu,
        F.text.in_([
            "💳 Кредиты", "💸 Долги", "💰 Доходы", "🛒 Расходы",
            "📊 Инвестиции", "🏦 Сбережения", "📅 Бюджет",
            "📈 График капитала", "📋 Отчёт", "⚙️ Категории"
        ])
    )
    
    # ==================== БЮДЖЕТ ====================
    # ==================== БЮДЖЕТ ====================
    # Меню бюджета
    dp.message.register(start_create_budget, F.text == "➕ Создать бюджет")
    dp.message.register(start_show_budgets, F.text == "📋 Мои бюджеты")
    dp.message.register(start_budget_forecast, F.text == "📊 Прогноз на 6 месяцев")

    # FSM для создания бюджета с категориями
    dp.callback_query.register(process_budget_month_selection, BudgetStates.selecting_month)
    dp.callback_query.register(process_income_category_selection, BudgetStates.selecting_income_categories)
    dp.message.register(process_income_category_amount, BudgetStates.waiting_income_category_amount)
    dp.callback_query.register(process_expense_category_selection, BudgetStates.selecting_expense_categories)
    dp.message.register(process_expense_category_amount, BudgetStates.waiting_expense_category_amount)

    # Просмотр бюджетов
    dp.callback_query.register(view_budget_details, F.data.startswith("view_budget_"))

    # Редактирование отдельных категорий
    dp.callback_query.register(edit_budget_category_start, F.data.startswith("edit_budget_cat_"))
    dp.callback_query.register(edit_specific_category, F.data.startswith("editcat_"))
    dp.message.register(process_edited_category_amount, BudgetStates.waiting_edited_category_amount)

    # Удаление бюджета
    dp.callback_query.register(delete_budget_callback, F.data.startswith("delete_budget_"))
    dp.callback_query.register(confirm_delete_budget, F.data.startswith("confirm_delete_"))

    # Возврат в главное меню
    dp.message.register(cmd_start, F.text == "🏠 Главное меню")
    
    # ==================== КРЕДИТЫ ====================
    # Меню кредитов
    dp.message.register(handle_add_credit, F.text == "➕ Добавить кредит")
    dp.message.register(show_user_credits, F.text == "📋 Мои кредиты")
    dp.message.register(handle_credit_payment, F.text == "✅ Внести платёж")
    dp.message.register(show_credit_recommendations, F.text == "🎯 Рекомендации")
    dp.message.register(handle_early_payment, F.text == "⚡ Досрочное погашение")
    dp.message.register(handle_credit_capabilities, F.text == "⚙️ Настроить возможности кредита")
    
    # FSM для добавления кредита
    dp.message.register(process_bank_name, CreditStates.waiting_bank_name)
    dp.message.register(process_monthly_payment, CreditStates.waiting_monthly_payment)
    dp.message.register(process_total_months, CreditStates.waiting_total_months)
    dp.message.register(process_interest_rate, CreditStates.waiting_interest_rate)
    dp.message.register(process_remaining_debt, CreditStates.waiting_remaining_debt)
    dp.message.register(process_start_date, CreditStates.waiting_start_date)
    
    # Callbacks для платежей
    dp.callback_query.register(
        process_credit_payment_callback,
        StateFilter(CreditStates.selecting_credit_for_payment)
    )
    dp.callback_query.register(
        confirm_credit_payment,
        StateFilter(CreditStates.confirming_payment)
    )
    
    # FSM для досрочного погашения
    dp.callback_query.register(
        process_early_credit_selection,
        StateFilter(CreditStates.selecting_credit_for_early)
    )
    dp.message.register(
        process_early_payment_amount,
        CreditStates.entering_early_amount
    )
    dp.callback_query.register(
        process_early_payment_type,
        StateFilter(CreditStates.selecting_early_type)
    )
    
    # FSM для настройки возможностей
    dp.callback_query.register(
        process_capabilities_credit_selection,
        StateFilter(CreditStates.selecting_credit_for_capabilities)
    )
    dp.callback_query.register(
        process_capability_toggle,
        StateFilter(CreditStates.updating_capabilities)
    )
    
    # ==================== ДОЛГИ ====================
    dp.message.register(handle_add_debt, F.text == "➕ Добавить долг")
    dp.message.register(show_user_debts, F.text == "📋 Мои долги")
    dp.message.register(handle_pay_debt, F.text == "✅ Погасить долг")
    
    # FSM для добавления долга
    dp.message.register(process_debt_person_name, DebtStates.waiting_person_name)
    dp.message.register(process_debt_amount, DebtStates.waiting_amount)
    dp.message.register(process_debt_type, DebtStates.waiting_type)
    dp.message.register(process_debt_description, DebtStates.waiting_description)
    
    # Callback для погашения долга
    dp.callback_query.register(
        process_debt_payment_callback,
        StateFilter(DebtStates.selecting_debt_for_payment)
    )
    
    # ==================== КАТЕГОРИИ ====================
    # ==================== КАТЕГОРИИ ====================
    dp.message.register(process_category_name, CategoryStates.waiting_name)

    # Регистрируем ту же функцию, но с разным cat_type через partial — обёртки не нужны
    dp.message.register(
        partial(handle_add_category, cat_type="income"),
        F.text == "➕ Категория дохода"
    )
    dp.message.register(
        partial(handle_add_category, cat_type="expense"),
        F.text == "➕ Категория расхода"
    )

    # ==================== РАСХОДЫ ====================
    # ==================== РАСХОДЫ ====================
    dp.message.register(handle_add_expense, F.text == "➕ Добавить расход")
    dp.message.register(show_user_expenses, F.text == "📋 Мои расходы")
    # ↓↓↓ добавлено ↓↓↓
    dp.message.register(handle_delete_last_expense, F.text == "🗑 Удалить последний расход")
    dp.message.register(handle_delete_expense_by_id, F.text == "🗑 Удалить расход по ID")
    # ↑↑↑ добавлено ↑↑↑

    # ==================== ДОХОДЫ ====================
    dp.message.register(handle_add_income, F.text == "➕ Добавить доход")
    # ↓↓↓ добавлено ↓↓↓
    dp.message.register(handle_delete_last_income, F.text == "🗑 Удалить последний доход")
    dp.message.register(handle_delete_income_by_id, F.text == "🗑 Удалить доход по ID")
    # ↑↑↑ добавлено ↑↑↑

    
    # FSM для добавления дохода
    dp.message.register(process_income_amount, IncomeStates.waiting_amount)
    dp.callback_query.register(
        process_income_category,
        StateFilter(IncomeStates.selecting_category)
    )
    dp.message.register(process_income_description, IncomeStates.waiting_description)
    
    
    # FSM для добавления расхода
    dp.message.register(process_expense_amount, ExpenseStates.waiting_amount)
    dp.callback_query.register(
        process_expense_category,
        StateFilter(ExpenseStates.selecting_category)
    )
    dp.message.register(process_expense_description, ExpenseStates.waiting_description)
    
    # ==================== ИНВЕСТИЦИИ ====================
    dp.message.register(handle_add_investment, F.text == "➕ Добавить инвестицию")
    dp.message.register(show_user_investments, F.text == "📋 Мои инвестиции")
    dp.message.register(handle_update_investment_value, F.text == "💹 Обновить стоимость")
    
    # FSM для добавления инвестиции
    dp.message.register(process_investment_asset_name, InvestmentStates.waiting_asset_name)
    dp.message.register(process_investment_amount, InvestmentStates.waiting_invested_amount)
    
    # FSM для обновления стоимости
    dp.callback_query.register(
        process_investment_selection,
        StateFilter(InvestmentStates.selecting_investment)
    )
    dp.message.register(process_investment_new_value, InvestmentStates.waiting_new_value)
    
    # ==================== СБЕРЕЖЕНИЯ ====================
    dp.message.register(process_savings_amount, SavingsStates.waiting_amount)
    
    # ==================== ОТЧЁТЫ И ГРАФИКИ ====================
    dp.message.register(show_capital_chart, F.text == "📈 График капитала")
    dp.message.register(show_financial_report, F.text == "📋 Отчёт")


async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    logger.info("Бот запускается...")
    
    # Инициализация базы данных
    db = Database()
    logger.info("База данных инициализирована")
    
    # Отправляем сообщение администратору (опционально)
    # await bot.send_message(ADMIN_ID, "🤖 Бот DoHot запущен!")


async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    logger.info("Бот останавливается...")
    # await bot.send_message(ADMIN_ID, "🤖 Бот DoHot остановлен")


async def main():
    """Основная функция запуска бота"""
    
    # Загружаем конфигурацию
    try:
        config = load_config()
        logger.info("Конфигурация загружена успешно")
    except ValueError as e:
        logger.error(f"Ошибка загрузки конфигурации: {e}")
        return
    
    # Инициализация бота и диспетчера
    bot = Bot(token=config.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(router)

    # Регистрируем все обработчики
    register_all_handlers(dp)
    logger.info("Обработчики зарегистрированы")
    
    # Настраиваем планировщик для напоминаний
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_payment_reminders,
        CronTrigger(
            hour=config.reminder_time_hour,
            minute=config.reminder_time_minute
        ),
        args=[bot]
    )
    scheduler.start()
    logger.info(f"Планировщик запущен. Напоминания в {config.reminder_time_hour:02d}:{config.reminder_time_minute:02d}")
    
    # Регистрируем startup и shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запускаем polling
    try:
        logger.info("Бот готов к работе!")
        logger.info("Нажмите Ctrl+C для остановки")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        # Закрываем ресурсы
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
