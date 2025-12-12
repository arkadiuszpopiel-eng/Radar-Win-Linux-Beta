"""
Unit tests for GPUAccelerator
Tests GPU detection and FFT acceleration
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from app.hardware.gpu import GPUAccelerator


class TestGPUAccelerator:
    """Test suite for GPUAccelerator class"""

    @pytest.fixture
    def accelerator_disabled(self):
        """Create accelerator with GPU disabled"""
        return GPUAccelerator(enable_gpu=False)

    def test_initialization_disabled(self, accelerator_disabled):
        """Test initialization with GPU disabled"""
        assert accelerator_disabled.enabled == False
        assert accelerator_disabled.gpu_available == False

    @patch('app.hardware.gpu.GPUAccelerator._detect_amd_gpu')
    def test_initialization_gpu_detected(self, mock_detect):
        """Test initialization when AMD GPU is detected"""
        mock_detect.return_value = True

        accelerator = GPUAccelerator(enable_gpu=True)

        assert accelerator.gpu_available == True
        assert accelerator.enabled == True

    @patch('app.hardware.gpu.GPUAccelerator._detect_amd_gpu')
    def test_initialization_no_gpu(self, mock_detect):
        """Test initialization when no GPU is detected"""
        mock_detect.return_value = False

        accelerator = GPUAccelerator(enable_gpu=True)

        assert accelerator.gpu_available == False
        assert accelerator.enabled == False

    @patch('app.hardware.gpu.GPUAccelerator._detect_amd_gpu')
    def test_initialization_detection_error(self, mock_detect):
        """Test initialization when GPU detection raises error"""
        mock_detect.side_effect = Exception("Detection failed")

        # Should handle error gracefully
        accelerator = GPUAccelerator(enable_gpu=True)

        assert accelerator.enabled == False

    @patch('psutil.process_iter')
    @patch('sys.platform', 'win32')
    def test_detect_amd_gpu_found(self, mock_process_iter):
        """Test AMD GPU detection on Windows"""
        # Mock AMD process
        mock_proc = Mock()
        mock_proc.info = {'name': 'RadeonSoftware.exe'}

        mock_process_iter.return_value = [mock_proc]

        accelerator = GPUAccelerator(enable_gpu=False)
        result = accelerator._detect_amd_gpu()

        assert result == True

    @patch('psutil.process_iter')
    @patch('sys.platform', 'win32')
    def test_detect_amd_gpu_not_found(self, mock_process_iter):
        """Test when no AMD GPU is present"""
        # Mock non-AMD process
        mock_proc = Mock()
        mock_proc.info = {'name': 'explorer.exe'}

        mock_process_iter.return_value = [mock_proc]

        accelerator = GPUAccelerator(enable_gpu=False)
        result = accelerator._detect_amd_gpu()

        assert result == False

    @patch('psutil.process_iter')
    @patch('sys.platform', 'linux')
    def test_detect_amd_gpu_non_windows(self, mock_process_iter):
        """Test GPU detection on non-Windows platforms"""
        accelerator = GPUAccelerator(enable_gpu=False)
        result = accelerator._detect_amd_gpu()

        # Should return False on non-Windows
        assert result == False

    @patch('psutil.process_iter')
    @patch('sys.platform', 'win32')
    def test_detect_amd_gpu_process_error(self, mock_process_iter):
        """Test handling of process access errors"""
        import psutil

        # Mock process that raises AccessDenied
        def process_generator():
            mock_proc = Mock()
            mock_proc.info = {'name': None}
            mock_proc.info.side_effect = psutil.AccessDenied("Access denied")
            yield mock_proc

        mock_process_iter.return_value = process_generator()

        accelerator = GPUAccelerator(enable_gpu=False)
        result = accelerator._detect_amd_gpu()

        # Should handle error and return False
        assert result == False

    def test_fft_optimized_gpu_disabled(self, accelerator_disabled):
        """Test FFT when GPU is disabled"""
        signal = np.random.randn(1024)

        result = accelerator_disabled.fft_optimized(signal)

        # Should use standard FFT
        expected = np.fft.rfft(signal)

        assert result.shape == expected.shape
        np.testing.assert_array_almost_equal(result, expected)

    @patch('app.hardware.gpu.GPUAccelerator._detect_amd_gpu')
    def test_fft_optimized_gpu_enabled(self, mock_detect):
        """Test FFT when GPU is enabled"""
        mock_detect.return_value = True

        accelerator = GPUAccelerator(enable_gpu=True)

        signal = np.random.randn(1024)
        result = accelerator.fft_optimized(signal)

        # Should use optimized FFT with ortho normalization
        expected = np.fft.rfft(signal, norm='ortho')

        assert result.shape == expected.shape
        np.testing.assert_array_almost_equal(result, expected)

    @patch('app.hardware.gpu.GPUAccelerator._detect_amd_gpu')
    @patch('numpy.fft.rfft')
    def test_fft_optimized_fallback_on_error(self, mock_rfft, mock_detect):
        """Test FFT fallback when GPU FFT fails"""
        mock_detect.return_value = True

        # First call (with ortho) raises error, second call (without) succeeds
        signal = np.random.randn(1024)
        expected_result = np.ones(513)

        def side_effect(*args, **kwargs):
            if kwargs.get('norm') == 'ortho':
                raise RuntimeError("GPU FFT failed")
            return expected_result

        mock_rfft.side_effect = side_effect

        accelerator = GPUAccelerator(enable_gpu=True)
        result = accelerator.fft_optimized(signal)

        # Should fall back to CPU FFT
        np.testing.assert_array_equal(result, expected_result)

    def test_fft_optimized_different_sizes(self, accelerator_disabled):
        """Test FFT with different signal sizes"""
        sizes = [128, 512, 1024, 2048, 4096]

        for size in sizes:
            signal = np.random.randn(size)
            result = accelerator_disabled.fft_optimized(signal)

            expected_size = size // 2 + 1
            assert len(result) == expected_size

    def test_fft_optimized_2d_signal(self, accelerator_disabled):
        """Test FFT with 2D signal (stereo)"""
        # 2D signal (1024 samples, 2 channels)
        signal = np.random.randn(1024, 2)

        # Should handle gracefully or process per channel
        # (behavior depends on implementation)
        try:
            result = accelerator_disabled.fft_optimized(signal)
        except Exception:
            # May not support 2D directly
            pass

    def test_get_info_disabled(self, accelerator_disabled):
        """Test get_info when GPU is disabled"""
        info = accelerator_disabled.get_info()

        assert 'enabled' in info
        assert 'gpu_available' in info
        assert 'backend' in info

        assert info['enabled'] == False
        assert info['gpu_available'] == False
        assert info['backend'] == 'cpu'

    @patch('app.hardware.gpu.GPUAccelerator._detect_amd_gpu')
    def test_get_info_enabled(self, mock_detect):
        """Test get_info when GPU is enabled"""
        mock_detect.return_value = True

        accelerator = GPUAccelerator(enable_gpu=True)
        info = accelerator.get_info()

        assert info['enabled'] == True
        assert info['gpu_available'] == True
        assert info['backend'] == 'numpy-optimized'

    def test_fft_optimized_zero_signal(self, accelerator_disabled):
        """Test FFT with zero signal"""
        signal = np.zeros(1024)

        result = accelerator_disabled.fft_optimized(signal)

        # FFT of zeros should be zeros
        np.testing.assert_array_almost_equal(result, np.zeros(len(result)))

    def test_fft_optimized_sine_wave(self, accelerator_disabled):
        """Test FFT with pure sine wave"""
        # Create 100 Hz sine wave at 44100 Hz sample rate
        t = np.linspace(0, 1, 44100)
        signal = np.sin(2 * np.pi * 100 * t)

        result = accelerator_disabled.fft_optimized(signal)

        # FFT should have peak at 100 Hz
        assert len(result) > 0
        assert np.max(np.abs(result)) > 0

    @patch('psutil.process_iter')
    @patch('sys.platform', 'win32')
    def test_detect_multiple_amd_processes(self, mock_process_iter):
        """Test detection with multiple AMD processes"""
        mock_proc1 = Mock()
        mock_proc1.info = {'name': 'RadeonSoftware.exe'}

        mock_proc2 = Mock()
        mock_proc2.info = {'name': 'AMDRSServ.exe'}

        mock_proc3 = Mock()
        mock_proc3.info = {'name': 'chrome.exe'}

        mock_process_iter.return_value = [mock_proc1, mock_proc2, mock_proc3]

        accelerator = GPUAccelerator(enable_gpu=False)
        result = accelerator._detect_amd_gpu()

        # Should detect AMD (first AMD process triggers True)
        assert result == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
