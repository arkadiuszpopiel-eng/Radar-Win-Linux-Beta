"""
RadarSuite v4.2.0 - Performance Profiler
Punkt 9: Performance profiling utilities

Provides:
- Execution time measurement decorators
- Memory usage tracking
- Performance statistics aggregation
- Bottleneck detection
"""

import time
import threading
from collections import defaultdict
from functools import wraps
from typing import Callable, Dict, List, Optional, TypeVar

try:
    from .logger import log
except ImportError:
    from core.logger import log

T = TypeVar('T')


# ============================================================================
# TIMING UTILITIES (v4.2.0 - Punkt 9)
# ============================================================================

class TimingStats:
    """
    Aggregates timing statistics for a specific operation.

    Tracks:
    - Total calls
    - Total time
    - Min/max/avg execution time
    - Recent execution times
    """

    def __init__(self, name: str, max_history: int = 100):
        self.name = name
        self.call_count: int = 0
        self.total_time: float = 0.0
        self.min_time: float = float('inf')
        self.max_time: float = 0.0
        self._recent_times: List[float] = []
        self._max_history = max_history
        self._lock = threading.Lock()

    def record(self, elapsed: float) -> None:
        """Record a single execution time."""
        with self._lock:
            self.call_count += 1
            self.total_time += elapsed
            self.min_time = min(self.min_time, elapsed)
            self.max_time = max(self.max_time, elapsed)

            self._recent_times.append(elapsed)
            if len(self._recent_times) > self._max_history:
                self._recent_times.pop(0)

    @property
    def avg_time(self) -> float:
        """Average execution time."""
        return self.total_time / self.call_count if self.call_count > 0 else 0.0

    @property
    def recent_avg(self) -> float:
        """Average of recent executions."""
        if not self._recent_times:
            return 0.0
        return sum(self._recent_times) / len(self._recent_times)

    def get_summary(self) -> dict:
        """Get summary statistics."""
        with self._lock:
            return {
                "name": self.name,
                "calls": self.call_count,
                "total_ms": self.total_time * 1000,
                "avg_ms": self.avg_time * 1000,
                "min_ms": self.min_time * 1000 if self.min_time != float('inf') else 0,
                "max_ms": self.max_time * 1000,
                "recent_avg_ms": self.recent_avg * 1000
            }

    def reset(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self.call_count = 0
            self.total_time = 0.0
            self.min_time = float('inf')
            self.max_time = 0.0
            self._recent_times.clear()


# ============================================================================
# PERFORMANCE PROFILER (v4.2.0 - Punkt 9)
# ============================================================================

class PerformanceProfiler:
    """
    Centralized performance profiling for RadarSuite.

    Features:
    - Function execution timing
    - Memory tracking (optional)
    - Bottleneck detection
    - Performance reports

    Usage:
        profiler = PerformanceProfiler()

        @profiler.profile("audio_processing")
        def process_audio(data):
            ...

        # Or manually:
        with profiler.measure("custom_operation"):
            do_something()

        # Get report:
        report = profiler.get_report()
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        """Initialize profiler state."""
        self._stats: Dict[str, TimingStats] = {}
        self._enabled: bool = True
        self._lock = threading.Lock()
        self._slow_threshold_ms: float = 100.0  # Warn if > 100ms

    def enable(self) -> None:
        """Enable profiling."""
        self._enabled = True
        log("Performance profiler enabled", "INFO", module="profiler")

    def disable(self) -> None:
        """Disable profiling."""
        self._enabled = False
        log("Performance profiler disabled", "INFO", module="profiler")

    def set_slow_threshold(self, threshold_ms: float) -> None:
        """Set threshold for slow operation warnings."""
        self._slow_threshold_ms = threshold_ms

    def _get_stats(self, name: str) -> TimingStats:
        """Get or create timing stats for an operation."""
        with self._lock:
            if name not in self._stats:
                self._stats[name] = TimingStats(name)
            return self._stats[name]

    def record(self, name: str, elapsed: float) -> None:
        """Record an execution time for an operation."""
        if not self._enabled:
            return

        stats = self._get_stats(name)
        stats.record(elapsed)

        # Warn if slow
        elapsed_ms = elapsed * 1000
        if elapsed_ms > self._slow_threshold_ms:
            log(
                f"Slow operation: {name} took {elapsed_ms:.1f}ms (threshold: {self._slow_threshold_ms}ms)",
                "WARNING",
                module="profiler"
            )

    def profile(self, name: Optional[str] = None) -> Callable:
        """
        Decorator for profiling function execution time.

        Args:
            name: Optional name for the operation (defaults to function name)

        Returns:
            Decorated function

        Example:
            @profiler.profile("audio_processing")
            def process_audio(data):
                ...
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            op_name = name or func.__qualname__

            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                if not self._enabled:
                    return func(*args, **kwargs)

                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    elapsed = time.perf_counter() - start
                    self.record(op_name, elapsed)

            return wrapper
        return decorator

    def measure(self, name: str) -> "ProfileContext":
        """
        Context manager for measuring a code block.

        Args:
            name: Name for the operation

        Returns:
            ProfileContext context manager

        Example:
            with profiler.measure("data_loading"):
                load_data()
        """
        return ProfileContext(self, name)

    def get_stats(self, name: str) -> Optional[dict]:
        """Get statistics for a specific operation."""
        with self._lock:
            if name in self._stats:
                return self._stats[name].get_summary()
            return None

    def get_report(self) -> dict:
        """
        Get full performance report.

        Returns:
            Dictionary with:
            - operations: List of all operation stats
            - slowest: Top 5 slowest operations by avg time
            - most_called: Top 5 most frequently called
            - total_time_ms: Total time spent in profiled code
        """
        with self._lock:
            all_stats = [s.get_summary() for s in self._stats.values()]

        # Sort by average time (slowest first)
        slowest = sorted(all_stats, key=lambda x: x["avg_ms"], reverse=True)[:5]

        # Sort by call count (most called first)
        most_called = sorted(all_stats, key=lambda x: x["calls"], reverse=True)[:5]

        # Total time
        total_time = sum(s["total_ms"] for s in all_stats)

        return {
            "operations": all_stats,
            "slowest": slowest,
            "most_called": most_called,
            "total_time_ms": total_time,
            "operation_count": len(all_stats)
        }

    def get_bottlenecks(self, threshold_ms: float = 50.0) -> List[dict]:
        """
        Identify performance bottlenecks.

        Args:
            threshold_ms: Minimum avg time to be considered a bottleneck

        Returns:
            List of operations exceeding threshold
        """
        with self._lock:
            bottlenecks = []
            for stats in self._stats.values():
                summary = stats.get_summary()
                if summary["avg_ms"] > threshold_ms:
                    bottlenecks.append(summary)

        return sorted(bottlenecks, key=lambda x: x["avg_ms"], reverse=True)

    def reset(self) -> None:
        """Reset all profiling statistics."""
        with self._lock:
            for stats in self._stats.values():
                stats.reset()
        log("Performance statistics reset", "INFO", module="profiler")

    def clear(self) -> None:
        """Clear all profiling data."""
        with self._lock:
            self._stats.clear()
        log("Performance profiler cleared", "INFO", module="profiler")

    def log_report(self) -> None:
        """Log a summary performance report."""
        report = self.get_report()

        log("=== Performance Report ===", "INFO", module="profiler")
        log(f"Total operations: {report['operation_count']}", "INFO", module="profiler")
        log(f"Total time: {report['total_time_ms']:.1f}ms", "INFO", module="profiler")

        if report['slowest']:
            log("Top 5 slowest operations:", "INFO", module="profiler")
            for op in report['slowest']:
                log(
                    f"  {op['name']}: avg={op['avg_ms']:.2f}ms, "
                    f"calls={op['calls']}, max={op['max_ms']:.2f}ms",
                    "INFO",
                    module="profiler"
                )


class ProfileContext:
    """Context manager for profiling code blocks."""

    def __init__(self, profiler: PerformanceProfiler, name: str):
        self.profiler = profiler
        self.name = name
        self.start: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self) -> "ProfileContext":
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.elapsed = time.perf_counter() - self.start
        self.profiler.record(self.name, self.elapsed)


# ============================================================================
# GLOBAL PROFILER INSTANCE
# ============================================================================

_profiler: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    """Get global PerformanceProfiler instance."""
    global _profiler
    if _profiler is None:
        _profiler = PerformanceProfiler()
    return _profiler


def profile(name: Optional[str] = None) -> Callable:
    """
    Decorator for profiling function execution time.

    Uses global profiler instance.

    Example:
        @profile("audio_processing")
        def process_audio(data):
            ...
    """
    return get_profiler().profile(name)


def measure(name: str) -> ProfileContext:
    """
    Context manager for measuring a code block.

    Uses global profiler instance.

    Example:
        with measure("data_loading"):
            load_data()
    """
    return get_profiler().measure(name)


# ============================================================================
# SIMPLE TIMING DECORATOR (Standalone)
# ============================================================================

def timed(func: Callable[..., T]) -> Callable[..., T]:
    """
    Simple decorator that logs execution time.

    Does not aggregate statistics, just logs each call.

    Example:
        @timed
        def slow_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            log(f"{func.__qualname__} took {elapsed:.2f}ms", "DEBUG", module="profiler")

    return wrapper
