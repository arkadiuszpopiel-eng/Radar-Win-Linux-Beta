"""
Unit tests for AudioProcessingCache
Tests FFT caching and thread safety
"""

import pytest
import numpy as np
import time
import threading
from unittest.mock import Mock, patch

from app.audio.cache import AudioProcessingCache


class TestAudioProcessingCache:
    """Test suite for AudioProcessingCache class"""

    @pytest.fixture
    def cache(self):
        """Create a fresh cache instance"""
        return AudioProcessingCache(max_size=5)

    @pytest.fixture
    def cache_with_gpu(self):
        """Create cache with mock GPU accelerator"""
        gpu = Mock()
        gpu.fft_optimized = Mock(side_effect=lambda x: np.fft.rfft(x))
        return AudioProcessingCache(max_size=5, gpu_accelerator=gpu)

    def test_initialization(self, cache):
        """Test cache initialization"""
        assert cache.max_size == 5
        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0
        assert cache.gpu_accelerator is None
        assert cache._lock is not None

    def test_initialization_with_gpu(self, cache_with_gpu):
        """Test initialization with GPU accelerator"""
        assert cache_with_gpu.gpu_accelerator is not None

    def test_compute_fft_mono(self, cache):
        """Test FFT computation with mono audio"""
        block = np.random.randn(1024)
        sample_rate = 44100

        result = cache.compute_fft(block, sample_rate)

        assert 'fft_data' in result
        assert 'freqs' in result
        assert 'power' in result
        assert 'mono' in result
        assert 'windowed' in result
        assert 'timestamp' in result

        # Check shapes
        assert len(result['fft_data']) == len(block) // 2 + 1
        assert len(result['freqs']) == len(block) // 2 + 1
        assert len(result['power']) == len(block) // 2 + 1
        assert len(result['mono']) == len(block)

    def test_compute_fft_stereo(self, cache):
        """Test FFT computation with stereo audio"""
        block = np.random.randn(1024, 2)
        sample_rate = 44100

        result = cache.compute_fft(block, sample_rate)

        # Should convert to mono
        assert len(result['mono']) == 1024
        assert result['mono'].ndim == 1

    def test_compute_fft_with_gpu(self, cache_with_gpu):
        """Test FFT computation using GPU"""
        block = np.random.randn(1024)
        sample_rate = 44100

        result = cache_with_gpu.compute_fft(block, sample_rate)

        # GPU accelerator should have been called
        cache_with_gpu.gpu_accelerator.fft_optimized.assert_called_once()

        assert 'fft_data' in result

    def test_compute_fft_without_gpu(self, cache):
        """Test FFT computation without GPU"""
        block = np.random.randn(1024)
        sample_rate = 44100

        result = cache.compute_fft(block, sample_rate)

        # Should use numpy FFT
        assert result is not None

    def test_cache_updates_misses(self, cache):
        """Test that cache tracks misses"""
        initial_misses = cache.misses

        block = np.random.randn(1024)
        cache.compute_fft(block, 44100)

        assert cache.misses == initial_misses + 1

    def test_cache_max_size(self, cache):
        """Test that cache respects max size"""
        # Add more than max_size entries
        for i in range(10):
            block = np.random.randn(1024)
            cache.compute_fft(block, 44100)

        # Should be capped at max_size
        assert len(cache.cache) == cache.max_size

    def test_get_stats(self, cache):
        """Test getting cache statistics"""
        # Compute some FFTs
        for _ in range(3):
            block = np.random.randn(1024)
            cache.compute_fft(block, 44100)

        stats = cache.get_stats()

        assert 'hits' in stats
        assert 'misses' in stats
        assert 'hit_rate' in stats
        assert 'size' in stats

        assert stats['misses'] == 3
        assert stats['size'] == 3

    def test_get_stats_hit_rate(self, cache):
        """Test hit rate calculation"""
        cache.hits = 7
        cache.misses = 3

        stats = cache.get_stats()

        # 7 hits out of 10 total = 70%
        assert stats['hit_rate'] == 70.0

    def test_get_stats_no_operations(self, cache):
        """Test stats when no operations have occurred"""
        stats = cache.get_stats()

        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 0
        assert stats['size'] == 0

    def test_thread_safety(self, cache):
        """Test thread-safe operations"""
        results = []
        errors = []

        def compute_fft_thread():
            try:
                for _ in range(10):
                    block = np.random.randn(1024)
                    result = cache.compute_fft(block, 44100)
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=compute_fft_thread)
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join(timeout=5.0)

        # Should complete without errors
        assert len(errors) == 0
        assert len(results) == 50  # 5 threads × 10 computations

    def test_fft_windowing(self, cache):
        """Test that Hanning window is applied"""
        block = np.ones(1024)
        result = cache.compute_fft(block, 44100)

        # Windowed signal should be different from original
        assert not np.allclose(result['windowed'], result['mono'])

        # Window should reduce edge discontinuities
        assert result['windowed'][0] < result['mono'][0]
        assert result['windowed'][-1] < result['mono'][-1]

    def test_fft_frequencies(self, cache):
        """Test that frequency array is correct"""
        block = np.random.randn(1024)
        sample_rate = 44100

        result = cache.compute_fft(block, sample_rate)

        freqs = result['freqs']

        # First frequency should be 0 Hz
        assert freqs[0] == 0.0

        # Last frequency should be Nyquist (sample_rate / 2)
        expected_nyquist = sample_rate / 2
        assert np.isclose(freqs[-1], expected_nyquist, rtol=0.01)

    def test_fft_power_spectrum(self, cache):
        """Test power spectrum calculation"""
        # Create pure tone at 1000 Hz
        sample_rate = 44100
        t = np.linspace(0, 1, sample_rate)
        block = np.sin(2 * np.pi * 1000 * t)

        result = cache.compute_fft(block, sample_rate)

        power = result['power']
        freqs = result['freqs']

        # Find peak frequency
        peak_idx = np.argmax(power)
        peak_freq = freqs[peak_idx]

        # Should be close to 1000 Hz
        assert np.isclose(peak_freq, 1000, atol=10)

    def test_timestamp(self, cache):
        """Test that timestamp is recorded"""
        before = time.time()

        block = np.random.randn(1024)
        result = cache.compute_fft(block, 44100)

        after = time.time()

        # Timestamp should be within range
        assert before <= result['timestamp'] <= after

    def test_mono_conversion_stereo(self, cache):
        """Test stereo to mono conversion"""
        # Create stereo signal (different left/right)
        left = np.ones(1024) * 2.0
        right = np.ones(1024) * 4.0
        stereo = np.column_stack((left, right))

        result = cache.compute_fft(stereo, 44100)

        # Mono should be average of left and right
        expected_mono = (left + right) / 2
        np.testing.assert_array_almost_equal(result['mono'], expected_mono)

    def test_different_sample_rates(self, cache):
        """Test FFT with different sample rates"""
        sample_rates = [44100, 48000, 96000]

        for sr in sample_rates:
            block = np.random.randn(1024)
            result = cache.compute_fft(block, sr)

            # Nyquist should be sr/2
            assert np.isclose(result['freqs'][-1], sr / 2, rtol=0.01)

    def test_different_block_sizes(self, cache):
        """Test FFT with different block sizes"""
        block_sizes = [512, 1024, 2048, 4096]

        for size in block_sizes:
            block = np.random.randn(size)
            result = cache.compute_fft(block, 44100)

            expected_fft_size = size // 2 + 1
            assert len(result['fft_data']) == expected_fft_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
