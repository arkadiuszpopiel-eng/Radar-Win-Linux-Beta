"""
RadarSuite v4.2.1-k0006 - MinimalRadarWidget

FIXED v4.2.1-k0006: Extracted from radar.py for improved modularity
Split radar.py (1674 lines) into focused, single-responsibility modules
"""

import math
import time

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                         QRadialGradient, QPainterPath)

from core import log
from .target_state import TargetState


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

