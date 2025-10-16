import sqlite3
from datetime import datetime, date
from typing import List, Optional, Dict
import json


class Database:
    def __init__(self, db_path: str = "dohot.db"):
        self.db_path = db_path
        self.init_database()
        
    def get_credit_expenses_for_budget(self, user_id: int) -> float:
        """
        Получить сумму кредитных расходов для бюджета
        Включает обычные кредиты + минимальные платежи по кредитным картам
        """
        from credit_cards import CreditCardManager
        
        total_credit_expenses = 0
        
        credits = self.get_user_credits(user_id, active_only=True)
        for credit in credits:
            total_credit_expenses += credit['monthly_payment']
        
        card_manager = CreditCardManager(self.db_path)
        total_card_payment = card_manager.get_total_minimum_payment(user_id)
        total_credit_expenses += total_card_payment
        
        return total_credit_expenses
    
    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица кредитов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                bank_name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                monthly_payment REAL NOT NULL,
                total_months INTEGER NOT NULL,
                interest_rate REAL NOT NULL,
                remaining_debt REAL NOT NULL,
                start_date DATE NOT NULL,
                current_month INTEGER DEFAULT 0,
                has_early_full BOOLEAN DEFAULT 1,
                has_early_partial_period BOOLEAN DEFAULT 1,
                has_early_partial_payment BOOLEAN DEFAULT 1,
                has_holidays BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица платежей по кредитам
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credit_id INTEGER NOT NULL,
                payment_date DATE NOT NULL,
                amount REAL NOT NULL,
                payment_type TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (credit_id) REFERENCES credits(id)
            )
        """)
        
        # Таблица кредитных каникул
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credit_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (credit_id) REFERENCES credits(id)
            )
        """)
        
        # Таблица долгов (взятых/выданных)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                person_name TEXT NOT NULL,
                amount REAL NOT NULL,
                debt_type TEXT NOT NULL,
                description TEXT,
                date DATE NOT NULL,
                is_paid BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица категорий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица доходов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER,
                amount REAL NOT NULL,
                description TEXT,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # Таблица расходов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER,
                amount REAL NOT NULL,
                description TEXT,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # Таблица инвестиций
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                asset_name TEXT NOT NULL,
                invested_amount REAL NOT NULL,
                current_value REAL NOT NULL,
                last_updated DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица сбережений
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ==================== ПОЛЬЗОВАТЕЛИ ====================
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        """, (user_id, username, first_name))
        conn.commit()
        conn.close()
    
    # ==================== КРЕДИТЫ ====================
    
    def add_credit(self, user_id: int, bank_name: str, monthly_payment: float,
                   total_months: int, interest_rate: float, remaining_debt: float,
                   start_date: str = None) -> int:
        if start_date is None:
            start_date = date.today().isoformat()
        
        # Проверяем, есть ли уже кредиты от этого банка
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM credits 
            WHERE user_id = ? AND bank_name = ? AND is_active = 1
        """, (user_id, bank_name))
        count = cursor.fetchone()[0]
        
        if count > 0:
            display_name = f"{bank_name} {monthly_payment:.2f}"
        else:
            display_name = bank_name
        
        cursor.execute("""
            INSERT INTO credits (
                user_id, bank_name, display_name, monthly_payment, 
                total_months, interest_rate, remaining_debt, start_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, bank_name, display_name, monthly_payment,
              total_months, interest_rate, remaining_debt, start_date))
        
        credit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return credit_id
    
    def update_credit_capabilities(self, credit_id: int, 
                                   has_early_full: bool = None,
                                   has_early_partial_period: bool = None,
                                   has_early_partial_payment: bool = None,
                                   has_holidays: bool = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if has_early_full is not None:
            updates.append("has_early_full = ?")
            params.append(has_early_full)
        if has_early_partial_period is not None:
            updates.append("has_early_partial_period = ?")
            params.append(has_early_partial_period)
        if has_early_partial_payment is not None:
            updates.append("has_early_partial_payment = ?")
            params.append(has_early_partial_payment)
        if has_holidays is not None:
            updates.append("has_holidays = ?")
            params.append(has_holidays)
        
        if updates:
            params.append(credit_id)
            query = f"UPDATE credits SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
    
    def get_user_credits(self, user_id: int, active_only: bool = True) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM credits WHERE user_id = ?"
        params = [user_id]
        
        if active_only:
            query += " AND is_active = 1"
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        credits = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return credits
    
    def get_credit_by_id(self, credit_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM credits WHERE id = ?", (credit_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(zip(columns, row))
        return None
    
    def update_credit_debt(self, credit_id: int, new_debt: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE credits SET remaining_debt = ? WHERE id = ?
        """, (new_debt, credit_id))
        conn.commit()
        conn.close()
    
    def add_credit_payment(self, credit_id: int, amount: float, 
                          payment_type: str, payment_date: str = None, notes: str = None):
        if payment_date is None:
            payment_date = date.today().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Добавляем платеж
        cursor.execute("""
            INSERT INTO credit_payments (credit_id, payment_date, amount, payment_type, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (credit_id, payment_date, amount, payment_type, notes))
        
        # Обновляем долг и текущий месяц
        credit = self.get_credit_by_id(credit_id)
        new_debt = credit['remaining_debt'] - amount
        
        if new_debt <= 0:
            new_debt = 0
            cursor.execute("UPDATE credits SET is_active = 0 WHERE id = ?", (credit_id,))
        
        cursor.execute("""
            UPDATE credits 
            SET remaining_debt = ?, current_month = current_month + 1 
            WHERE id = ?
        """, (new_debt, credit_id))
        
        conn.commit()
        conn.close()
    
    def add_credit_holiday(self, credit_id: int, start_date: str, end_date: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO credit_holidays (credit_id, start_date, end_date)
            VALUES (?, ?, ?)
        """, (credit_id, start_date, end_date))
        conn.commit()
        conn.close()
    
    # ==================== ДОЛГИ ====================
    
    def add_debt(self, user_id: int, person_name: str, amount: float,
                 debt_type: str, description: str = None, debt_date: str = None) -> int:
        if debt_date is None:
            debt_date = date.today().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO debts (user_id, person_name, amount, debt_type, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, person_name, amount, debt_type, description, debt_date))
        
        debt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return debt_id
    
    def get_user_debts(self, user_id: int, unpaid_only: bool = True) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM debts WHERE user_id = ?"
        params = [user_id]
        
        if unpaid_only:
            query += " AND is_paid = 0"
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        debts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return debts
    
    def mark_debt_paid(self, debt_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE debts SET is_paid = 1 WHERE id = ?", (debt_id,))
        conn.commit()
        conn.close()
    
    # ==================== КАТЕГОРИИ ====================
    
    def add_category(self, user_id: int, name: str, cat_type: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO categories (user_id, name, type)
            VALUES (?, ?, ?)
        """, (user_id, name, cat_type))
        
        category_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return category_id
    
    def get_user_categories(self, user_id: int, cat_type: str = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if cat_type:
            cursor.execute("""
                SELECT * FROM categories WHERE user_id = ? AND type = ?
            """, (user_id, cat_type))
        else:
            cursor.execute("SELECT * FROM categories WHERE user_id = ?", (user_id,))
        
        columns = [description[0] for description in cursor.description]
        categories = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return categories
    
    # ==================== ДОХОДЫ ====================
    
    def add_income(self, user_id: int, amount: float, category_id: int = None,
                   description: str = None, income_date: str = None) -> int:
        if income_date is None:
            income_date = date.today().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO incomes (user_id, category_id, amount, description, date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, category_id, amount, description, income_date))
        
        income_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return income_id
    
    def get_user_incomes(self, user_id: int, start_date: str = None, 
                        end_date: str = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM incomes WHERE user_id = ?"
        params = [user_id]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        incomes = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return incomes
    
    # ==================== РАСХОДЫ ====================
    
    def add_expense(self, user_id: int, amount: float, category_id: int = None,
                    description: str = None, expense_date: str = None) -> int:
        if expense_date is None:
            expense_date = date.today().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses (user_id, category_id, amount, description, date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, category_id, amount, description, expense_date))
        
        expense_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return expense_id
    
    def get_user_expenses(self, user_id: int, start_date: str = None,
                         end_date: str = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM expenses WHERE user_id = ?"
        params = [user_id]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        expenses = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return expenses
    
    # ==================== ИНВЕСТИЦИИ ====================
    
    def add_investment(self, user_id: int, asset_name: str, 
                      invested_amount: float, current_value: float = None) -> int:
        if current_value is None:
            current_value = invested_amount
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investments (user_id, asset_name, invested_amount, 
                                    current_value, last_updated)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, asset_name, invested_amount, current_value, date.today().isoformat()))
        
        investment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return investment_id
    
    def update_investment_value(self, investment_id: int, new_value: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE investments 
            SET current_value = ?, last_updated = ? 
            WHERE id = ?
        """, (new_value, date.today().isoformat(), investment_id))
        conn.commit()
        conn.close()
    
    def get_user_investments(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM investments WHERE user_id = ?", (user_id,))
        columns = [description[0] for description in cursor.description]
        investments = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return investments
    
    # ==================== СБЕРЕЖЕНИЯ ====================
    
    def add_savings(self, user_id: int, amount: float, savings_date: str = None) -> int:
        if savings_date is None:
            savings_date = date.today().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO savings (user_id, amount, date)
            VALUES (?, ?, ?)
        """, (user_id, amount, savings_date))
        
        savings_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return savings_id
    
    def get_latest_savings(self, user_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM savings 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (user_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(zip(columns, row))
        return None

# ==================== ПЛАНИРОВАНИЕ БЮДЖЕТА ====================
    
    def create_or_update_budget(self, user_id: int, month: int, year: int,
                                income_categories: dict = None, expense_categories: dict = None,
                                credit_expenses: float = 0, notes: str = None) -> int:
        """
        Создать или обновить бюджет на месяц с детализацией по категориям
        
        Args:
            user_id: ID пользователя
            month: Месяц (1-12)
            year: Год
            income_categories: Словарь {category_id: amount} для доходов
            expense_categories: Словарь {category_id: amount} для расходов
            credit_expenses: Расходы по кредитам
            notes: Примечания
        
        Returns:
            ID бюджета
        """
        import json
        
        if income_categories is None:
            income_categories = {}
        if expense_categories is None:
            expense_categories = {}
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем, существует ли бюджет
        cursor.execute("""
            SELECT id FROM budget_plans 
            WHERE user_id = ? AND month = ? AND year = ?
        """, (user_id, month, year))
        
        existing = cursor.fetchone()
        
        # Конвертируем в JSON строки
        income_json = json.dumps(income_categories)
        expense_json = json.dumps(expense_categories)
        
        # Рассчитываем общие суммы
        total_income = sum(income_categories.values())
        total_expenses = sum(expense_categories.values())
        
        if existing:
            # Обновляем существующий
            cursor.execute("""
                UPDATE budget_plans
                SET planned_income = ?,
                    planned_expenses = ?,
                    credit_expenses = ?,
                    custom_expenses = ?,
                    notes = ?,
                    income_categories = ?,
                    expense_categories = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (total_income, total_expenses, credit_expenses, 
                None, notes, income_json, expense_json, existing[0]))
            budget_id = existing[0]
        else:
            # Создаем новый
            cursor.execute("""
                INSERT INTO budget_plans (
                    user_id, month, year, planned_income, planned_expenses,
                    credit_expenses, custom_expenses, notes, income_categories, expense_categories
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, month, year, total_income, total_expenses,
                credit_expenses, None, notes, income_json, expense_json))
            budget_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return budget_id

    def update_budget_category(self, budget_id: int, category_type: str, 
                            category_id: int, amount: float) -> bool:
        """
        Обновить планируемую сумму для конкретной категории в бюджете
        
        Args:
            budget_id: ID бюджета
            category_type: 'income' или 'expense'
            category_id: ID категории
            amount: Новая сумма
        
        Returns:
            True если успешно
        """
        import json
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Получаем текущий бюджет
        cursor.execute("""
            SELECT income_categories, expense_categories 
            FROM budget_plans WHERE id = ?
        """, (budget_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        
        income_cats = json.loads(row[0]) if row[0] else {}
        expense_cats = json.loads(row[1]) if row[1] else {}
        
        # Обновляем нужную категорию
        if category_type == 'income':
            income_cats[str(category_id)] = amount
            new_income = sum(income_cats.values())
            cursor.execute("""
                UPDATE budget_plans 
                SET income_categories = ?, planned_income = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json.dumps(income_cats), new_income, budget_id))
        else:
            expense_cats[str(category_id)] = amount
            new_expenses = sum(expense_cats.values())
            cursor.execute("""
                UPDATE budget_plans 
                SET expense_categories = ?, planned_expenses = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json.dumps(expense_cats), new_expenses, budget_id))
        
        conn.commit()
        conn.close()
        return True

    def get_budget_with_categories(self, user_id: int, month: int, year: int) -> Optional[Dict]:
        """Получить бюджет с распарсенными категориями"""
        import json
        
        budget = self.get_budget(user_id, month, year)
        if not budget:
            return None
        
        # Парсим JSON строки в словари
        if budget.get('income_categories'):
            budget['income_categories'] = json.loads(budget['income_categories'])
        else:
            budget['income_categories'] = {}
        
        if budget.get('expense_categories'):
            budget['expense_categories'] = json.loads(budget['expense_categories'])
        else:
            budget['expense_categories'] = {}
        
        return budget

    def check_expense_against_budget(self, user_id: int, category_id: int, 
                                    amount: float, expense_date: str) -> Dict:
        """
        Проверяет расход на соответствие бюджету
        
        Returns:
            Dict с информацией: {
                'has_budget': bool,
                'category_in_budget': bool,
                'spent_before': float,
                'planned': float,
                'spent_after': float,
                'percent_used': float,
                'over_budget': bool
            }
        """
        import json
        from datetime import datetime
        
        # Определяем месяц и год из даты расхода
        date_obj = datetime.strptime(expense_date, '%Y-%m-%d')
        month = date_obj.month
        year = date_obj.year
        
        # Получаем бюджет
        budget = self.get_budget(user_id, month, year)
        
        result = {
            'has_budget': False,
            'category_in_budget': False,
            'spent_before': 0,
            'planned': 0,
            'spent_after': 0,
            'percent_used': 0,
            'over_budget': False
        }
        
        if not budget:
            return result
        
        result['has_budget'] = True
        
        # Парсим категории расходов из бюджета
        expense_cats = json.loads(budget['expense_categories']) if budget.get('expense_categories') else {}
        
        # Проверяем есть ли эта категория в бюджете
        cat_key = str(category_id)
        if cat_key not in expense_cats:
            return result
        
        result['category_in_budget'] = True
        result['planned'] = expense_cats[cat_key]
        
        # Считаем сколько уже потрачено по этой категории за месяц (до добавления нового расхода)
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        expenses = self.get_user_expenses(user_id, start_date, end_date)
        spent = sum(e['amount'] for e in expenses if e.get('category_id') == category_id)
        
        result['spent_before'] = spent
        result['spent_after'] = spent + amount
        
        if result['planned'] > 0:
            result['percent_used'] = (result['spent_after'] / result['planned']) * 100
            result['over_budget'] = result['spent_after'] > result['planned']
        
        return result
    
    def get_budget(self, user_id: int, month: int, year: int) -> Optional[Dict]:
        """Получить бюджет на месяц"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM budget_plans
            WHERE user_id = ? AND month = ? AND year = ?
        """, (user_id, month, year))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_user_budgets(self, user_id: int, limit: int = 12) -> List[Dict]:
        """Получить список бюджетов пользователя"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM budget_plans
            WHERE user_id = ?
            ORDER BY year DESC, month DESC
            LIMIT ?
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def delete_budget(self, budget_id: int) -> bool:
        """Удалить бюджет"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM budget_plans WHERE id = ?", (budget_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted


    # -------- Удаление дохода --------
    def delete_income(self, user_id: int, income_id: int) -> bool:
        """Удаляет доход по ID, проверяя владельца.
        Returns True если удалено, False если записи нет или не принадлежит пользователю.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM incomes WHERE id = ? AND user_id = ?", (income_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def get_last_income(self, user_id: int):
        """Возвращает последний доход пользователя (dict) или None"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM incomes WHERE user_id = ? ORDER BY id DESC LIMIT 1""", (user_id,))
        row = cursor.fetchone()
        columns = [d[0] for d in cursor.description] if cursor.description else []
        conn.close()
        if row:
            return dict(zip(columns, row))
        return None

    # -------- Удаление расхода --------
    def delete_expense(self, user_id: int, expense_id: int) -> bool:
        """Удаляет расход по ID, проверяя владельца.
        Returns True если удалено, False если записи нет или не принадлежит пользователю.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def get_last_expense(self, user_id: int):
        """Возвращает последний расход пользователя (dict) или None"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1""", (user_id,))
        row = cursor.fetchone()
        columns = [d[0] for d in cursor.description] if cursor.description else []
        conn.close()
        if row:
            return dict(zip(columns, row))
        return None

    def suggest_budget_categories(self, user_id: int, lookback_months: int = 3) -> Dict:
        """
        Предлагает категории и суммы для бюджета на основе истории
        
        Args:
            user_id: ID пользователя
            lookback_months: Сколько месяцев назад анализировать
        
        Returns:
            Dict с предложениями: {
                'income': {category_id: avg_amount},
                'expense': {category_id: avg_amount}
            }
        """
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_months * 30)
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Получаем доходы и расходы за период
        incomes = self.get_user_incomes(user_id, start_str, end_str)
        expenses = self.get_user_expenses(user_id, start_str, end_str)
        
        # Группируем по категориям и считаем средние
        income_by_cat = defaultdict(list)
        for inc in incomes:
            if inc.get('category_id'):
                income_by_cat[inc['category_id']].append(inc['amount'])
        
        expense_by_cat = defaultdict(list)
        for exp in expenses:
            if exp.get('category_id'):
                expense_by_cat[exp['category_id']].append(exp['amount'])
        
        # Считаем средние значения
        suggested_income = {
            cat_id: sum(amounts) / lookback_months 
            for cat_id, amounts in income_by_cat.items()
        }
        
        suggested_expense = {
            cat_id: sum(amounts) / lookback_months 
            for cat_id, amounts in expense_by_cat.items()
        }
        
        return {
            'income': suggested_income,
            'expense': suggested_expense
        }
