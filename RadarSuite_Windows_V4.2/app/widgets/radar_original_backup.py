"""
RadarSuite v4.2.1 - Military Sci-Fi HUD Radar
Ultra-readable military radar interface with Walk/Run/Shot indicators

FIXED v4.2.1: Added comprehensive type hints
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRectF, QPointF
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QPalette, QFont,
                         QLinearGradient, QRadialGradient, QPainterPath,
                         QPolygonF, QPaintEvent)

from core import log, tr, VERSION

if TYPE_CHECKING:
    from numpy.typing import NDArray


# =============================================================================
# TARGET STATE ICONS - Walk / Run / Shot
# =============================================================================

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


# =============================================================================
# MILITARY SCI-FI HUD RADAR WIDGET
# =============================================================================

class MilitaryHUDRadar(QWidget):
    """
    Military Sci-Fi HUD Radar Display

    Features:
    - Central radar with concentric circles and grid
    - Walk/Run/Shot target icons with labels
    - Left panel: Target list with distance/speed
    - Right panel: Tactical data and system status
    - Bottom panel: Status bar (LOCK, SCAN, RANGE)
    """

    target_clicked = pyqtSignal(int)  # Signal when target is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        log("MilitaryHUDRadar.__init__", "INFO")

        self.setMinimumSize(600, 500)
        self.setStyleSheet("background-color: #030508;")

        # Colors
        self.COLOR_BG = QColor(3, 5, 8)
        self.COLOR_GRID = QColor(0, 60, 80, 80)
        self.COLOR_GRID_MAJOR = QColor(0, 100, 120, 120)
        self.COLOR_SWEEP = QColor(0, 255, 100, 150)
        self.COLOR_TEXT = QColor(0, 200, 150)
        self.COLOR_TEXT_DIM = QColor(0, 120, 100)
        self.COLOR_ACCENT = QColor(0, 255, 200)
        self.COLOR_WARNING = QColor(255, 200, 0)
        self.COLOR_DANGER = QColor(255, 50, 50)

        # Fonts
        self.FONT_MAIN = QFont("Consolas", 9)
        self.FONT_LABEL = QFont("Consolas", 8)
        self.FONT_STATUS = QFont("Consolas", 10, QFont.Bold)
        self.FONT_TITLE = QFont("Consolas", 11, QFont.Bold)

        # Radar state
        self.sweep_angle = 0
        self.radar_radius = 180
        self.max_distance = 100  # meters

        # Targets: list of dict {id, angle, distance, state, speed, label}
        self.targets = []
        self.selected_target_id = None

        # System status
        self.scan_mode = "ACTIVE"
        self.lock_status = "SCANNING"
        self.range_mode = "100m"

        # Animation timer
        self.sweep_timer = QTimer()
        self.sweep_timer.timeout.connect(self._update_sweep)
        self.sweep_timer.start(50)  # 20 FPS sweep

        # Performance tracking
        self.last_update_time = time.time()
        self.fps = 0

    def _update_sweep(self):
        """Update sweep line animation"""
        self.sweep_angle = (self.sweep_angle + 3) % 360
        self.update()

    def update_sweep(self, angle_deg):
        """Update sweep angle from external source (main tick)"""
        self.sweep_angle = angle_deg % 360
        self.update()

    # =========================================================================
    # TARGET MANAGEMENT
    # =========================================================================

    def add_target(
        self,
        target_id: int,
        angle: float,
        distance: float,
        state: int = TargetState.UNKNOWN,
        speed: float = 0.0,
        label: str = ""
    ) -> None:
        """Add or update a target on the radar (v4.2.1: type hints)."""
        # Check if target exists
        for t in self.targets:
            if t['id'] == target_id:
                t['angle'] = angle
                t['distance'] = min(distance, self.max_distance)
                t['state'] = state
                t['speed'] = speed
                t['label'] = label
                t['last_seen'] = time.time()
                return

        # Add new target
        self.targets.append({
            'id': target_id,
            'angle': angle,
            'distance': min(distance, self.max_distance),
            'state': state,
            'speed': speed,
            'label': label,
            'last_seen': time.time()
        })

    def update_target(self, angle_deg, distance):
        """
        Update/add primary target position (compatible with main.py interface)

        Args:
            angle_deg: Angle in degrees (or None to clear)
            distance: Distance value (or None to clear)
        """
        if angle_deg is None or distance is None:
            # Clear primary target
            self.targets = [t for t in self.targets if t['id'] != 0]
            return

        # Update or add primary target (id=0)
        for t in self.targets:
            if t['id'] == 0:
                t['angle'] = angle_deg
                t['distance'] = min(distance, self.max_distance)
                t['last_seen'] = time.time()
                return

        # Add new primary target
        self.targets.append({
            'id': 0,
            'angle': angle_deg,
            'distance': min(distance, self.max_distance),
            'state': TargetState.UNKNOWN,
            'speed': 0,
            'label': 'TARGET',
            'last_seen': time.time()
        })

    def update_target_by_id(self, target_id, angle=None, distance=None, state=None,
                      speed=None):
        """Update specific target properties by ID"""
        for t in self.targets:
            if t['id'] == target_id:
                if angle is not None:
                    t['angle'] = angle
                if distance is not None:
                    t['distance'] = min(distance, self.max_distance)
                if state is not None:
                    t['state'] = state
                if speed is not None:
                    t['speed'] = speed
                t['last_seen'] = time.time()
                return

    def remove_target(self, target_id: int) -> None:
        """Remove target from radar (v4.2.1: type hints)."""
        self.targets = [t for t in self.targets if t['id'] != target_id]

    def clear_targets(self) -> None:
        """Clear all targets (v4.2.1: type hints)."""
        self.targets = []

    def cleanup_stale_targets(self, max_age_seconds: float = 3.0) -> None:
        """
        Remove targets that haven't been updated recently (FIXED v4.2.0)
        Defensive cleanup for stuck targets on radar UI
        """
        current_time = time.time()
        before_count = len(self.targets)
        self.targets = [t for t in self.targets
                       if (current_time - t.get('last_seen', current_time)) < max_age_seconds]
        removed = before_count - len(self.targets)
        if removed > 0:
            from core.logger import log
            log(f"MilitaryHUDRadar: Cleaned {removed} stale targets (>{max_age_seconds}s old)", "DEBUG")

    def set_system_status(self, scan_mode=None, lock_status=None, range_mode=None):
        """Update system status indicators"""
        if scan_mode:
            self.scan_mode = scan_mode
        if lock_status:
            self.lock_status = lock_status
        if range_mode:
            self.range_mode = range_mode

    # =========================================================================
    # PAINTING
    # =========================================================================

    def paintEvent(self, event):
        """Main paint event - draws entire HUD"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # Get dimensions
        w = self.width()
        h = self.height()

        # Calculate radar center and radius
        panel_width = 150
        status_height = 40
        radar_area_w = w - panel_width * 2
        radar_area_h = h - status_height
        self.radar_radius = min(radar_area_w, radar_area_h) // 2 - 20
        center_x = w // 2
        center_y = (h - status_height) // 2

        # Draw background
        painter.fillRect(0, 0, w, h, self.COLOR_BG)

        # Draw components
        self._draw_radar_grid(painter, center_x, center_y)
        self._draw_sweep_line(painter, center_x, center_y)
        self._draw_targets(painter, center_x, center_y)
        self._draw_left_panel(painter, panel_width)
        self._draw_right_panel(painter, w, panel_width)
        self._draw_status_bar(painter, w, h, status_height)
        self._draw_corner_decorations(painter, w, h)

    def _draw_radar_grid(self, painter, cx, cy):
        """Draw radar grid with concentric circles and coordinate lines"""
        r = self.radar_radius

        # Background glow
        gradient = QRadialGradient(cx, cy, r)
        gradient.setColorAt(0, QColor(0, 30, 40, 60))
        gradient.setColorAt(0.7, QColor(0, 20, 30, 30))
        gradient.setColorAt(1, QColor(0, 10, 15, 10))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Concentric circles
        for i, ratio in enumerate([0.25, 0.5, 0.75, 1.0]):
            radius = int(r * ratio)
            if ratio == 1.0:
                painter.setPen(QPen(self.COLOR_GRID_MAJOR, 2))
            else:
                painter.setPen(QPen(self.COLOR_GRID, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

            # Distance labels
            dist_label = f"{int(self.max_distance * ratio)}m"
            painter.setFont(self.FONT_LABEL)
            painter.setPen(self.COLOR_TEXT_DIM)
            painter.drawText(cx + 5, cy - radius + 12, dist_label)

        # Radial lines (every 30 degrees)
        painter.setPen(QPen(self.COLOR_GRID, 1))
        for angle in range(0, 360, 30):
            rad = math.radians(angle - 90)
            x1 = cx + int(r * 0.1 * math.cos(rad))
            y1 = cy + int(r * 0.1 * math.sin(rad))
            x2 = cx + int(r * math.cos(rad))
            y2 = cy + int(r * math.sin(rad))
            painter.drawLine(x1, y1, x2, y2)

        # Cardinal direction labels
        painter.setFont(self.FONT_STATUS)
        painter.setPen(self.COLOR_TEXT)
        offset = r + 15
        painter.drawText(cx - 5, cy - offset, "N")
        painter.drawText(cx - 5, cy + offset + 10, "S")
        painter.drawText(cx + offset, cy + 5, "E")
        painter.drawText(cx - offset - 10, cy + 5, "W")

        # Cross-hair at center
        painter.setPen(QPen(self.COLOR_ACCENT, 1))
        ch_size = 10
        painter.drawLine(cx - ch_size, cy, cx + ch_size, cy)
        painter.drawLine(cx, cy - ch_size, cx, cy + ch_size)

    def _draw_sweep_line(self, painter, cx, cy):
        """Draw rotating sweep line with trail effect"""
        r = self.radar_radius

        # Trail effect (fading arc)
        for i in range(30):
            trail_angle = self.sweep_angle - i * 2
            alpha = int(150 * (1 - i / 30))
            rad = math.radians(trail_angle - 90)
            x = cx + int(r * math.cos(rad))
            y = cy + int(r * math.sin(rad))
            painter.setPen(QPen(QColor(0, 255, 100, alpha), 1))
            painter.drawLine(cx, cy, x, y)

        # Main sweep line
        rad = math.radians(self.sweep_angle - 90)
        x = cx + int(r * math.cos(rad))
        y = cy + int(r * math.sin(rad))
        painter.setPen(QPen(self.COLOR_SWEEP, 2))
        painter.drawLine(cx, cy, x, y)

    def _draw_targets(self, painter, cx, cy):
        """Draw all targets with state icons"""
        r = self.radar_radius

        for target in self.targets:
            # Calculate position
            angle_rad = math.radians(target['angle'] - 90)
            dist_ratio = target['distance'] / self.max_distance
            tx = cx + int(r * dist_ratio * math.cos(angle_rad))
            ty = cy + int(r * dist_ratio * math.sin(angle_rad))

            # Get state color
            state_color = TargetState.COLORS.get(target['state'], self.COLOR_TEXT)

            # Draw target based on state
            if target['state'] == TargetState.WALK:
                self._draw_walk_icon(painter, tx, ty, state_color)
            elif target['state'] == TargetState.RUN:
                self._draw_run_icon(painter, tx, ty, state_color)
            elif target['state'] == TargetState.SHOT:
                self._draw_shot_icon(painter, tx, ty, state_color)
            else:
                # Unknown - simple dot
                painter.setBrush(QBrush(state_color))
                painter.setPen(QPen(state_color.lighter(150), 2))
                painter.drawEllipse(tx - 6, ty - 6, 12, 12)

            # Draw state label
            label = TargetState.LABELS.get(target['state'], "???")
            painter.setFont(self.FONT_LABEL)
            painter.setPen(state_color)
            painter.drawText(tx + 12, ty + 4, label)

            # Draw target ID/label if exists
            if target['label']:
                painter.drawText(tx + 12, ty + 16, target['label'])

    def _draw_walk_icon(self, painter, x, y, color):
        """Draw walking person silhouette"""
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)

        # Head
        painter.drawEllipse(x - 3, y - 12, 6, 6)

        # Body
        painter.drawLine(x, y - 6, x, y + 2)

        # Arms (one forward, one back)
        painter.drawLine(x, y - 4, x - 5, y - 1)
        painter.drawLine(x, y - 4, x + 4, y - 6)

        # Legs (walking stance)
        painter.drawLine(x, y + 2, x - 4, y + 10)
        painter.drawLine(x, y + 2, x + 4, y + 10)

        # Glow effect
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 50), 6))
        painter.drawEllipse(x - 8, y - 14, 16, 26)

    def _draw_run_icon(self, painter, x, y, color):
        """Draw running person silhouette"""
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)

        # Head (leaning forward)
        painter.drawEllipse(x + 2, y - 12, 6, 6)

        # Body (angled forward)
        painter.drawLine(x + 5, y - 6, x - 2, y + 2)

        # Arms (dynamic running pose)
        painter.drawLine(x + 1, y - 3, x - 6, y - 8)
        painter.drawLine(x + 1, y - 3, x + 8, y)

        # Legs (wide running stride)
        painter.drawLine(x - 2, y + 2, x - 8, y + 10)
        painter.drawLine(x - 2, y + 2, x + 6, y + 8)

        # Speed lines
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 100), 1))
        painter.drawLine(x - 10, y - 2, x - 15, y - 2)
        painter.drawLine(x - 10, y + 2, x - 14, y + 2)
        painter.drawLine(x - 10, y + 6, x - 13, y + 6)

        # Glow effect
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 50), 6))
        painter.drawEllipse(x - 10, y - 14, 20, 26)

    def _draw_shot_icon(self, painter, x, y, color):
        """Draw bullet/shot icon"""
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))

        # Bullet shape (pointed oval)
        path = QPainterPath()
        path.moveTo(x + 8, y)
        path.lineTo(x - 4, y - 4)
        path.lineTo(x - 6, y)
        path.lineTo(x - 4, y + 4)
        path.closeSubpath()
        painter.drawPath(path)

        # Muzzle flash lines
        painter.setPen(QPen(color.lighter(150), 1))
        painter.drawLine(x - 8, y, x - 14, y)
        painter.drawLine(x - 7, y - 3, x - 12, y - 5)
        painter.drawLine(x - 7, y + 3, x - 12, y + 5)

        # Impact ring effect
        painter.setPen(QPen(QColor(255, 100, 100, 80), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(x - 10, y - 10, 20, 20)

    def _draw_left_panel(self, painter, panel_width):
        """Draw left panel - Target list"""
        h = self.height() - 40
        x = 5
        y = 5

        # Panel background
        painter.fillRect(x, y, panel_width - 10, h - 10,
                        QColor(0, 15, 20, 200))
        painter.setPen(QPen(self.COLOR_GRID_MAJOR, 1))
        painter.drawRect(x, y, panel_width - 10, h - 10)

        # Title
        painter.setFont(self.FONT_TITLE)
        painter.setPen(self.COLOR_ACCENT)
        painter.drawText(x + 10, y + 20, tr('targets'))

        # Separator line
        painter.setPen(QPen(self.COLOR_GRID, 1))
        painter.drawLine(x + 5, y + 28, x + panel_width - 15, y + 28)

        # Target list
        painter.setFont(self.FONT_LABEL)
        ty = y + 45
        for i, target in enumerate(self.targets[:8]):  # Max 8 targets shown
            state_color = TargetState.COLORS.get(target['state'], self.COLOR_TEXT_DIM)
            state_label = TargetState.LABELS.get(target['state'], "???")

            # Status indicator
            painter.setBrush(QBrush(state_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(x + 10, ty - 4, 6, 6)

            # Target info
            painter.setPen(state_color)
            painter.drawText(x + 20, ty,
                           f"T{target['id']:02d} {target['distance']:.0f}m")
            painter.setPen(self.COLOR_TEXT_DIM)
            painter.drawText(x + 20, ty + 12,
                           f"{state_label} {target['speed']:.1f}m/s")

            ty += 32

        # Count
        painter.setFont(self.FONT_LABEL)
        painter.setPen(self.COLOR_TEXT_DIM)
        painter.drawText(x + 10, h - 20, f"{tr('count')}: {len(self.targets)}")

    def _draw_right_panel(self, painter, w, panel_width):
        """Draw right panel - Tactical data"""
        h = self.height() - 40
        x = w - panel_width + 5
        y = 5

        # Panel background
        painter.fillRect(x, y, panel_width - 10, h - 10,
                        QColor(0, 15, 20, 200))
        painter.setPen(QPen(self.COLOR_GRID_MAJOR, 1))
        painter.drawRect(x, y, panel_width - 10, h - 10)

        # Title
        painter.setFont(self.FONT_TITLE)
        painter.setPen(self.COLOR_ACCENT)
        painter.drawText(x + 10, y + 20, tr('tactical'))

        # Separator
        painter.setPen(QPen(self.COLOR_GRID, 1))
        painter.drawLine(x + 5, y + 28, x + panel_width - 15, y + 28)

        # System data
        painter.setFont(self.FONT_LABEL)
        ty = y + 50

        # Mode
        painter.setPen(self.COLOR_TEXT_DIM)
        painter.drawText(x + 10, ty, tr('mode_label'))
        painter.setPen(self.COLOR_ACCENT)
        painter.drawText(x + 55, ty, self.scan_mode)
        ty += 20

        # Range
        painter.setPen(self.COLOR_TEXT_DIM)
        painter.drawText(x + 10, ty, tr('range_label'))
        painter.setPen(self.COLOR_TEXT)
        painter.drawText(x + 55, ty, self.range_mode)
        ty += 20

        # Lock status
        painter.setPen(self.COLOR_TEXT_DIM)
        painter.drawText(x + 10, ty, tr('lock_label'))
        if "LOCK" in self.lock_status:
            painter.setPen(self.COLOR_DANGER)
        else:
            painter.setPen(self.COLOR_TEXT)
        painter.drawText(x + 55, ty, self.lock_status)
        ty += 30

        # Separator
        painter.setPen(QPen(self.COLOR_GRID, 1))
        painter.drawLine(x + 5, ty - 5, x + panel_width - 15, ty - 5)
        ty += 15

        # Statistics
        painter.setPen(self.COLOR_TEXT_DIM)
        painter.drawText(x + 10, ty, tr('statistics'))
        ty += 18

        walk_count = sum(1 for t in self.targets if t['state'] == TargetState.WALK)
        run_count = sum(1 for t in self.targets if t['state'] == TargetState.RUN)
        shot_count = sum(1 for t in self.targets if t['state'] == TargetState.SHOT)

        painter.setPen(TargetState.COLORS[TargetState.WALK])
        painter.drawText(x + 10, ty, f"{tr('walk')}: {walk_count}")
        ty += 16
        painter.setPen(TargetState.COLORS[TargetState.RUN])
        painter.drawText(x + 10, ty, f"{tr('run')}:  {run_count}")
        ty += 16
        painter.setPen(TargetState.COLORS[TargetState.SHOT])
        painter.drawText(x + 10, ty, f"{tr('shot')}: {shot_count}")

        # FPS counter at bottom
        current_time = time.time()
        if current_time - self.last_update_time > 0:
            self.fps = 1.0 / (current_time - self.last_update_time + 0.001)
        self.last_update_time = current_time

        painter.setPen(self.COLOR_TEXT_DIM)
        painter.drawText(x + 10, h - 20, f"FPS: {self.fps:.0f}")

    def _draw_status_bar(self, painter, w, h, bar_height):
        """Draw bottom status bar"""
        y = h - bar_height

        # Background
        painter.fillRect(0, y, w, bar_height, QColor(0, 20, 25, 230))
        painter.setPen(QPen(self.COLOR_GRID_MAJOR, 1))
        painter.drawLine(0, y, w, y)

        # Status items
        painter.setFont(self.FONT_STATUS)
        items = [
            (tr('scan'), self.scan_mode == "ACTIVE", 50),
            (tr('lock'), "LOCK" in self.lock_status, 150),
            (tr('range'), True, 250),
            (tr('audio'), True, 350),
            (tr('system'), True, 450),
        ]

        for label, active, x_pos in items:
            if active:
                # Active indicator box
                painter.fillRect(x_pos - 5, y + 8, 60, 24,
                               QColor(0, 60, 50, 150))
                painter.setPen(self.COLOR_ACCENT)
            else:
                painter.setPen(self.COLOR_TEXT_DIM)

            painter.drawText(x_pos, y + 26, label)

        # Timestamp
        painter.setPen(self.COLOR_TEXT_DIM)
        timestamp = time.strftime("%H:%M:%S")
        painter.drawText(w - 80, y + 26, timestamp)

    def _draw_corner_decorations(self, painter, w, h):
        """Draw sci-fi corner decorations"""
        painter.setPen(QPen(self.COLOR_GRID_MAJOR, 2))
        corner_size = 20

        # Top-left
        painter.drawLine(0, corner_size, 0, 0)
        painter.drawLine(0, 0, corner_size, 0)

        # Top-right
        painter.drawLine(w - corner_size, 0, w, 0)
        painter.drawLine(w, 0, w, corner_size)

        # Bottom-left
        painter.drawLine(0, h - corner_size, 0, h)
        painter.drawLine(0, h, corner_size, h)

        # Bottom-right
        painter.drawLine(w - corner_size, h, w, h)
        painter.drawLine(w, h - corner_size, w, h)


# =============================================================================
# MINIMAL RADAR WIDGET (RADAR ONLY - NO PANELS)
# =============================================================================

class MinimalRadarWidget(QWidget):
    """
    Minimal radar widget showing ONLY the radar display
    No TARGETS, TACTICAL, or other panels - just the radar circle

    FIXED v4.1.2: Created for clean detached window experience
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        log("MinimalRadarWidget.__init__", "INFO")

        self.setMinimumSize(400, 400)
        self.setStyleSheet("background-color: #030508;")

        # Colors
        self.COLOR_BG = QColor(3, 5, 8)
        self.COLOR_GRID = QColor(0, 60, 80, 80)
        self.COLOR_GRID_MAJOR = QColor(0, 100, 120, 120)
        self.COLOR_SWEEP = QColor(0, 255, 100, 150)
        self.COLOR_TEXT = QColor(0, 200, 150)
        self.COLOR_TEXT_DIM = QColor(0, 120, 100)
        self.COLOR_ACCENT = QColor(0, 255, 200)

        # Fonts
        self.FONT_MAIN = QFont("Consolas", 9)
        self.FONT_LABEL = QFont("Consolas", 8)
        self.FONT_STATUS = QFont("Consolas", 10, QFont.Bold)

        # Radar state
        self.sweep_angle = 0
        self.radar_radius = 180
        self.max_distance = 100  # meters

        # Targets
        self.targets = []

        # Animation timer
        self.sweep_timer = QTimer()
        self.sweep_timer.timeout.connect(self._update_sweep)
        self.sweep_timer.start(50)  # 20 FPS

    def _update_sweep(self):
        """Update sweep line animation"""
        self.sweep_angle = (self.sweep_angle + 3) % 360
        self.update()

    def update_sweep(self, angle_deg):
        """Update sweep angle from external source"""
        self.sweep_angle = angle_deg % 360
        self.update()

    def add_target(self, target_id, angle, distance, state=TargetState.UNKNOWN,
                   speed=0, label=""):
        """Add or update a target"""
        for t in self.targets:
            if t['id'] == target_id:
                t['angle'] = angle
                t['distance'] = min(distance, self.max_distance)
                t['state'] = state
                t['speed'] = speed
                t['label'] = label
                t['last_seen'] = time.time()
                return

        self.targets.append({
            'id': target_id,
            'angle': angle,
            'distance': min(distance, self.max_distance),
            'state': state,
            'speed': speed,
            'label': label,
            'last_seen': time.time()
        })

    def clear_targets(self):
        """Clear all targets"""
        self.targets = []

    def cleanup_stale_targets(self, max_age_seconds=3.0):
        """
        Remove targets that haven't been updated recently (FIXED v4.2.0)
        Defensive cleanup for stuck targets on minimal radar
        """
        current_time = time.time()
        before_count = len(self.targets)
        self.targets = [t for t in self.targets
                       if (current_time - t.get('last_seen', current_time)) < max_age_seconds]
        removed = before_count - len(self.targets)
        if removed > 0:
            from core.logger import log
            log(f"MinimalRadar: Cleaned {removed} stale targets (>{max_age_seconds}s old)", "DEBUG")

    def paintEvent(self, event):
        """Paint ONLY the radar - no side panels"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()
        h = self.height()

        # Calculate radar center and radius (full window, no side panels)
        self.radar_radius = min(w, h) // 2 - 40
        center_x = w // 2
        center_y = h // 2

        # Draw background
        painter.fillRect(0, 0, w, h, self.COLOR_BG)

        # Draw radar components
        self._draw_radar_grid(painter, center_x, center_y)
        self._draw_sweep_line(painter, center_x, center_y)
        self._draw_targets(painter, center_x, center_y)

    def _draw_radar_grid(self, painter, cx, cy):
        """Draw radar grid"""
        r = self.radar_radius

        # Background glow
        gradient = QRadialGradient(cx, cy, r)
        gradient.setColorAt(0, QColor(0, 30, 40, 60))
        gradient.setColorAt(0.7, QColor(0, 20, 30, 30))
        gradient.setColorAt(1, QColor(0, 10, 15, 10))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Concentric circles
        for i, ratio in enumerate([0.25, 0.5, 0.75, 1.0]):
            radius = int(r * ratio)
            if ratio == 1.0:
                painter.setPen(QPen(self.COLOR_GRID_MAJOR, 2))
            else:
                painter.setPen(QPen(self.COLOR_GRID, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

            # Distance labels
            dist_label = f"{int(self.max_distance * ratio)}m"
            painter.setFont(self.FONT_LABEL)
            painter.setPen(self.COLOR_TEXT_DIM)
            painter.drawText(cx + 5, cy - radius + 12, dist_label)

        # Radial lines (every 30 degrees)
        painter.setPen(QPen(self.COLOR_GRID, 1))
        for angle in range(0, 360, 30):
            rad = math.radians(angle - 90)
            x1 = cx + int(r * 0.1 * math.cos(rad))
            y1 = cy + int(r * 0.1 * math.sin(rad))
            x2 = cx + int(r * math.cos(rad))
            y2 = cy + int(r * math.sin(rad))
            painter.drawLine(x1, y1, x2, y2)

        # Cardinal direction labels
        painter.setFont(self.FONT_STATUS)
        painter.setPen(self.COLOR_TEXT)
        offset = r + 15
        painter.drawText(cx - 5, cy - offset, "N")
        painter.drawText(cx - 5, cy + offset + 10, "S")
        painter.drawText(cx + offset, cy + 5, "E")
        painter.drawText(cx - offset - 10, cy + 5, "W")

        # Cross-hair at center
        painter.setPen(QPen(self.COLOR_ACCENT, 1))
        ch_size = 10
        painter.drawLine(cx - ch_size, cy, cx + ch_size, cy)
        painter.drawLine(cx, cy - ch_size, cx, cy + ch_size)

    def _draw_sweep_line(self, painter, cx, cy):
        """Draw rotating sweep line"""
        r = self.radar_radius

        # Trail effect
        for i in range(30):
            trail_angle = self.sweep_angle - i * 2
            alpha = int(150 * (1 - i / 30))
            rad = math.radians(trail_angle - 90)
            x = cx + int(r * math.cos(rad))
            y = cy + int(r * math.sin(rad))
            painter.setPen(QPen(QColor(0, 255, 100, alpha), 1))
            painter.drawLine(cx, cy, x, y)

        # Main sweep line
        rad = math.radians(self.sweep_angle - 90)
        x = cx + int(r * math.cos(rad))
        y = cy + int(r * math.sin(rad))
        painter.setPen(QPen(self.COLOR_SWEEP, 2))
        painter.drawLine(cx, cy, x, y)

    def _draw_targets(self, painter, cx, cy):
        """Draw targets on radar"""
        r = self.radar_radius

        for target in self.targets:
            # Calculate position
            angle_rad = math.radians(target['angle'] - 90)
            dist_ratio = target['distance'] / self.max_distance
            tx = cx + int(r * dist_ratio * math.cos(angle_rad))
            ty = cy + int(r * dist_ratio * math.sin(angle_rad))

            # Get state color
            state_color = TargetState.COLORS.get(target['state'], self.COLOR_TEXT)

            # Draw target based on state
            if target['state'] == TargetState.WALK:
                self._draw_walk_icon(painter, tx, ty, state_color)
            elif target['state'] == TargetState.RUN:
                self._draw_run_icon(painter, tx, ty, state_color)
            elif target['state'] == TargetState.SHOT:
                self._draw_shot_icon(painter, tx, ty, state_color)
            else:
                # Unknown - simple dot
                painter.setBrush(QBrush(state_color))
                painter.setPen(QPen(state_color.lighter(150), 2))
                painter.drawEllipse(tx - 6, ty - 6, 12, 12)

            # Draw state label
            label = TargetState.LABELS.get(target['state'], "???")
            painter.setFont(self.FONT_LABEL)
            painter.setPen(state_color)
            painter.drawText(tx + 12, ty + 4, label)

            # Draw target ID
            if target['label']:
                painter.drawText(tx + 12, ty + 16, target['label'])

    def _draw_walk_icon(self, painter, x, y, color):
        """Draw walking person icon"""
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(x - 3, y - 12, 6, 6)  # Head
        painter.drawLine(x, y - 6, x, y + 2)  # Body
        painter.drawLine(x, y - 4, x - 5, y - 1)  # Arm
        painter.drawLine(x, y - 4, x + 4, y - 6)  # Arm
        painter.drawLine(x, y + 2, x - 4, y + 10)  # Leg
        painter.drawLine(x, y + 2, x + 4, y + 10)  # Leg
        # Glow
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 50), 6))
        painter.drawEllipse(x - 8, y - 14, 16, 26)

    def _draw_run_icon(self, painter, x, y, color):
        """Draw running person icon"""
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(x + 2, y - 12, 6, 6)  # Head
        painter.drawLine(x + 5, y - 6, x - 2, y + 2)  # Body
        painter.drawLine(x + 1, y - 3, x - 6, y - 8)  # Arm
        painter.drawLine(x + 1, y - 3, x + 8, y)  # Arm
        painter.drawLine(x - 2, y + 2, x - 7, y + 10)  # Leg
        painter.drawLine(x - 2, y + 2, x + 3, y + 10)  # Leg
        # Glow
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 50), 6))
        painter.drawEllipse(x - 9, y - 14, 18, 26)

    def _draw_shot_icon(self, painter, x, y, color):
        """Draw shot/explosion icon"""
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        # Star burst pattern
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = x + int(4 * math.cos(rad))
            y1 = y + int(4 * math.sin(rad))
            x2 = x + int(10 * math.cos(rad))
            y2 = y + int(10 * math.sin(rad))
            painter.drawLine(x1, y1, x2, y2)
        # Glow
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 80), 8))
        painter.drawEllipse(x - 10, y - 10, 20, 20)


# =============================================================================
# DETACHABLE RADAR WINDOW
# =============================================================================

class DetachableRadarWidget(QWidget):
    """
    Independent radar widget that can be detached from main window
    Works even when main window is minimized

    FIXED v4.1.2: Uses MinimalRadarWidget for clean radar-only display
    """

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint)
        log("DetachableRadarWidget.__init__", "INFO")

        self.setWindowTitle(f"{tr('radar')} - RadarSuite {VERSION}")
        self.setGeometry(100, 100, 600, 600)

        # Frameless mode
        self.is_frameless = False

        # Opacity
        self.window_opacity = 1.0
        self.setWindowOpacity(self.window_opacity)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # FIXED v4.1.2: Use MinimalRadarWidget instead of MilitaryHUDRadar
        # This provides ONLY the radar circle, no TARGETS/TACTICAL panels
        self.radar_widget = MinimalRadarWidget()
        layout.addWidget(self.radar_widget)

        self.setLayout(layout)

        # Dragging support for frameless mode
        self.dragging = False
        self.drag_position = QPoint()

    def set_opacity(self, opacity):
        """Set window opacity (0.0 - 1.0)"""
        self.window_opacity = max(0.0, min(1.0, opacity))
        self.setWindowOpacity(self.window_opacity)

    def set_frameless(self, frameless):
        """Toggle frameless window mode"""
        self.is_frameless = frameless

        if frameless:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        self.show()

    def mousePressEvent(self, event):
        """Handle mouse press for dragging in frameless mode"""
        if self.is_frameless and event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.is_frameless and self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self.is_frameless:
            self.dragging = False
            event.accept()


# =============================================================================
# LEGACY RADAR WIDGET (for compatibility)
# =============================================================================

class RadarWidget(pg.PlotWidget):
    """Legacy Radar visualization using pyqtgraph - kept for compatibility"""

    def __init__(self):
        super().__init__()

        self.setBackground("#050505")
        self.setAspectLocked(True)
        self.setXRange(-110, 110)
        self.setYRange(-110, 110)
        self.showGrid(x=True, y=True, alpha=0.25)
        self.setMouseEnabled(False, False)

        # Circles
        self.circles = []
        for radius in [25, 50, 75, 100]:
            circle = pg.QtWidgets.QGraphicsEllipseItem(-radius, -radius, radius * 2, radius * 2)
            circle.setPen(pg.mkPen(color=(0, 100, 200), width=1))
            self.addItem(circle)
            self.circles.append(circle)

        # Radial lines
        self.radials = []
        for angle_deg in range(0, 360, 45):
            angle_rad = math.radians(angle_deg)
            x = 100 * math.cos(angle_rad)
            y = 100 * math.sin(angle_rad)
            line = pg.PlotDataItem([0, x], [0, y], pen=pg.mkPen(color=(0, 100, 200), width=1))
            self.addItem(line)
            self.radials.append(line)

        # Distance labels
        self.distance_texts = []
        for radius in [25, 50, 75]:
            text = pg.TextItem(f"{radius}m", color=(100, 150, 255), anchor=(0.5, 0.5))
            text.setPos(0, radius)
            self.addItem(text)
            self.distance_texts.append(text)

        # Sweep line
        self.sweep_line = pg.PlotDataItem([0, 0], [0, 100], pen=pg.mkPen(color=(0, 255, 0), width=2))
        self.addItem(self.sweep_line)
        self.sweep_angle = 0

        # Target echo
        self.echo = pg.ScatterPlotItem(size=15, brush=pg.mkBrush(255, 0, 0, 200))
        self.addItem(self.echo)
        self.target_pos = None

    def update_sweep(self, angle_deg):
        """Update sweep line angle"""
        self.sweep_angle = angle_deg
        angle_rad = math.radians(angle_deg - 90)
        x = 100 * math.cos(angle_rad)
        y = 100 * math.sin(angle_rad)
        self.sweep_line.setData([0, x], [0, y])

    def update_target(self, angle_deg, distance):
        """Update target position"""
        if angle_deg is None or distance is None:
            self.echo.setData([], [])
            self.target_pos = None
            return

        distance = max(5, min(100, distance))

        angle_rad = math.radians(angle_deg - 90)
        x = distance * math.cos(angle_rad)
        y = distance * math.sin(angle_rad)

        self.echo.setData([x], [y])
        self.target_pos = (x, y)


# =============================================================================
# 3D SPHERE WALLHACK HUD RADAR (Military Sci-Fi Style)
# =============================================================================

class Military3DRadar(gl.GLViewWidget):
    """
    3D Sphere Wallhack HUD Radar - Military Sci-Fi Style

    Features:
    - Semi-transparent holographic sphere
    - Neon green/cyan color scheme
    - Walk/Run/Shot target markers with colored indicators
    - Lines connecting targets to sphere surface
    - X/Y/Z coordinate axes
    - Player icon at center
    - Wallhack-style visibility effect
    """

    def __init__(self):
        super().__init__()
        log("Military3DRadar.__init__", "INFO")

        # Dark background for contrast
        self.setBackgroundColor('#020508')
        self.setCameraPosition(distance=180, elevation=25, azimuth=45)

        # Enable mouse rotation
        self.setMouseTracking(True)

        # Settings
        self.max_distance = 100
        self.sweep_angle = 0

        # Colors (neon green/cyan theme)
        self.COLOR_SPHERE = (0, 0.8, 0.6, 0.08)
        self.COLOR_SPHERE_EDGE = (0, 1, 0.8, 0.25)
        self.COLOR_GRID = (0, 0.6, 0.5, 0.3)
        self.COLOR_AXIS_X = (1, 0.3, 0.3, 0.8)
        self.COLOR_AXIS_Y = (0.3, 1, 0.3, 0.8)
        self.COLOR_AXIS_Z = (0.3, 0.6, 1, 0.8)
        self.COLOR_SWEEP = (0, 1, 0.5, 0.6)
        self.COLOR_WALK = (0, 0.8, 0.4, 1)
        self.COLOR_RUN = (1, 0.8, 0, 1)
        self.COLOR_SHOT = (1, 0.2, 0.2, 1)
        self.COLOR_UNKNOWN = (0.5, 0.5, 0.5, 1)

        # Target data: list of {id, x, y, z, state, speed, distance}
        self.targets_data = []

        # Build the 3D scene
        self._build_holographic_sphere()
        self._build_coordinate_system()
        self._build_player_marker()
        self._build_sweep_plane()
        self._build_target_markers()

        # Auto-rotation timer
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self._auto_rotate)
        self.rotation_timer.start(50)

    def _build_holographic_sphere(self):
        """Build semi-transparent holographic sphere grid"""
        # Main sphere shells (distance rings)
        self.sphere_shells = []
        for radius in [25, 50, 75, 100]:
            # Create wireframe sphere
            md = gl.MeshData.sphere(rows=16, cols=24, radius=radius)
            sphere = gl.GLMeshItem(
                meshdata=md,
                color=self.COLOR_SPHERE,
                shader='balloon',
                drawEdges=True,
                edgeColor=self.COLOR_SPHERE_EDGE,
                smooth=False,
                glOptions='translucent'
            )
            self.addItem(sphere)
            self.sphere_shells.append(sphere)

        # Horizontal rings (latitude)
        self.h_rings = []
        for z in [-75, -50, -25, 0, 25, 50, 75]:
            # Calculate ring radius at this height
            if abs(z) < 100:
                ring_radius = math.sqrt(100**2 - z**2)
                theta = np.linspace(0, 2 * np.pi, 60)
                x = ring_radius * np.cos(theta)
                y = ring_radius * np.sin(theta)
                z_arr = np.full_like(theta, z)
                pts = np.vstack([x, y, z_arr]).T

                ring = gl.GLLinePlotItem(
                    pos=pts,
                    color=self.COLOR_GRID,
                    width=1.5 if z == 0 else 1,
                    antialias=True
                )
                self.addItem(ring)
                self.h_rings.append(ring)

        # Vertical rings (longitude)
        self.v_rings = []
        for angle in range(0, 180, 30):
            theta = np.linspace(0, 2 * np.pi, 60)
            x = 100 * np.cos(theta) * np.cos(np.radians(angle))
            y = 100 * np.cos(theta) * np.sin(np.radians(angle))
            z = 100 * np.sin(theta)
            pts = np.vstack([x, y, z]).T

            ring = gl.GLLinePlotItem(
                pos=pts,
                color=self.COLOR_GRID,
                width=1,
                antialias=True
            )
            self.addItem(ring)
            self.v_rings.append(ring)

    def _build_coordinate_system(self):
        """Build X/Y/Z axes with arrows"""
        axis_length = 115

        # X axis (Red) - Left/Right
        self.x_axis = gl.GLLinePlotItem(
            pos=np.array([[-axis_length, 0, 0], [axis_length, 0, 0]]),
            color=self.COLOR_AXIS_X,
            width=2,
            antialias=True
        )
        self.addItem(self.x_axis)

        # Y axis (Green) - Forward/Back
        self.y_axis = gl.GLLinePlotItem(
            pos=np.array([[0, -axis_length, 0], [0, axis_length, 0]]),
            color=self.COLOR_AXIS_Y,
            width=2,
            antialias=True
        )
        self.addItem(self.y_axis)

        # Z axis (Blue) - Up/Down
        self.z_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, -axis_length], [0, 0, axis_length]]),
            color=self.COLOR_AXIS_Z,
            width=2,
            antialias=True
        )
        self.addItem(self.z_axis)

        # Axis arrow heads
        arrow_size = 8
        for axis, direction, color in [
            ('x', [1, 0, 0], self.COLOR_AXIS_X),
            ('y', [0, 1, 0], self.COLOR_AXIS_Y),
            ('z', [0, 0, 1], self.COLOR_AXIS_Z)
        ]:
            pos = np.array(direction) * axis_length
            # Arrow cone
            md = gl.MeshData.cylinder(rows=4, cols=8, radius=[arrow_size/2, 0], length=arrow_size)
            arrow = gl.GLMeshItem(
                meshdata=md,
                color=color,
                shader='shaded',
                smooth=True
            )
            arrow.translate(*pos)
            # Rotate arrow to point along axis
            if axis == 'x':
                arrow.rotate(90, 0, 1, 0)
            elif axis == 'y':
                arrow.rotate(-90, 1, 0, 0)
            # z axis already points up
            self.addItem(arrow)

    def _build_player_marker(self):
        """Build player position marker at center"""
        # Player dot
        self.player_marker = gl.GLScatterPlotItem(
            pos=np.array([[0, 0, 0]]),
            color=(0, 1, 1, 1),
            size=15,
            pxMode=True
        )
        self.addItem(self.player_marker)

        # Player direction indicator (small forward arrow)
        self.player_direction = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 15, 0]]),
            color=(0, 1, 1, 0.8),
            width=3,
            antialias=True
        )
        self.addItem(self.player_direction)

        # Crosshair at player position
        ch_size = 12
        crosshair_pts = np.array([
            [-ch_size, 0, 0], [ch_size, 0, 0],
            [0, -ch_size, 0], [0, ch_size, 0],
            [0, 0, -ch_size], [0, 0, ch_size]
        ])
        self.crosshair = gl.GLLinePlotItem(
            pos=crosshair_pts.reshape(-1, 3),
            color=(0, 1, 1, 0.5),
            width=1,
            antialias=True,
            mode='lines'
        )
        self.addItem(self.crosshair)

    def _build_sweep_plane(self):
        """Build rotating sweep plane"""
        # Sweep line on XY plane
        self.sweep_line = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 100, 0]]),
            color=self.COLOR_SWEEP,
            width=2,
            antialias=True
        )
        self.addItem(self.sweep_line)

        # Sweep arc (fading trail effect simulated with multiple lines)
        self.sweep_trail = []
        for i in range(15):
            alpha = 0.4 * (1 - i / 15)
            trail = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, 100, 0]]),
                color=(0, 1, 0.5, alpha),
                width=1,
                antialias=True
            )
            self.addItem(trail)
            self.sweep_trail.append(trail)

    def _build_target_markers(self):
        """Build target scatter plot and connection lines"""
        # Main target scatter
        self.target_scatter = gl.GLScatterPlotItem(
            pos=np.array([[0, 0, 0]]),
            color=(1, 0, 0, 0),
            size=18,
            pxMode=True
        )
        self.addItem(self.target_scatter)

        # Target glow (larger, semi-transparent)
        self.target_glow = gl.GLScatterPlotItem(
            pos=np.array([[0, 0, 0]]),
            color=(1, 0, 0, 0),
            size=30,
            pxMode=True
        )
        self.addItem(self.target_glow)

        # Connection lines from targets to sphere surface
        self.target_lines = []
        for _ in range(20):  # Max 20 targets
            line = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, 0, 0]]),
                color=(0, 1, 0.5, 0),
                width=1,
                antialias=True
            )
            self.addItem(line)
            self.target_lines.append(line)

        # Vertical drop lines (from target to XY plane)
        self.target_drops = []
        for _ in range(20):
            drop = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, 0, 0]]),
                color=(0, 0.5, 1, 0),
                width=1,
                antialias=True,
                mode='line_strip'
            )
            self.addItem(drop)
            self.target_drops.append(drop)

    def _auto_rotate(self):
        """Auto-rotate sweep and update display"""
        self.sweep_angle = (self.sweep_angle + 2) % 360
        self._update_sweep_visual()

    def _update_sweep_visual(self):
        """Update sweep line and trail"""
        angle_rad = math.radians(self.sweep_angle - 90)
        x = 100 * math.cos(angle_rad)
        y = 100 * math.sin(angle_rad)

        # Main sweep line
        self.sweep_line.setData(pos=np.array([[0, 0, 0], [x, y, 0]]))

        # Trail lines
        for i, trail in enumerate(self.sweep_trail):
            trail_angle = self.sweep_angle - (i + 1) * 4
            trail_rad = math.radians(trail_angle - 90)
            tx = 100 * math.cos(trail_rad)
            ty = 100 * math.sin(trail_rad)
            trail.setData(pos=np.array([[0, 0, 0], [tx, ty, 0]]))

    # =========================================================================
    # TARGET MANAGEMENT
    # =========================================================================

    def add_target(self, target_id, angle, distance, elevation=0,
                   state=TargetState.UNKNOWN, speed=0):
        """Add or update target in 3D space"""
        # Calculate 3D position
        angle_rad = math.radians(angle - 90)
        elev_rad = math.radians(elevation)

        dist = min(distance, self.max_distance)
        horiz_dist = dist * math.cos(elev_rad)
        x = horiz_dist * math.cos(angle_rad)
        y = horiz_dist * math.sin(angle_rad)
        z = dist * math.sin(elev_rad)

        # Check if target exists
        for t in self.targets_data:
            if t['id'] == target_id:
                t.update({
                    'x': x, 'y': y, 'z': z,
                    'angle': angle, 'distance': dist, 'elevation': elevation,
                    'state': state, 'speed': speed
                })
                self._update_target_visuals()
                return

        # Add new target
        self.targets_data.append({
            'id': target_id,
            'x': x, 'y': y, 'z': z,
            'angle': angle, 'distance': dist, 'elevation': elevation,
            'state': state, 'speed': speed
        })
        self._update_target_visuals()

    def remove_target(self, target_id):
        """Remove target"""
        self.targets_data = [t for t in self.targets_data if t['id'] != target_id]
        self._update_target_visuals()

    def clear_targets(self):
        """Clear all targets"""
        self.targets_data = []
        self._update_target_visuals()

    def _update_target_visuals(self):
        """Update all target visual elements"""
        if not self.targets_data:
            # Hide all
            self.target_scatter.setData(
                pos=np.array([[0, 0, 0]]),
                color=(1, 0, 0, 0)
            )
            self.target_glow.setData(
                pos=np.array([[0, 0, 0]]),
                color=(1, 0, 0, 0)
            )
            for line in self.target_lines:
                line.setData(pos=np.array([[0, 0, 0], [0, 0, 0]]), color=(0, 0, 0, 0))
            for drop in self.target_drops:
                drop.setData(pos=np.array([[0, 0, 0], [0, 0, 0]]), color=(0, 0, 0, 0))
            return

        # Build position and color arrays
        positions = []
        colors = []
        glow_colors = []

        for t in self.targets_data:
            positions.append([t['x'], t['y'], t['z']])

            # Color based on state
            if t['state'] == TargetState.WALK:
                color = self.COLOR_WALK
            elif t['state'] == TargetState.RUN:
                color = self.COLOR_RUN
            elif t['state'] == TargetState.SHOT:
                color = self.COLOR_SHOT
            else:
                color = self.COLOR_UNKNOWN

            colors.append(color)
            glow_colors.append((color[0], color[1], color[2], 0.3))

        positions = np.array(positions)
        colors = np.array(colors)
        glow_colors = np.array(glow_colors)

        # Update scatter plots
        self.target_scatter.setData(pos=positions, color=colors, size=18)
        self.target_glow.setData(pos=positions, color=glow_colors, size=35)

        # Update connection lines to sphere surface
        for i, t in enumerate(self.targets_data[:20]):
            if i < len(self.target_lines):
                # Line from target to sphere surface (radial)
                dist = math.sqrt(t['x']**2 + t['y']**2 + t['z']**2)
                if dist > 0:
                    scale = 100 / dist
                    surf_x = t['x'] * scale
                    surf_y = t['y'] * scale
                    surf_z = t['z'] * scale
                else:
                    surf_x, surf_y, surf_z = 0, 0, 100

                state_color = colors[i] if i < len(colors) else self.COLOR_UNKNOWN
                line_color = (state_color[0], state_color[1], state_color[2], 0.4)

                self.target_lines[i].setData(
                    pos=np.array([[t['x'], t['y'], t['z']], [surf_x, surf_y, surf_z]]),
                    color=line_color
                )

                # Vertical drop line to XY plane
                drop_color = (0, 0.6, 1, 0.3)
                self.target_drops[i].setData(
                    pos=np.array([[t['x'], t['y'], t['z']], [t['x'], t['y'], 0]]),
                    color=drop_color
                )

        # Hide unused lines
        for i in range(len(self.targets_data), 20):
            if i < len(self.target_lines):
                self.target_lines[i].setData(
                    pos=np.array([[0, 0, 0], [0, 0, 0]]),
                    color=(0, 0, 0, 0)
                )
            if i < len(self.target_drops):
                self.target_drops[i].setData(
                    pos=np.array([[0, 0, 0], [0, 0, 0]]),
                    color=(0, 0, 0, 0)
                )

    # Legacy compatibility methods
    def update_sweep(self, angle_deg):
        """Update sweep angle (legacy compatibility)"""
        self.sweep_angle = angle_deg
        self._update_sweep_visual()

    def update_target(self, angle_deg, distance, elevation_deg=0):
        """Update single target (legacy compatibility)"""
        if angle_deg is None or distance is None:
            self.clear_targets()
            return

        self.add_target(
            target_id=0,
            angle=angle_deg,
            distance=distance,
            elevation=elevation_deg,
            state=TargetState.UNKNOWN
        )


# =============================================================================
# LEGACY 3D RADAR (kept for compatibility)
# =============================================================================

class Radar3DWidget(gl.GLViewWidget):
    """
    Legacy 3D Sphere Radar - kept for compatibility
    Use Military3DRadar for new implementations
    """

    def __init__(self):
        super().__init__()
        log("Radar3DWidget.__init__ (legacy)", "INFO")

        self.setBackgroundColor('#050505')
        self.setCameraPosition(distance=150, elevation=20, azimuth=45)

        # Create sphere grid
        self.sphere_items = []
        for radius in [25, 50, 75, 100]:
            md = gl.MeshData.sphere(rows=20, cols=20, radius=radius)
            sphere = gl.GLMeshItem(
                meshdata=md,
                color=(0, 0.4, 0.8, 0.15),
                shader='balloon',
                drawEdges=True,
                edgeColor=(0, 0.4, 0.8, 0.3),
                smooth=False
            )
            self.addItem(sphere)
            self.sphere_items.append(sphere)

        # Coordinate axes
        axis_length = 110
        axis_width = 2

        x_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [axis_length, 0, 0]]),
            color=(1, 0, 0, 0.8), width=axis_width, antialias=True
        )
        self.addItem(x_axis)

        y_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, axis_length, 0]]),
            color=(0, 1, 0, 0.8), width=axis_width, antialias=True
        )
        self.addItem(y_axis)

        z_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 0, axis_length]]),
            color=(0, 0, 1, 0.8), width=axis_width, antialias=True
        )
        self.addItem(z_axis)

        # Grid
        grid = gl.GLGridItem()
        grid.scale(10, 10, 1)
        grid.setColor((0.3, 0.3, 0.3, 0.5))
        self.addItem(grid)

        # Target scatter
        self.targets = []
        self.target_scatter = gl.GLScatterPlotItem(
            pos=np.array([[0, 0, 0]]),
            color=(1, 0, 0, 0), size=12, pxMode=True
        )
        self.addItem(self.target_scatter)

        # Sweep line
        self.sweep_line_3d = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 100, 0]]),
            color=(0, 1, 0, 0.6), width=2, antialias=True
        )
        self.addItem(self.sweep_line_3d)
        self.sweep_angle = 0

    def update_sweep(self, angle_deg):
        """Update 3D sweep line angle"""
        self.sweep_angle = angle_deg
        angle_rad = math.radians(angle_deg - 90)
        x = 100 * math.cos(angle_rad)
        y = 100 * math.sin(angle_rad)
        self.sweep_line_3d.setData(
            pos=np.array([[0, 0, 0], [x, y, 0]]),
            color=(0, 1, 0, 0.6), width=2
        )

    def update_target(self, angle_deg, distance, elevation_deg=0):
        """Update target position in 3D space"""
        if angle_deg is None or distance is None:
            self.target_scatter.setData(
                pos=np.array([[0, 0, 0]]),
                color=(1, 0, 0, 0)
            )
            self.targets = []
            return

        distance = max(5, min(100, distance))
        elevation_deg = max(-90, min(90, elevation_deg))

        angle_rad = math.radians(angle_deg - 90)
        elevation_rad = math.radians(elevation_deg)

        horizontal_distance = distance * math.cos(elevation_rad)
        x = horizontal_distance * math.cos(angle_rad)
        y = horizontal_distance * math.sin(angle_rad)
        z = distance * math.sin(elevation_rad)

        self.targets = [(x, y, z)]

        if elevation_deg > 15:
            color = (1, 0.5, 0, 1)
        elif elevation_deg < -15:
            color = (0.5, 0, 1, 1)
        else:
            color = (1, 0, 0, 1)

        self.target_scatter.setData(
            pos=np.array([[x, y, z]]),
            color=color, size=12
        )

    def clear_targets(self):
        """Clear all targets"""
        self.targets = []
        self.target_scatter.setData(
            pos=np.array([[0, 0, 0]]),
            color=(1, 0, 0, 0)
        )
