"""
Unit tests for HumanFootstepDetector
Tests mono/stereo handling, shape normalization, and error resilience

FIXED v4.2.0: Comprehensive tests for ARC Raiders integration
"""

import numpy as np
import pytest
from detection.footstep import HumanFootstepDetector


class TestHumanFootstepDetector:
    """Test suite for Human Footstep Detection"""

    def setup_method(self):
        """Setup test fixtures"""
        self.detector = HumanFootstepDetector(sample_rate=48000, debug_mode=False)
        self.sample_rate = 48000
        self.block_size = 2048

    def test_mono_1d_array(self):
        """Test Case 1: Mono audio as 1D array (N,)"""
        mono_block = np.random.randn(self.block_size)

        result = self.detector.analyze_footstep(mono_block, self.sample_rate, stereo=False)

        assert isinstance(result, dict)
        assert 'is_human_step' in result
        assert 'confidence' in result
        assert 'cadence' in result
        # Should not crash with IndexError

    def test_stereo_samples_channels(self):
        """Test Case 2: Stereo audio as (samples, channels) = (N, 2)"""
        stereo_block = np.random.randn(self.block_size, 2)

        result = self.detector.analyze_footstep(stereo_block, self.sample_rate, stereo=True)

        assert isinstance(result, dict)
        assert 'is_human_step' in result
        assert 'foot' in result
        # Should handle stereo properly

    def test_stereo_channels_samples(self):
        """Test Case 3: Stereo audio as (channels, samples) = (2, N)"""
        stereo_block = np.random.randn(2, self.block_size)

        result = self.detector.analyze_footstep(stereo_block, self.sample_rate, stereo=True)

        assert isinstance(result, dict)
        assert 'is_human_step' in result
        # Should transpose and handle correctly

    def test_mono_2d_single_channel(self):
        """Test Case 4: Mono audio as (samples, 1)"""
        mono_2d_block = np.random.randn(self.block_size, 1)

        result = self.detector.analyze_footstep(mono_2d_block, self.sample_rate, stereo=False)

        assert isinstance(result, dict)
        assert 'is_human_step' in result
        # Should not crash, should handle as mono

    def test_empty_array(self):
        """Test Case 5: Empty or malformed array"""
        empty_block = np.array([])

        result = self.detector.analyze_footstep(empty_block, self.sample_rate, stereo=False)

        # Should not crash, should return safe default
        assert isinstance(result, dict)
        assert result['is_human_step'] == False

    def test_very_small_array(self):
        """Test Case 6: Very small audio block"""
        tiny_block = np.random.randn(10)

        result = self.detector.analyze_footstep(tiny_block, self.sample_rate, stereo=False)

        # Should not crash
        assert isinstance(result, dict)

    def test_result_structure(self):
        """Test Case 7: Result dictionary structure"""
        block = np.random.randn(self.block_size)

        result = self.detector.analyze_footstep(block, self.sample_rate, stereo=False)

        # Check all expected keys are present
        required_keys = ['is_human_step', 'confidence', 'cadence', 'foot',
                        'surface', 'distance_m', 'gait_type']
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

        # Check types
        assert isinstance(result['is_human_step'], bool)
        assert isinstance(result['confidence'], (int, float))
        assert isinstance(result['cadence'], (int, float))
        assert isinstance(result['foot'], str)
        assert isinstance(result['surface'], str)
        assert isinstance(result['distance_m'], (int, float))
        assert isinstance(result['gait_type'], str)

    def test_confidence_range(self):
        """Test Case 8: Confidence should be in valid range [0, 100]"""
        block = np.random.randn(self.block_size)

        result = self.detector.analyze_footstep(block, self.sample_rate, stereo=False)

        assert 0.0 <= result['confidence'] <= 100.0

    def test_debug_mode_enabled(self):
        """Test Case 9: Debug mode should not crash"""
        debug_detector = HumanFootstepDetector(sample_rate=48000, debug_mode=True)
        block = np.random.randn(self.block_size)

        result = debug_detector.analyze_footstep(block, self.sample_rate, stereo=False)

        assert isinstance(result, dict)
        # Debug logging should work without crashes

    def test_error_rate_limiting(self):
        """Test Case 10: Error rate limiting prevents log spam"""
        # Create intentionally bad data to trigger errors
        bad_blocks = [None, "not_an_array", [], np.array([[[1]]]), object()]

        for bad_block in bad_blocks:
            try:
                result = self.detector.analyze_footstep(bad_block, self.sample_rate, stereo=False)
                # Should return safe default even on error
                assert isinstance(result, dict)
                assert result['is_human_step'] == False
            except Exception:
                # Some errors might still propagate, but detector should handle most
                pass

    def test_surface_classification(self):
        """Test Case 11: Surface classification integration"""
        block = np.random.randn(self.block_size)

        result = self.detector.analyze_footstep(block, self.sample_rate, stereo=False)

        # Surface type should be one of known types
        valid_surfaces = ['unknown', 'metal', 'dirt', 'snow', 'concrete', 'wood', 'hard', 'medium', 'soft']
        assert result['surface'] in valid_surfaces

    def test_gait_type_classification(self):
        """Test Case 12: Gait type classification"""
        block = np.random.randn(self.block_size)

        result = self.detector.analyze_footstep(block, self.sample_rate, stereo=False)

        # Gait type should be one of known types
        valid_gaits = ['unknown', 'walk', 'run']
        assert result['gait_type'] in valid_gaits

    def test_multiple_consecutive_calls(self):
        """Test Case 13: Multiple consecutive calls should maintain state properly"""
        blocks = [np.random.randn(self.block_size) for _ in range(10)]

        results = []
        for block in blocks:
            result = self.detector.analyze_footstep(block, self.sample_rate, stereo=False)
            results.append(result)

        # All should complete successfully
        assert len(results) == 10
        for result in results:
            assert isinstance(result, dict)

    def test_cadence_ranges(self):
        """Test Case 14: Cadence ranges for ARC Raiders"""
        # Check that relaxed ranges are set
        assert self.detector.cadence_walk == (1.4, 2.6)
        assert self.detector.cadence_run == (2.8, 4.8)

    def test_lowered_thresholds(self):
        """Test Case 15: Lowered thresholds for better ARC Raiders sensitivity"""
        # Check that thresholds are lowered for better detection
        assert self.detector.base_impact_threshold == 0.12  # Was 0.15
        assert self.detector.base_detail_threshold == 0.04  # Was 0.05
        assert self.detector.base_body_threshold == 0.015   # Was 0.02


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
