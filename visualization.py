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
    """
    Класс для генерации финансовых графиков и диаграмм
    Создаёт красивые визуализации данных с высоким качеством (300 DPI)
    """
    
    def __init__(self, charts_dir: str = "charts"):
        """
        Инициализация генератора графиков
        
        Args:
            charts_dir: Директория для сохранения графиков
        """
        self.charts_dir = charts_dir
        if not os.path.exists(charts_dir):
            os.makedirs(charts_dir)
    
    def generate_capital_chart(self, net_worth_data: Dict) -> str:
        """
        Генерирует круговую диаграмму капитала
        Показывает структуру активов и обязательств
        
        Args:
            net_worth_data: Словарь с данными о капитале
            
        Returns:
            Путь к созданному файлу или None при ошибке
        """
        try:
            # Создаём две диаграммы рядом: активы и обязательства
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Левая диаграмма - Активы
            assets = {
                'Сбережения': net_worth_data['savings'],
                'Инвестиции': net_worth_data['investments'],
                'Долги выданные': net_worth_data['debts_given']
            }
            
            # Убираем нулевые значения для чистоты диаграммы
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
                
                # Настройка шрифтов для читаемости
                for text in texts:
                    text.set_fontsize(10)
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(9)
                    autotext.set_weight('bold')
                
                ax1.set_title(f'Активы\nВсего: {net_worth_data["total_assets"]:,.0f} ₽', 
                            fontsize=12, weight='bold')
            else:
                # Если нет активов, показываем соответствующее сообщение
                ax1.text(0.5, 0.5, 'Нет активов', ha='center', va='center', 
                        fontsize=14, transform=ax1.transAxes)
            
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
                # Отсутствие обязательств - это хорошо!
                ax2.text(0.5, 0.5, 'Нет обязательств', ha='center', va='center', 
                        fontsize=14, transform=ax2.transAxes, color='green')
            
            plt.tight_layout()
            
            # Сохраняем график с уникальным именем
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
        Использует горизонтальные столбчатые диаграммы для наглядности
        
        Args:
            income_by_category: Словарь {категория: сумма} для доходов
            expense_by_category: Словарь {категория: сумма} для расходов
            
        Returns:
            Путь к созданному файлу или None при ошибке
        """
        try:
            # Создаём две диаграммы рядом
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # ===== ЛЕВАЯ ДИАГРАММА: ДОХОДЫ =====
            if income_by_category:
                # Сортируем по убыванию для наглядности
                sorted_income = dict(sorted(
                    income_by_category.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                ))
                
                # Горизонтальная столбчатая диаграмма
                ax1.barh(list(sorted_income.keys()), list(sorted_income.values()), 
                        color='#2ecc71')
                ax1.set_xlabel('Сумма (₽)', fontsize=10)
                ax1.set_title(f'Доходы по категориям\nВсего: {sum(income_by_category.values()):,.0f} ₽',
                            fontsize=12, weight='bold')
                ax1.grid(axis='x', alpha=0.3)
                
                # Добавляем значения на графике для точности
                for i, (cat, val) in enumerate(sorted_income.items()):
                    ax1.text(val, i, f' {val:,.0f} ₽', 
                           va='center', fontsize=9)
            else:
                ax1.text(0.5, 0.5, 'Нет данных о доходах', 
                        ha='center', va='center', fontsize=12, transform=ax1.transAxes)
            
            # ===== ПРАВАЯ ДИАГРАММА: РАСХОДЫ =====
            if expense_by_category:
                # Сортируем по убыванию
                sorted_expense = dict(sorted(
                    expense_by_category.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                ))
                
                # ИСПРАВЛЕНО: убрана дублированная часть кода
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
        Показывает прогноз остатка долга для каждого кредита
        
        Args:
            credits: Список словарей с данными о кредитах
            
        Returns:
            Путь к созданному файлу или None при ошибке
        """
        try:
            if not credits:
                return None
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Используем разные цвета для каждого кредита
            colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
            
            for i, credit in enumerate(credits):
                # Пропускаем неактивные кредиты
                if not credit['is_active']:
                    continue
                
                # Парсим дату начала кредита
                start_date = datetime.strptime(credit['start_date'], '%Y-%m-%d').date()
                current_month = credit['current_month']
                total_months = credit['total_months']
                
                # Создаём массив дат от текущего момента до конца кредита
                dates = [start_date + timedelta(days=30*m) for m in range(current_month, total_months + 1)]
                
                # Рассчитываем прогнозный остаток долга по месяцам
                # Это упрощенная модель без учёта процентов
                monthly_payment = credit['monthly_payment']
                remaining = credit['remaining_debt']
                debts = []
                
                for _ in range(len(dates)):
                    debts.append(remaining)
                    remaining = max(0, remaining - monthly_payment)
                
                # Рисуем линию для текущего кредита
                ax.plot(dates, debts, 
                       marker='o', 
                       label=credit['display_name'],
                       color=colors[i % len(colors)],
                       linewidth=2)
            
            # Настройка осей и заголовка
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
        Сравнивает вложенную сумму с текущей стоимостью
        
        Args:
            investments: Список словарей с данными об инвестициях
            
        Returns:
            Путь к созданному файлу или None при ошибке
        """
        try:
            if not investments:
                return None
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Извлекаем данные из списка инвестиций
            assets = [inv['asset_name'] for inv in investments]
            invested = [inv['invested_amount'] for inv in investments]
            current = [inv['current_value'] for inv in investments]
            
            # Настройка позиций столбцов
            x = range(len(assets))
            width = 0.35
            
            # Создаём два набора столбцов: вложено и текущая стоимость
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
            
            # Добавляем процент доходности над столбцами
            for i, inv in enumerate(investments):
                profit = inv['current_value'] - inv['invested_amount']
                profit_pct = (profit / inv['invested_amount'] * 100) if inv['invested_amount'] > 0 else 0
                
                # Цвет зависит от прибыльности
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
    
    def generate_full_financial_dashboard(self, user_id: int, db) -> List[str]:
        """
        Генерирует полный набор графиков для финансовой панели
        Создаёт до 6 различных графиков в зависимости от доступных данных
        
        Args:
            user_id: ID пользователя
            db: Объект базы данных
            
        Returns:
            Список путей к созданным графикам
        """
        from calculations import FinancialCalculator
        
        charts = []
        
        try:
            # Получаем все необходимые данные из базы
            credits = db.get_user_credits(user_id)
            debts = db.get_user_debts(user_id)
            investments = db.get_user_investments(user_id)
            savings_data = db.get_latest_savings(user_id)
            
            # Определяем период анализа (последние 30 дней)
            today = date.today()
            start_date = (today - timedelta(days=30)).isoformat()
            end_date = today.isoformat()
            
            categories = db.get_user_categories(user_id)
            incomes = db.get_user_incomes(user_id, start_date, end_date)
            expenses = db.get_user_expenses(user_id, start_date, end_date)
            
            savings = savings_data['amount'] if savings_data else 0
            
            # 1. График капитала (активы и обязательства)
            net_worth = FinancialCalculator.calculate_net_worth(savings, credits, debts, investments)
            chart_capital = self.generate_capital_chart(net_worth)
            if chart_capital:
                charts.append(chart_capital)
            
            # 2. График доходов и расходов по категориям
            category_summary = FinancialCalculator.calculate_category_summary(incomes, expenses, categories)
            chart_income_expense = self.generate_income_expense_chart(
                category_summary['income_by_category'],
                category_summary['expense_by_category']
            )
            if chart_income_expense:
                charts.append(chart_income_expense)
            
            # 3. График погашения кредитов (если есть кредиты)
            if credits:
                chart_credits = self.generate_credits_timeline(credits)
                if chart_credits:
                    charts.append(chart_credits)
            
            # 4. График доходности инвестиций (если есть инвестиции)
            if investments:
                chart_investments = self.generate_investment_performance(investments)
                if chart_investments:
                    charts.append(chart_investments)
            
            # 5. График динамики баланса
            chart_balance = self.generate_balance_trend(incomes, expenses, start_date, end_date)
            if chart_balance:
                charts.append(chart_balance)
            
            # 6. Круговая диаграмма топ-10 расходов
            if expenses:
                chart_expense_pie = self.generate_expense_pie_chart(expenses, categories)
                if chart_expense_pie:
                    charts.append(chart_expense_pie)
            
        except Exception as e:
            print(f"Error generating full dashboard: {e}")
        
        return charts
    
    def generate_balance_trend(self, incomes: List, expenses: List, 
                               start_date: str, end_date: str) -> str:
        """
        Генерирует график динамики баланса (доходы минус расходы)
        Показывает накопительный эффект во времени
        
        Args:
            incomes: Список доходов
            expenses: Список расходов
            start_date: Начало периода (ISO формат)
            end_date: Конец периода (ISO формат)
            
        Returns:
            Путь к созданному файлу или None при ошибке
        """
        try:
            if not incomes and not expenses:
                return None
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Группируем доходы и расходы по дням
            daily_income = {}
            daily_expense = {}
            
            for income in incomes:
                income_date = income['date']
                daily_income[income_date] = daily_income.get(income_date, 0) + income['amount']
            
            for expense in expenses:
                expense_date = expense['date']
                daily_expense[expense_date] = daily_expense.get(expense_date, 0) + expense['amount']
            
            # Создаём полный диапазон дат для непрерывного графика
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            dates = []
            incomes_values = []
            expenses_values = []
            balance_values = []
            cumulative_balance = 0
            
            # Проходим по всем датам в диапазоне
            current_date = start
            while current_date <= end:
                date_str = current_date.isoformat()
                income_val = daily_income.get(date_str, 0)
                expense_val = daily_expense.get(date_str, 0)
                
                # Накопительный баланс
                cumulative_balance += (income_val - expense_val)
                
                dates.append(current_date)
                incomes_values.append(income_val)
                expenses_values.append(expense_val)
                balance_values.append(cumulative_balance)
                
                current_date += timedelta(days=1)
            
            # Рисуем основную линию баланса
            ax.plot(dates, balance_values, label='Накопительный баланс', 
                   color='#3498db', linewidth=2, marker='o', markersize=3)
            ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            
            # Заливаем области профицита и дефицита разными цветами
            ax.fill_between(dates, 0, balance_values, where=[b >= 0 for b in balance_values],
                           color='#2ecc71', alpha=0.3, label='Профицит')
            ax.fill_between(dates, 0, balance_values, where=[b < 0 for b in balance_values],
                           color='#e74c3c', alpha=0.3, label='Дефицит')
            
            ax.set_xlabel('Дата', fontsize=11)
            ax.set_ylabel('Баланс (₽)', fontsize=11)
            ax.set_title('Динамика баланса', fontsize=14, weight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Форматирование дат на оси X
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Сохраняем
            filename = f"balance_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.charts_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"Error generating balance trend: {e}")
            return None
    
    def generate_expense_pie_chart(self, expenses: List, categories: List) -> str:
        """
        Генерирует круговую диаграмму топ-10 категорий расходов
        Наглядно показывает структуру трат
        
        Args:
            expenses: Список расходов
            categories: Список категорий
            
        Returns:
            Путь к созданному файлу или None при ошибке
        """
        try:
            # Создаём маппинг ID категории -> название
            category_map = {c['id']: c['name'] for c in categories}
            category_map[None] = 'Без категории'
            
            # Группируем расходы по категориям
            expense_by_category = {}
            for expense in expenses:
                cat_id = expense.get('category_id')
                cat_name = category_map.get(cat_id, 'Без категории')
                expense_by_category[cat_name] = expense_by_category.get(cat_name, 0) + expense['amount']
            
            if not expense_by_category:
                return None
            
            # Берём только топ-10 категорий для читаемости
            sorted_expenses = sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)[:10]
            
            labels = [item[0] for item in sorted_expenses]
            values = [item[1] for item in sorted_expenses]
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Используем цветовую схему Set3 для разнообразия
            colors = plt.cm.Set3(range(len(labels)))
            
            # Создаём круговую диаграмму с процентами и суммами
            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct=lambda pct: f'{pct:.1f}%\n({pct/100 * sum(values):,.0f} ₽)',
                startangle=90,
                colors=colors
            )
            
            # Настройка шрифтов
            for text in texts:
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(8)
                autotext.set_weight('bold')
            
            ax.set_title(f'Топ-10 категорий расходов\nВсего: {sum(values):,.0f} ₽', 
                        fontsize=14, weight='bold')
            
            plt.tight_layout()
            
            # Сохраняем
            filename = f"expense_pie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.charts_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"Error generating expense pie chart: {e}")
            return None
    
    def generate_budget_comparison_chart(self, budget_data: Dict, actual_data: Dict) -> str:
        """
        Генерирует сравнительный график бюджет vs. факт
        Показывает насколько хорошо соблюдается бюджет
        
        Args:
            budget_data: Словарь {категория: планируемая_сумма}
            actual_data: Словарь {категория: фактическая_сумма}
            
        Returns:
            Путь к созданному файлу или None при ошибке
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            categories = list(budget_data.keys())
            budget_values = list(budget_data.values())
            actual_values = [actual_data.get(cat, 0) for cat in categories]
            
            # Настройка позиций столбцов
            x = range(len(categories))
            width = 0.35
            
            # Создаём два набора столбцов: план и факт
            bars1 = ax.bar([i - width/2 for i in x], budget_values, width, 
                          label='План', color='#3498db', alpha=0.8)
            bars2 = ax.bar([i + width/2 for i in x], actual_values, width, 
                          label='Факт', color='#e74c3c', alpha=0.8)
            
            # Добавляем процент выполнения над столбцами
            for i, (budget, actual) in enumerate(zip(budget_values, actual_values)):
                if budget > 0:
                    percent = (actual / budget * 100)
                    # Зелёный если уложились, красный если превысили
                    color = '#2ecc71' if percent <= 100 else '#e74c3c'
                    ax.text(i, max(budget, actual), f'{percent:.0f}%', 
                           ha='center', va='bottom', fontsize=9, 
                           weight='bold', color=color)
            
            ax.set_ylabel('Сумма (₽)', fontsize=11)
            ax.set_title('Бюджет vs. Факт', fontsize=14, weight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            
            # Сохраняем
            filename = f"budget_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.charts_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"Error generating budget comparison chart: {e}")
            return None
