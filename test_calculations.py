import pytest
from datetime import date, timedelta
import sys
import os

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations import FinancialCalculator


class TestFinancialCalculator:
    """Тесты для финансового калькулятора"""
    
    def test_calculate_remaining_months(self):
        """Тест расчета оставшихся месяцев"""
        credit = {
            'total_months': 36,
            'current_month': 12
        }
        
        result = FinancialCalculator.calculate_remaining_months(credit)
        assert result == 24
    
    def test_calculate_remaining_months_zero(self):
        """Тест когда кредит только начат"""
        credit = {
            'total_months': 24,
            'current_month': 0
        }
        
        result = FinancialCalculator.calculate_remaining_months(credit)
        assert result == 24
    
    def test_calculate_next_payment_date(self):
        """Тест расчета даты следующего платежа"""
        today = date.today()
        credit = {
            'start_date': today.isoformat(),
            'current_month': 0
        }
        
        result = FinancialCalculator.calculate_next_payment_date(credit)
        
        # Следующий платеж через месяц
        from dateutil.relativedelta import relativedelta
        expected = today + relativedelta(months=1)
        
        assert result == expected
    
    def test_calculate_early_payment_reduce_period(self):
        """Тест досрочного погашения с сокращением срока"""
        credit = {
            'remaining_debt': 500000,
            'monthly_payment': 15000,
            'interest_rate': 12.0,
            'current_month': 10,
            'total_months': 40
        }
        
        early_payment = 100000
        
        result = FinancialCalculator.calculate_effective_rate_with_early_payment(
            credit, early_payment, 'reduce_period'
        )
        
        assert result['new_debt'] == 400000
        assert result['new_payment'] == 15000
        assert result['type'] == 'reduce_period'
        assert result['saved_months'] > 0
        assert result['saved_amount'] > 0
    
    def test_calculate_early_payment_reduce_payment(self):
        """Тест досрочного погашения с сокращением платежа"""
        credit = {
            'remaining_debt': 500000,
            'monthly_payment': 15000,
            'interest_rate': 12.0,
            'current_month': 10,
            'total_months': 40
        }
        
        early_payment = 100000
        
        result = FinancialCalculator.calculate_effective_rate_with_early_payment(
            credit, early_payment, 'reduce_payment'
        )
        
        assert result['new_debt'] == 400000
        assert result['new_payment'] < 15000
        assert result['type'] == 'reduce_payment'
        assert result['saved_amount'] > 0
    
    def test_recommend_early_payment_avalanche(self):
        """Тест рекомендации стратегии Avalanche"""
        credits = [
            {
                'id': 1,
                'display_name': 'Кредит 1',
                'remaining_debt': 300000,
                'monthly_payment': 10000,
                'interest_rate': 18.0,
                'current_month': 5,
                'total_months': 36,
                'is_active': True
            },
            {
                'id': 2,
                'display_name': 'Кредит 2',
                'remaining_debt': 500000,
                'monthly_payment': 15000,
                'interest_rate': 8.0,
                'current_month': 10,
                'total_months': 48,
                'is_active': True
            }
        ]
        
        result = FinancialCalculator.recommend_early_payment_strategy(credits)
        
        assert result['best_strategy'] == 'avalanche'
        assert result['avalanche']['credit']['interest_rate'] == 18.0
    
    def test_recommend_early_payment_snowball(self):
        """Тест рекомендации стратегии Snowball"""
        credits = [
            {
                'id': 1,
                'display_name': 'Кредит 1',
                'remaining_debt': 100000,
                'monthly_payment': 5000,
                'interest_rate': 12.0,
                'current_month': 5,
                'total_months': 24,
                'is_active': True
            },
            {
                'id': 2,
                'display_name': 'Кредит 2',
                'remaining_debt': 500000,
                'monthly_payment': 15000,
                'interest_rate': 13.0,
                'current_month': 10,
                'total_months': 48,
                'is_active': True
            }
        ]
        
        result = FinancialCalculator.recommend_early_payment_strategy(credits)
        
        # Разница в ставках мала (<2%), должна быть snowball
        assert result['best_strategy'] == 'snowball'
        assert result['snowball']['credit']['remaining_debt'] == 100000
    
    def test_calculate_net_worth(self):
        """Тест расчета чистого капитала"""
        savings = 500000
        credits = [
            {'remaining_debt': 1000000, 'is_active': True},
            {'remaining_debt': 500000, 'is_active': True}
        ]
        debts = [
            {'amount': 50000, 'debt_type': 'taken', 'is_paid': False},
            {'amount': 30000, 'debt_type': 'given', 'is_paid': False}
        ]
        investments = [
            {'current_value': 200000}
        ]
        
        result = FinancialCalculator.calculate_net_worth(
            savings, credits, debts, investments
        )
        
        assert result['savings'] == 500000
        assert result['investments'] == 200000
        assert result['debts_given'] == 30000
        assert result['total_assets'] == 730000
        assert result['credits'] == 1500000
        assert result['debts_taken'] == 50000
        assert result['total_liabilities'] == 1550000
        assert result['net_worth'] == -820000
    
    def test_calculate_category_summary(self):
        """Тест сводки по категориям"""
        categories = [
            {'id': 1, 'name': 'Зарплата'},
            {'id': 2, 'name': 'Фриланс'},
            {'id': 3, 'name': 'Продукты'},
            {'id': 4, 'name': 'Транспорт'}
        ]
        
        incomes = [
            {'category_id': 1, 'amount': 80000},
            {'category_id': 1, 'amount': 80000},
            {'category_id': 2, 'amount': 25000}
        ]
        
        expenses = [
            {'category_id': 3, 'amount': 15000},
            {'category_id': 3, 'amount': 12000},
            {'category_id': 4, 'amount': 5000}
        ]
        
        result = FinancialCalculator.calculate_category_summary(
            incomes, expenses, categories
        )
        
        assert result['income_by_category']['Зарплата'] == 160000
        assert result['income_by_category']['Фриланс'] == 25000
        assert result['total_income'] == 185000
        
        assert result['expense_by_category']['Продукты'] == 27000
        assert result['expense_by_category']['Транспорт'] == 5000
        assert result['total_expense'] == 32000
        
        assert result['balance'] == 153000
    
    def test_calculate_net_worth_empty_credits(self):
        """Тест расчета капитала без кредитов"""
        savings = 100000
        credits = []
        debts = []
        investments = []
        
        result = FinancialCalculator.calculate_net_worth(
            savings, credits, debts, investments
        )
        
        assert result['net_worth'] == 100000
        assert result['total_liabilities'] == 0
    
    def test_early_payment_full_amount(self):
        """Тест полного досрочного погашения"""
        credit = {
            'remaining_debt': 100000,
            'monthly_payment': 10000,
            'interest_rate': 12.0,
            'current_month': 5,
            'total_months': 24
        }
        
        # Платим всю сумму
        result = FinancialCalculator.calculate_effective_rate_with_early_payment(
            credit, 100000, 'reduce_period'
        )
        
        assert result['new_debt'] == 0


class TestEdgeCases:
    """Тесты граничных случаев"""
    
    def test_zero_interest_rate(self):
        """Тест с нулевой процентной ставкой"""
        credit = {
            'remaining_debt': 100000,
            'monthly_payment': 5000,
            'interest_rate': 0.0,
            'current_month': 5,
            'total_months': 20
        }
        
        result = FinancialCalculator.calculate_effective_rate_with_early_payment(
            credit, 20000, 'reduce_period'
        )
        
        assert result['new_debt'] == 80000
    
    def test_empty_credits_list(self):
        """Тест с пустым списком кредитов"""
        result = FinancialCalculator.recommend_early_payment_strategy([])
        
        assert result['strategy'] is None
    
    def test_single_credit(self):
        """Тест с одним кредитом"""
        credits = [
            {
                'id': 1,
                'display_name': 'Единственный кредит',
                'remaining_debt': 300000,
                'monthly_payment': 10000,
                'interest_rate': 12.0,
                'current_month': 5,
                'total_months': 36,
                'is_active': True
            }
        ]
        
        result = FinancialCalculator.recommend_early_payment_strategy(credits)
        
        # Должна быть рекомендация даже для одного кредита
        assert result['best_strategy'] in ['avalanche', 'snowball']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
