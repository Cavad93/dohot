import sqlite3
import shutil
import os
from datetime import datetime, date
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """Управление резервными копиями базы данных"""
    
    def __init__(self, db_path: str = "dohot.db", backup_dir: str = "backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
    
    def create_backup(self) -> Optional[str]:
        """
        Создать резервную копию базы данных
        
        Returns:
            Путь к файлу резервной копии или None при ошибке
        """
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"Database file {self.db_path} not found")
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"dohot_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
            
            return backup_path
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Восстановить базу данных из резервной копии
        
        Args:
            backup_path: Путь к файлу резервной копии
            
        Returns:
            True при успехе, False при ошибке
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup file {backup_path} not found")
                return False
            
            # Создаём резервную копию текущей БД перед восстановлением
            if os.path.exists(self.db_path):
                safety_backup = f"{self.db_path}.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.db_path, safety_backup)
                logger.info(f"Safety backup created: {safety_backup}")
            
            # Восстанавливаем из бэкапа
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Database restored from: {backup_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """
        Получить список всех резервных копий
        
        Returns:
            Список словарей с информацией о бэкапах
        """
        backups = []
        
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("dohot_backup_") and filename.endswith(".db"):
                    filepath = os.path.join(self.backup_dir, filename)
                    stat = os.stat(filepath)
                    
                    backups.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime)
                    })
            
            # Сортируем по дате создания (новые первые)
            backups.sort(key=lambda x: x['created'], reverse=True)
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10):
        """
        Удалить старые резервные копии, оставив только последние
        
        Args:
            keep_count: Количество последних копий для сохранения
        """
        try:
            backups = self.list_backups()
            
            if len(backups) > keep_count:
                to_delete = backups[keep_count:]
                
                for backup in to_delete:
                    os.remove(backup['filepath'])
                    logger.info(f"Deleted old backup: {backup['filename']}")
                
                logger.info(f"Cleaned up {len(to_delete)} old backups")
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")


class DatabaseValidator:
    """Валидация и проверка целостности базы данных"""
    
    def __init__(self, db_path: str = "dohot.db"):
        self.db_path = db_path
    
    def check_integrity(self) -> bool:
        """
        Проверить целостность базы данных
        
        Returns:
            True если БД в порядке, False если есть проблемы
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем целостность
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            conn.close()
            
            if result[0] == "ok":
                logger.info("Database integrity check: OK")
                return True
            else:
                logger.error(f"Database integrity check failed: {result[0]}")
                return False
        except Exception as e:
            logger.error(f"Error checking database integrity: {e}")
            return False
    
    def check_tables(self) -> Dict[str, bool]:
        """
        Проверить наличие всех необходимых таблиц
        
        Returns:
            Словарь с результатами проверки каждой таблицы
        """
        required_tables = [
            'users', 'credits', 'credit_payments', 'credit_holidays',
            'debts', 'categories', 'incomes', 'expenses',
            'investments', 'savings'
        ]
        
        results = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = set(row[0] for row in cursor.fetchall())
            
            for table in required_tables:
                results[table] = table in existing_tables
            
            conn.close()
            
            missing_tables = [t for t, exists in results.items() if not exists]
            if missing_tables:
                logger.warning(f"Missing tables: {missing_tables}")
            else:
                logger.info("All required tables exist")
        except Exception as e:
            logger.error(f"Error checking tables: {e}")
        
        return results
    
    def get_database_stats(self) -> Dict:
        """
        Получить статистику по базе данных
        
        Returns:
            Словарь со статистикой
        """
        stats = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Размер БД
            if os.path.exists(self.db_path):
                stats['size_bytes'] = os.path.getsize(self.db_path)
                stats['size_mb'] = stats['size_bytes'] / (1024 * 1024)
            
            # Количество записей в таблицах
            tables = ['users', 'credits', 'debts', 'incomes', 'expenses', 'investments']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # Общее количество пользователей
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users")
            stats['total_users'] = cursor.fetchone()[0]
            
            conn.close()
            
            logger.info(f"Database stats collected: {stats}")
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
        
        return stats


class DataExporter:
    """Экспорт данных в различные форматы"""
    
    def __init__(self, db_path: str = "dohot.db"):
        self.db_path = db_path
    
    def export_to_csv(self, user_id: int, output_dir: str = "exports") -> Dict[str, str]:
        """
        Экспортировать все данные пользователя в CSV файлы
        
        Args:
            user_id: ID пользователя
            output_dir: Директория для сохранения файлов
            
        Returns:
            Словарь с путями к созданным файлам
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        exported_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            import csv
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Экспортируем кредиты
            cursor.execute("SELECT * FROM credits WHERE user_id = ?", (user_id,))
            credits = cursor.fetchall()
            if credits:
                filename = f"credits_{user_id}_{timestamp}.csv"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=credits[0].keys())
                    writer.writeheader()
                    writer.writerows([dict(row) for row in credits])
                exported_files['credits'] = filepath
            
            # Экспортируем долги
            cursor.execute("SELECT * FROM debts WHERE user_id = ?", (user_id,))
            debts = cursor.fetchall()
            if debts:
                filename = f"debts_{user_id}_{timestamp}.csv"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=debts[0].keys())
                    writer.writeheader()
                    writer.writerows([dict(row) for row in debts])
                exported_files['debts'] = filepath
            
            # Экспортируем доходы
            cursor.execute("SELECT * FROM incomes WHERE user_id = ?", (user_id,))
            incomes = cursor.fetchall()
            if incomes:
                filename = f"incomes_{user_id}_{timestamp}.csv"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=incomes[0].keys())
                    writer.writeheader()
                    writer.writerows([dict(row) for row in incomes])
                exported_files['incomes'] = filepath
            
            # Экспортируем расходы
            cursor.execute("SELECT * FROM expenses WHERE user_id = ?", (user_id,))
            expenses = cursor.fetchall()
            if expenses:
                filename = f"expenses_{user_id}_{timestamp}.csv"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=expenses[0].keys())
                    writer.writeheader()
                    writer.writerows([dict(row) for row in expenses])
                exported_files['expenses'] = filepath
            
            # Экспортируем инвестиции
            cursor.execute("SELECT * FROM investments WHERE user_id = ?", (user_id,))
            investments = cursor.fetchall()
            if investments:
                filename = f"investments_{user_id}_{timestamp}.csv"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=investments[0].keys())
                    writer.writeheader()
                    writer.writerows([dict(row) for row in investments])
                exported_files['investments'] = filepath
            
            conn.close()
            logger.info(f"Exported {len(exported_files)} files for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
        
        return exported_files


class DateHelper:
    """Вспомогательные функции для работы с датами"""
    
    @staticmethod
    def parse_date(date_string: str) -> Optional[date]:
        """
        Парсинг даты из различных форматов
        
        Args:
            date_string: Строка с датой
            
        Returns:
            date объект или None при ошибке
        """
        formats = [
            "%d.%m.%Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%Y/%m/%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt).date()
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def format_date(date_obj: date, format: str = "%d.%m.%Y") -> str:
        """
        Форматирование даты в строку
        
        Args:
            date_obj: date объект
            format: Формат строки
            
        Returns:
            Отформатированная строка
        """
        return date_obj.strftime(format)
    
    @staticmethod
    def get_month_name(month: int, lang: str = "ru") -> str:
        """
        Получить название месяца
        
        Args:
            month: Номер месяца (1-12)
            lang: Язык ('ru' или 'en')
            
        Returns:
            Название месяца
        """
        if lang == "ru":
            months = [
                "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
            ]
        else:
            months = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
        
        return months[month - 1] if 1 <= month <= 12 else ""


class NumberFormatter:
    """Форматирование чисел"""
    
    @staticmethod
    def format_money(amount: float, currency: str = "руб.") -> str:
        """
        Форматирование денежной суммы
        
        Args:
            amount: Сумма
            currency: Валюта
            
        Returns:
            Отформатированная строка
        """
        return f"{amount:,.2f} {currency}".replace(",", " ")
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """
        Форматирование процентов
        
        Args:
            value: Значение
            decimals: Количество знаков после запятой
            
        Returns:
            Отформатированная строка
        """
        return f"{value:.{decimals}f}%"
    
    @staticmethod
    def parse_money(money_string: str) -> Optional[float]:
        """
        Парсинг денежной суммы из строки
        
        Args:
            money_string: Строка с суммой
            
        Returns:
            float значение или None при ошибке
        """
        try:
            # Убираем пробелы, запятые, заменяем точку
            cleaned = money_string.replace(" ", "").replace(",", ".")
            # Убираем буквы (валюту)
            cleaned = ''.join(c for c in cleaned if c.isdigit() or c == '.')
            return float(cleaned)
        except (ValueError, AttributeError):
            return None


class TextHelper:
    """Вспомогательные функции для работы с текстом"""
    
    @staticmethod
    def truncate(text: str, max_length: int = 50, suffix: str = "...") -> str:
        """
        Обрезать текст до указанной длины
        
        Args:
            text: Исходный текст
            max_length: Максимальная длина
            suffix: Суффикс для обрезанного текста
            
        Returns:
            Обрезанный текст
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        Экранировать специальные символы Markdown
        
        Args:
            text: Исходный текст
            
        Returns:
            Экранированный текст
        """
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, '\\' + char)
        return text


def format_credit_info(credit: Dict, detailed: bool = False) -> str:
    """
    Форматирование информации о кредите для отображения
    
    Args:
        credit: Словарь с данными кредита
        detailed: Показывать детальную информацию
        
    Returns:
        Отформатированная строка
    """
    from calculations import FinancialCalculator
    
    text = f"🏦 {credit['display_name']}\n"
    text += f"💰 Остаток: {NumberFormatter.format_money(credit['remaining_debt'])}\n"
    text += f"💵 Платёж: {NumberFormatter.format_money(credit['monthly_payment'])}\n"
    
    if detailed:
        remaining = FinancialCalculator.calculate_remaining_months(credit)
        next_payment = FinancialCalculator.calculate_next_payment_date(credit)
        
        text += f"📈 Ставка: {credit['interest_rate']}%\n"
        text += f"⏱ Осталось: {remaining} мес.\n"
        text += f"📅 Следующий платёж: {DateHelper.format_date(next_payment)}\n"
        text += f"📊 Прогресс: {credit['current_month']}/{credit['total_months']} мес.\n"
    
    return text


def format_debt_info(debt: Dict) -> str:
    """
    Форматирование информации о долге для отображения
    
    Args:
        debt: Словарь с данными долга
        
    Returns:
        Отформатированная строка
    """
    debt_type_text = "Взял у" if debt['debt_type'] == 'taken' else "Дал"
    status = "✅" if debt['is_paid'] else "🔴"
    
    text = f"{status} {debt_type_text} {debt['person_name']}\n"
    text += f"💰 Сумма: {NumberFormatter.format_money(debt['amount'])}\n"
    text += f"📅 Дата: {debt['date']}\n"
    
    if debt['description']:
        text += f"📝 {debt['description']}\n"
    
    return text
