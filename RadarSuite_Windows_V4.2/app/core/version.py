"""Compatibility shim for build metadata access.

This module provides ``get_build_id`` for callers that historically used
``core.version``. The implementation delegates to the canonical
``app.version`` module to avoid duplication.
"""

from app.version import get_build_id

__all__ = ["get_build_id"]
