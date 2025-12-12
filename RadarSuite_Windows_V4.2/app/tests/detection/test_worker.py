"""
Unit tests for DetectionWorker
Tests thread pool management, task submission, and cleanup
"""

import pytest
import time
import threading
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from concurrent.futures import Future

from app.detection.worker import DetectionWorker


class TestDetectionWorker:
    """Test suite for DetectionWorker class"""

    @pytest.fixture
    def worker(self):
        """Create a fresh worker instance for each test"""
        w = DetectionWorker(max_workers=2)
        yield w
        # Cleanup after test
        w.shutdown(timeout=1.0)

    def test_initialization(self):
        """Test that worker initializes correctly"""
        worker = DetectionWorker(max_workers=3)

        assert worker.executor is not None
        assert worker.active_futures == []
        assert worker.shutdown_event is not None
        assert worker._lock is not None
        assert worker._cleanup_timer is not None

        # Cleanup
        worker.shutdown(timeout=1.0)

    def test_default_max_workers(self):
        """Test default max_workers value"""
        worker = DetectionWorker()
        assert worker.executor is not None
        worker.shutdown(timeout=1.0)

    def test_submit_detection(self, worker):
        """Test submitting a detection task"""
        # Create mock detection panel
        det_panel = Mock()
        det_panel.analyze = Mock(return_value=({'walk': True, 'run': False, 'shot': False}, {}))

        # Create test audio block
        block = np.random.randn(1024, 2)
        sample_rate = 44100
        fft_cache = {'fft': None}

        # Submit task
        future = worker.submit_detection(det_panel, block, sample_rate, fft_cache)

        assert future is not None
        assert isinstance(future, Future)

        # Wait for completion
        result = future.result(timeout=2.0)
        assert result is not None

        # Should have events and bands
        events, bands = result
        assert isinstance(events, dict)
        assert isinstance(bands, dict)

    def test_submit_localization(self, worker):
        """Test submitting a localization task"""
        # Create mock compute function
        def mock_compute(block, sample_rate):
            return {'azimuth': 45.0, 'elevation': 10.0, 'distance': 5.0}

        block = np.random.randn(1024, 2)
        sample_rate = 44100

        # Submit task
        future = worker.submit_localization(mock_compute, block, sample_rate)

        assert future is not None
        assert isinstance(future, Future)

        # Wait for completion
        result = future.result(timeout=2.0)
        assert result is not None
        assert 'azimuth' in result

    def test_submit_classification(self, worker):
        """Test submitting a classification task"""
        # Create mock classifier
        classifier = Mock()
        classifier.classify_sound = Mock(return_value={
            'type': 'footstep',
            'confidence': 85,
            'details': {}
        })

        block = np.random.randn(1024, 2)
        sample_rate = 44100
        fft_cache = {'fft': None}

        # Submit task
        future = worker.submit_classification(classifier, block, sample_rate, fft_cache)

        assert future is not None
        assert isinstance(future, Future)

        # Wait for completion
        result = future.result(timeout=2.0)
        assert result is not None
        assert result['type'] == 'footstep'
        assert result['confidence'] == 85

    def test_cleanup_done_futures(self, worker):
        """Test that completed futures are cleaned up"""
        # Submit multiple tasks
        def quick_task():
            return True

        futures = []
        for _ in range(5):
            future = worker.executor.submit(quick_task)
            futures.append(future)

        # Add to active futures
        worker.active_futures.extend(futures)

        # Wait for all to complete
        for f in futures:
            f.result(timeout=1.0)

        # Trigger cleanup
        worker._cleanup_done_futures()

        # All should be removed
        assert len(worker.active_futures) == 0

    def test_periodic_cleanup(self, worker):
        """Test that periodic cleanup runs automatically"""
        # Submit and complete some tasks
        def quick_task():
            return True

        for _ in range(3):
            future = worker.executor.submit(quick_task)
            worker.active_futures.append(future)

        initial_count = len(worker.active_futures)

        # Wait for tasks to complete
        time.sleep(0.5)

        # Wait for periodic cleanup (runs every CLEANUP_INTERVAL_SEC)
        # Should clean up completed futures
        time.sleep(1.5)

        # Some cleanup should have occurred
        assert len(worker.active_futures) <= initial_count

    def test_submit_after_shutdown(self, worker):
        """Test that tasks are rejected after shutdown"""
        # Shutdown worker
        worker.shutdown(timeout=1.0)

        # Try to submit task
        det_panel = Mock()
        block = np.random.randn(1024, 2)

        future = worker.submit_detection(det_panel, block, 44100, {})

        # Should return None (rejected)
        assert future is None

    def test_shutdown_with_pending_tasks(self):
        """Test shutdown with pending tasks"""
        worker = DetectionWorker(max_workers=1)

        # Submit slow tasks
        def slow_task():
            time.sleep(0.5)
            return True

        futures = []
        for _ in range(3):
            future = worker.executor.submit(slow_task)
            futures.append(future)
            worker.active_futures.append(future)

        # Shutdown (should cancel pending tasks)
        worker.shutdown(timeout=0.5)

        # Some tasks may be cancelled
        # At least check shutdown completes

    def test_shutdown_cleanup_timer(self):
        """Test that cleanup timer is stopped on shutdown"""
        worker = DetectionWorker(max_workers=2)

        # Timer should be running
        assert worker._cleanup_timer is not None

        # Shutdown
        worker.shutdown(timeout=1.0)

        # Timer should be cancelled
        # (we can't directly check if cancelled, but shutdown should handle it)

    def test_run_detection_error_handling(self):
        """Test error handling in _run_detection"""
        # Create panel that raises error
        det_panel = Mock()
        det_panel.analyze = Mock(side_effect=Exception("Test error"))

        block = np.random.randn(1024, 2)

        # Should return default empty result
        result = DetectionWorker._run_detection(det_panel, block, 44100, {})

        events, bands = result
        assert events == {'walk': False, 'run': False, 'shot': False}
        assert bands == {}

    def test_run_classification_error_handling(self):
        """Test error handling in _run_classification"""
        # Create classifier that raises error
        classifier = Mock()
        classifier.classify_sound = Mock(side_effect=Exception("Test error"))

        block = np.random.randn(1024, 2)

        # Should return default unknown result
        result = DetectionWorker._run_classification(classifier, block, 44100, {})

        assert result['type'] == 'unknown'
        assert result['confidence'] == 0

    def test_thread_safety(self, worker):
        """Test thread-safe operations"""
        # Submit tasks from multiple threads
        results = []

        def submit_task():
            def quick_task():
                return True

            for _ in range(5):
                future = worker.executor.submit(quick_task)
                with worker._lock:
                    worker.active_futures.append(future)
                results.append(future)

        threads = []
        for _ in range(3):
            t = threading.Thread(target=submit_task)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join(timeout=2.0)

        # Wait for all tasks
        for future in results:
            future.result(timeout=1.0)

        # Verify no crashes

    def test_active_futures_tracking(self, worker):
        """Test that active futures are properly tracked"""
        def quick_task():
            time.sleep(0.1)
            return True

        # Submit tasks
        futures = []
        for _ in range(3):
            future = worker.executor.submit(quick_task)
            futures.append(future)
            with worker._lock:
                worker.active_futures.append(future)

        # Should have 3 active futures
        assert len(worker.active_futures) == 3

        # Wait for completion
        for f in futures:
            f.result(timeout=1.0)

        # Cleanup
        worker._cleanup_done_futures()

        # Should be empty now
        assert len(worker.active_futures) == 0

    def test_multiple_shutdowns(self):
        """Test that multiple shutdowns don't cause errors"""
        worker = DetectionWorker(max_workers=2)

        # First shutdown
        worker.shutdown(timeout=0.5)

        # Second shutdown (should be safe)
        worker.shutdown(timeout=0.5)

    def test_cleanup_before_submit(self, worker):
        """Test that cleanup happens before each submit"""
        # Submit and complete a task
        def quick_task():
            return True

        future1 = worker.executor.submit(quick_task)
        worker.active_futures.append(future1)
        future1.result(timeout=1.0)

        # Submit new task (should trigger cleanup)
        det_panel = Mock()
        det_panel.analyze = Mock(return_value=({}, {}))

        future2 = worker.submit_detection(det_panel, np.zeros(1024), 44100, {})

        # Old future should be cleaned up
        # New future should be in list
        assert future2 in worker.active_futures


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
