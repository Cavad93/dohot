"""
Модуль для работы с кредитными картами
Отдельная реализация от обычных кредитов
"""

import sqlite3
from datetime import date, datetime
from typing import List, Dict, Optional


class CreditCardManager:
    """Менеджер для управления кредитными картами"""
    
    def __init__(self, db_path: str = 'financial_bot.db'):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Инициализация таблиц для кредитных карт"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_name TEXT NOT NULL,
                bank_name TEXT NOT NULL,
                credit_limit REAL NOT NULL,
                current_balance REAL NOT NULL,
                interest_rate REAL NOT NULL,
                minimum_payment_percent REAL NOT NULL,
                grace_period_days INTEGER DEFAULT 55,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_card_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                transaction_date DATE NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_before REAL NOT NULL,
                balance_after REAL NOT NULL,
                interest_charged REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES credit_cards(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_credit_card(self, user_id: int, card_name: str, bank_name: str,
                       credit_limit: float, interest_rate: float,
                       minimum_payment_percent: float = 5.0,
                       grace_period_days: int = 55) -> int:
        """
        Добавить новую кредитную карту
        
        Args:
            user_id: ID пользователя
            card_name: Название карты (например, "Momentum", "All Airlines")
            bank_name: Название банка
            credit_limit: Кредитный лимит
            interest_rate: Годовая процентная ставка
            minimum_payment_percent: Процент минимального платежа от задолженности
            grace_period_days: Льготный период (дней)
            
        Returns:
            ID созданной карты
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO credit_cards (
                user_id, card_name, bank_name, credit_limit, current_balance,
                interest_rate, minimum_payment_percent, grace_period_days
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, card_name, bank_name, credit_limit, credit_limit,
              interest_rate, minimum_payment_percent, grace_period_days))
        
        card_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return card_id
    
    def get_user_credit_cards(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """Получить кредитные карты пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM credit_cards WHERE user_id = ?"
        params = [user_id]
        
        if active_only:
            query += " AND is_active = 1"
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        cards = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return cards
    
    def get_card_by_id(self, card_id: int) -> Optional[Dict]:
        """Получить карту по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM credit_cards WHERE id = ?", (card_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(zip(columns, row))
        return None
    
    def calculate_interest(self, amount: float, annual_rate: float, days: int = 30) -> float:
        """
        Рассчитать проценты за период
        
        Args:
            amount: Сумма задолженности
            annual_rate: Годовая ставка в процентах
            days: Количество дней
            
        Returns:
            Сумма процентов
        """
        daily_rate = annual_rate / 365 / 100
        return amount * daily_rate * days
    
    def add_money_to_card(self, card_id: int, amount: float,
                         transaction_date: str = None, notes: str = None) -> Dict:
        """
        Пополнить кредитную карту с учетом процентов
        
        Args:
            card_id: ID карты
            amount: Сумма пополнения
            transaction_date: Дата транзакции
            notes: Примечания
            
        Returns:
            Dict с информацией о транзакции:
            {
                'balance_before': float,
                'amount_added': float,
                'interest_charged': float,
                'balance_after': float,
                'available_credit': float
            }
        """
        if transaction_date is None:
            transaction_date = date.today().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        card = self.get_card_by_id(card_id)
        if not card:
            conn.close()
            raise ValueError(f"Карта с ID {card_id} не найдена")
        
        balance_before = card['current_balance']
        used_credit = card['credit_limit'] - balance_before
        
        if used_credit <= 0:
            conn.close()
            return {
                'balance_before': balance_before,
                'amount_added': 0,
                'interest_charged': 0,
                'balance_after': balance_before,
                'available_credit': balance_before,
                'message': 'Карта не используется, пополнение не требуется'
            }
        
        interest_charged = self.calculate_interest(used_credit, card['interest_rate'])
        
        effective_repayment = amount - interest_charged
        
        if effective_repayment < 0:
            effective_repayment = 0
            interest_charged = amount
        
        new_balance = min(balance_before + effective_repayment, card['credit_limit'])
        
        cursor.execute("""
            UPDATE credit_cards 
            SET current_balance = ?
            WHERE id = ?
        """, (new_balance, card_id))
        
        cursor.execute("""
            INSERT INTO credit_card_transactions (
                card_id, transaction_date, transaction_type, amount,
                balance_before, balance_after, interest_charged, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (card_id, transaction_date, 'repayment', amount,
              balance_before, new_balance, interest_charged, notes))
        
        conn.commit()
        conn.close()
        
        return {
            'balance_before': balance_before,
            'amount_added': amount,
            'interest_charged': interest_charged,
            'effective_repayment': effective_repayment,
            'balance_after': new_balance,
            'available_credit': new_balance,
            'used_credit': card['credit_limit'] - new_balance
        }
    
    def spend_from_card(self, card_id: int, amount: float,
                       transaction_date: str = None, notes: str = None) -> Dict:
        """
        Потратить деньги с кредитной карты
        
        Args:
            card_id: ID карты
            amount: Сумма покупки
            transaction_date: Дата транзакции
            notes: Примечания
            
        Returns:
            Dict с информацией о транзакции
        """
        if transaction_date is None:
            transaction_date = date.today().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        card = self.get_card_by_id(card_id)
        if not card:
            conn.close()
            raise ValueError(f"Карта с ID {card_id} не найдена")
        
        balance_before = card['current_balance']
        
        if amount > balance_before:
            conn.close()
            raise ValueError(f"Недостаточно средств на карте. Доступно: {balance_before:.2f}")
        
        new_balance = balance_before - amount
        
        cursor.execute("""
            UPDATE credit_cards 
            SET current_balance = ?
            WHERE id = ?
        """, (new_balance, card_id))
        
        cursor.execute("""
            INSERT INTO credit_card_transactions (
                card_id, transaction_date, transaction_type, amount,
                balance_before, balance_after, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (card_id, transaction_date, 'purchase', amount,
              balance_before, new_balance, notes))
        
        conn.commit()
        conn.close()
        
        return {
            'balance_before': balance_before,
            'amount_spent': amount,
            'balance_after': new_balance,
            'available_credit': new_balance,
            'used_credit': card['credit_limit'] - new_balance
        }
    
    def calculate_minimum_payment(self, card_id: int) -> float:
        """Рассчитать минимальный платеж по карте"""
        card = self.get_card_by_id(card_id)
        if not card:
            return 0
        
        used_credit = card['credit_limit'] - card['current_balance']
        
        if used_credit <= 0:
            return 0
        
        minimum_payment = used_credit * (card['minimum_payment_percent'] / 100)
        
        minimum_payment = max(minimum_payment, 300)
        
        return round(minimum_payment, 2)
    
    def get_cards_requiring_payment(self, user_id: int) -> List[Dict]:
        """
        Получить карты, по которым требуется платеж
        Возвращает карты с задолженностью и рассчитанным минимальным платежом
        """
        cards = self.get_user_credit_cards(user_id, active_only=True)
        cards_with_debt = []
        
        for card in cards:
            used_credit = card['credit_limit'] - card['current_balance']
            if used_credit > 0:
                minimum_payment = self.calculate_minimum_payment(card['id'])
                card['used_credit'] = used_credit
                card['minimum_payment'] = minimum_payment
                cards_with_debt.append(card)
        
        return cards_with_debt
    
    def get_total_minimum_payment(self, user_id: int) -> float:
        """Получить общую сумму минимальных платежей по всем картам"""
        cards = self.get_cards_requiring_payment(user_id)
        return sum(card['minimum_payment'] for card in cards)
    
    def get_card_transactions(self, card_id: int, limit: int = 50) -> List[Dict]:
        """Получить историю транзакций по карте"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM credit_card_transactions 
            WHERE card_id = ? 
            ORDER BY transaction_date DESC, created_at DESC 
            LIMIT ?
        """, (card_id, limit))
        
        columns = [description[0] for description in cursor.description]
        transactions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return transactions
    
    def deactivate_card(self, card_id: int):
        """Деактивировать карту"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE credit_cards SET is_active = 0 WHERE id = ?", (card_id,))
        conn.commit()
        conn.close()