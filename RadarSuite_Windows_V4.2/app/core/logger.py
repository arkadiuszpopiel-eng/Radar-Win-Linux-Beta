"""
RadarSuite v4.2.0 - Thread-safe Logging Module
FIXED v3.5.0: Race condition eliminated via RotatingFileHandler
FIXED v4.2.0: Added TRACE/VERBOSE levels for better log filtering
FIXED v4.2.1-k0008: Use centralized LOG_DIR from paths.py
"""

import logging
import logging.handlers
import threading
from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================

# Legacy paths (deprecated - use paths.py instead)
ROOT = Path(__file__).parent.parent.parent
SUPER_LOG = ROOT / "super_log.txt"  # Deprecated: moved to log/super_log.txt

# Import centralized paths (v4.2.1-k0008)
# Note: Import after legacy definitions to avoid circular imports
try:
    from .paths import SUPER_LOG_FILE
    _USE_NEW_PATHS = True
except ImportError:
    # Fallback to legacy path if paths.py not available yet
    SUPER_LOG_FILE = SUPER_LOG
    _USE_NEW_PATHS = False


# ============================================================================
# CUSTOM LOG LEVELS (FIXED v4.2.0)
# ============================================================================

# Define custom log levels for better filtering
TRACE = 5      # Very frequent, low-level technical logs (e.g., cleanup thread)
VERBOSE = 15   # Aggregated diagnostics and summaries (e.g., 60s metrics)

# Register custom levels with Python's logging module
logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(VERBOSE, "VERBOSE")


# ============================================================================
# THREAD-SAFE LOGGER (FIX 1 - v3.5.0)
# ============================================================================

class ThreadSafeLogger:
    """
    Thread-safe logger using Python's logging module

    FIXED v3.5.0: Race condition in multi-threaded logging
    - Uses RotatingFileHandler (thread-safe, automatic rotation)
    - Max 10MB per file, 5 backups
    - Singleton pattern for global access
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_logger()
        return cls._instance

    def _init_logger(self):
        """Initialize logger with rotating file handler"""
        self.logger = logging.getLogger('RadarSuite')
        self.logger.setLevel(TRACE)  # FIXED v4.2.0: Accept all levels including TRACE

        # Remove existing handlers (avoid duplicates)
        self.logger.handlers.clear()

        # Rotating file handler (max 10MB, 5 backups) - THREAD-SAFE
        # FIXED v4.2.1-k0008: Use centralized log directory
        file_handler = logging.handlers.RotatingFileHandler(
            str(SUPER_LOG_FILE),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(TRACE)  # FIXED v4.2.0: Accept all levels including TRACE

        # Formatter with timestamp
        formatter = logging.Formatter(
            '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Console handler for errors only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def log(self, msg: str, level: str = "INFO"):
        """Thread-safe log method (FIXED v4.2.0: Added TRACE/VERBOSE)"""
        level_map = {
            "TRACE": TRACE,
            "DEBUG": logging.DEBUG,
            "VERBOSE": VERBOSE,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "WARN": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }

        log_level = level_map.get(level.upper(), logging.INFO)
        self.logger.log(log_level, msg)


# Global logger instance (singleton)
_thread_safe_logger = ThreadSafeLogger()

# ============================================================================
# PER-MODULE LOG LEVEL CONTROL (ENHANCED v4.2.0 - Punkt 7)
# ============================================================================

# Module-specific log levels (default to INFO)
_module_log_levels = {}

# Default global log level
_global_log_level = logging.INFO


def set_module_log_level(module_name: str, level: str):
    """
    Set log level for a specific module.

    Args:
        module_name: Name of the module (e.g., 'audio', 'detection', 'tracking')
        level: Log level string ('TRACE', 'DEBUG', 'VERBOSE', 'INFO', 'WARNING', 'ERROR')

    Example:
        set_module_log_level('detection', 'DEBUG')  # Verbose detection logs
        set_module_log_level('audio', 'WARNING')    # Quiet audio logs
    """
    level_map = {
        "TRACE": TRACE,
        "DEBUG": logging.DEBUG,
        "VERBOSE": VERBOSE,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    _module_log_levels[module_name.lower()] = level_map.get(level.upper(), logging.INFO)


def get_module_log_level(module_name: str) -> int:
    """Get the log level for a specific module."""
    return _module_log_levels.get(module_name.lower(), _global_log_level)


def set_global_log_level(level: str):
    """Set the global default log level."""
    global _global_log_level
    level_map = {
        "TRACE": TRACE,
        "DEBUG": logging.DEBUG,
        "VERBOSE": VERBOSE,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    _global_log_level = level_map.get(level.upper(), logging.INFO)


def log(msg: str, level: str = "INFO", module: str = None):
    """
    Thread-safe logging wrapper with per-module level control.

    FIXED v3.5.0: Race condition eliminated via logging.handlers.RotatingFileHandler
    ENHANCED v4.2.0: Per-module log level control (Punkt 7)

    Args:
        msg: Log message
        level: Log level ('TRACE', 'DEBUG', 'VERBOSE', 'INFO', 'WARNING', 'ERROR')
        module: Optional module name for per-module filtering

    Example:
        log("Audio initialized", "INFO", module="audio")
        log("Detection result", "DEBUG", module="detection")
    """
    # Check module-specific level if provided
    if module:
        level_map = {
            "TRACE": TRACE,
            "DEBUG": logging.DEBUG,
            "VERBOSE": VERBOSE,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "WARN": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        msg_level = level_map.get(level.upper(), logging.INFO)
        module_level = get_module_log_level(module)

        # Skip if message level is below module's configured level
        if msg_level < module_level:
            return

    _thread_safe_logger.log(msg, level)
