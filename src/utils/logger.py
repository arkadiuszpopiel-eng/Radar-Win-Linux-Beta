"""
System logowania dla aplikacji YOLO Detection.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


class Logger:
    """Manager logów aplikacji."""

    def __init__(self, name: str = "YOLODetection", log_dir: str = "logs", console_level=logging.INFO, file_level=logging.DEBUG):
        """Inicjalizacja loggera.

        Args:
            name: Nazwa loggera.
            log_dir: Katalog dla plików logów.
            console_level: Poziom logowania do konsoli.
            file_level: Poziom logowania do pliku.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Wyczyść istniejące handlery
        self.logger.handlers.clear()

        # Utwórz katalog dla logów
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Format logów
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File Handler (rotating)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"yolo_detection_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.log_file = log_file

    def get_logger(self) -> logging.Logger:
        """Pobierz logger.

        Returns:
            Logger instance.
        """
        return self.logger

    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)

    def critical(self, message: str):
        """Log critical message."""
        self.logger.critical(message)

    def exception(self, message: str):
        """Log exception with traceback."""
        self.logger.exception(message)


# Global logger instance
_global_logger = None


def get_logger(name: str = "YOLODetection") -> Logger:
    """Pobierz globalny logger.

    Args:
        name: Nazwa loggera.

    Returns:
        Logger instance.
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = Logger(name)

    return _global_logger
