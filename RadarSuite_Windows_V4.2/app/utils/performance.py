"""
RadarSuite V4.2.1 - Performance Monitor & Memory Optimizer
Real-time FPS, CPU, memory, latency tracking
ENHANCED v4.2.1: ZADANIE 6 - Memory profiling and optimization
"""

import gc
import sys
import time
import weakref
import threading
import psutil
import numpy as np
from collections import deque
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from functools import wraps

from core.logger import log


@dataclass
class MemorySnapshot:
    """Snapshot of memory state at a point in time."""
    timestamp: float
    rss_mb: float
    vms_mb: float
    percent: float
    gc_objects: int
    numpy_arrays: int = 0
    numpy_mb: float = 0.0


@dataclass
class MemoryStats:
    """Aggregated memory statistics."""
    current_mb: float = 0.0
    peak_mb: float = 0.0
    average_mb: float = 0.0
    gc_collections: Dict[int, int] = field(default_factory=dict)
    leak_suspects: List[str] = field(default_factory=list)


class MemoryOptimizer:
    """
    Memory optimization and profiling utilities.

    ADDED v4.2.1: ZADANIE 6 - Memory management for RadarSuite.

    Features:
    - Periodic memory snapshots
    - Leak detection (growing object counts)
    - Automatic garbage collection control
    - NumPy array tracking
    - Buffer pool management
    """

    # Thresholds
    MEMORY_WARNING_MB = 500
    MEMORY_CRITICAL_MB = 1000
    LEAK_DETECTION_WINDOW = 60  # seconds
    GC_FORCE_THRESHOLD_MB = 800

    def __init__(self, enable_profiling: bool = False):
        """
        Initialize memory optimizer.

        Args:
            enable_profiling: Enable detailed profiling (adds overhead)
        """
        log("MemoryOptimizer.__init__", "INFO")
        self.process = psutil.Process()
        self.enable_profiling = enable_profiling

        # Snapshot history
        self._snapshots: deque = deque(maxlen=100)
        self._snapshot_interval = 5.0  # seconds
        self._last_snapshot_time = 0.0

        # Peak tracking
        self._peak_memory_mb = 0.0

        # Leak detection
        self._object_counts: Dict[str, int] = {}
        self._growing_types: List[str] = []

        # Buffer pools for reuse
        self._buffer_pools: Dict[str, List[np.ndarray]] = {
            'audio_block': [],
            'fft_buffer': [],
            'spectrum_buffer': [],
        }
        self._pool_stats = {'hits': 0, 'misses': 0}

        # Weak references to tracked objects
        self._tracked_objects: weakref.WeakSet = weakref.WeakSet()

        # GC control
        self._gc_disabled = False
        self._last_gc_time = time.time()

    def take_snapshot(self) -> MemorySnapshot:
        """Take a memory snapshot."""
        try:
            mem_info = self.process.memory_info()
            mem_percent = self.process.memory_percent()

            snapshot = MemorySnapshot(
                timestamp=time.time(),
                rss_mb=mem_info.rss / (1024 * 1024),
                vms_mb=mem_info.vms / (1024 * 1024),
                percent=mem_percent,
                gc_objects=len(gc.get_objects())
            )

            # Track NumPy arrays if profiling enabled
            if self.enable_profiling:
                arrays = [obj for obj in gc.get_objects()
                         if isinstance(obj, np.ndarray)]
                snapshot.numpy_arrays = len(arrays)
                snapshot.numpy_mb = sum(a.nbytes for a in arrays) / (1024 * 1024)

            self._snapshots.append(snapshot)

            # Update peak
            if snapshot.rss_mb > self._peak_memory_mb:
                self._peak_memory_mb = snapshot.rss_mb

            return snapshot

        except Exception as e:
            log(f"Memory snapshot failed: {e}", "WARNING")
            return MemorySnapshot(
                timestamp=time.time(),
                rss_mb=0.0,
                vms_mb=0.0,
                percent=0.0,
                gc_objects=0
            )

    def check_memory(self) -> Optional[str]:
        """
        Check memory status and return warning if needed.

        Returns:
            Warning message if memory is high, None otherwise.
        """
        current_time = time.time()

        # Take snapshot if interval passed
        if current_time - self._last_snapshot_time >= self._snapshot_interval:
            snapshot = self.take_snapshot()
            self._last_snapshot_time = current_time

            # Check thresholds
            if snapshot.rss_mb >= self.MEMORY_CRITICAL_MB:
                self._force_gc()
                return f"CRITICAL: Memory usage {snapshot.rss_mb:.0f}MB (forced GC)"
            elif snapshot.rss_mb >= self.MEMORY_WARNING_MB:
                return f"WARNING: Memory usage {snapshot.rss_mb:.0f}MB"

        return None

    def get_stats(self) -> MemoryStats:
        """Get aggregated memory statistics."""
        stats = MemoryStats()

        if self._snapshots:
            latest = self._snapshots[-1]
            stats.current_mb = latest.rss_mb
            stats.average_mb = np.mean([s.rss_mb for s in self._snapshots])

        stats.peak_mb = self._peak_memory_mb
        stats.gc_collections = {
            i: gc.get_count()[i] for i in range(3)
        }
        stats.leak_suspects = self._growing_types.copy()

        return stats

    def detect_leaks(self) -> List[str]:
        """
        Detect potential memory leaks by tracking object count growth.

        Returns:
            List of type names with growing counts.
        """
        if not self.enable_profiling:
            return []

        current_counts: Dict[str, int] = {}

        # Count objects by type
        for obj in gc.get_objects():
            type_name = type(obj).__name__
            current_counts[type_name] = current_counts.get(type_name, 0) + 1

        # Compare with previous
        growing = []
        for type_name, count in current_counts.items():
            prev_count = self._object_counts.get(type_name, 0)
            if count > prev_count * 1.5 and count > 100:  # 50% growth, min 100 objects
                growing.append(f"{type_name}: {prev_count} -> {count}")

        self._object_counts = current_counts
        self._growing_types = growing

        return growing

    # ========================================================================
    # BUFFER POOL MANAGEMENT
    # ========================================================================

    def get_buffer(self, pool_name: str, shape: tuple, dtype=np.float32) -> np.ndarray:
        """
        Get a buffer from pool or create new one.

        Args:
            pool_name: Name of buffer pool
            shape: Required shape
            dtype: NumPy dtype

        Returns:
            NumPy array (possibly reused from pool)
        """
        pool = self._buffer_pools.get(pool_name, [])

        # Look for matching buffer
        for i, buf in enumerate(pool):
            if buf.shape == shape and buf.dtype == dtype:
                self._pool_stats['hits'] += 1
                return pool.pop(i)

        # Create new
        self._pool_stats['misses'] += 1
        return np.zeros(shape, dtype=dtype)

    def return_buffer(self, pool_name: str, buffer: np.ndarray):
        """
        Return a buffer to pool for reuse.

        Args:
            pool_name: Name of buffer pool
            buffer: Buffer to return
        """
        if pool_name not in self._buffer_pools:
            self._buffer_pools[pool_name] = []

        # Limit pool size
        if len(self._buffer_pools[pool_name]) < 10:
            buffer.fill(0)  # Clear data
            self._buffer_pools[pool_name].append(buffer)

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get buffer pool statistics."""
        return {
            'hits': self._pool_stats['hits'],
            'misses': self._pool_stats['misses'],
            'hit_rate': (
                self._pool_stats['hits'] /
                max(1, self._pool_stats['hits'] + self._pool_stats['misses'])
            ),
            'pool_sizes': {k: len(v) for k, v in self._buffer_pools.items()}
        }

    # ========================================================================
    # GARBAGE COLLECTION CONTROL
    # ========================================================================

    def _force_gc(self):
        """Force garbage collection."""
        gc.collect()
        self._last_gc_time = time.time()
        log("Forced garbage collection", "DEBUG")

    def optimize_gc_for_realtime(self):
        """
        Configure GC for real-time audio processing.

        Disables automatic GC and relies on manual collection
        during idle periods to avoid audio glitches.
        """
        gc.disable()
        self._gc_disabled = True
        log("GC disabled for real-time processing", "INFO")

    def restore_gc(self):
        """Restore normal GC behavior."""
        gc.enable()
        self._gc_disabled = False
        log("GC restored to normal", "INFO")

    def gc_if_idle(self, idle_threshold_ms: float = 50.0):
        """
        Run GC if system appears idle.

        Args:
            idle_threshold_ms: Minimum idle time before GC
        """
        if not self._gc_disabled:
            return

        # Check if enough time has passed since last GC
        current_time = time.time()
        if current_time - self._last_gc_time > 10.0:  # At least 10 seconds between GC
            gc.collect(0)  # Only generation 0 (fast)
            self._last_gc_time = current_time

    def cleanup(self):
        """Cleanup resources and restore settings."""
        self.restore_gc()
        self._buffer_pools.clear()
        self._snapshots.clear()
        log("MemoryOptimizer cleanup complete", "INFO")


class PerformanceMonitor:
    """
    Monitor application performance metrics
    Tracks FPS, CPU usage, memory usage, latency
    """

    def __init__(self):
        log("PerformanceMonitor.__init__", "INFO")
        self.frame_times = deque(maxlen=60)  # Last 60 frames
        self.last_frame_time = time.time()
        self.process = psutil.Process()

        # Metrics
        self.fps = 0.0
        self.cpu_percent = 0.0
        self.memory_mb = 0.0
        self.latency_ms = 0.0

        # Latency tracking
        self.audio_in_time = 0.0
        self.radar_update_time = 0.0

    def start_frame(self):
        """Mark start of processing frame"""
        self.audio_in_time = time.time()

    def end_frame(self):
        """Mark end of processing frame"""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        self.last_frame_time = current_time

        # Calculate latency (audio in → radar update)
        if self.audio_in_time > 0:
            self.latency_ms = (current_time - self.audio_in_time) * 1000.0

    def update(self):
        """Update performance metrics"""
        # Calculate FPS
        if len(self.frame_times) > 0:
            avg_frame_time = np.mean(self.frame_times)
            self.fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0

        # CPU and memory (sample every 10 frames to reduce overhead)
        if len(self.frame_times) % 10 == 0:
            try:
                self.cpu_percent = self.process.cpu_percent()
                self.memory_mb = self.process.memory_info().rss / (1024 * 1024)
            except (psutil.Error, AttributeError) as e:
                log(f"Performance monitoring error: {e}", level="WARNING")
                self.cpu_percent = 0.0
                self.memory_mb = 0.0

    def get_stats(self):
        """Get current performance statistics"""
        return {
            'fps': self.fps,
            'cpu_percent': self.cpu_percent,
            'memory_mb': self.memory_mb,
            'latency_ms': self.latency_ms
        }

