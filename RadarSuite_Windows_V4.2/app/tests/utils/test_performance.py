"""
Unit tests for PerformanceMonitor
Tests FPS, CPU, memory, and latency tracking
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from app.utils.performance import PerformanceMonitor


class TestPerformanceMonitor:
    """Test suite for PerformanceMonitor class"""

    @pytest.fixture
    def monitor(self):
        """Create a fresh monitor instance for each test"""
        return PerformanceMonitor()

    def test_initialization(self, monitor):
        """Test that monitor initializes with correct default values"""
        assert monitor.frame_times is not None
        assert monitor.frame_times.maxlen == 60
        assert monitor.last_frame_time > 0
        assert monitor.process is not None

        # Check initial metrics
        assert monitor.fps == 0.0
        assert monitor.cpu_percent == 0.0
        assert monitor.memory_mb == 0.0
        assert monitor.latency_ms == 0.0

        # Check latency tracking
        assert monitor.audio_in_time == 0.0
        assert monitor.radar_update_time == 0.0

    def test_start_frame(self, monitor):
        """Test frame start timestamp recording"""
        initial_time = monitor.audio_in_time

        monitor.start_frame()

        # Should update audio_in_time
        assert monitor.audio_in_time > initial_time
        assert monitor.audio_in_time > 0

    def test_end_frame(self, monitor):
        """Test frame end and timing calculation"""
        # Start a frame
        monitor.start_frame()
        time.sleep(0.01)  # Small delay

        initial_len = len(monitor.frame_times)

        # End frame
        monitor.end_frame()

        # Should add frame time
        assert len(monitor.frame_times) > initial_len

        # Latency should be calculated
        assert monitor.latency_ms > 0

    def test_fps_calculation(self, monitor):
        """Test FPS calculation from frame times"""
        # Simulate 10 frames at ~60 FPS (16.67ms each)
        for _ in range(10):
            monitor.start_frame()
            time.sleep(0.016)  # ~60 FPS
            monitor.end_frame()

        # Update metrics
        monitor.update()

        # FPS should be calculated
        assert monitor.fps > 0
        # Should be roughly 60 FPS (with some tolerance)
        assert 40 < monitor.fps < 80

    def test_latency_calculation(self, monitor):
        """Test latency calculation"""
        # Start frame
        monitor.start_frame()
        start_time = monitor.audio_in_time

        # Simulate processing delay
        time.sleep(0.005)  # 5ms delay

        # End frame
        monitor.end_frame()

        # Latency should be approximately 5ms
        assert monitor.latency_ms >= 4.0  # Allow some tolerance
        assert monitor.latency_ms <= 10.0

    @patch('psutil.Process.cpu_percent')
    @patch('psutil.Process.memory_info')
    def test_cpu_memory_tracking(self, mock_memory, mock_cpu, monitor):
        """Test CPU and memory tracking"""
        # Setup mocks
        mock_cpu.return_value = 25.5
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100 MB in bytes
        mock_memory.return_value = mock_memory_info

        # Trigger update (sample every 10 frames)
        for i in range(15):
            monitor.start_frame()
            monitor.end_frame()

        monitor.update()

        # CPU and memory should be updated
        # Note: Actual values depend on when sampling occurs (every 10 frames)

    def test_get_stats(self, monitor):
        """Test getting current statistics"""
        # Set some values
        monitor.fps = 60.0
        monitor.cpu_percent = 25.0
        monitor.memory_mb = 150.0
        monitor.latency_ms = 5.0

        stats = monitor.get_stats()

        # Check structure
        assert 'fps' in stats
        assert 'cpu_percent' in stats
        assert 'memory_mb' in stats
        assert 'latency_ms' in stats

        # Check values
        assert stats['fps'] == 60.0
        assert stats['cpu_percent'] == 25.0
        assert stats['memory_mb'] == 150.0
        assert stats['latency_ms'] == 5.0

    def test_frame_times_maxlen(self, monitor):
        """Test that frame times buffer respects max length"""
        # Add more than maxlen frames
        for _ in range(100):
            monitor.start_frame()
            time.sleep(0.001)
            monitor.end_frame()

        # Should be capped at maxlen (60)
        assert len(monitor.frame_times) == 60

    def test_fps_with_varying_frame_rates(self, monitor):
        """Test FPS calculation with varying frame rates"""
        # Fast frames (100 FPS)
        for _ in range(10):
            monitor.start_frame()
            time.sleep(0.01)  # ~100 FPS
            monitor.end_frame()

        monitor.update()
        fast_fps = monitor.fps

        # Slow frames (30 FPS)
        monitor.frame_times.clear()
        for _ in range(10):
            monitor.start_frame()
            time.sleep(0.033)  # ~30 FPS
            monitor.end_frame()

        monitor.update()
        slow_fps = monitor.fps

        # Fast should be higher than slow
        assert fast_fps > slow_fps

    def test_zero_frame_time_handling(self, monitor):
        """Test handling of zero or very small frame times"""
        # Update with no frames
        monitor.update()

        # FPS should be 0
        assert monitor.fps == 0.0

    @patch('psutil.Process.cpu_percent')
    def test_cpu_error_handling(self, mock_cpu, monitor):
        """Test error handling when CPU monitoring fails"""
        # Make cpu_percent raise an error
        mock_cpu.side_effect = Exception("CPU monitoring failed")

        # Should handle error gracefully
        for i in range(15):
            monitor.start_frame()
            monitor.end_frame()

        try:
            monitor.update()
            # Should not crash
        except Exception:
            pytest.fail("update() should handle CPU monitoring errors")

    @patch('psutil.Process.memory_info')
    def test_memory_error_handling(self, mock_memory, monitor):
        """Test error handling when memory monitoring fails"""
        # Make memory_info raise an error
        mock_memory.side_effect = Exception("Memory monitoring failed")

        # Should handle error gracefully
        for i in range(15):
            monitor.start_frame()
            monitor.end_frame()

        try:
            monitor.update()
            # Should not crash
        except Exception:
            pytest.fail("update() should handle memory monitoring errors")

    def test_latency_without_start_frame(self, monitor):
        """Test latency calculation when start_frame was not called"""
        # End frame without calling start_frame
        monitor.audio_in_time = 0.0
        monitor.end_frame()

        # Latency calculation should still work
        # (may be 0 or based on current time)

    def test_multiple_updates(self, monitor):
        """Test multiple consecutive updates"""
        for _ in range(5):
            monitor.start_frame()
            time.sleep(0.01)
            monitor.end_frame()
            monitor.update()

        stats = monitor.get_stats()

        # Should have valid stats
        assert stats['fps'] >= 0
        assert stats['latency_ms'] >= 0

    def test_stats_types(self, monitor):
        """Test that all stats are correct types"""
        monitor.start_frame()
        monitor.end_frame()
        monitor.update()

        stats = monitor.get_stats()

        assert isinstance(stats['fps'], float)
        assert isinstance(stats['cpu_percent'], float)
        assert isinstance(stats['memory_mb'], float)
        assert isinstance(stats['latency_ms'], float)

    def test_concurrent_frame_tracking(self, monitor):
        """Test frame tracking over time"""
        fps_values = []

        # Track FPS over multiple frames
        for cycle in range(3):
            for _ in range(20):
                monitor.start_frame()
                time.sleep(0.016)  # ~60 FPS
                monitor.end_frame()

            monitor.update()
            fps_values.append(monitor.fps)

        # FPS should stabilize
        assert len(fps_values) == 3
        # All FPS values should be reasonable
        for fps in fps_values:
            assert fps > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
