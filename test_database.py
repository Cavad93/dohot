import pytest
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database


@pytest.fixture
def db():
    """Создает тестовую базу данных"""
    test_db_path = "test_dohot.db"
    
    # Удаляем если существует
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    db = Database(test_db_path)
    yield db
    
    # Очистка после тестов
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


class TestUsers:
    """Тесты для пользователей"""
    
    def test_add_user(self, db):
        """Тест добавления пользователя"""
        db.add_user(12345, "testuser", "Test User")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (12345,))
        user = cursor.fetchone()
        conn.close()
        
        assert user is not None
        assert user[0] == 12345
        assert user[1] == "testuser"
        assert user[2] == "Test User"
    
    def test_add_duplicate_user(self, db):
        """Тест добавления дублирующегося пользователя"""
        db.add_user(12345, "testuser", "Test User")
        db.add_user(12345, "testuser2", "Test User 2")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (12345,))
        count = cursor.fetchone()[0]
        conn.close()
        
        # Должен быть только один пользователь
        assert count == 1


class TestCredits:
    """Тесты для кредитов"""
    
    def test_add_credit(self, db):
        """Тест добавления кредита"""
        db.add_user(12345, "testuser", "Test User")
        
        credit_id = db.add_credit(
            user_id=12345,
            bank_name="Сбербанк",
            monthly_payment=15000,
            total_months=36,
            interest_rate=12.5,
            remaining_debt=500000
        )
        
        assert credit_id > 0
        
        credit = db.get_credit_by_id(credit_id)
        assert credit is not None
        assert credit['bank_name'] == "Сбербанк"
        assert credit['monthly_payment'] == 15000
        assert credit['display_name'] == "Сбербанк"
    
    def test_add_multiple_credits_same_bank(self, db):
        """Тест добавления нескольких кредитов в одном банке"""
        db.add_user(12345, "testuser", "Test User")
        
        credit_id1 = db.add_credit(
            user_id=12345,
            bank_name="Сбербанк",
            monthly_payment=15000,
            total_months=36,
            interest_rate=12.5,
            remaining_debt=500000
        )
        
        credit_id2 = db.add_credit(
            user_id=12345,
            bank_name="Сбербанк",
            monthly_payment=10000,
            total_months=24,
            interest_rate=14.0,
            remaining_debt=200000
        )
        
        credit1 = db.get_credit_by_id(credit_id1)
        credit2 = db.get_credit_by_id(credit_id2)
        
        # Первый кредит сохраняет простое название
        assert credit1['display_name'] == "Сбербанк"
        # Второй получает название с платежом
        assert "15000" in credit2['display_name']
    
    def test_get_user_credits(self, db):
        """Тест получения кредитов пользователя"""
        db.add_user(12345, "testuser", "Test User")
        
        db.add_credit(12345, "Сбербанк", 15000, 36, 12.5, 500000)
        db.add_credit(12345, "Альфа-Банк", 10000, 24, 14.0, 200000)
        
        credits = db.get_user_credits(12345)
        
        assert len(credits) == 2
    
    def test_update_credit_debt(self, db):
        """Тест обновления долга"""
        db.add_user(12345, "testuser", "Test User")
        credit_id = db.add_credit(12345, "Сбербанк", 15000, 36, 12.5, 500000)
        
        db.update_credit_debt(credit_id, 485000)
        
        credit = db.get_credit_by_id(credit_id)
        assert credit['remaining_debt'] == 485000
    
    def test_add_credit_payment(self, db):
        """Тест внесения платежа"""
        db.add_user(12345, "testuser", "Test User")
        credit_id = db.add_credit(12345, "Сбербанк", 15000, 36, 12.5, 500000)
        
        db.add_credit_payment(credit_id, 15000, 'regular')
        
        credit = db.get_credit_by_id(credit_id)
        assert credit['remaining_debt'] == 485000
        assert credit['current_month'] == 1
    
    def test_credit_full_payment(self, db):
        """Тест полного погашения кредита"""
        db.add_user(12345, "testuser", "Test User")
        credit_id = db.add_credit(12345, "Сбербанк", 15000, 36, 12.5, 15000)
        
        db.add_credit_payment(credit_id, 15000, 'regular')
        
        credit = db.get_credit_by_id(credit_id)
        assert credit['remaining_debt'] == 0
        assert credit['is_active'] == 0
    
    def test_update_credit_capabilities(self, db):
        """Тест обновления возможностей кредита"""
        db.add_user(12345, "testuser", "Test User")
        credit_id = db.add_credit(12345, "Сбербанк", 15000, 36, 12.5, 500000)
        
        db.update_credit_capabilities(
            credit_id,
            has_early_full=True,
            has_early_partial_period=False,
            has_early_partial_payment=False,
            has_holidays=True
        )
        
        credit = db.get_credit_by_id(credit_id)
        assert credit['has_early_full'] == 1
        assert credit['has_early_partial_period'] == 0
        assert credit['has_early_partial_payment'] == 0
        assert credit['has_holidays'] == 1


class TestDebts:
    """Тесты для долгов"""
    
    def test_add_debt(self, db):
        """Тест добавления долга"""
        db.add_user(12345, "testuser", "Test User")
        
        debt_id = db.add_debt(
            user_id=12345,
            person_name="Иван",
            amount=50000,
            debt_type="taken",
            description="На ремонт"
        )
        
        assert debt_id > 0
        
        debts = db.get_user_debts(12345)
        assert len(debts) == 1
        assert debts[0]['person_name'] == "Иван"
        assert debts[0]['amount'] == 50000
        assert debts[0]['debt_type'] == "taken"
    
    def test_mark_debt_paid(self, db):
        """Тест погашения долга"""
        db.add_user(12345, "testuser", "Test User")
        debt_id = db.add_debt(12345, "Иван", 50000, "taken")
        
        db.mark_debt_paid(debt_id)
        
        unpaid_debts = db.get_user_debts(12345, unpaid_only=True)
        all_debts = db.get_user_debts(12345, unpaid_only=False)
        
        assert len(unpaid_debts) == 0
        assert len(all_debts) == 1
        assert all_debts[0]['is_paid'] == 1


class TestCategories:
    """Тесты для категорий"""
    
    def test_add_category(self, db):
        """Тест добавления категории"""
        db.add_user(12345, "testuser", "Test User")
        
        category_id = db.add_category(12345, "Зарплата", "income")
        
        assert category_id > 0
        
        categories = db.get_user_categories(12345, "income")
        assert len(categories) == 1
        assert categories[0]['name'] == "Зарплата"
        assert categories[0]['type'] == "income"
    
    def test_get_categories_by_type(self, db):
        """Тест получения категорий по типу"""
        db.add_user(12345, "testuser", "Test User")
        
        db.add_category(12345, "Зарплата", "income")
        db.add_category(12345, "Фриланс", "income")
        db.add_category(12345, "Продукты", "expense")
        
        income_cats = db.get_user_categories(12345, "income")
        expense_cats = db.get_user_categories(12345, "expense")
        all_cats = db.get_user_categories(12345)
        
        assert len(income_cats) == 2
        assert len(expense_cats) == 1
        assert len(all_cats) == 3


class TestIncomesAndExpenses:
    """Тесты для доходов и расходов"""
    
    def test_add_income(self, db):
        """Тест добавления дохода"""
        db.add_user(12345, "testuser", "Test User")
        category_id = db.add_category(12345, "Зарплата", "income")
        
        income_id = db.add_income(
            user_id=12345,
            amount=80000,
            category_id=category_id,
            description="Зарплата за октябрь"
        )
        
        assert income_id > 0
        
        incomes = db.get_user_incomes(12345)
        assert len(incomes) == 1
        assert incomes[0]['amount'] == 80000
    
    def test_add_expense(self, db):
        """Тест добавления расхода"""
        db.add_user(12345, "testuser", "Test User")
        category_id = db.add_category(12345, "Продукты", "expense")
        
        expense_id = db.add_expense(
            user_id=12345,
            amount=15000,
            category_id=category_id
        )
        
        assert expense_id > 0
        
        expenses = db.get_user_expenses(12345)
        assert len(expenses) == 1
        assert expenses[0]['amount'] == 15000
    
    def test_filter_by_date(self, db):
        """Тест фильтрации по дате"""
        db.add_user(12345, "testuser", "Test User")
        
        db.add_income(12345, 80000, income_date="2025-01-15")
        db.add_income(12345, 90000, income_date="2025-02-15")
        
        incomes = db.get_user_incomes(
            12345,
            start_date="2025-02-01",
            end_date="2025-02-28"
        )
        
        assert len(incomes) == 1
        assert incomes[0]['amount'] == 90000


class TestInvestments:
    """Тесты для инвестиций"""
    
    def test_add_investment(self, db):
        """Тест добавления инвестиции"""
        db.add_user(12345, "testuser", "Test User")
        
        investment_id = db.add_investment(
            user_id=12345,
            asset_name="Газпром",
            invested_amount=100000
        )
        
        assert investment_id > 0
        
        investments = db.get_user_investments(12345)
        assert len(investments) == 1
        assert investments[0]['asset_name'] == "Газпром"
        assert investments[0]['current_value'] == 100000
    
    def test_update_investment_value(self, db):
        """Тест обновления стоимости инвестиции"""
        db.add_user(12345, "testuser", "Test User")
        investment_id = db.add_investment(12345, "Газпром", 100000)
        
        db.update_investment_value(investment_id, 115000)
        
        investments = db.get_user_investments(12345)
        assert investments[0]['current_value'] == 115000


class TestSavings:
    """Тесты для сбережений"""
    
    def test_add_savings(self, db):
        """Тест добавления сбережений"""
        db.add_user(12345, "testuser", "Test User")
        
        savings_id = db.add_savings(12345, 500000)
        
        assert savings_id > 0
        
        savings = db.get_latest_savings(12345)
        assert savings['amount'] == 500000
    
    def test_get_latest_savings(self, db):
        """Тест получения последних сбережений"""
        db.add_user(12345, "testuser", "Test User")
        
        db.add_savings(12345, 100000, "2025-01-01")
        db.add_savings(12345, 150000, "2025-02-01")
        db.add_savings(12345, 200000, "2025-03-01")
        
        savings = db.get_latest_savings(12345)
        assert savings['amount'] == 200000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
