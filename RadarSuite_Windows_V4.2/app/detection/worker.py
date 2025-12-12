"""
RadarSuite v4.2.0 - Detection Worker
Thread pool for parallel detection processing with enhanced error handling and resource management

FIXED v4.2.0:
- Use MAX_WORKERS from core.constants as default
- Proper exception handling with detailed error reporting
- Safe cleanup mechanism without recursive timers
- Backpressure protection against unbounded task growth
- Clean shutdown with deterministic resource cleanup
"""

import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, Tuple

from core.logger import log
from core.constants import MAX_WORKERS, CLEANUP_INTERVAL_SEC, DETECTION_TIMEOUT_SEC


class DetectionResult:
    """
    Detection result with explicit error handling
    Allows higher layers to distinguish success from failure
    """
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

    def __bool__(self):
        """Allow truthiness check: if result: ..."""
        return self.success


class DetectionWorker:
    """
    Worker thread pool for parallel audio detection processing
    Offloads heavy computation from main UI thread

    ENHANCED v4.2.0:
    - Consistent configuration using core.constants
    - Explicit error propagation instead of silent failures
    - Safe cleanup without recursive timers
    - Backpressure protection (max active tasks = 2x pool size)
    - Thread-safe shutdown with deterministic cleanup
    """

    # Backpressure limit: allow queue to grow to 2x pool size
    MAX_ACTIVE_FUTURES_MULTIPLIER = 2

    def __init__(self, max_workers: int = MAX_WORKERS):
        """
        Initialize detection worker pool

        Args:
            max_workers: Thread pool size (default from core.constants.MAX_WORKERS)
        """
        log(f"DetectionWorker.__init__ (max_workers={max_workers})", "INFO")

        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="DetectionWorker"
        )
        self.active_futures = []
        self.shutdown_event = threading.Event()
        self._lock = threading.Lock()

        # FIXED v4.2.0: Safe cleanup using dedicated thread instead of recursive Timer
        self._cleanup_thread = None

        # FIXED v4.2.0: Statistics for VERBOSE logging
        self._total_cleaned = 0
        self._last_verbose_log = time.time()

        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """
        Start cleanup thread (safer than recursive Timer)
        Thread runs until shutdown_event is set
        """
        def cleanup_loop():
            """Periodic cleanup loop"""
            while not self.shutdown_event.wait(timeout=CLEANUP_INTERVAL_SEC):
                try:
                    self._cleanup_done_futures()
                except Exception as e:
                    log(f"Error in cleanup thread: {e}", "ERROR")

        self._cleanup_thread = threading.Thread(
            target=cleanup_loop,
            name="DetectionWorker-Cleanup",
            daemon=True
        )
        self._cleanup_thread.start()
        log("Cleanup thread started", "TRACE")  # FIXED v4.2.0: TRACE level to reduce spam

    def _cleanup_done_futures(self):
        """
        Remove completed futures from list (memory leak prevention)
        FIXED v4.2.0: TRACE level for frequent logs, VERBOSE for 60s summaries
        """
        with self._lock:
            before_count = len(self.active_futures)
            self.active_futures = [f for f in self.active_futures if not f.done()]
            cleaned_count = before_count - len(self.active_futures)

            if cleaned_count > 0:
                self._total_cleaned += cleaned_count
                # TRACE level - only visible when debugging memory leaks
                log(f"Cleaned {cleaned_count} completed futures (remaining: {len(self.active_futures)})", "TRACE")

            # VERBOSE summary every 60 seconds
            current_time = time.time()
            if current_time - self._last_verbose_log >= 60.0:
                log(f"Cleanup stats (60s): total_cleaned={self._total_cleaned}, "
                    f"current_active={len(self.active_futures)}, "
                    f"pool_size={self.max_workers}", "VERBOSE")
                self._total_cleaned = 0  # Reset counter
                self._last_verbose_log = current_time

    def _check_backpressure(self) -> bool:
        """
        Check if we're at backpressure limit

        Returns:
            True if we can accept more tasks, False if limit reached
        """
        max_active = self.max_workers * self.MAX_ACTIVE_FUTURES_MULTIPLIER

        with self._lock:
            active_count = len([f for f in self.active_futures if not f.done()])

            if active_count >= max_active:
                log(
                    f"Backpressure limit reached: {active_count}/{max_active} active tasks. "
                    f"Rejecting new task to prevent unbounded growth.",
                    "WARNING"
                )
                return False

            # Warn when approaching limit
            if active_count >= max_active * 0.8:
                log(
                    f"Approaching backpressure limit: {active_count}/{max_active} active tasks",
                    "WARNING"
                )

        return True

    def submit_detection(self, det_panel, block, sample_rate, fft_cache) -> Optional[Any]:
        """
        Submit detection task to worker pool

        Args:
            det_panel: Detection panel instance
            block: Audio block to analyze
            sample_rate: Sample rate in Hz
            fft_cache: Cached FFT data

        Returns:
            Future object or None if rejected (shutdown or backpressure)
        """
        if self.shutdown_event.is_set():
            log("Worker pool shutting down, rejecting new detection task", "WARNING")
            return None

        # FIXED v4.2.0: Backpressure protection
        if not self._check_backpressure():
            return None

        # Cleanup before submit to prevent unbounded growth
        with self._lock:
            self.active_futures = [f for f in self.active_futures if not f.done()]

        future = self.executor.submit(
            self._run_detection,
            det_panel,
            block,
            sample_rate,
            fft_cache
        )

        with self._lock:
            self.active_futures.append(future)

        return future

    def submit_localization(self, compute_func, block, sample_rate) -> Optional[Any]:
        """
        Submit 3D localization task to worker pool

        Args:
            compute_func: Localization computation function
            block: Audio block to analyze
            sample_rate: Sample rate in Hz

        Returns:
            Future object or None if rejected (shutdown or backpressure)
        """
        if self.shutdown_event.is_set():
            log("Worker pool shutting down, rejecting new localization task", "WARNING")
            return None

        # FIXED v4.2.0: Backpressure protection
        if not self._check_backpressure():
            return None

        # Cleanup before submit
        with self._lock:
            self.active_futures = [f for f in self.active_futures if not f.done()]

        future = self.executor.submit(compute_func, block, sample_rate)

        with self._lock:
            self.active_futures.append(future)

        return future

    def submit_classification(self, classifier, block, sample_rate, fft_cache) -> Optional[Any]:
        """
        Submit sound classification task to worker pool

        Args:
            classifier: Classifier instance
            block: Audio block to analyze
            sample_rate: Sample rate in Hz
            fft_cache: Cached FFT data

        Returns:
            Future object or None if rejected (shutdown or backpressure)
        """
        if self.shutdown_event.is_set():
            log("Worker pool shutting down, rejecting new classification task", "WARNING")
            return None

        # FIXED v4.2.0: Backpressure protection
        if not self._check_backpressure():
            return None

        # Cleanup before submit
        with self._lock:
            self.active_futures = [f for f in self.active_futures if not f.done()]

        future = self.executor.submit(
            self._run_classification,
            classifier,
            block,
            sample_rate,
            fft_cache
        )

        with self._lock:
            self.active_futures.append(future)

        return future

    @staticmethod
    def _run_detection(det_panel, block, sample_rate, fft_cache) -> DetectionResult:
        """
        Run detection in worker thread

        FIXED v4.2.0: Proper error handling with detailed logging

        Args:
            det_panel: Detection panel instance
            block: Audio block
            sample_rate: Sample rate in Hz
            fft_cache: Cached FFT data

        Returns:
            DetectionResult with success/error state
        """
        try:
            # Use cached FFT data
            events, bands = det_panel.analyze(block, sample_rate, fft_cache=fft_cache)
            return DetectionResult(
                success=True,
                data={'events': events, 'bands': bands}
            )
        except Exception as e:
            # FIXED v4.2.0: Detailed error logging with traceback
            error_msg = f"Detection worker failed: {type(e).__name__}: {e}"
            log(error_msg, "ERROR")
            log(f"Traceback: {traceback.format_exc()}", "DEBUG")

            # Return error result instead of masking failure
            return DetectionResult(
                success=False,
                data={'events': {'walk': False, 'run': False, 'shot': False}, 'bands': {}},
                error=error_msg
            )

    @staticmethod
    def _run_classification(classifier, block, sample_rate, fft_cache) -> DetectionResult:
        """
        Run classification in worker thread

        FIXED v4.2.0: Proper error handling with detailed logging

        Args:
            classifier: Classifier instance
            block: Audio block
            sample_rate: Sample rate in Hz
            fft_cache: Cached FFT data

        Returns:
            DetectionResult with success/error state
        """
        try:
            result = classifier.classify_sound(block, sample_rate, fft_cache=fft_cache)
            return DetectionResult(
                success=True,
                data=result
            )
        except Exception as e:
            # FIXED v4.2.0: Detailed error logging with traceback
            error_msg = f"Classification worker failed: {type(e).__name__}: {e}"
            log(error_msg, "ERROR")
            log(f"Traceback: {traceback.format_exc()}", "DEBUG")

            # Return error result instead of masking failure
            return DetectionResult(
                success=False,
                data={'type': 'unknown', 'confidence': 0, 'details': {}},
                error=error_msg
            )

    @property
    def is_shutdown(self) -> bool:
        """Check if worker pool is shut down"""
        return self.shutdown_event.is_set()

    def get_active_task_count(self) -> int:
        """
        Get number of currently active (not done) tasks

        Returns:
            Count of active tasks
        """
        with self._lock:
            return len([f for f in self.active_futures if not f.done()])

    def shutdown(self, timeout: float = DETECTION_TIMEOUT_SEC):
        """
        Thread-safe shutdown with deterministic cleanup

        Args:
            timeout: Maximum time to wait for tasks to complete (seconds)

        ENHANCED v4.2.0:
        - Proper cleanup thread termination
        - Clear active_futures list after shutdown
        - Deterministic resource cleanup
        """
        log(f"DetectionWorker.shutdown (timeout={timeout}s)", "INFO")
        self.shutdown_event.set()

        # Wait for cleanup thread to finish (it checks shutdown_event)
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            # Give cleanup thread time to notice shutdown_event
            self._cleanup_thread.join(timeout=1.0)
            if self._cleanup_thread.is_alive():
                log("Cleanup thread did not terminate in time (daemon will be killed)", "WARNING")
            else:
                log("Cleanup thread terminated cleanly", "TRACE")  # FIXED v4.2.0: TRACE level

        # Cancel pending futures
        cancelled_count = 0
        with self._lock:
            for future in self.active_futures:
                if not future.done():
                    cancelled = future.cancel()
                    if cancelled:
                        cancelled_count += 1

        if cancelled_count > 0:
            log(f"Cancelled {cancelled_count} pending tasks", "INFO")

        # Shutdown executor and wait for running tasks
        start_time = time.time()
        try:
            # Shutdown without waiting (we'll implement manual timeout)
            self.executor.shutdown(wait=False)

            # Wait for all futures to complete with timeout
            with self._lock:
                remaining = [f for f in self.active_futures if not f.done()]

            while remaining and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                with self._lock:
                    remaining = [f for f in self.active_futures if not f.done()]

            if remaining:
                log(
                    f"Forced shutdown - {len(remaining)} tasks still running after {timeout}s",
                    "WARNING"
                )
            else:
                log("DetectionWorker shutdown complete - all tasks finished", "INFO")

        except Exception as e:
            log(f"DetectionWorker shutdown error: {e}", "WARNING")
        finally:
            # FIXED v4.2.0: Clear futures list to free memory
            with self._lock:
                self.active_futures.clear()
            log("DetectionWorker cleanup completed", "TRACE")  # FIXED v4.2.0: TRACE level
