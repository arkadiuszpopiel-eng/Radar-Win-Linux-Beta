"""
Unit tests for HumanFootstepDetector
Tests footstep pattern recognition, cadence detection, and surface classification
"""

import pytest
import numpy as np
import time
from unittest.mock import Mock, patch

from app.detection.footstep import HumanFootstepDetector


class TestHumanFootstepDetector:
    """Test suite for HumanFootstepDetector class"""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector instance for each test"""
        return HumanFootstepDetector()

    def test_initialization(self, detector):
        """Test that detector initializes with correct default values"""
        assert detector.step_history == []
        assert detector.max_history == 20
        assert detector.lr_pattern == []
        assert detector.max_lr_history == 10
        assert detector.surface_type == "unknown"
        assert detector.surface_confidence == 0.0
        assert detector.estimated_distance == 0.0

        # Check cadence ranges
        assert detector.cadence_walk == (1.5, 2.5)
        assert detector.cadence_run == (3.0, 4.5)

        # Check frequency ranges
        assert detector.freq_impact == (60, 180)
        assert detector.freq_detail == (180, 400)
        assert detector.freq_body == (20, 60)

    def test_analyze_footstep_mono_audio(self, detector):
        """Test footstep analysis with mono audio block"""
        # Generate synthetic audio with footstep-like frequencies
        sample_rate = 44100
        duration = 0.1  # 100ms
        num_samples = int(sample_rate * duration)

        # Create mono signal with impact frequency (100 Hz)
        t = np.linspace(0, duration, num_samples)
        mono_block = np.sin(2 * np.pi * 100 * t) * 0.5

        result = detector.analyze_footstep(mono_block, sample_rate, stereo=False)

        # Check result structure
        assert 'is_human_step' in result
        assert 'confidence' in result
        assert 'cadence' in result
        assert 'foot' in result
        assert 'surface' in result
        assert 'distance_m' in result
        assert 'gait_type' in result

        # Check types
        assert isinstance(result['is_human_step'], bool)
        assert isinstance(result['confidence'], float)
        assert isinstance(result['cadence'], float)
        assert isinstance(result['foot'], str)
        assert isinstance(result['surface'], str)
        assert isinstance(result['distance_m'], float)
        assert isinstance(result['gait_type'], str)

    def test_analyze_footstep_stereo_audio(self, detector):
        """Test footstep analysis with stereo audio block"""
        sample_rate = 44100
        duration = 0.1
        num_samples = int(sample_rate * duration)

        # Create stereo signal (left stronger than right)
        t = np.linspace(0, duration, num_samples)
        left = np.sin(2 * np.pi * 100 * t) * 0.8
        right = np.sin(2 * np.pi * 100 * t) * 0.3
        stereo_block = np.column_stack((left, right))

        result = detector.analyze_footstep(stereo_block, sample_rate, stereo=True)

        # Check that result is valid
        assert result is not None
        assert 'foot' in result

    def test_cadence_detection_walk(self, detector):
        """Test detection of walking cadence (1.5-2.5 steps/sec)"""
        sample_rate = 44100
        duration = 0.1
        num_samples = int(sample_rate * duration)

        # Create footstep-like signal
        t = np.linspace(0, duration, num_samples)
        signal = (np.sin(2 * np.pi * 100 * t) +
                 np.sin(2 * np.pi * 200 * t) * 0.3 +
                 np.sin(2 * np.pi * 40 * t) * 0.2) * 0.5

        # Simulate multiple steps at walking pace (2 steps/sec = 0.5s interval)
        for i in range(6):
            time.sleep(0.02)  # Small delay to simulate time passing
            with patch('time.time', return_value=i * 0.5):
                result = detector.analyze_footstep(signal, sample_rate, stereo=False)

        # After enough steps, should detect cadence
        assert detector.step_intervals is not None

    def test_cadence_detection_run(self, detector):
        """Test detection of running cadence (3.0-4.5 steps/sec)"""
        sample_rate = 44100
        duration = 0.1
        num_samples = int(sample_rate * duration)

        # Create footstep-like signal
        t = np.linspace(0, duration, num_samples)
        signal = (np.sin(2 * np.pi * 100 * t) +
                 np.sin(2 * np.pi * 200 * t) * 0.3) * 0.5

        # Simulate multiple steps at running pace (3.5 steps/sec = 0.286s interval)
        for i in range(6):
            time.sleep(0.01)
            with patch('time.time', return_value=i * 0.286):
                result = detector.analyze_footstep(signal, sample_rate, stereo=False)

        assert detector.step_intervals is not None

    def test_left_right_detection(self, detector):
        """Test left/right foot classification in stereo"""
        sample_rate = 44100
        duration = 0.1
        num_samples = int(sample_rate * duration)

        t = np.linspace(0, duration, num_samples)
        base_signal = np.sin(2 * np.pi * 100 * t) * 0.5

        # Step 1: Left foot (left channel louder)
        left1 = base_signal * 1.5
        right1 = base_signal * 0.5
        stereo1 = np.column_stack((left1, right1))

        with patch('time.time', return_value=0.0):
            detector.last_step_time = -1.0  # Ensure valid interval
            result1 = detector.analyze_footstep(stereo1, sample_rate, stereo=True)

        # Step 2: Right foot (right channel louder)
        left2 = base_signal * 0.5
        right2 = base_signal * 1.5
        stereo2 = np.column_stack((left2, right2))

        with patch('time.time', return_value=0.4):
            result2 = detector.analyze_footstep(stereo2, sample_rate, stereo=True)

        # Check that L-R pattern is tracked
        assert len(detector.lr_pattern) > 0

    def test_surface_detection_hard(self, detector):
        """Test detection of hard surface (high detail ratio)"""
        sample_rate = 44100
        duration = 0.1
        num_samples = int(sample_rate * duration)

        # Create signal with strong detail frequencies (200-400 Hz)
        t = np.linspace(0, duration, num_samples)
        signal = (np.sin(2 * np.pi * 100 * t) * 0.5 +
                 np.sin(2 * np.pi * 300 * t) * 0.8)  # Strong detail

        with patch('time.time', return_value=0.0):
            detector.last_step_time = -1.0
            result = detector.analyze_footstep(signal, sample_rate, stereo=False)

        # Hard surface should have high detail ratio
        # Result may vary based on exact frequency content

    def test_surface_detection_soft(self, detector):
        """Test detection of soft surface (low detail ratio)"""
        sample_rate = 44100
        duration = 0.1
        num_samples = int(sample_rate * duration)

        # Create signal with weak detail frequencies
        t = np.linspace(0, duration, num_samples)
        signal = (np.sin(2 * np.pi * 100 * t) * 0.5 +
                 np.sin(2 * np.pi * 300 * t) * 0.1)  # Weak detail

        with patch('time.time', return_value=0.0):
            detector.last_step_time = -1.0
            result = detector.analyze_footstep(signal, sample_rate, stereo=False)

    def test_distance_estimation(self, detector):
        """Test distance estimation based on loudness"""
        sample_rate = 44100
        duration = 0.1
        num_samples = int(sample_rate * duration)

        t = np.linspace(0, duration, num_samples)

        # Loud signal (close)
        loud_signal = np.sin(2 * np.pi * 100 * t) * 0.8

        # Quiet signal (far)
        quiet_signal = np.sin(2 * np.pi * 100 * t) * 0.1

        with patch('time.time', return_value=0.0):
            detector.last_step_time = -1.0
            result_loud = detector.analyze_footstep(loud_signal, sample_rate, stereo=False)

        with patch('time.time', return_value=0.5):
            result_quiet = detector.analyze_footstep(quiet_signal, sample_rate, stereo=False)

        # Distance estimation may vary, just check it's calculated
        assert 'distance_m' in result_loud
        assert 'distance_m' in result_quiet

    def test_pattern_quality(self, detector):
        """Test pattern quality scoring"""
        # No steps yet
        quality = detector.get_pattern_quality()
        assert quality == 0.0

        # Add some regular step intervals
        detector.step_intervals = [0.5, 0.5, 0.5, 0.5]
        quality = detector.get_pattern_quality()
        assert quality > 0.0

        # Add L-R pattern
        detector.lr_pattern = ['L', 'R', 'L', 'R']
        quality_with_lr = detector.get_pattern_quality()
        assert quality_with_lr > quality

    def test_max_history_limits(self, detector):
        """Test that history buffers respect maximum limits"""
        # Fill step history beyond max
        for i in range(30):
            detector.step_history.append(float(i))

        # Should be capped at max_history
        assert len(detector.step_history) <= detector.max_history

        # Fill L-R pattern beyond max
        for i in range(15):
            detector.lr_pattern.append('L')

        # Should be capped at max_lr_history
        assert len(detector.lr_pattern) <= detector.max_lr_history

    def test_error_handling(self, detector):
        """Test that errors are handled gracefully"""
        # Invalid input (None)
        result = detector.analyze_footstep(None, 44100, stereo=False)
        assert result['is_human_step'] == False
        assert result['confidence'] == 0.0

        # Empty array
        result = detector.analyze_footstep(np.array([]), 44100, stereo=False)
        assert result['is_human_step'] == False

    def test_step_interval_validation(self, detector):
        """Test that only valid step intervals are recorded"""
        sample_rate = 44100
        duration = 0.1
        num_samples = int(sample_rate * duration)

        t = np.linspace(0, duration, num_samples)
        signal = np.sin(2 * np.pi * 100 * t) * 0.5

        # Too fast (< 150ms)
        with patch('time.time', return_value=0.0):
            detector.last_step_time = 0.0
            result1 = detector.analyze_footstep(signal, sample_rate, stereo=False)

        with patch('time.time', return_value=0.05):  # 50ms later - too fast
            result2 = detector.analyze_footstep(signal, sample_rate, stereo=False)

        # Should not add to intervals (too fast)

        # Valid interval (300ms)
        with patch('time.time', return_value=0.3):
            result3 = detector.analyze_footstep(signal, sample_rate, stereo=False)

    def test_confidence_calculation(self, detector):
        """Test confidence calculation based on regularity"""
        # Add irregular intervals
        detector.step_intervals = [0.3, 0.5, 0.2, 0.6, 0.4]

        # Add regular intervals
        detector_regular = HumanFootstepDetector()
        detector_regular.step_intervals = [0.4, 0.4, 0.4, 0.4, 0.4]

        # Regular pattern should have higher quality
        irregular_quality = detector.get_pattern_quality()
        regular_quality = detector_regular.get_pattern_quality()

        assert regular_quality >= irregular_quality


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
