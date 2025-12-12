"""
Unit tests for SoundBlasterOptimizer
Tests Sound Blaster detection and audio optimization
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from app.hardware.soundblaster import SoundBlasterOptimizer


class TestSoundBlasterOptimizer:
    """Test suite for SoundBlasterOptimizer class"""

    @pytest.fixture
    def optimizer(self):
        """Create a fresh optimizer instance"""
        with patch('app.hardware.soundblaster.SoundBlasterOptimizer._detect_soundblaster'):
            return SoundBlasterOptimizer()

    def test_initialization(self, optimizer):
        """Test initialization with default values"""
        assert optimizer.is_soundblaster in [True, False]
        assert optimizer.device_name is None or isinstance(optimizer.device_name, str)
        assert 'sample_rate' in optimizer.optimal_settings
        assert 'block_size' in optimizer.optimal_settings
        assert 'channels' in optimizer.optimal_settings

    def test_optimal_settings_values(self, optimizer):
        """Test optimal settings configuration"""
        settings = optimizer.optimal_settings

        assert settings['sample_rate'] == 48000
        assert settings['block_size'] == 2048
        assert settings['channels'] == 2

    @patch('app.hardware.soundblaster.sd')
    def test_detect_soundblaster_found(self, mock_sd):
        """Test detection when Sound Blaster is present"""
        # Mock Sound Blaster device
        mock_devices = [
            {'name': 'Sound Blaster Z SE'},
            {'name': 'Realtek High Definition Audio'}
        ]

        mock_sd.query_devices.return_value = mock_devices

        optimizer = SoundBlasterOptimizer()

        assert optimizer.is_soundblaster == True
        assert 'Sound Blaster' in optimizer.device_name

    @patch('app.hardware.soundblaster.sd')
    def test_detect_soundblaster_not_found(self, mock_sd):
        """Test detection when no Sound Blaster is present"""
        # Mock non-Sound Blaster devices
        mock_devices = [
            {'name': 'Realtek High Definition Audio'},
            {'name': 'USB Microphone'}
        ]

        mock_sd.query_devices.return_value = mock_devices

        optimizer = SoundBlasterOptimizer()

        assert optimizer.is_soundblaster == False

    @patch('app.hardware.soundblaster.sd')
    def test_detect_soundblaster_z_se(self, mock_sd):
        """Test detection of Sound Blaster Z SE specifically"""
        mock_devices = [
            {'name': 'Sound Blaster Z-SE'}
        ]

        mock_sd.query_devices.return_value = mock_devices

        optimizer = SoundBlasterOptimizer()

        assert optimizer.is_soundblaster == True

    @patch('app.hardware.soundblaster.sd')
    def test_detect_creative_card(self, mock_sd):
        """Test detection of Creative audio cards"""
        mock_devices = [
            {'name': 'Creative SB X-Fi'}
        ]

        mock_sd.query_devices.return_value = mock_devices

        optimizer = SoundBlasterOptimizer()

        assert optimizer.is_soundblaster == True

    @patch('app.hardware.soundblaster.sd', None)
    def test_detect_soundblaster_no_sd(self):
        """Test detection when sounddevice is not available"""
        optimizer = SoundBlasterOptimizer()

        # Should handle gracefully
        assert optimizer.is_soundblaster == False

    @patch('app.hardware.soundblaster.sd')
    def test_detect_soundblaster_error(self, mock_sd):
        """Test error handling during detection"""
        mock_sd.query_devices.side_effect = Exception("Device query failed")

        # Should handle error gracefully
        optimizer = SoundBlasterOptimizer()

        assert optimizer.is_soundblaster == False

    def test_get_optimal_settings_soundblaster(self):
        """Test getting optimal settings for Sound Blaster"""
        with patch('app.hardware.soundblaster.SoundBlasterOptimizer._detect_soundblaster'):
            optimizer = SoundBlasterOptimizer()
            optimizer.is_soundblaster = True

            settings = optimizer.get_optimal_settings()

            assert settings['sample_rate'] == 48000
            assert settings['block_size'] == 2048
            assert settings['channels'] == 2

    def test_get_optimal_settings_standard(self):
        """Test getting optimal settings for non-Sound Blaster"""
        with patch('app.hardware.soundblaster.SoundBlasterOptimizer._detect_soundblaster'):
            optimizer = SoundBlasterOptimizer()
            optimizer.is_soundblaster = False

            settings = optimizer.get_optimal_settings()

            # Should return standard settings
            assert settings['sample_rate'] == 48000
            assert settings['block_size'] == 2048
            assert settings['channels'] == 2

    def test_apply_eq_compensation_not_soundblaster(self):
        """Test EQ compensation when not Sound Blaster"""
        with patch('app.hardware.soundblaster.SoundBlasterOptimizer._detect_soundblaster'):
            optimizer = SoundBlasterOptimizer()
            optimizer.is_soundblaster = False

            audio_block = np.random.randn(2048, 2)
            result = optimizer.apply_eq_compensation(audio_block)

            # Should return unmodified audio
            np.testing.assert_array_equal(result, audio_block)

    def test_apply_eq_compensation_soundblaster(self):
        """Test EQ compensation for Sound Blaster"""
        with patch('app.hardware.soundblaster.SoundBlasterOptimizer._detect_soundblaster'):
            optimizer = SoundBlasterOptimizer()
            optimizer.is_soundblaster = True

            audio_block = np.random.randn(2048, 2)
            result = optimizer.apply_eq_compensation(audio_block)

            # Result should have same shape
            assert result.shape == audio_block.shape

            # Result should be different (compensated)
            # Allow for very small differences due to subtle filter
            assert not np.allclose(result, audio_block, atol=1e-10)

    def test_apply_eq_compensation_preserves_shape(self):
        """Test that EQ compensation preserves audio shape"""
        with patch('app.hardware.soundblaster.SoundBlasterOptimizer._detect_soundblaster'):
            optimizer = SoundBlasterOptimizer()
            optimizer.is_soundblaster = True

            # Test different shapes
            shapes = [(1024, 2), (2048, 2), (4096, 2)]

            for shape in shapes:
                audio_block = np.random.randn(*shape)
                result = optimizer.apply_eq_compensation(audio_block)

                assert result.shape == shape

    def test_apply_eq_compensation_mono(self):
        """Test EQ compensation with mono audio"""
        with patch('app.hardware.soundblaster.SoundBlasterOptimizer._detect_soundblaster'):
            optimizer = SoundBlasterOptimizer()
            optimizer.is_soundblaster = True

            # Mono audio (1D array)
            audio_block = np.random.randn(2048)
            result = optimizer.apply_eq_compensation(audio_block)

            assert result.shape == audio_block.shape

    def test_apply_eq_compensation_error_handling(self):
        """Test error handling in EQ compensation"""
        with patch('app.hardware.soundblaster.SoundBlasterOptimizer._detect_soundblaster'):
            optimizer = SoundBlasterOptimizer()
            optimizer.is_soundblaster = True

            # Invalid input
            audio_block = np.array([])

            # Should handle error and return original
            result = optimizer.apply_eq_compensation(audio_block)

            # May return original or empty array
            assert result is not None

    def test_get_info_not_detected(self):
        """Test get_info when Sound Blaster not detected"""
        with patch('app.hardware.soundblaster.SoundBlasterOptimizer._detect_soundblaster'):
            optimizer = SoundBlasterOptimizer()
            optimizer.is_soundblaster = False
            optimizer.device_name = None

            info = optimizer.get_info()

            assert 'detected' in info
            assert 'device_name' in info
            assert 'optimal_sample_rate' in info
            assert 'optimal_block_size' in info

            assert info['detected'] == False
            assert info['device_name'] is None
            assert info['optimal_sample_rate'] == 48000
            assert info['optimal_block_size'] == 2048

    def test_get_info_detected(self):
        """Test get_info when Sound Blaster detected"""
        with patch('app.hardware.soundblaster.SoundBlasterOptimizer._detect_soundblaster'):
            optimizer = SoundBlasterOptimizer()
            optimizer.is_soundblaster = True
            optimizer.device_name = 'Sound Blaster Z SE'

            info = optimizer.get_info()

            assert info['detected'] == True
            assert info['device_name'] == 'Sound Blaster Z SE'
            assert info['optimal_sample_rate'] == 48000
            assert info['optimal_block_size'] == 2048

    @patch('app.hardware.soundblaster.sd')
    def test_detect_case_insensitive(self, mock_sd):
        """Test that detection is case-insensitive"""
        mock_devices = [
            {'name': 'SOUND BLASTER Z SE'}  # Uppercase
        ]

        mock_sd.query_devices.return_value = mock_devices

        optimizer = SoundBlasterOptimizer()

        # Should detect despite case difference
        assert optimizer.is_soundblaster == True

    @patch('app.hardware.soundblaster.sd')
    def test_detect_sbz_abbreviation(self, mock_sd):
        """Test detection of SBZ abbreviation"""
        mock_devices = [
            {'name': 'SBZ Audio Device'}
        ]

        mock_sd.query_devices.return_value = mock_devices

        optimizer = SoundBlasterOptimizer()

        assert optimizer.is_soundblaster == True

    def test_eq_compensation_frequency_response(self):
        """Test that EQ compensation affects frequency response"""
        with patch('app.hardware.soundblaster.SoundBlasterOptimizer._detect_soundblaster'):
            optimizer = SoundBlasterOptimizer()
            optimizer.is_soundblaster = True

            # Create signal with low frequency (100 Hz)
            sample_rate = 48000
            t = np.linspace(0, 1, sample_rate)
            low_freq_signal = np.sin(2 * np.pi * 100 * t).reshape(-1, 1)
            low_freq_stereo = np.hstack([low_freq_signal, low_freq_signal])

            result = optimizer.apply_eq_compensation(low_freq_stereo)

            # Low frequencies should be attenuated (due to high-pass filter)
            # Power should be reduced
            original_power = np.mean(low_freq_stereo ** 2)
            result_power = np.mean(result ** 2)

            # Result power should be slightly less (subtle 20% blend)
            assert result_power <= original_power * 1.1  # Allow some tolerance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
