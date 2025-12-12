"""
RadarSuite v3.5.0 - Led Widgets
"""

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSlider, QCheckBox, QSpinBox, QGroupBox, QFormLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPalette

from core import log, tr, VERSION, TOAST_DURATION_MS, TOAST_MAX_COUNT


class DetachableLedWidget(QWidget):
    """
    Independent LED Edge Alert widget
    Works even when main window is minimized
    """

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint)
        log("DetachableLedWidget.__init__", "INFO")

        self.setWindowTitle(f"{tr('led_alert')} - RadarSuite {VERSION}")
        self.setGeometry(100, 600, 800, 150)

        # Frameless mode
        self.is_frameless = False

        # Opacity
        self.window_opacity = 1.0
        self.setWindowOpacity(self.window_opacity)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # LED overlay
        self.led_overlay = LedOverlayWidget()
        layout.addWidget(self.led_overlay)

        self.setLayout(layout)

        # Dragging support
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
        """Handle mouse press for dragging"""
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


# ============================================================================
# SPECTRUM WIDGET
# ============================================================================


class LedOverlayWidget(QWidget):
    """LED Edge Alert - colored bars on screen edges"""

    def __init__(self):
        super().__init__()
        log("LedOverlayWidget.__init__", "INFO")

        self.setMinimumHeight(100)

        self.bars = {
            'G1': {'color': QColor(0, 0, 0), 'intensity': 0.0},
            'G2': {'color': QColor(0, 0, 0), 'intensity': 0.0},
            'G3': {'color': QColor(0, 0, 0), 'intensity': 0.0},
            'D1': {'color': QColor(0, 0, 0), 'intensity': 0.0},
            'D2': {'color': QColor(0, 0, 0), 'intensity': 0.0},
            'D3': {'color': QColor(0, 0, 0), 'intensity': 0.0},
            'L1': {'color': QColor(0, 0, 0), 'intensity': 0.0},
            'L2': {'color': QColor(0, 0, 0), 'intensity': 0.0},
            'P1': {'color': QColor(0, 0, 0), 'intensity': 0.0},
            'P2': {'color': QColor(0, 0, 0), 'intensity': 0.0},
        }

        self.global_alpha = 0.8

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(50)

    def _tick(self):
        """Decay bar intensities"""
        for bar in self.bars.values():
            bar['intensity'] -= 0.08
            bar['intensity'] = max(0.0, bar['intensity'])

        self.update()

    def update_from_events(self, events, bands, energy, balance):
        """Update LED bars based on detection events"""
        walk = events.get('walk', False)
        run = events.get('run', False)
        shot = events.get('shot', False)

        walk_i = events.get('walk_int', 0.0)
        run_i = events.get('run_int', 0.0)
        shot_i = events.get('shot_int', 0.0)

        if balance < -0.2:
            side = 'left'
        elif balance > 0.2:
            side = 'right'
        else:
            side = 'center'

        if side == 'left':
            side_bars = ['L1', 'L2']
            flank_bars = ['G1', 'D1']
        elif side == 'right':
            side_bars = ['P1', 'P2']
            flank_bars = ['G3', 'D3']
        else:
            side_bars = ['G2', 'D2']
            flank_bars = ['G1', 'G3', 'D1', 'D3']

        if walk or run:
            strength = max(walk_i, run_i)
            color = self._walk_run_color(strength)

            for bar_name in side_bars + flank_bars:
                self.bars[bar_name]['color'] = color
                self.bars[bar_name]['intensity'] = min(1.0, self.bars[bar_name]['intensity'] + 0.3)

        if shot:
            shot_color = QColor(80, 160, 255)

            for bar_name in side_bars + flank_bars:
                self.bars[bar_name]['color'] = shot_color
                self.bars[bar_name]['intensity'] = min(1.0, self.bars[bar_name]['intensity'] + 0.5)

    def _walk_run_color(self, strength):
        """Generate color gradient for walk/run"""
        if strength < 0.5:
            r = int(255 * (strength * 2))
            g = 255
            b = 0
        else:
            r = 255
            g = int(255 * (1.0 - (strength - 0.5) * 2))
            b = 0

        return QColor(r, g, b)

    def paintEvent(self, event):
        """Draw LED bars"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        bar_thickness = 20

        # Top bars
        self._draw_bar(painter, 0, 0, width // 3, bar_thickness, self.bars['G1'])
        self._draw_bar(painter, width // 3, 0, width // 3, bar_thickness, self.bars['G2'])
        self._draw_bar(painter, 2 * width // 3, 0, width // 3, bar_thickness, self.bars['G3'])

        # Bottom bars
        self._draw_bar(painter, 0, height - bar_thickness, width // 3, bar_thickness, self.bars['D1'])
        self._draw_bar(painter, width // 3, height - bar_thickness, width // 3, bar_thickness, self.bars['D2'])
        self._draw_bar(painter, 2 * width // 3, height - bar_thickness, width // 3, bar_thickness, self.bars['D3'])

        # Left bars
        mid_height = (height - 2 * bar_thickness) // 2
        self._draw_bar(painter, 0, bar_thickness, bar_thickness, mid_height, self.bars['L1'])
        self._draw_bar(painter, 0, bar_thickness + mid_height, bar_thickness, mid_height, self.bars['L2'])

        # Right bars
        self._draw_bar(painter, width - bar_thickness, bar_thickness, bar_thickness, mid_height, self.bars['P1'])
        self._draw_bar(painter, width - bar_thickness, bar_thickness + mid_height, bar_thickness, mid_height, self.bars['P2'])

    def _draw_bar(self, painter, x, y, w, h, bar_data):
        """Draw single LED bar"""
        if bar_data['intensity'] <= 0:
            return

        color = bar_data['color']
        alpha = int(255 * bar_data['intensity'] * self.global_alpha)
        color.setAlpha(alpha)

        painter.fillRect(x, y, w, h, color)


# ============================================================================
# MAIN WINDOW
# ============================================================================


