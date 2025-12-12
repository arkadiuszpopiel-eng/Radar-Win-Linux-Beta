"""
RadarSuite v3.5.0 - Audio Processing Cache
Thread-safe FFT caching for performance
FIXED v3.5.0: Thread safety with locks
"""

import time
import threading
import numpy as np
from collections import deque

from core.logger import log


class AudioProcessingCache:
    """
    Cache for audio processing results to avoid redundant computations
    Caches FFT results, spectral analysis, etc.

    ENHANCED v3.5.0: GPU acceleration support via GPUAccelerator
    FIXED v3.5.0: Thread-safe cache operations with lock
    """

    def __init__(self, max_size=5, gpu_accelerator=None):
        log("AudioProcessingCache.__init__", "INFO")
        self.max_size = max_size
        self.cache = deque(maxlen=max_size)
        self.hits = 0
        self.misses = 0
        self.gpu_accelerator = gpu_accelerator

        # FIXED v3.5.0: Thread lock for concurrent access
        self._lock = threading.Lock()

    def compute_fft(self, block, sample_rate):
        """
        Compute FFT with caching (THREAD-SAFE)
        Returns: (fft_data, freqs, power, mono_signal)

        ENHANCED v3.5.0: Uses GPU acceleration if available
        FIXED v3.5.0: Thread-safe via lock
        """
        # Convert to mono
        if block.ndim == 2:
            mono = np.mean(block, axis=1)
        else:
            mono = block.ravel()

        # Apply Hanning window
        window = np.hanning(len(mono))
        windowed = mono * window

        # Compute FFT (GPU-accelerated if available)
        if self.gpu_accelerator is not None:
            fft_data = self.gpu_accelerator.fft_optimized(windowed)
        else:
            fft_data = np.fft.rfft(windowed)

        freqs = np.fft.rfftfreq(len(mono), d=1.0/sample_rate)
        power = np.abs(fft_data)

        # Cache result (THREAD-SAFE)
        result = {
            'fft_data': fft_data,
            'freqs': freqs,
            'power': power,
            'mono': mono,
            'windowed': windowed,
            'timestamp': time.time()
        }

        with self._lock:  # FIXED v3.5.0: Protect cache operations
            self.cache.append(result)
            self.misses += 1

        return result

    def get_stats(self):
        """Get cache statistics (THREAD-SAFE)"""
        with self._lock:  # FIXED v3.5.0: Protect reads
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'size': len(self.cache)
            }

    def clear(self):
        """
        Clear all cached data (THREAD-SAFE).
        OPTIMIZATION v4.2.1: Memory cleanup for long sessions.
        """
        with self._lock:
            old_size = len(self.cache)
            self.cache.clear()
            log(f"AudioProcessingCache cleared: {old_size} items removed", "INFO")

    def get_memory_usage(self):
        """
        Estimate memory usage of cached data (THREAD-SAFE).
        OPTIMIZATION v4.2.1: Memory profiling.

        Returns:
            Approximate memory usage in bytes
        """
        with self._lock:
            total_bytes = 0
            for item in self.cache:
                # Estimate size of numpy arrays
                for key in ['fft_data', 'freqs', 'power', 'mono', 'windowed']:
                    if key in item and isinstance(item[key], np.ndarray):
                        total_bytes += item[key].nbytes
            return total_bytes

    def cleanup_old_entries(self, max_age_seconds=300):
        """
        Remove cache entries older than specified age (THREAD-SAFE).
        OPTIMIZATION v4.2.1: Time-based cache cleanup.

        Args:
            max_age_seconds: Maximum age of cache entries in seconds (default: 5 minutes)
        """
        with self._lock:
            current_time = time.time()
            initial_size = len(self.cache)

            # Filter cache to keep only recent entries
            self.cache = deque(
                (item for item in self.cache if current_time - item.get('timestamp', 0) <= max_age_seconds),
                maxlen=self.max_size
            )

            removed = initial_size - len(self.cache)
            if removed > 0:
                log(f"AudioProcessingCache: Cleaned up {removed} old entries", "INFO")



