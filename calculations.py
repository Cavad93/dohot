from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Tuple
import math


class FinancialCalculator:
    
    @staticmethod
    def calculate_remaining_months(credit: Dict) -> int:
        """Рассчитывает сколько месяцев осталось до погашения кредита"""
        return credit['total_months'] - credit['current_month']
    
    @staticmethod
    def calculate_next_payment_date(credit: Dict) -> date:
        """Рассчитывает дату следующего платежа"""
        start_date = datetime.strptime(credit['start_date'], '%Y-%m-%d').date()
        next_payment = start_date + relativedelta(months=credit['current_month'] + 1)
        return next_payment
    
    @staticmethod
    def calculate_credit_overpayment(credit: Dict, payments: List[Dict]) -> float:
        """Рассчитывает переплату по кредиту"""
        total_paid = sum(p['amount'] for p in payments)
        # Примерная переплата = всего заплачено - (начальный долг - остаток)
        # Для точного расчета нужна начальная сумма кредита
        # Упрощенная версия: переплата = сумма всех процентных платежей
        return 0  # TODO: улучшить расчет когда будет начальная сумма
    
    @staticmethod
    def calculate_effective_rate_with_early_payment(credit: Dict, 
                                                     early_payment: float,
                                                     payment_type: str) -> Dict:
        """
        Рассчитывает эффективную ставку при досрочном погашении
        payment_type: 'reduce_period' или 'reduce_payment'
        """
        remaining_debt = credit['remaining_debt']
        monthly_payment = credit['monthly_payment']
        interest_rate = credit['interest_rate'] / 100 / 12  # месячная ставка
        remaining_months = FinancialCalculator.calculate_remaining_months(credit)
        
        # После досрочного платежа
        new_debt = remaining_debt - early_payment
        
        if payment_type == 'reduce_period':
            # Платеж остается тем же, срок сокращается
            # Рассчитываем новый срок
            if interest_rate > 0:
                new_months = math.log(monthly_payment / (monthly_payment - new_debt * interest_rate)) / math.log(1 + interest_rate)
                new_months = math.ceil(new_months)
            else:
                new_months = math.ceil(new_debt / monthly_payment)
            
            saved_months = remaining_months - new_months
            saved_amount = saved_months * monthly_payment - (new_debt - remaining_months * monthly_payment)
            
            return {
                'new_debt': new_debt,
                'new_months': new_months,
                'new_payment': monthly_payment,
                'saved_months': saved_months,
                'saved_amount': saved_amount,
                'type': 'reduce_period'
            }
        
        else:  # reduce_payment
            # Срок остается тем же, платеж сокращается
            if interest_rate > 0:
                new_payment = (new_debt * interest_rate * (1 + interest_rate) ** remaining_months) / \
                              ((1 + interest_rate) ** remaining_months - 1)
            else:
                new_payment = new_debt / remaining_months
            
            saved_per_month = monthly_payment - new_payment
            saved_amount = saved_per_month * remaining_months
            
            return {
                'new_debt': new_debt,
                'new_months': remaining_months,
                'new_payment': new_payment,
                'saved_months': 0,
                'saved_amount': saved_amount,
                'type': 'reduce_payment'
            }
    
    @staticmethod
    def recommend_early_payment_strategy(credits: List[Dict]) -> Dict:
        """
        Рекомендует какой кредит гасить первым и каким способом
        Стратегии:
        1. Avalanche (лавина) - гасим кредит с максимальной ставкой
        2. Snowball (снежный ком) - гасим кредит с минимальным остатком
        """
        if not credits:
            return {'strategy': None, 'recommendation': 'Нет активных кредитов'}
        
        # Стратегия Avalanche - наибольшая экономия
        highest_rate_credit = max(credits, key=lambda c: c['interest_rate'])
        
        # Стратегия Snowball - психологический эффект
        lowest_debt_credit = min(credits, key=lambda c: c['remaining_debt'])
        
        # Рассчитываем потенциальную экономию
        avalanche_saving = highest_rate_credit['remaining_debt'] * (highest_rate_credit['interest_rate'] / 100) / 12
        snowball_months = FinancialCalculator.calculate_remaining_months(lowest_debt_credit)
        
        recommendation = {
            'avalanche': {
                'credit': highest_rate_credit,
                'reason': f"Наибольшая процентная ставка {highest_rate_credit['interest_rate']}%",
                'monthly_interest_saving': avalanche_saving
            },
            'snowball': {
                'credit': lowest_debt_credit,
                'reason': f"Наименьший остаток долга {lowest_debt_credit['remaining_debt']:.2f}",
                'months_to_close': snowball_months
            }
        }
        
        # Рекомендуем avalanche если разница в ставках существенная (>2%)
        if highest_rate_credit['interest_rate'] - lowest_debt_credit['interest_rate'] > 2:
            recommendation['best_strategy'] = 'avalanche'
            recommendation['explanation'] = (
                f"Рекомендуем гасить досрочно '{highest_rate_credit['display_name']}' "
                f"со ставкой {highest_rate_credit['interest_rate']}%. "
                f"Экономия на процентах: ~{avalanche_saving:.2f} руб/месяц"
            )
        else:
            recommendation['best_strategy'] = 'snowball'
            recommendation['explanation'] = (
                f"Рекомендуем гасить досрочно '{lowest_debt_credit['display_name']}' "
                f"с остатком {lowest_debt_credit['remaining_debt']:.2f} руб. "
                f"До полного погашения: ~{snowball_months} мес."
            )
        
        # Рекомендация по типу досрочного погашения
        avg_months = sum(FinancialCalculator.calculate_remaining_months(c) for c in credits) / len(credits)
        if avg_months > 24:
            recommendation['payment_type_recommendation'] = 'reduce_period'
            recommendation['payment_type_explanation'] = (
                "При длительном сроке кредитов рекомендуем сокращение срока - "
                "это даст максимальную экономию на процентах"
            )
        else:
            recommendation['payment_type_recommendation'] = 'reduce_payment'
            recommendation['payment_type_explanation'] = (
                "При небольшом сроке кредитов рекомендуем сокращение платежа - "
                "это освободит больше средств в месячном бюджете"
            )
        
        return recommendation
    
    @staticmethod
    def calculate_net_worth(savings: float, credits: List[Dict], 
                           debts: List[Dict], investments: List[Dict]) -> Dict:
        """Рассчитывает чистый капитал (сбережения - долги)"""
        total_credits = sum(c['remaining_debt'] for c in credits if c['is_active'])
        total_debts_taken = sum(d['amount'] for d in debts if d['debt_type'] == 'taken' and not d['is_paid'])
        total_debts_given = sum(d['amount'] for d in debts if d['debt_type'] == 'given' and not d['is_paid'])
        total_investments = sum(i['current_value'] for i in investments)
        
        net_worth = savings + total_investments + total_debts_given - total_credits - total_debts_taken
        
        return {
            'net_worth': net_worth,
            'savings': savings,
            'investments': total_investments,
            'debts_given': total_debts_given,
            'total_assets': savings + total_investments + total_debts_given,
            'credits': total_credits,
            'debts_taken': total_debts_taken,
            'total_liabilities': total_credits + total_debts_taken
        }
    
    @staticmethod
    def calculate_category_summary(incomes: List[Dict], expenses: List[Dict],
                                   categories: List[Dict]) -> Dict:
        """Формирует сводку по категориям доходов и расходов"""
        category_map = {c['id']: c['name'] for c in categories}
        
        income_by_category = {}
        for income in incomes:
            cat_id = income.get('category_id')
            cat_name = category_map.get(cat_id, 'Без категории')
            income_by_category[cat_name] = income_by_category.get(cat_name, 0) + income['amount']
        
        expense_by_category = {}
        for expense in expenses:
            cat_id = expense.get('category_id')
            cat_name = category_map.get(cat_id, 'Без категории')
            expense_by_category[cat_name] = expense_by_category.get(cat_name, 0) + expense['amount']
        
        return {
            'income_by_category': income_by_category,
            'expense_by_category': expense_by_category,
            'total_income': sum(income_by_category.values()),
            'total_expense': sum(expense_by_category.values()),
            'balance': sum(income_by_category.values()) - sum(expense_by_category.values())
        }
    
    @staticmethod
    def generate_financial_report(user_id: int, db, period_days: int = 30) -> str:
        """Генерирует подробный финансовый отчет"""
        today = date.today()
        start_date = (today - timedelta(days=period_days)).isoformat()
        end_date = today.isoformat()
        
        # Получаем данные
        credits = db.get_user_credits(user_id)
        debts = db.get_user_debts(user_id, unpaid_only=False)
        categories = db.get_user_categories(user_id)
        incomes = db.get_user_incomes(user_id, start_date, end_date)
        expenses = db.get_user_expenses(user_id, start_date, end_date)
        investments = db.get_user_investments(user_id)
        savings_data = db.get_latest_savings(user_id)
        
        savings = savings_data['amount'] if savings_data else 0
        
        # Рассчитываем показатели
        net_worth = FinancialCalculator.calculate_net_worth(savings, credits, debts, investments)
        category_summary = FinancialCalculator.calculate_category_summary(incomes, expenses, categories)
        
        # Формируем отчет
        report = f"""
📊 ПОДРОБНЫЙ ФИНАНСОВЫЙ ОТЧЕТ
Период: {start_date} - {end_date}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 ЧИСТЫЙ КАПИТАЛ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Чистый капитал: {net_worth['net_worth']:,.2f} руб.

Активы:
  • Сбережения: {net_worth['savings']:,.2f} руб.
  • Инвестиции: {net_worth['investments']:,.2f} руб.
  • Долги выданные: {net_worth['debts_given']:,.2f} руб.
  Всего активов: {net_worth['total_assets']:,.2f} руб.

Обязательства:
  • Кредиты: {net_worth['credits']:,.2f} руб.
  • Долги взятые: {net_worth['debts_taken']:,.2f} руб.
  Всего обязательств: {net_worth['total_liabilities']:,.2f} руб.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💳 КРЕДИТЫ (активные: {len([c for c in credits if c['is_active']])})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for credit in credits:
            if credit['is_active']:
                remaining = FinancialCalculator.calculate_remaining_months(credit)
                next_payment = FinancialCalculator.calculate_next_payment_date(credit)
                report += f"""
{credit['display_name']}
  Остаток долга: {credit['remaining_debt']:,.2f} руб.
  Ежемесячный платеж: {credit['monthly_payment']:,.2f} руб.
  Процентная ставка: {credit['interest_rate']}%
  Осталось месяцев: {remaining}
  Следующий платеж: {next_payment.strftime('%d.%m.%Y')}
"""
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 ДОХОДЫ И РАСХОДЫ (за {period_days} дней)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Доходы по категориям:
"""
        
        for cat, amount in category_summary['income_by_category'].items():
            report += f"  • {cat}: {amount:,.2f} руб.\n"
        
        report += f"\nВсего доходов: {category_summary['total_income']:,.2f} руб.\n\n"
        report += "Расходы по категориям:\n"
        
        for cat, amount in category_summary['expense_by_category'].items():
            report += f"  • {cat}: {amount:,.2f} руб.\n"
        
        report += f"\nВсего расходов: {category_summary['total_expense']:,.2f} руб.\n"
        report += f"Баланс: {category_summary['balance']:,.2f} руб.\n"
        
        # Долги
        active_debts = [d for d in debts if not d['is_paid']]
        if active_debts:
            report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💸 ДОЛГИ (активных: {len(active_debts)})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            for debt in active_debts:
                debt_type_text = "Взял у" if debt['debt_type'] == 'taken' else "Дал"
                report += f"{debt_type_text} {debt['person_name']}: {debt['amount']:,.2f} руб.\n"
        
        # Инвестиции
        if investments:
            report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ИНВЕСТИЦИИ (всего активов: {len(investments)})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            for inv in investments:
                profit = inv['current_value'] - inv['invested_amount']
                profit_percent = (profit / inv['invested_amount'] * 100) if inv['invested_amount'] > 0 else 0
                report += f"""
{inv['asset_name']}
  Вложено: {inv['invested_amount']:,.2f} руб.
  Текущая стоимость: {inv['current_value']:,.2f} руб.
  Прибыль/убыток: {profit:,.2f} руб. ({profit_percent:+.2f}%)
"""
        
        # Рекомендации
        if credits:
            recommendation = FinancialCalculator.recommend_early_payment_strategy(
                [c for c in credits if c['is_active']]
            )
            if recommendation.get('best_strategy'):
                report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 РЕКОМЕНДАЦИИ ПО ДОСРОЧНОМУ ПОГАШЕНИЮ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{recommendation['explanation']}

{recommendation['payment_type_explanation']}
"""
        
        report += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        return report
