"""
RadarSuite V4.2.1 - Toast Widgets
"""

import time
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSlider, QCheckBox, QSpinBox, QGroupBox, QFormLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPalette

from core import log, tr, TOAST_DURATION_MS, TOAST_MAX_COUNT


class ToastNotification(QWidget):
    """
    Non-blocking toast notifications
    Appears in bottom-right corner with auto-fade
    Color-coded by message type (success/error/warning/info)

    ADDED v3.5.0: Toast notification system
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Toast queue and active toasts
        self.toast_queue = []
        self.active_toasts = []
        self.max_toasts = 3
        self.toast_height = 60
        self.toast_width = 350
        self.toast_margin = 10

        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_toasts)
        self.animation_timer.start(16)  # ~60 FPS

    def show_toast(self, message, toast_type='info', duration=3000):
        """
        Show toast notification

        Args:
            message: Text to display
            toast_type: 'success', 'error', 'warning', 'info'
            duration: Display duration in milliseconds (default 3000ms)
        """
        toast_data = {
            'message': message,
            'type': toast_type,
            'duration': duration,
            'created_time': time.time(),
            'opacity': 0.0,
            'y_offset': 0
        }

        self.toast_queue.append(toast_data)
        self._process_queue()

    def _process_queue(self):
        """Process toast queue and show pending toasts"""
        while len(self.active_toasts) < self.max_toasts and len(self.toast_queue) > 0:
            toast = self.toast_queue.pop(0)
            self.active_toasts.append(toast)

    def _update_toasts(self):
        """Update toast animations and remove expired toasts"""
        if not self.active_toasts:
            return

        current_time = time.time()
        toasts_to_remove = []

        for i, toast in enumerate(self.active_toasts):
            elapsed = (current_time - toast['created_time']) * 1000  # ms

            # Fade in (first 200ms)
            if elapsed < 200:
                toast['opacity'] = elapsed / 200.0
            # Full opacity (until duration - 500ms)
            elif elapsed < toast['duration'] - 500:
                toast['opacity'] = 1.0
            # Fade out (last 500ms)
            elif elapsed < toast['duration']:
                remaining = toast['duration'] - elapsed
                toast['opacity'] = remaining / 500.0
            # Expired
            else:
                toasts_to_remove.append(toast)

            # Target Y position based on index
            toast['y_offset'] = i * (self.toast_height + self.toast_margin)

        # Remove expired toasts
        for toast in toasts_to_remove:
            self.active_toasts.remove(toast)

        # Process queue if space available
        if toasts_to_remove:
            self._process_queue()

        # Trigger repaint
        self.update()

    def paintEvent(self, event):
        """Paint all active toasts"""
        if not self.active_toasts:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()
        base_x = screen.width() - self.toast_width - self.toast_margin
        base_y = screen.height() - self.toast_margin

        for toast in self.active_toasts:
            opacity = int(toast['opacity'] * 255)
            if opacity <= 0:
                continue

            # Position
            x = base_x
            y = base_y - self.toast_height - toast['y_offset']

            # Color based on type
            colors = {
                'success': QColor(46, 204, 113, opacity),  # Green
                'error': QColor(231, 76, 60, opacity),     # Red
                'warning': QColor(241, 196, 15, opacity),  # Yellow
                'info': QColor(52, 152, 219, opacity)      # Blue
            }
            bg_color = colors.get(toast['type'], colors['info'])

            # Draw background
            painter.setBrush(bg_color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, self.toast_width, self.toast_height, 8, 8)

            # Draw text
            text_color = QColor(255, 255, 255, opacity)
            painter.setPen(text_color)
            font = painter.font()
            font.setPixelSize(14)
            font.setBold(True)
            painter.setFont(font)

            text_rect = QRect(x + 15, y, self.toast_width - 30, self.toast_height)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, toast['message'])

    def get_stats(self):
        """Get toast notification statistics"""
        return {
            'active_toasts': len(self.active_toasts),
            'queued_toasts': len(self.toast_queue)
        }






