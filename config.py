import os
from dataclasses import dataclass


@dataclass
class BotConfig:
    """Конфигурация бота"""
    
    # Telegram
    bot_token: str
    
    # База данных
    db_path: str = "dohot.db"
    
    # Директории
    charts_dir: str = "charts"
    
    # Напоминания
    reminder_time_hour: int = 9
    reminder_time_minute: int = 0
    
    @classmethod
    def from_env(cls):
        """Создание конфигурации из переменных окружения"""
        bot_token = os.getenv("BOT_TOKEN")
        
        if not bot_token:
            raise ValueError(
                "BOT_TOKEN не найден в переменных окружения!\n"
                "Создайте файл .env со строкой: BOT_TOKEN=your_token_here\n"
                "Или установите переменную окружения: export BOT_TOKEN=your_token_here"
            )
        
        return cls(
            bot_token=bot_token,
            db_path=os.getenv("DB_PATH", "dohot.db"),
            charts_dir=os.getenv("CHARTS_DIR", "charts"),
            reminder_time_hour=int(os.getenv("REMINDER_HOUR", "9")),
            reminder_time_minute=int(os.getenv("REMINDER_MINUTE", "0"))
        )


def load_config() -> BotConfig:
    """
    Загрузка конфигурации
    
    Порядок загрузки:
    1. Переменные окружения
    2. Файл .env (если установлен python-dotenv)
    """
    
    # Попытка загрузить из .env файла
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv не установлен, используем только переменные окружения
    
    return BotConfig.from_env()
