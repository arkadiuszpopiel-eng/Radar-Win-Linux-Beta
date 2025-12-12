"""
Pytest compatibility layer
Tries to import pytest, falls back to shim if not available
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    from tests import pytest_shim as pytest
    PYTEST_AVAILABLE = False

__all__ = ['pytest', 'PYTEST_AVAILABLE']
