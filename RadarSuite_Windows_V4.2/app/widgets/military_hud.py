"""
RadarSuite v4.2.1-k0006 - MilitaryHUDRadar

FIXED v4.2.1-k0006: Extracted from radar.py for improved modularity
Split radar.py (1674 lines) into focused, single-responsibility modules
"""

from typing import Optional
import math
import time

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                         QRadialGradient, QPainterPath)

from core import log, tr
from .target_state import TargetState


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

