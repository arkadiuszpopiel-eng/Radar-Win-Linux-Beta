"""
RadarSuite v3.5.0 - Point 12: Core Constants Tests
Tests for core/constants.py
"""

from tests.compat import pytest
from core import constants


class TestConstants:
    """Test suite for application constants"""

    def test_version_constant_exists(self):
        """Verify VERSION constant is defined"""
        assert hasattr(constants, 'VERSION')
        assert isinstance(constants.VERSION, str)
        assert len(constants.VERSION) > 0

    def test_performance_constants(self):
        """Verify performance-related constants"""
        assert hasattr(constants, 'MAX_WORKERS')
        assert isinstance(constants.MAX_WORKERS, int)
        assert constants.MAX_WORKERS > 0

        assert hasattr(constants, 'TICK_INTERVAL_MS')
        assert isinstance(constants.TICK_INTERVAL_MS, int)
        assert constants.TICK_INTERVAL_MS > 0

    def test_audio_constants(self):
        """Verify audio-related constants"""
        assert hasattr(constants, 'SAMPLE_RATE')
        assert isinstance(constants.SAMPLE_RATE, int)
        assert constants.SAMPLE_RATE > 0

        assert hasattr(constants, 'BLOCK_SIZE')
        assert isinstance(constants.BLOCK_SIZE, int)
        assert constants.BLOCK_SIZE > 0

    def test_timing_constants(self):
        """Verify timing-related constants"""
        assert hasattr(constants, 'GAME_SCAN_INTERVAL_MS')
        assert isinstance(constants.GAME_SCAN_INTERVAL_MS, int)
        assert constants.GAME_SCAN_INTERVAL_MS > 0

        assert hasattr(constants, 'STARTUP_DELAY_MS')
        assert isinstance(constants.STARTUP_DELAY_MS, int)
        assert constants.STARTUP_DELAY_MS >= 0

    def test_ui_constants(self):
        """Verify UI-related constants"""
        assert hasattr(constants, 'TOAST_DURATION_MS')
        assert isinstance(constants.TOAST_DURATION_MS, int)

        assert hasattr(constants, 'TOAST_MAX_COUNT')
        assert isinstance(constants.TOAST_MAX_COUNT, int)

    def test_detection_constants(self):
        """Verify detection thresholds"""
        assert hasattr(constants, 'ENERGY_THRESHOLD')
        assert isinstance(constants.ENERGY_THRESHOLD, (int, float))
        assert constants.ENERGY_THRESHOLD > 0

    def test_constants_immutability(self):
        """Verify constants are not accidentally mutable collections"""
        # This is a code smell check - constants should not be lists/dicts
        for name in dir(constants):
            if name.isupper() and not name.startswith('_'):
                value = getattr(constants, name)
                # Constants should be primitives or tuples (immutable)
                assert not isinstance(value, (list, dict, set)), \
                    f"Constant {name} is mutable type {type(value)}"
