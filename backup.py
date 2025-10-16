#!/usr/bin/env python3
"""
Скрипт для создания резервных копий базы данных DoHot

Использование:
    python backup.py                    # Создать резервную копию
    python backup.py --restore backup.db # Восстановить из копии
    python backup.py --list             # Показать список копий
    python backup.py --cleanup          # Удалить старые копии
"""

import argparse
import sys
import os
from datetime import datetime

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import BackupManager, DatabaseValidator
from logger_config import setup_logger

logger = setup_logger("backup")


def create_backup(backup_manager: BackupManager) -> bool:
    """
    Создать резервную копию
    
    Args:
        backup_manager: Менеджер резервных копий
        
    Returns:
        True при успехе
    """
    print("🔄 Создание резервной копии...")
    
    backup_path = backup_manager.create_backup()
    
    if backup_path:
        print(f"✅ Резервная копия создана: {backup_path}")
        
        # Проверяем размер
        size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        print(f"📦 Размер: {size_mb:.2f} MB")
        
        return True
    else:
        print("❌ Ошибка при создании резервной копии")
        return False


def restore_backup(backup_manager: BackupManager, backup_path: str) -> bool:
    """
    Восстановить из резервной копии
    
    Args:
        backup_manager: Менеджер резервных копий
        backup_path: Путь к файлу резервной копии
        
    Returns:
        True при успехе
    """
    print(f"🔄 Восстановление из {backup_path}...")
    
    # Подтверждение
    response = input("⚠️  Это перезапишет текущую базу данных! Продолжить? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Отменено")
        return False
    
    success = backup_manager.restore_backup(backup_path)
    
    if success:
        print("✅ База данных восстановлена успешно")
        
        # Проверяем целостность
        validator = DatabaseValidator()
        if validator.check_integrity():
            print("✅ Проверка целостности пройдена")
        else:
            print("⚠️  Предупреждение: проблемы с целостностью базы данных")
        
        return True
    else:
        print("❌ Ошибка при восстановлении")
        return False


def list_backups(backup_manager: BackupManager):
    """
    Показать список резервных копий
    
    Args:
        backup_manager: Менеджер резервных копий
    """
    backups = backup_manager.list_backups()
    
    if not backups:
        print("📭 Резервных копий не найдено")
        return
    
    print(f"\n📋 Найдено резервных копий: {len(backups)}\n")
    print(f"{'№':<4} {'Имя файла':<35} {'Размер':<10} {'Дата создания':<20}")
    print("-" * 70)
    
    for i, backup in enumerate(backups, 1):
        size_mb = backup['size'] / (1024 * 1024)
        created = backup['created'].strftime("%Y-%m-%d %H:%M:%S")
        print(f"{i:<4} {backup['filename']:<35} {size_mb:>6.2f} MB {created:<20}")
    
    # Показываем общий размер
    total_size = sum(b['size'] for b in backups) / (1024 * 1024)
    print("-" * 70)
    print(f"Общий размер: {total_size:.2f} MB")


def cleanup_old_backups(backup_manager: BackupManager, keep_count: int = 10):
    """
    Удалить старые резервные копии
    
    Args:
        backup_manager: Менеджер резервных копий
        keep_count: Количество копий для сохранения
    """
    backups = backup_manager.list_backups()
    
    if len(backups) <= keep_count:
        print(f"✅ Всего {len(backups)} копий, очистка не требуется")
        return
    
    to_delete_count = len(backups) - keep_count
    print(f"🗑️  Будет удалено {to_delete_count} старых копий (оставим последние {keep_count})")
    
    response = input("Продолжить? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Отменено")
        return
    
    backup_manager.cleanup_old_backups(keep_count)
    print(f"✅ Удалено {to_delete_count} старых копий")


def check_database(validator: DatabaseValidator):
    """
    Проверить базу данных
    
    Args:
        validator: Валидатор базы данных
    """
    print("🔍 Проверка базы данных...\n")
    
    # Проверка целостности
    print("1️⃣  Проверка целостности...")
    if validator.check_integrity():
        print("   ✅ OK")
    else:
        print("   ❌ Обнаружены проблемы!")
    
    # Проверка таблиц
    print("\n2️⃣  Проверка таблиц...")
    tables = validator.check_tables()
    for table, exists in tables.items():
        status = "✅" if exists else "❌"
        print(f"   {status} {table}")
    
    # Статистика
    print("\n3️⃣  Статистика базы данных:")
    stats = validator.get_database_stats()
    
    if 'size_mb' in stats:
        print(f"   📦 Размер: {stats['size_mb']:.2f} MB")
    
    if 'total_users' in stats:
        print(f"   👥 Пользователей: {stats['total_users']}")
    
    if 'credits_count' in stats:
        print(f"   💳 Кредитов: {stats['credits_count']}")
    
    if 'debts_count' in stats:
        print(f"   💸 Долгов: {stats['debts_count']}")
    
    if 'incomes_count' in stats:
        print(f"   💰 Записей доходов: {stats['incomes_count']}")
    
    if 'expenses_count' in stats:
        print(f"   🛒 Записей расходов: {stats['expenses_count']}")
    
    if 'investments_count' in stats:
        print(f"   📊 Инвестиций: {stats['investments_count']}")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Утилита резервного копирования DoHot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python backup.py                               # Создать резервную копию
  python backup.py --restore backups/backup.db   # Восстановить из копии
  python backup.py --list                        # Показать список копий
  python backup.py --cleanup --keep 5            # Оставить только 5 последних копий
  python backup.py --check                       # Проверить базу данных
        """
    )
    
    parser.add_argument(
        '--db',
        default='dohot.db',
        help='Путь к базе данных (по умолчанию: dohot.db)'
    )
    
    parser.add_argument(
        '--backup-dir',
        default='backups',
        help='Директория для резервных копий (по умолчанию: backups)'
    )
    
    parser.add_argument(
        '--restore',
        metavar='BACKUP_FILE',
        help='Восстановить базу данных из резервной копии'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='Показать список резервных копий'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Удалить старые резервные копии'
    )
    
    parser.add_argument(
        '--keep',
        type=int,
        default=10,
        help='Количество копий для сохранения при очистке (по умолчанию: 10)'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Проверить целостность базы данных'
    )
    
    args = parser.parse_args()
    
    # Создаём менеджер и валидатор
    backup_manager = BackupManager(args.db, args.backup_dir)
    validator = DatabaseValidator(args.db)
    
    # Выполняем запрошенное действие
    if args.restore:
        success = restore_backup(backup_manager, args.restore)
        sys.exit(0 if success else 1)
    
    elif args.list:
        list_backups(backup_manager)
        sys.exit(0)
    
    elif args.cleanup:
        cleanup_old_backups(backup_manager, args.keep)
        sys.exit(0)
    
    elif args.check:
        check_database(validator)
        sys.exit(0)
    
    else:
        # По умолчанию создаём резервную копию
        success = create_backup(backup_manager)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        logger.error(f"Backup script error: {e}", exc_info=True)
        sys.exit(1)
