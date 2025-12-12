"""
RadarSuite v3.5.0 - Point 12: Logger Tests
Tests for core/logger.py
"""

from tests.compat import pytest
import logging
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.logger import ThreadSafeLogger, log


class TestThreadSafeLogger:
    """Test suite for ThreadSafeLogger class"""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton between tests"""
        # Clear the singleton instance
        ThreadSafeLogger._instance = None
        yield
        # Cleanup
        ThreadSafeLogger._instance = None

    def test_singleton_pattern(self):
        """Test that ThreadSafeLogger is a singleton"""
        logger1 = ThreadSafeLogger()
        logger2 = ThreadSafeLogger()

        assert logger1 is logger2

    def test_logger_initialization(self):
        """Test that logger is properly initialized"""
        logger = ThreadSafeLogger()

        assert hasattr(logger, 'logger')
        assert isinstance(logger.logger, logging.Logger)
        assert logger.logger.name == 'RadarSuite'
        assert logger.logger.level == logging.DEBUG

    def test_logger_has_handlers(self):
        """Test that logger has file and console handlers"""
        logger = ThreadSafeLogger()

        # Should have at least 2 handlers (file + console)
        assert len(logger.logger.handlers) >= 2

        # Check for RotatingFileHandler
        has_rotating_handler = any(
            isinstance(h, logging.handlers.RotatingFileHandler)
            for h in logger.logger.handlers
        )
        assert has_rotating_handler

        # Check for console handler
        has_console_handler = any(
            isinstance(h, logging.StreamHandler)
            for h in logger.logger.handlers
        )
        assert has_console_handler

    def test_log_method_levels(self):
        """Test that log() method handles different levels"""
        logger = ThreadSafeLogger()

        # Mock the underlying logger
        with patch.object(logger.logger, 'log') as mock_log:
            logger.log("Debug message", "DEBUG")
            mock_log.assert_called_with(logging.DEBUG, "Debug message")

            logger.log("Info message", "INFO")
            mock_log.assert_called_with(logging.INFO, "Info message")

            logger.log("Warning message", "WARNING")
            mock_log.assert_called_with(logging.WARNING, "Warning message")

            logger.log("Error message", "ERROR")
            mock_log.assert_called_with(logging.ERROR, "Error message")

            logger.log("Critical message", "CRITICAL")
            mock_log.assert_called_with(logging.CRITICAL, "Critical message")

    def test_log_method_case_insensitive(self):
        """Test that log levels are case-insensitive"""
        logger = ThreadSafeLogger()

        with patch.object(logger.logger, 'log') as mock_log:
            logger.log("Test", "info")
            mock_log.assert_called_with(logging.INFO, "Test")

            logger.log("Test", "INFO")
            mock_log.assert_called_with(logging.INFO, "Test")

            logger.log("Test", "InFo")
            mock_log.assert_called_with(logging.INFO, "Test")

    def test_log_method_default_level(self):
        """Test that default log level is INFO"""
        logger = ThreadSafeLogger()

        with patch.object(logger.logger, 'log') as mock_log:
            logger.log("Default level message")
            mock_log.assert_called_with(logging.INFO, "Default level message")

    def test_log_method_invalid_level(self):
        """Test that invalid level defaults to INFO"""
        logger = ThreadSafeLogger()

        with patch.object(logger.logger, 'log') as mock_log:
            logger.log("Invalid level", "INVALID_LEVEL")
            mock_log.assert_called_with(logging.INFO, "Invalid level")

    def test_thread_safety_concurrent_logging(self):
        """Test that concurrent logging from multiple threads is thread-safe"""
        logger = ThreadSafeLogger()
        log_count = [0]
        errors = []

        def log_messages(thread_id, count):
            try:
                for i in range(count):
                    logger.log(f"Thread {thread_id} message {i}", "INFO")
                    log_count[0] += 1
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        messages_per_thread = 10
        thread_count = 5

        for i in range(thread_count):
            thread = threading.Thread(target=log_messages, args=(i, messages_per_thread))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have logged all messages without errors
        assert len(errors) == 0
        assert log_count[0] == thread_count * messages_per_thread

    def test_rotating_file_handler_configuration(self):
        """Test that RotatingFileHandler is configured correctly"""
        logger = ThreadSafeLogger()

        # Find the RotatingFileHandler
        rotating_handler = None
        for handler in logger.logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                rotating_handler = handler
                break

        assert rotating_handler is not None
        assert rotating_handler.maxBytes == 10 * 1024 * 1024  # 10MB
        assert rotating_handler.backupCount == 5


class TestLogFunction:
    """Test suite for log() convenience function"""

    def test_log_function_calls_singleton(self):
        """Test that log() function uses singleton logger"""
        with patch.object(ThreadSafeLogger, 'log') as mock_log:
            # Reset singleton
            ThreadSafeLogger._instance = None

            log("Test message", "INFO")

            # Should have created singleton and called its log method
            # Note: The actual call happens on the instance, not the class
            # So we need to check if it was called

    def test_log_function_various_levels(self):
        """Test log() function with various levels"""
        # This is an integration test - it should work without mocking
        # Just verify it doesn't raise exceptions
        try:
            log("Debug message", "DEBUG")
            log("Info message", "INFO")
            log("Warning message", "WARNING")
            log("Error message", "ERROR")
        except Exception as e:
            pytest.fail(f"log() function raised exception: {e}")

    def test_log_function_default_level(self):
        """Test log() function default level"""
        try:
            log("Default level message")
        except Exception as e:
            pytest.fail(f"log() function raised exception: {e}")


class TestLoggerPaths:
    """Test suite for logger paths"""

    def test_super_log_path_defined(self):
        """Test that SUPER_LOG path is defined"""
        from core.logger import SUPER_LOG
        assert SUPER_LOG is not None
        assert isinstance(SUPER_LOG, Path)

    def test_root_path_defined(self):
        """Test that ROOT path is defined"""
        from core.logger import ROOT
        assert ROOT is not None
        assert isinstance(ROOT, Path)
