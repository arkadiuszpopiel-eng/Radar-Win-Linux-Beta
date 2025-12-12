"""
RadarSuite v4.2.1-k0006 - Radar Widgets (Re-export Layer)

FIXED v4.2.1-k0006: Modular architecture
Split original 1674-line radar.py into 7 focused modules for improved maintainability:
- target_state.py (27 lines) - TargetState enum
- military_hud.py (600 lines) - MilitaryHUDRadar main widget
- minimal_radar.py (276 lines) - MinimalRadarWidget
- detachable_radar.py (77 lines) - DetachableRadarWidget
- radar_widget.py (78 lines) - RadarWidget (pyqtgraph)
- military_3d.py (458 lines) - Military3DRadar (OpenGL)
- radar_3d.py (125 lines) - Radar3DWidget (OpenGL)

This file re-exports all classes for backward compatibility.
Existing code using "from widgets.radar import X" will continue to work.
"""

# Re-export all radar classes for backward compatibility
from .target_state import TargetState
from .military_hud import MilitaryHUDRadar
from .minimal_radar import MinimalRadarWidget
from .detachable_radar import DetachableRadarWidget
from .radar_widget import RadarWidget
from .military_3d import Military3DRadar
from .radar_3d import Radar3DWidget

__all__ = [
    'TargetState',
    'MilitaryHUDRadar',
    'MinimalRadarWidget',
    'DetachableRadarWidget',
    'RadarWidget',
    'Military3DRadar',
    'Radar3DWidget',
]
