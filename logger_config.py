import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime


def setup_logger(
    name: str = "dohot",
    log_dir: str = "logs",
    log_level: str = "INFO",
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Настройка логирования для приложения
    
    Args:
        name: Имя логгера
        log_dir: Директория для логов
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Выводить логи в консоль
        file_output: Записывать логи в файл
        max_bytes: Максимальный размер файла лога
        backup_count: Количество резервных копий логов
        
    Returns:
        Настроенный логгер
    """
    
    # Создаём директорию для логов
    if file_output and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Создаём логгер
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Очищаем существующие хэндлеры
    logger.handlers.clear()
    
    # Формат логов
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консольный хэндлер
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # Файловый хэндлер (ротация по размеру)
    if file_output:
        file_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, f"{name}.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # Отдельный файл для ошибок
        error_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, f"{name}_errors.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
    
    return logger


def setup_daily_logger(
    name: str = "dohot",
    log_dir: str = "logs",
    log_level: str = "INFO"
) -> logging.Logger:
    """
    Настройка логирования с ротацией по дням
    
    Args:
        name: Имя логгера
        log_dir: Директория для логов
        log_level: Уровень логирования
        
    Returns:
        Настроенный логгер
    """
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers.clear()
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файл с ротацией по дням
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, f"{name}.log"),
        when='midnight',
        interval=1,
        backupCount=30,  # Хранить 30 дней
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"
    logger.addHandler(file_handler)
    
    return logger


class UserActivityLogger:
    """Логирование активности пользователей"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.logger = logging.getLogger("user_activity")
        self.logger.setLevel(logging.INFO)
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Файл для логов активности
        handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, "user_activity.log"),
            when='midnight',
            interval=1,
            backupCount=90,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_action(self, user_id: int, username: str, action: str, details: str = ""):
        """
        Логировать действие пользователя
        
        Args:
            user_id: ID пользователя
            username: Username пользователя
            action: Тип действия
            details: Дополнительные детали
        """
        message = f"user_id={user_id} username={username} action={action}"
        if details:
            message += f" details={details}"
        
        self.logger.info(message)
    
    def log_credit_added(self, user_id: int, username: str, bank_name: str, amount: float):
        """Логировать добавление кредита"""
        self.log_action(
            user_id, username, "credit_added",
            f"bank={bank_name} amount={amount}"
        )
    
    def log_payment_made(self, user_id: int, username: str, credit_id: int, amount: float):
        """Логировать внесение платежа"""
        self.log_action(
            user_id, username, "payment_made",
            f"credit_id={credit_id} amount={amount}"
        )
    
    def log_early_payment(self, user_id: int, username: str, credit_id: int, 
                         amount: float, payment_type: str):
        """Логировать досрочное погашение"""
        self.log_action(
            user_id, username, "early_payment",
            f"credit_id={credit_id} amount={amount} type={payment_type}"
        )
    
    def log_report_generated(self, user_id: int, username: str):
        """Логировать генерацию отчёта"""
        self.log_action(user_id, username, "report_generated")


class PerformanceLogger:
    """Логирование производительности"""
    
    def __init__(self, log_dir: str = "logs"):
        self.logger = logging.getLogger("performance")
        self.logger.setLevel(logging.INFO)
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        handler = RotatingFileHandler(
            filename=os.path.join(log_dir, "performance.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_execution_time(self, function_name: str, execution_time: float):
        """
        Логировать время выполнения функции
        
        Args:
            function_name: Название функции
            execution_time: Время выполнения в секундах
        """
        self.logger.info(f"{function_name} executed in {execution_time:.4f}s")
    
    def log_database_query(self, query_type: str, execution_time: float):
        """Логировать выполнение запроса к БД"""
        self.logger.info(f"DB query {query_type} executed in {execution_time:.4f}s")


def log_exception(logger: logging.Logger, exc: Exception, context: str = ""):
    """
    Логировать исключение с контекстом
    
    Args:
        logger: Логгер
        exc: Исключение
        context: Контекст возникновения
    """
    message = f"Exception in {context}: {type(exc).__name__}: {str(exc)}"
    logger.error(message, exc_info=True)


# Декоратор для логирования выполнения функций
def log_function_call(logger: logging.Logger):
    """
    Декоратор для логирования вызовов функций
    
    Args:
        logger: Логгер для использования
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator


# Декоратор для измерения времени выполнения
def measure_time(logger: logging.Logger):
    """
    Декоратор для измерения времени выполнения функций
    
    Args:
        logger: Логгер для использования
    """
    import time
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f}s")
            return result
        return wrapper
    return decorator


# Пример использования
if __name__ == "__main__":
    # Базовое логирование
    logger = setup_logger(
        name="dohot",
        log_level="DEBUG",
        console_output=True,
        file_output=True
    )
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Логирование активности
    activity_logger = UserActivityLogger()
    activity_logger.log_credit_added(12345, "john_doe", "Sberbank", 100000)
    
    # Логирование производительности
    perf_logger = PerformanceLogger()
    perf_logger.log_execution_time("calculate_credit_payment", 0.0234)
    
    print("Логи созданы в директории 'logs/'")
