#!/usr/bin/env python3
"""
Система миграций для базы данных DoHot

Миграции позволяют безопасно обновлять структуру БД при выходе новых версий.

Использование:
    python migrations.py --check    # Проверить текущую версию
    python migrations.py --migrate  # Применить миграции
    python migrations.py --rollback # Откатить последнюю миграцию
"""

import sqlite3
import argparse
import sys
from datetime import datetime
from typing import List, Tuple


class Migration:
    """Базовый класс для миграции"""
    
    def __init__(self, version: int, description: str):
        self.version = version
        self.description = description
    
    def up(self, conn: sqlite3.Connection):
        """Применить миграцию"""
        raise NotImplementedError
    
    def down(self, conn: sqlite3.Connection):
        """Откатить миграцию"""
        raise NotImplementedError


class Migration001_InitialSchema(Migration):
    """Начальная схема базы данных"""
    
    def __init__(self):
        super().__init__(1, "Initial schema")
    
    def up(self, conn: sqlite3.Connection):
        """Создаёт начальную схему (уже реализовано в database.py)"""
        pass
    
    def down(self, conn: sqlite3.Connection):
        """Откат невозможен для начальной схемы"""
        pass


class Migration002_AddCreditNotes(Migration):
    """Добавляет поле notes в таблицу кредитов"""
    
    def __init__(self):
        super().__init__(2, "Add notes field to credits")
    
    def up(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE credits ADD COLUMN notes TEXT")
            conn.commit()
            print(f"✅ Migration {self.version}: {self.description} - applied")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"⚠️  Migration {self.version}: Already applied")
            else:
                raise
    
    def down(self, conn: sqlite3.Connection):
        # SQLite не поддерживает DROP COLUMN, нужно пересоздавать таблицу
        print(f"⚠️  Migration {self.version}: Rollback not supported (SQLite limitation)")


class Migration003_AddCategoryIcons(Migration):
    """Добавляет иконки для категорий"""
    
    def __init__(self):
        super().__init__(3, "Add icon field to categories")
    
    def up(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE categories ADD COLUMN icon TEXT")
            conn.commit()
            print(f"✅ Migration {self.version}: {self.description} - applied")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"⚠️  Migration {self.version}: Already applied")
            else:
                raise
    
    def down(self, conn: sqlite3.Connection):
        print(f"⚠️  Migration {self.version}: Rollback not supported (SQLite limitation)")


class Migration004_AddPaymentReminders(Migration):
    """Добавляет таблицу напоминаний о платежах"""
    
    def __init__(self):
        super().__init__(4, "Add payment reminders table")
    
    def up(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credit_id INTEGER NOT NULL,
                reminder_date DATE NOT NULL,
                is_sent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (credit_id) REFERENCES credits(id)
            )
        """)
        conn.commit()
        print(f"✅ Migration {self.version}: {self.description} - applied")
    
    def down(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS payment_reminders")
        conn.commit()
        print(f"✅ Migration {self.version}: Rolled back")


class Migration005_AddRecurringTransactions(Migration):
    """Добавляет поддержку повторяющихся транзакций"""
    
    def __init__(self):
        super().__init__(5, "Add recurring transactions support")
    
    def up(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        
        # Добавляем поля для повторяющихся доходов
        try:
            cursor.execute("ALTER TABLE incomes ADD COLUMN is_recurring BOOLEAN DEFAULT 0")
            cursor.execute("ALTER TABLE incomes ADD COLUMN recurring_type TEXT")
            cursor.execute("ALTER TABLE incomes ADD COLUMN recurring_day INTEGER")
        except sqlite3.OperationalError:
            pass
        
        # Добавляем поля для повторяющихся расходов
        try:
            cursor.execute("ALTER TABLE expenses ADD COLUMN is_recurring BOOLEAN DEFAULT 0")
            cursor.execute("ALTER TABLE expenses ADD COLUMN recurring_type TEXT")
            cursor.execute("ALTER TABLE expenses ADD COLUMN recurring_day INTEGER")
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        print(f"✅ Migration {self.version}: {self.description} - applied")
    
    def down(self, conn: sqlite3.Connection):
        print(f"⚠️  Migration {self.version}: Rollback not supported (SQLite limitation)")


class Migration006_AddBudgetPlanning(Migration):
    """Добавляет таблицу планирования бюджета"""
    
    def __init__(self):
        super().__init__(6, "Add budget planning table")
    
    def up(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budget_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                planned_income REAL DEFAULT 0,
                planned_expenses REAL DEFAULT 0,
                credit_expenses REAL DEFAULT 0,
                custom_expenses TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, month, year)
            )
        """)
        conn.commit()
        print(f"✅ Migration {self.version}: {self.description} - applied")
    
    def down(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS budget_plans")
        conn.commit()
        print(f"✅ Migration {self.version}: Rolled back")

class Migration007_BudgetCategoriesSupport(Migration):
    """Добавляет поддержку категорий в бюджете"""
    
    def __init__(self):
        super().__init__(7, "Add budget categories support")
    
    def up(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        
        # Добавляем поля для хранения категорий доходов и расходов
        try:
            cursor.execute("ALTER TABLE budget_plans ADD COLUMN income_categories TEXT")
            cursor.execute("ALTER TABLE budget_plans ADD COLUMN expense_categories TEXT")
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        print(f"✅ Migration {self.version}: {self.description} - applied")
    
    def down(self, conn: sqlite3.Connection):
        print(f"⚠️  Migration {self.version}: Rollback not supported (SQLite limitation)")


class MigrationManager:
    """Менеджер миграций"""
    
    def __init__(self, db_path: str = "dohot.db"):
        self.db_path = db_path
        self.migrations: List[Migration] = [
            Migration001_InitialSchema(),
            Migration002_AddCreditFields(),
            Migration003_AddDebtFields(),
            Migration004_AddUserPreferences(),
            Migration005_AddRecurringTransactions(),
            Migration006_AddBudgetPlanning(),
            Migration007_BudgetCategoriesSupport(),
        ]
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Создаёт таблицу для отслеживания миграций"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_current_version(self) -> int:
        """Получить текущую версию схемы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(version) FROM schema_migrations")
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result[0] is not None else 0
    
    def get_applied_migrations(self) -> List[Tuple[int, str, str]]:
        """Получить список применённых миграций"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT version, description, applied_at 
            FROM schema_migrations 
            ORDER BY version
        """)
        
        migrations = cursor.fetchall()
        conn.close()
        
        return migrations
    
    def migrate(self, target_version: int = None):
        """
        Применить миграции
        
        Args:
            target_version: Версия до которой мигрировать (None = последняя)
        """
        current_version = self.get_current_version()
        target = target_version or self.migrations[-1].version
        
        print(f"📊 Текущая версия: {current_version}")
        print(f"🎯 Целевая версия: {target}\n")
        
        if current_version >= target:
            print("✅ База данных уже на целевой версии")
            return
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            for migration in self.migrations:
                if migration.version <= current_version:
                    continue
                
                if migration.version > target:
                    break
                
                print(f"🔄 Применяю миграцию {migration.version}: {migration.description}")
                
                migration.up(conn)
                
                # Записываем в таблицу миграций
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO schema_migrations (version, description)
                    VALUES (?, ?)
                """, (migration.version, migration.description))
                conn.commit()
            
            print(f"\n✅ Миграция завершена! Текущая версия: {self.get_current_version()}")
        
        except Exception as e:
            print(f"\n❌ Ошибка при миграции: {e}")
            conn.rollback()
            raise
        
        finally:
            conn.close()
    
    def rollback(self, steps: int = 1):
        """
        Откатить миграции
        
        Args:
            steps: Количество шагов для отката
        """
        current_version = self.get_current_version()
        
        if current_version == 0:
            print("⚠️  Нет миграций для отката")
            return
        
        print(f"📊 Текущая версия: {current_version}")
        print(f"🔙 Откатываем {steps} миграций\n")
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            for i in range(steps):
                if current_version == 0:
                    break
                
                # Находим миграцию для отката
                migration = next(
                    (m for m in self.migrations if m.version == current_version),
                    None
                )
                
                if migration:
                    print(f"🔄 Откатываю миграцию {migration.version}: {migration.description}")
                    migration.down(conn)
                
                # Удаляем из таблицы миграций
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM schema_migrations 
                    WHERE version = ?
                """, (current_version,))
                conn.commit()
                
                current_version -= 1
            
            print(f"\n✅ Откат завершён! Текущая версия: {self.get_current_version()}")
        
        except Exception as e:
            print(f"\n❌ Ошибка при откате: {e}")
            conn.rollback()
            raise
        
        finally:
            conn.close()
    
    def status(self):
        """Показать статус миграций"""
        current_version = self.get_current_version()
        applied = self.get_applied_migrations()
        
        print(f"📊 Текущая версия: {current_version}")
        print(f"📝 Доступно миграций: {len(self.migrations)}\n")
        
        print("Применённые миграции:")
        print(f"{'Версия':<8} {'Описание':<40} {'Применена':<20}")
        print("-" * 70)
        
        for version, description, applied_at in applied:
            print(f"{version:<8} {description:<40} {applied_at:<20}")
        
        print("\nДоступные миграции:")
        print(f"{'Версия':<8} {'Описание':<40} {'Статус':<15}")
        print("-" * 70)
        
        for migration in self.migrations:
            status = "✅ Применена" if migration.version <= current_version else "⏳ Ожидает"
            print(f"{migration.version:<8} {migration.description:<40} {status:<15}")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Система миграций DoHot",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--db',
        default='dohot.db',
        help='Путь к базе данных (по умолчанию: dohot.db)'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Проверить текущую версию схемы'
    )
    
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Применить все ожидающие миграции'
    )
    
    parser.add_argument(
        '--rollback',
        type=int,
        metavar='STEPS',
        help='Откатить N последних миграций'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Показать статус всех миграций'
    )
    
    parser.add_argument(
        '--version',
        type=int,
        metavar='VERSION',
        help='Мигрировать до конкретной версии'
    )
    
    args = parser.parse_args()
    
    manager = MigrationManager(args.db)
    
    if args.check:
        current = manager.get_current_version()
        print(f"📊 Текущая версия схемы: {current}")
        sys.exit(0)
    
    elif args.status:
        manager.status()
        sys.exit(0)
    
    elif args.migrate:
        manager.migrate(args.version)
        sys.exit(0)
    
    elif args.rollback:
        manager.rollback(args.rollback)
        sys.exit(0)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
