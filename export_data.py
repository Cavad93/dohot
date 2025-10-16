#!/usr/bin/env python3
"""
Скрипт для экспорта данных пользователей DoHot

Позволяет экспортировать данные в CSV, JSON для анализа или переноса.

Использование:
    python export_data.py --user 12345              # Экспорт данных пользователя
    python export_data.py --user 12345 --format json # Экспорт в JSON
    python export_data.py --all                     # Экспорт всех пользователей
"""

import argparse
import sys
import os
import json
import csv
from datetime import datetime
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import DataExporter
from database import Database


def export_user_data_csv(db: Database, user_id: int, output_dir: str = "exports"):
    """
    Экспортировать данные пользователя в CSV
    
    Args:
        db: Database instance
        user_id: ID пользователя
        output_dir: Директория для сохранения
    """
    print(f"📊 Экспорт данных пользователя {user_id} в CSV...\n")
    
    exporter = DataExporter(db.db_path)
    files = exporter.export_to_csv(user_id, output_dir)
    
    if files:
        print("✅ Экспортированы файлы:")
        for data_type, filepath in files.items():
            size = os.path.getsize(filepath) / 1024
            print(f"   • {data_type}: {filepath} ({size:.2f} KB)")
        print(f"\n📁 Всего файлов: {len(files)}")
    else:
        print("⚠️  Нет данных для экспорта")


def export_user_data_json(db: Database, user_id: int, output_dir: str = "exports"):
    """
    Экспортировать данные пользователя в JSON
    
    Args:
        db: Database instance
        user_id: ID пользователя
        output_dir: Директория для сохранения
    """
    print(f"📊 Экспорт данных пользователя {user_id} в JSON...\n")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Собираем все данные
    data = {
        'user_id': user_id,
        'export_date': datetime.now().isoformat(),
        'credits': db.get_user_credits(user_id, active_only=False),
        'debts': db.get_user_debts(user_id, unpaid_only=False),
        'categories': db.get_user_categories(user_id),
        'incomes': db.get_user_incomes(user_id),
        'expenses': db.get_user_expenses(user_id),
        'investments': db.get_user_investments(user_id),
        'savings': db.get_latest_savings(user_id)
    }
    
    # Сохраняем в JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"user_{user_id}_data_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    size_kb = os.path.getsize(filepath) / 1024
    print(f"✅ Данные экспортированы: {filepath} ({size_kb:.2f} KB)")
    
    # Статистика
    print(f"\n📊 Статистика:")
    print(f"   • Кредитов: {len(data['credits'])}")
    print(f"   • Долгов: {len(data['debts'])}")
    print(f"   • Категорий: {len(data['categories'])}")
    print(f"   • Доходов: {len(data['incomes'])}")
    print(f"   • Расходов: {len(data['expenses'])}")
    print(f"   • Инвестиций: {len(data['investments'])}")


def export_all_users(db: Database, format: str = "csv", output_dir: str = "exports"):
    """
    Экспортировать данные всех пользователей
    
    Args:
        db: Database instance
        format: Формат экспорта ('csv' или 'json')
        output_dir: Директория для сохранения
    """
    print("📊 Экспорт данных всех пользователей...\n")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not user_ids:
        print("⚠️  Пользователи не найдены")
        return
    
    print(f"👥 Найдено пользователей: {len(user_ids)}\n")
    
    for i, user_id in enumerate(user_ids, 1):
        print(f"[{i}/{len(user_ids)}] Экспорт пользователя {user_id}...")
        
        if format == "csv":
            export_user_data_csv(db, user_id, output_dir)
        else:
            export_user_data_json(db, user_id, output_dir)
        
        print()
    
    print(f"✅ Экспорт завершён! Данные сохранены в: {output_dir}")


def generate_summary_report(db: Database, output_dir: str = "exports"):
    """
    Сгенерировать сводный отчёт по всем пользователям
    
    Args:
        db: Database instance
        output_dir: Директория для сохранения
    """
    print("📊 Генерация сводного отчёта...\n")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Общая статистика
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*), SUM(remaining_debt) FROM credits WHERE is_active = 1")
    total_credits, total_debt = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM debts WHERE is_paid = 0")
    total_debts, total_debt_amount = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM incomes")
    total_incomes_count, total_incomes_amount = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM expenses")
    total_expenses_count, total_expenses_amount = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*), SUM(current_value) FROM investments")
    total_investments_count, total_investments_value = cursor.fetchone()
    
    conn.close()
    
    # Формируем отчёт
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║           СВОДНЫЙ ОТЧЁТ DOHOT                                 ║
║           Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                           ║
╚══════════════════════════════════════════════════════════════╝

👥 ПОЛЬЗОВАТЕЛИ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Всего пользователей: {total_users}

💳 КРЕДИТЫ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Активных кредитов: {total_credits or 0}
Общая сумма долга: {total_debt or 0:,.2f} руб.

💸 ДОЛГИ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Активных долгов: {total_debts or 0}
Общая сумма: {total_debt_amount or 0:,.2f} руб.

💰 ДОХОДЫ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Записей доходов: {total_incomes_count or 0}
Общая сумма: {total_incomes_amount or 0:,.2f} руб.

🛒 РАСХОДЫ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Записей расходов: {total_expenses_count or 0}
Общая сумма: {total_expenses_amount or 0:,.2f} руб.

📊 ИНВЕСТИЦИИ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Активов: {total_investments_count or 0}
Общая стоимость: {total_investments_value or 0:,.2f} руб.

💵 БАЛАНС
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Доходы - Расходы: {(total_incomes_amount or 0) - (total_expenses_amount or 0):,.2f} руб.
"""
    
    # Сохраняем отчёт
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"summary_report_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n✅ Отчёт сохранён: {filepath}")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Экспорт данных DoHot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python export_data.py --user 12345                   # Экспорт одного пользователя в CSV
  python export_data.py --user 12345 --format json     # Экспорт в JSON
  python export_data.py --all                          # Экспорт всех пользователей
  python export_data.py --summary                      # Сводный отчёт
        """
    )
    
    parser.add_argument(
        '--db',
        default='dohot.db',
        help='Путь к базе данных (по умолчанию: dohot.db)'
    )
    
    parser.add_argument(
        '--user',
        type=int,
        metavar='USER_ID',
        help='ID пользователя для экспорта'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Экспортировать всех пользователей'
    )
    
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='Формат экспорта (по умолчанию: csv)'
    )
    
    parser.add_argument(
        '--output',
        default='exports',
        help='Директория для сохранения (по умолчанию: exports)'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Сгенерировать сводный отчёт'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.db):
        print(f"❌ База данных не найдена: {args.db}")
        sys.exit(1)
    
    db = Database(args.db)
    
    if args.summary:
        generate_summary_report(db, args.output)
    elif args.user:
        if args.format == 'csv':
            export_user_data_csv(db, args.user, args.output)
        else:
            export_user_data_json(db, args.user, args.output)
    elif args.all:
        export_all_users(db, args.format, args.output)
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
        import traceback
        traceback.print_exc()
        sys.exit(1)
