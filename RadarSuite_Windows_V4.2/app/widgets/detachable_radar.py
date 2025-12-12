"""
RadarSuite v4.2.1-k0006 - DetachableRadarWidget

FIXED v4.2.1-k0006: Extracted from radar.py for improved modularity
Split radar.py (1674 lines) into focused, single-responsibility modules
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from core import log
from .minimal_radar import MinimalRadarWidget
from .target_state import TargetState


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

