import sqlite3
from datetime import datetime, date
from typing import List, Optional, Dict
import json


class Database:
    def __init__(self, db_path: str = "dohot.db"):
        self.db_path = db_path
        self.init_database()
    
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
