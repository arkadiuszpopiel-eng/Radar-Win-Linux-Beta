"""
RadarSuite v3.5.0 - Point 12: Shared Test Fixtures
Provides common fixtures and utilities for all tests
"""

from tests.compat import pytest
import sys
import os
from pathlib import Path

# Add app directory to path for imports
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'audio': {
            'sample_rate': 48000,
            'block_size': 2048,
            'channels': 2,
            'device': None,
        },
        'performance': {
            'use_gpu': False,  # Disable GPU for tests
            'max_workers': 2,
            'cache_size': 5,
        },
        'detection': {
            'threshold': 0.5,
            'min_confidence': 0.6,
            'cooldown_ms': 100,
        },
        'tracking': {
            'max_targets': 3,
            'timeout_seconds': 5.0,
        },
        'ui': {
            'theme': 'dark',
            'fps': 20,
            'enable_3d': False,
        }
    }


@pytest.fixture
def mock_audio_data():
    """Generate mock audio data for testing"""
    import numpy as np
    sample_rate = 48000
    duration = 0.1  # 100ms
    samples = int(sample_rate * duration)

    # Generate simple sine wave
    t = np.linspace(0, duration, samples)
    frequency = 440  # A4 note
    audio = np.sin(2 * np.pi * frequency * t)

    return audio.astype(np.float32)


@pytest.fixture
def temp_config_file(tmp_path, sample_config):
    """Create a temporary config file for testing"""
    import json

    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config, f, indent=2)

    return config_file


@pytest.fixture
def mock_logger():
    """Mock logger to avoid file I/O in tests"""
    class MockLogger:
        def __init__(self):
            self.logs = []

        def log(self, message, level="INFO"):
            self.logs.append((level, message))

        def get_logs(self, level=None):
            if level:
                return [msg for lvl, msg in self.logs if lvl == level]
            return self.logs

        def clear(self):
            self.logs.clear()

    return MockLogger()


@pytest.fixture
def di_container():
    """Create a fresh DI container for testing"""
    from core.di import ServiceContainer
    container = ServiceContainer()
    yield container
    container.reset()


@pytest.fixture(autouse=True)
def reset_singletons():
    """Auto-reset singletons between tests to prevent state leakage"""
    yield
    # Cleanup happens after each test
    # Add any singleton cleanup here if needed
