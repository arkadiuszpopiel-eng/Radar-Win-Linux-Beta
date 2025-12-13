"""
RadarSuite v4.2.0 - Standardized Error Handler
Consistent error handling patterns across all modules

Created as part of 10-point development plan (Punkt 3)
ENHANCED v4.2.0: Added ErrorReporter for statistics tracking (Punkt 7)
"""

import sys
import traceback
from functools import wraps
from typing import Callable, Any, Optional, TypeVar, Union
from enum import Enum

try:
    from .logger import log
except ImportError:
    from core.logger import log


class ErrorSeverity(Enum):
    """Error severity levels for consistent handling"""
    LOW = "LOW"           # Log only, continue execution
    MEDIUM = "MEDIUM"     # Log + notify user, continue
    HIGH = "HIGH"         # Log + notify + attempt recovery
    CRITICAL = "CRITICAL" # Log + notify + may terminate


class RadarSuiteError(Exception):
    """Base exception for RadarSuite application errors"""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.original_error = original_error

    def __str__(self):
        if self.original_error:
            return f"{self.message} (caused by: {type(self.original_error).__name__}: {self.original_error})"
        return self.message


class AudioError(RadarSuiteError):
    """Audio capture/processing errors"""
    pass


class DetectionError(RadarSuiteError):
    """Detection algorithm errors"""
    pass


class ConfigurationError(RadarSuiteError):
    """Configuration/settings errors"""
    pass


class UIError(RadarSuiteError):
    """User interface errors"""
    pass


T = TypeVar('T')


def safe_call(
    func: Callable[..., T],
    *args,
    default: T = None,
    log_errors: bool = True,
    error_prefix: str = "",
    **kwargs
) -> T:
    """
    Safely call a function with error handling.

    Args:
        func: Function to call
        *args: Positional arguments
        default: Default value to return on error
        log_errors: Whether to log errors
        error_prefix: Prefix for error messages
        **kwargs: Keyword arguments

    Returns:
        Function result or default value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            prefix = f"{error_prefix}: " if error_prefix else ""
            log(f"{prefix}Error in {func.__name__}: {e}", "ERROR")
        return default


def handle_errors(
    default_return: Any = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    log_errors: bool = True,
    reraise: bool = False
):
    """
    Decorator for standardized error handling.

    Usage:
        @handle_errors(default_return=[], severity=ErrorSeverity.LOW)
        def get_devices():
            return device_list

    Args:
        default_return: Value to return on error
        severity: Error severity level
        log_errors: Whether to log errors
        reraise: Whether to re-raise exception after handling

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RadarSuiteError as e:
                # Our custom errors - handle based on severity
                if log_errors:
                    log(f"[{e.severity.value}] {func.__name__}: {e}", "ERROR")
                if reraise:
                    raise
                return default_return
            except Exception as e:
                # Unexpected errors - always log
                if log_errors:
                    log(f"[{severity.value}] Unexpected error in {func.__name__}: {e}", "ERROR")
                    log(traceback.format_exc(), "DEBUG")
                if reraise:
                    raise RadarSuiteError(str(e), severity, e)
                return default_return
        return wrapper
    return decorator


def log_and_suppress(func: Callable) -> Callable:
    """
    Simple decorator that logs errors and suppresses them.
    Use for non-critical operations that should never crash the app.

    Usage:
        @log_and_suppress
        def update_ui_element():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log(f"Suppressed error in {func.__name__}: {e}", "WARNING")
            return None
    return wrapper


def ensure_not_none(value: Optional[T], default: T, name: str = "value") -> T:
    """
    Ensure a value is not None, logging if default is used.

    Args:
        value: Value to check
        default: Default to use if None
        name: Name for logging

    Returns:
        Original value or default
    """
    if value is None:
        log(f"{name} was None, using default", "DEBUG")
        return default
    return value


class ErrorContext:
    """
    Context manager for error handling with cleanup.

    Usage:
        with ErrorContext("audio processing", cleanup=cleanup_func):
            process_audio()
    """

    def __init__(
        self,
        operation: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        cleanup: Optional[Callable] = None,
        suppress: bool = True
    ):
        self.operation = operation
        self.severity = severity
        self.cleanup = cleanup
        self.suppress = suppress
        self.error: Optional[Exception] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.error = exc_val
            log(f"[{self.severity.value}] Error during {self.operation}: {exc_val}", "ERROR")

            if self.cleanup:
                try:
                    self.cleanup()
                except Exception as cleanup_error:
                    log(f"Cleanup error: {cleanup_error}", "WARNING")

            return self.suppress  # True = suppress exception

        return False


# Error rate limiting to prevent log spam
_error_counts = {}
_error_last_time = {}


def log_error_rate_limited(
    error_key: str,
    message: str,
    interval_seconds: float = 5.0,
    level: str = "ERROR"
):
    """
    Log an error with rate limiting to prevent spam.

    Args:
        error_key: Unique key for this error type
        message: Error message
        interval_seconds: Minimum seconds between logs
        level: Log level
    """
    import time
    current_time = time.time()

    # Initialize if not seen
    if error_key not in _error_counts:
        _error_counts[error_key] = 0
        _error_last_time[error_key] = 0

    _error_counts[error_key] += 1

    # Check if enough time has passed
    if current_time - _error_last_time[error_key] >= interval_seconds:
        count = _error_counts[error_key]
        if count > 1:
            log(f"{message} (occurred {count}x in last {interval_seconds}s)", level)
        else:
            log(message, level)

        # Reset counters
        _error_counts[error_key] = 0
        _error_last_time[error_key] = current_time


# ============================================================================
# ERROR REPORTER (v4.2.0 - Punkt 7)
# ============================================================================

class ErrorReporter:
    """
    Centralized error reporting and statistics tracking.

    Tracks error counts by type, maintains history, and provides summaries.
    Singleton pattern for global access.

    Usage:
        reporter = ErrorReporter()
        reporter.report(error, context="audio_processing")
        summary = reporter.get_summary()
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        """Initialize error tracking state."""
        self._error_counts: dict = {}
        self._error_history: list = []
        self._max_history: int = 100

    def report(
        self,
        error: Exception,
        context: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> None:
        """
        Report an error occurrence.

        Args:
            error: The exception that occurred
            context: Optional context string (e.g., function name)
            severity: Error severity level
        """
        import time

        error_type = type(error).__name__

        # Update counts
        if error_type not in self._error_counts:
            self._error_counts[error_type] = 0
        self._error_counts[error_type] += 1

        # Add to history
        entry = {
            "timestamp": time.time(),
            "type": error_type,
            "message": str(error),
            "context": context or "unknown",
            "severity": severity.value
        }
        self._error_history.append(entry)

        # Trim history if exceeds max
        if len(self._error_history) > self._max_history:
            self._error_history = self._error_history[-self._max_history:]

        # Log the error
        log(
            f"Error reported: [{severity.value}] {error_type} in {context or 'unknown'}: {error}",
            "ERROR"
        )

    def get_summary(self) -> dict:
        """
        Get error summary statistics.

        Returns:
            Dictionary with:
            - total_errors: Total count of all errors
            - by_type: Dict of error counts by type
            - by_severity: Dict of error counts by severity
            - recent_errors: Last 10 errors
        """
        by_severity = {}
        for entry in self._error_history:
            sev = entry["severity"]
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "total_errors": sum(self._error_counts.values()),
            "by_type": self._error_counts.copy(),
            "by_severity": by_severity,
            "recent_count": len(self._error_history),
            "recent_errors": self._error_history[-10:]
        }

    def get_error_rate(self, window_seconds: float = 60.0) -> float:
        """
        Get error rate (errors per second) in recent time window.

        Args:
            window_seconds: Time window to calculate rate

        Returns:
            Errors per second
        """
        import time
        current_time = time.time()
        cutoff = current_time - window_seconds

        recent = [e for e in self._error_history if e["timestamp"] > cutoff]
        return len(recent) / window_seconds if window_seconds > 0 else 0.0

    def clear(self) -> None:
        """Clear all error statistics."""
        self._error_counts.clear()
        self._error_history.clear()
        log("Error statistics cleared", "INFO")


# Global error reporter instance (singleton)
_error_reporter: Optional[ErrorReporter] = None


def get_error_reporter() -> ErrorReporter:
    """Get global ErrorReporter instance."""
    global _error_reporter
    if _error_reporter is None:
        _error_reporter = ErrorReporter()
    return _error_reporter


def report_error(
    error: Exception,
    context: Optional[str] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
) -> None:
    """
    Report an error to the global error reporter.

    Args:
        error: The exception that occurred
        context: Optional context string
        severity: Error severity level
    """
    get_error_reporter().report(error, context, severity)


def get_error_summary() -> dict:
    """Get error summary from global reporter."""
    return get_error_reporter().get_summary()
