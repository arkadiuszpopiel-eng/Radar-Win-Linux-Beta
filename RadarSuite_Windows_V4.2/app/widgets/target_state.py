"""
RadarSuite v4.2.1-k0006 - Target State Definitions
Enumeration-like class for target movement states

FIXED v4.2.1-k0006: Extracted from radar.py for improved modularity
"""

from typing import Dict
from PyQt5.QtGui import QColor


class TargetState:
    """Target movement states with type hints (v4.2.1)."""

    UNKNOWN: int = 0
    WALK: int = 1
    RUN: int = 2
    SHOT: int = 3

    LABELS: Dict[int, str] = {
        UNKNOWN: "???",
        WALK: "WALK",
        RUN: "RUN",
        SHOT: "SHOT"
    }

    COLORS: Dict[int, QColor] = {
        UNKNOWN: QColor(100, 100, 100),
        WALK: QColor(0, 200, 100),      # Green
        RUN: QColor(255, 200, 0),       # Yellow/Orange
        SHOT: QColor(255, 50, 50)       # Red
    }
