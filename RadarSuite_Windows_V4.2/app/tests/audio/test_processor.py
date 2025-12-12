"""
RadarSuite v4.2.0 - AudioProcessor Tests
Unit tests for audio processing and 3D localization

Created as part of 10-point development plan (Punkt 4)
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from audio.processor import AudioProcessor, get_audio_processor


class TestAudioProcessor:
    """Test suite for AudioProcessor class"""

    @pytest.fixture
    def processor(self):
        """Create AudioProcessor instance for testing"""
        return AudioProcessor(sample_rate=48000)

    @pytest.fixture
    def stereo_block(self):
        """Generate stereo test audio block"""
        t = np.linspace(0, 0.1, 4800)  # 100ms at 48kHz
        left = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine
        right = 0.5 * np.sin(2 * np.pi * 440 * t)
        return np.column_stack([left, right])

    @pytest.fixture
    def silent_block(self):
        """Generate silent stereo block"""
        return np.zeros((4800, 2))

    # ========================================================================
    # Test apply_processing()
    # ========================================================================

    def test_apply_processing_passthrough(self, processor, stereo_block):
        """Test that unity gain passes audio unchanged"""
        result = processor.apply_processing(
            stereo_block,
            auto_gain=False,
            manual_gain=1.0,
            noise_gate_db=-80.0
        )
        np.testing.assert_array_almost_equal(result, stereo_block, decimal=5)

    def test_apply_processing_manual_gain(self, processor, stereo_block):
        """Test manual gain application"""
        result = processor.apply_processing(
            stereo_block,
            auto_gain=False,
            manual_gain=2.0,
            noise_gate_db=-80.0
        )
        # Result should be 2x input (but clipped if needed)
        expected = stereo_block * 2.0
        max_val = np.max(np.abs(expected))
        if max_val > 1.0:
            expected /= max_val
        np.testing.assert_array_almost_equal(result, expected, decimal=5)

    def test_apply_processing_noise_gate(self, processor):
        """Test noise gate mutes quiet signals"""
        # Very quiet signal
        quiet_block = np.random.randn(4800, 2) * 0.0001
        result = processor.apply_processing(
            quiet_block,
            auto_gain=False,
            manual_gain=1.0,
            noise_gate_db=-40.0  # High threshold
        )
        # Should be muted (all zeros)
        assert np.max(np.abs(result)) == 0.0

    def test_apply_processing_auto_gain(self, processor):
        """Test auto-gain normalizes to target level"""
        # Quiet signal
        quiet_block = np.random.randn(4800, 2) * 0.01
        result = processor.apply_processing(
            quiet_block,
            auto_gain=True,
            manual_gain=1.0,
            noise_gate_db=-80.0
        )
        # Result should be louder than input
        assert np.sqrt(np.mean(result ** 2)) > np.sqrt(np.mean(quiet_block ** 2))

    def test_apply_processing_prevents_clipping(self, processor, stereo_block):
        """Test that output never exceeds ±1.0"""
        result = processor.apply_processing(
            stereo_block,
            auto_gain=False,
            manual_gain=100.0,  # Very high gain
            noise_gate_db=-80.0
        )
        assert np.max(np.abs(result)) <= 1.0

    def test_apply_processing_handles_none(self, processor):
        """Test handling of None input"""
        result = processor.apply_processing(None)
        assert result is None

    def test_apply_processing_handles_empty(self, processor):
        """Test handling of empty array"""
        result = processor.apply_processing(np.array([]))
        assert len(result) == 0

    # ========================================================================
    # Test compute_orientation()
    # ========================================================================

    def test_compute_orientation_stereo(self, processor, stereo_block):
        """Test energy and balance computation for stereo"""
        energy, balance = processor.compute_orientation(stereo_block)
        assert 0.0 <= energy <= 1.0
        assert -1.0 <= balance <= 1.0

    def test_compute_orientation_balanced(self, processor, stereo_block):
        """Test balanced stereo has near-zero balance"""
        energy, balance = processor.compute_orientation(stereo_block)
        assert abs(balance) < 0.1  # Should be close to zero

    def test_compute_orientation_left_heavy(self, processor):
        """Test left-heavy signal has negative balance"""
        t = np.linspace(0, 0.1, 4800)
        left = np.sin(2 * np.pi * 440 * t)
        right = np.sin(2 * np.pi * 440 * t) * 0.1  # Much quieter
        block = np.column_stack([left, right])

        energy, balance = processor.compute_orientation(block)
        assert balance < -0.5  # Should be negative (left-heavy)

    def test_compute_orientation_right_heavy(self, processor):
        """Test right-heavy signal has positive balance"""
        t = np.linspace(0, 0.1, 4800)
        left = np.sin(2 * np.pi * 440 * t) * 0.1  # Much quieter
        right = np.sin(2 * np.pi * 440 * t)
        block = np.column_stack([left, right])

        energy, balance = processor.compute_orientation(block)
        assert balance > 0.5  # Should be positive (right-heavy)

    def test_compute_orientation_silent(self, processor, silent_block):
        """Test silent signal returns zero energy"""
        energy, balance = processor.compute_orientation(silent_block)
        assert energy < 1e-10
        assert abs(balance) < 0.1

    def test_compute_orientation_mono(self, processor):
        """Test mono signal handling"""
        mono = np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, 4800))
        energy, balance = processor.compute_orientation(mono)
        assert energy > 0
        assert balance == 0.0  # Mono has no balance

    # ========================================================================
    # Test compute_location_3d()
    # ========================================================================

    def test_compute_location_3d_returns_dict(self, processor, stereo_block):
        """Test that compute_location_3d returns expected dictionary"""
        result = processor.compute_location_3d(stereo_block)

        assert isinstance(result, dict)
        assert 'angle' in result
        assert 'distance' in result
        assert 'elevation' in result
        assert 'confidence' in result

    def test_compute_location_3d_angle_range(self, processor, stereo_block):
        """Test angle is within valid range"""
        result = processor.compute_location_3d(stereo_block)
        assert -180.0 <= result['angle'] <= 180.0

    def test_compute_location_3d_distance_range(self, processor, stereo_block):
        """Test distance is within valid range"""
        result = processor.compute_location_3d(stereo_block)
        assert 0.5 <= result['distance'] <= 15.0

    def test_compute_location_3d_elevation_range(self, processor, stereo_block):
        """Test elevation is within valid range"""
        result = processor.compute_location_3d(stereo_block)
        assert -45.0 <= result['elevation'] <= 45.0

    def test_compute_location_3d_confidence_range(self, processor, stereo_block):
        """Test confidence is within valid range"""
        result = processor.compute_location_3d(stereo_block)
        assert 0.0 <= result['confidence'] <= 1.0

    def test_compute_location_3d_silent_low_confidence(self, processor, silent_block):
        """Test silent signal has low confidence"""
        result = processor.compute_location_3d(silent_block)
        assert result['confidence'] < 0.1

    def test_compute_location_3d_mono_fails_gracefully(self, processor):
        """Test mono input returns default values"""
        mono = np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, 4800))
        result = processor.compute_location_3d(mono)

        # Should return defaults for mono
        assert result['confidence'] == 0.0

    # ========================================================================
    # Test compute_elevation()
    # ========================================================================

    def test_compute_elevation_returns_float(self, processor, stereo_block):
        """Test elevation returns float value"""
        elevation = processor.compute_elevation(stereo_block)
        assert isinstance(elevation, float)

    def test_compute_elevation_range(self, processor, stereo_block):
        """Test elevation is within valid range"""
        elevation = processor.compute_elevation(stereo_block)
        assert -45.0 <= elevation <= 45.0

    def test_compute_elevation_low_freq(self, processor):
        """Test low frequency gives low elevation"""
        t = np.linspace(0, 0.1, 4800)
        low_freq = np.sin(2 * np.pi * 100 * t)  # 100 Hz
        block = np.column_stack([low_freq, low_freq])

        elevation = processor.compute_elevation(block)
        assert elevation < 0  # Low freq = below horizon

    def test_compute_elevation_high_freq(self, processor):
        """Test high frequency gives high elevation"""
        t = np.linspace(0, 0.1, 4800)
        high_freq = np.sin(2 * np.pi * 5000 * t)  # 5 kHz
        block = np.column_stack([high_freq, high_freq])

        elevation = processor.compute_elevation(block)
        assert elevation > 0  # High freq = above horizon

    # ========================================================================
    # Test generate_test_signal()
    # ========================================================================

    def test_generate_test_signal_mono(self, processor):
        """Test mono test signal generation"""
        signal = processor.generate_test_signal(4800, channels=1)
        assert signal.shape == (4800,)

    def test_generate_test_signal_stereo(self, processor):
        """Test stereo test signal generation"""
        signal = processor.generate_test_signal(4800, channels=2)
        assert signal.shape == (4800, 2)

    def test_generate_test_signal_angle_left(self, processor):
        """Test left angle produces louder left channel"""
        signal = processor.generate_test_signal(4800, channels=2, angle=-45.0)
        left_energy = np.sqrt(np.mean(signal[:, 0] ** 2))
        right_energy = np.sqrt(np.mean(signal[:, 1] ** 2))
        assert left_energy > right_energy

    def test_generate_test_signal_angle_right(self, processor):
        """Test right angle produces louder right channel"""
        signal = processor.generate_test_signal(4800, channels=2, angle=45.0)
        left_energy = np.sqrt(np.mean(signal[:, 0] ** 2))
        right_energy = np.sqrt(np.mean(signal[:, 1] ** 2))
        assert right_energy > left_energy

    # ========================================================================
    # Test singleton pattern
    # ========================================================================

    def test_get_audio_processor_singleton(self):
        """Test singleton returns same instance"""
        p1 = get_audio_processor(48000)
        p2 = get_audio_processor(48000)
        assert p1 is p2


class TestErrorHandler:
    """Test suite for error_handler module"""

    def test_handle_errors_decorator(self):
        """Test handle_errors decorator catches exceptions"""
        from core.error_handler import handle_errors

        @handle_errors(default_return=-1)
        def failing_function():
            raise ValueError("Test error")

        result = failing_function()
        assert result == -1

    def test_safe_call(self):
        """Test safe_call function"""
        from core.error_handler import safe_call

        def add(a, b):
            return a + b

        # Normal call
        assert safe_call(add, 1, 2) == 3

        # Error call
        def fail():
            raise RuntimeError("Test")

        assert safe_call(fail, default=0) == 0

    def test_ensure_not_none(self):
        """Test ensure_not_none helper"""
        from core.error_handler import ensure_not_none

        assert ensure_not_none(5, 0) == 5
        assert ensure_not_none(None, 0) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
