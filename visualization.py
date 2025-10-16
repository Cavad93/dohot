import matplotlib
matplotlib.use('Agg')  # Для работы без GUI
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date, timedelta
from typing import Dict, List
import os

# Настройка matplotlib для русского языка
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


class ChartGenerator:
    def __init__(self, charts_dir: str = "charts"):
        self.charts_dir = charts_dir
        if not os.path.exists(charts_dir):
            os.makedirs(charts_dir)
    
    def generate_capital_chart(self, net_worth_data: Dict) -> str:
        """
        Генерирует круговую диаграмму капитала
        """
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Левая диаграмма - Активы
            assets = {
                'Сбережения': net_worth_data['savings'],
                'Инвестиции': net_worth_data['investments'],
                'Долги выданные': net_worth_data['debts_given']
            }
            
            # Убираем нулевые значения
            assets = {k: v for k, v in assets.items() if v > 0}
            
            if assets:
                colors_assets = ['#2ecc71', '#3498db', '#9b59b6']
                wedges, texts, autotexts = ax1.pie(
                    assets.values(),
                    labels=assets.keys(),
                    autopct=lambda pct: f'{pct:.1f}%\n({pct/100 * sum(assets.values()):,.0f} ₽)',
                    startangle=90,
                    colors=colors_assets
                )
                
                for text in texts:
                    text.set_fontsize(10)
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(9)
                    autotext.set_weight('bold')
                
                ax1.set_title(f'Активы\nВсего: {net_worth_data["total_assets"]:,.0f} ₽', 
                            fontsize=12, weight='bold')
            else:
                ax1.text(0.5, 0.5, 'Нет данных об активах', 
                        ha='center', va='center', fontsize=12)
                ax1.set_xlim(-1, 1)
                ax1.set_ylim(-1, 1)
            
            # Правая диаграмма - Обязательства
            liabilities = {
                'Кредиты': net_worth_data['credits'],
                'Долги взятые': net_worth_data['debts_taken']
            }
            
            # Убираем нулевые значения
            liabilities = {k: v for k, v in liabilities.items() if v > 0}
            
            if liabilities:
                colors_liabilities = ['#e74c3c', '#e67e22']
                wedges, texts, autotexts = ax2.pie(
                    liabilities.values(),
                    labels=liabilities.keys(),
                    autopct=lambda pct: f'{pct:.1f}%\n({pct/100 * sum(liabilities.values()):,.0f} ₽)',
                    startangle=90,
                    colors=colors_liabilities
                )
                
                for text in texts:
                    text.set_fontsize(10)
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(9)
                    autotext.set_weight('bold')
                
                ax2.set_title(f'Обязательства\nВсего: {net_worth_data["total_liabilities"]:,.0f} ₽',
                            fontsize=12, weight='bold')
            else:
                ax2.text(0.5, 0.5, 'Нет обязательств', 
                        ha='center', va='center', fontsize=12)
                ax2.set_xlim(-1, 1)
                ax2.set_ylim(-1, 1)
            
            # Общий заголовок
            net_worth_color = '#2ecc71' if net_worth_data['net_worth'] >= 0 else '#e74c3c'
            fig.suptitle(
                f'Чистый капитал: {net_worth_data["net_worth"]:,.0f} ₽',
                fontsize=16, weight='bold', color=net_worth_color
            )
            
            plt.tight_layout()
            
            # Сохраняем
            filename = f"capital_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.charts_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"Error generating capital chart: {e}")
            return None
    
    def generate_income_expense_chart(self, income_by_category: Dict, 
                                     expense_by_category: Dict) -> str:
        """
        Генерирует диаграмму доходов и расходов по категориям
        """
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Доходы
            if income_by_category:
                sorted_income = dict(sorted(
                    income_by_category.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                ))
                
                ax1.barh(list(sorted_income.keys()), list(sorted_income.values()), 
                        color='#2ecc71')
                ax1.set_xlabel('Сумма (₽)', fontsize=10)
                ax1.set_title(f'Доходы по категориям\nВсего: {sum(income_by_category.values()):,.0f} ₽',
                            fontsize=12, weight='bold')
                ax1.grid(axis='x', alpha=0.3)
                
                # Добавляем значения на графике
                for i, (cat, val) in enumerate(sorted_income.items()):
                    ax1.text(val, i, f' {val:,.0f} ₽', 
                           va='center', fontsize=9)
            else:
                ax1.text(0.5, 0.5, 'Нет данных о доходах', 
                        ha='center', va='center', fontsize=12, transform=ax1.transAxes)
            
            # Расходы
            if expense_by_category:
                sorted_expense = dict(sorted(
                    expense_by_category.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                ))
                
                ax2.barh(list(sorted_expense.keys()), list(sorted_expense.values()), 
                        color='#e74c3c')
                ax2.set_xlabel('Сумма (₽)', fontsize=10)
                ax2.set_title(f'Расходы по категориям\nВсего: {sum(expense_by_category.values()):,.0f} ₽',
                            fontsize=12, weight='bold')
                ax2.grid(axis='x', alpha=0.3)
                
                # Добавляем значения на графике
                for i, (cat, val) in enumerate(sorted_expense.items()):
                    ax2.text(val, i, f' {val:,.0f} ₽', 
                           va='center', fontsize=9)
            else:
                ax2.text(0.5, 0.5, 'Нет данных о расходах', 
                        ha='center', va='center', fontsize=12, transform=ax2.transAxes)
            
            plt.tight_layout()
            
            # Сохраняем
            filename = f"income_expense_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.charts_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"Error generating income/expense chart: {e}")
            return None
    
    def generate_credits_timeline(self, credits: List[Dict]) -> str:
        """
        Генерирует график погашения кредитов по времени
        """
        try:
            if not credits:
                return None
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
            
            for i, credit in enumerate(credits):
                if not credit['is_active']:
                    continue
                
                start_date = datetime.strptime(credit['start_date'], '%Y-%m-%d').date()
                current_month = credit['current_month']
                total_months = credit['total_months']
                
                # Рассчитываем даты
                dates = [start_date + timedelta(days=30*m) for m in range(current_month, total_months + 1)]
                
                # Примерный остаток долга по месяцам (упрощенная модель)
                monthly_payment = credit['monthly_payment']
                remaining = credit['remaining_debt']
                debts = []
                
                for _ in range(len(dates)):
                    debts.append(remaining)
                    remaining = max(0, remaining - monthly_payment)
                
                ax.plot(dates, debts, 
                       marker='o', 
                       label=credit['display_name'],
                       color=colors[i % len(colors)],
                       linewidth=2)
            
            ax.set_xlabel('Дата', fontsize=11)
            ax.set_ylabel('Остаток долга (₽)', fontsize=11)
            ax.set_title('График погашения кредитов', fontsize=14, weight='bold')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            
            # Форматирование дат на оси X
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m.%Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Сохраняем
            filename = f"credits_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.charts_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"Error generating credits timeline: {e}")
            return None
    
    def generate_investment_performance(self, investments: List[Dict]) -> str:
        """
        Генерирует диаграмму доходности инвестиций
        """
        try:
            if not investments:
                return None
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            assets = [inv['asset_name'] for inv in investments]
            invested = [inv['invested_amount'] for inv in investments]
            current = [inv['current_value'] for inv in investments]
            
            x = range(len(assets))
            width = 0.35
            
            bars1 = ax.bar([i - width/2 for i in x], invested, width, 
                          label='Вложено', color='#3498db')
            bars2 = ax.bar([i + width/2 for i in x], current, width, 
                          label='Текущая стоимость', color='#2ecc71')
            
            ax.set_ylabel('Сумма (₽)', fontsize=11)
            ax.set_title('Доходность инвестиций', fontsize=14, weight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(assets, rotation=45, ha='right')
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
            
            # Добавляем значения и процент доходности
            for i, inv in enumerate(investments):
                profit = inv['current_value'] - inv['invested_amount']
                profit_pct = (profit / inv['invested_amount'] * 100) if inv['invested_amount'] > 0 else 0
                
                # Процент над столбцом текущей стоимости
                color = '#2ecc71' if profit >= 0 else '#e74c3c'
                ax.text(i + width/2, inv['current_value'], 
                       f'{profit_pct:+.1f}%', 
                       ha='center', va='bottom', 
                       fontsize=9, weight='bold', color=color)
            
            plt.tight_layout()
            
            # Сохраняем
            filename = f"investment_perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.charts_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"Error generating investment performance chart: {e}")
            return None
