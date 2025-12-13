"""
RadarSuite v4.2.1 - Waveform Timeline Widget
Interactive audio waveform visualization with zoom/scroll and segment selection

ADDED v4.2.1: ZADANIE 4 - Timeline editor for ML training
- Waveform visualization with zoom/scroll
- Segment selection (start/end timestamps)
- Label markers overlay
- Playback position indicator
"""

import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QScrollBar, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QLinearGradient,
    QPainterPath, QMouseEvent, QWheelEvent
)

# FIXED v4.2.1-k0003: Corrected imports to use absolute paths
# These rely on main.py adding app/ to sys.path
from app.core.logger import log
try:
    from app.core.translations import tr
except ImportError:
    def tr(x): return x


class WaveformDisplay(QWidget):
    """
    Custom widget that renders audio waveform with interactive features.

    Features:
    - Waveform rendering with RMS envelope
    - Zoom in/out support
    - Selection of time segments
    - Label markers display
    - Current playback position indicator
    """

    # Signals
    selection_changed = pyqtSignal(float, float)  # start_sec, end_sec
    position_clicked = pyqtSignal(float)  # timestamp in seconds

    # Colors
    COLOR_BACKGROUND = QColor(20, 20, 25)
    COLOR_WAVEFORM = QColor(0, 180, 220, 180)
    COLOR_WAVEFORM_PEAK = QColor(0, 220, 255, 220)
    COLOR_SELECTION = QColor(255, 200, 0, 60)
    COLOR_SELECTION_BORDER = QColor(255, 200, 0, 200)
    COLOR_PLAYHEAD = QColor(255, 80, 80)
    COLOR_GRID = QColor(60, 60, 70)
    COLOR_LABEL_MARKER = QColor(0, 255, 100, 200)
    COLOR_TEXT = QColor(180, 180, 180)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setMinimumWidth(400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

        # Audio data
        self._audio_data = None  # Full audio buffer
        self._sample_rate = 48000
        self._duration_sec = 0.0

        # View state
        self._view_start_sec = 0.0  # Start of visible region
        self._view_duration_sec = 10.0  # Duration of visible region
        self._zoom_level = 1.0  # 1.0 = 10 seconds visible

        # Selection state
        self._selection_start_sec = None
        self._selection_end_sec = None
        self._is_selecting = False

        # Playback position
        self._playhead_sec = 0.0

        # Label markers (list of (timestamp_sec, label_class) tuples)
        self._markers = []

        # Mouse interaction
        self._mouse_pressed = False
        self._drag_start_x = 0

        # Precomputed waveform cache
        self._waveform_cache = None
        self._cache_view_params = None

    def set_audio_data(self, audio_data: np.ndarray, sample_rate: int):
        """
        Set audio data for visualization.

        Args:
            audio_data: Audio samples (mono or stereo)
            sample_rate: Sample rate in Hz
        """
        if audio_data is None or len(audio_data) == 0:
            self._audio_data = None
            self._duration_sec = 0.0
            self._waveform_cache = None
            self.update()
            return

        # Convert to mono if stereo
        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)

        self._audio_data = audio_data.flatten()
        self._sample_rate = sample_rate
        self._duration_sec = len(self._audio_data) / sample_rate

        # Reset view to show entire waveform
        self._view_start_sec = 0.0
        self._view_duration_sec = min(10.0, self._duration_sec)
        self._zoom_level = self._view_duration_sec / 10.0

        # Clear cache
        self._waveform_cache = None
        self._cache_view_params = None

        self.update()

    def set_markers(self, markers: list):
        """
        Set label markers to display.

        Args:
            markers: List of (timestamp_sec, label_class) tuples
        """
        self._markers = markers
        self.update()

    def set_playhead(self, timestamp_sec: float):
        """Set playback position indicator."""
        self._playhead_sec = timestamp_sec
        self.update()

    def get_selection(self):
        """Get current selection (start_sec, end_sec) or None."""
        if self._selection_start_sec is not None and self._selection_end_sec is not None:
            return (
                min(self._selection_start_sec, self._selection_end_sec),
                max(self._selection_start_sec, self._selection_end_sec)
            )
        return None

    def clear_selection(self):
        """Clear current selection."""
        self._selection_start_sec = None
        self._selection_end_sec = None
        self.update()

    def zoom_in(self):
        """Zoom in (show less time)."""
        if self._zoom_level > 0.1:
            center = self._view_start_sec + self._view_duration_sec / 2
            self._zoom_level = max(0.1, self._zoom_level * 0.7)
            self._view_duration_sec = 10.0 * self._zoom_level
            self._view_start_sec = max(0, center - self._view_duration_sec / 2)
            self._clamp_view()
            self._waveform_cache = None
            self.update()

    def zoom_out(self):
        """Zoom out (show more time)."""
        if self._duration_sec > 0:
            max_zoom = self._duration_sec / 10.0
            if self._zoom_level < max_zoom:
                center = self._view_start_sec + self._view_duration_sec / 2
                self._zoom_level = min(max_zoom, self._zoom_level * 1.4)
                self._view_duration_sec = 10.0 * self._zoom_level
                self._view_start_sec = max(0, center - self._view_duration_sec / 2)
                self._clamp_view()
                self._waveform_cache = None
                self.update()

    def scroll_to(self, position_ratio: float):
        """Scroll view to position (0.0 = start, 1.0 = end)."""
        if self._duration_sec > self._view_duration_sec:
            max_start = self._duration_sec - self._view_duration_sec
            self._view_start_sec = position_ratio * max_start
            self._clamp_view()
            self._waveform_cache = None
            self.update()

    def _clamp_view(self):
        """Ensure view stays within valid bounds."""
        if self._duration_sec > 0:
            self._view_start_sec = max(0, self._view_start_sec)
            if self._view_start_sec + self._view_duration_sec > self._duration_sec:
                self._view_start_sec = max(0, self._duration_sec - self._view_duration_sec)

    def _x_to_time(self, x: int) -> float:
        """Convert x pixel coordinate to time in seconds."""
        if self.width() == 0:
            return 0.0
        return self._view_start_sec + (x / self.width()) * self._view_duration_sec

    def _time_to_x(self, time_sec: float) -> int:
        """Convert time in seconds to x pixel coordinate."""
        if self._view_duration_sec == 0:
            return 0
        relative_time = time_sec - self._view_start_sec
        return int((relative_time / self._view_duration_sec) * self.width())

    def paintEvent(self, event):
        """Render the waveform display."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        center_y = h // 2

        # Background
        painter.fillRect(0, 0, w, h, self.COLOR_BACKGROUND)

        # Draw time grid
        self._draw_grid(painter, w, h)

        # Draw waveform
        if self._audio_data is not None and len(self._audio_data) > 0:
            self._draw_waveform(painter, w, h, center_y)

        # Draw selection highlight
        if self._selection_start_sec is not None and self._selection_end_sec is not None:
            self._draw_selection(painter, h)

        # Draw label markers
        self._draw_markers(painter, h)

        # Draw playhead
        self._draw_playhead(painter, h)

        # Draw time labels
        self._draw_time_labels(painter, w, h)

    def _draw_grid(self, painter: QPainter, w: int, h: int):
        """Draw time grid lines."""
        painter.setPen(QPen(self.COLOR_GRID, 1, Qt.DotLine))

        # Determine grid interval based on zoom level
        if self._view_duration_sec <= 2:
            interval = 0.1
        elif self._view_duration_sec <= 10:
            interval = 0.5
        elif self._view_duration_sec <= 30:
            interval = 1.0
        elif self._view_duration_sec <= 120:
            interval = 5.0
        else:
            interval = 10.0

        # Draw vertical grid lines
        t = (int(self._view_start_sec / interval) + 1) * interval
        while t < self._view_start_sec + self._view_duration_sec:
            x = self._time_to_x(t)
            painter.drawLine(x, 0, x, h)
            t += interval

        # Draw center line
        painter.setPen(QPen(self.COLOR_GRID, 1, Qt.SolidLine))
        painter.drawLine(0, h // 2, w, h // 2)

    def _draw_waveform(self, painter: QPainter, w: int, h: int, center_y: int):
        """Draw the audio waveform."""
        # Calculate sample range for visible region
        start_sample = int(self._view_start_sec * self._sample_rate)
        end_sample = int((self._view_start_sec + self._view_duration_sec) * self._sample_rate)

        start_sample = max(0, start_sample)
        end_sample = min(len(self._audio_data), end_sample)

        if end_sample <= start_sample:
            return

        visible_data = self._audio_data[start_sample:end_sample]

        # Downsample for rendering
        samples_per_pixel = max(1, len(visible_data) // w)

        if samples_per_pixel > 1:
            # Use min/max envelope for each pixel column
            num_columns = len(visible_data) // samples_per_pixel

            path_min = QPainterPath()
            path_max = QPainterPath()

            for i in range(num_columns):
                chunk = visible_data[i * samples_per_pixel:(i + 1) * samples_per_pixel]
                if len(chunk) > 0:
                    min_val = float(np.min(chunk))
                    max_val = float(np.max(chunk))

                    y_min = center_y + int(min_val * center_y * 0.9)
                    y_max = center_y + int(max_val * center_y * 0.9)

                    if i == 0:
                        path_min.moveTo(i, y_min)
                        path_max.moveTo(i, y_max)
                    else:
                        path_min.lineTo(i, y_min)
                        path_max.lineTo(i, y_max)

            # Draw filled waveform
            painter.setPen(QPen(self.COLOR_WAVEFORM, 1))
            painter.drawPath(path_min)
            painter.drawPath(path_max)

            # Fill between
            fill_path = QPainterPath(path_max)
            for i in range(num_columns - 1, -1, -1):
                if i < path_min.elementCount():
                    elem = path_min.elementAt(i)
                    fill_path.lineTo(elem.x, elem.y)

            painter.fillPath(fill_path, QBrush(self.COLOR_WAVEFORM))
        else:
            # Direct rendering for high zoom
            painter.setPen(QPen(self.COLOR_WAVEFORM_PEAK, 1))

            prev_y = center_y
            for i, sample in enumerate(visible_data):
                x = int(i * w / len(visible_data))
                y = center_y + int(float(sample) * center_y * 0.9)
                if i > 0:
                    painter.drawLine(x - 1, prev_y, x, y)
                prev_y = y

    def _draw_selection(self, painter: QPainter, h: int):
        """Draw selection highlight."""
        start = min(self._selection_start_sec, self._selection_end_sec)
        end = max(self._selection_start_sec, self._selection_end_sec)

        x1 = self._time_to_x(start)
        x2 = self._time_to_x(end)

        # Fill
        painter.fillRect(x1, 0, x2 - x1, h, QBrush(self.COLOR_SELECTION))

        # Border
        painter.setPen(QPen(self.COLOR_SELECTION_BORDER, 2))
        painter.drawLine(x1, 0, x1, h)
        painter.drawLine(x2, 0, x2, h)

    def _draw_markers(self, painter: QPainter, h: int):
        """Draw label markers."""
        painter.setFont(QFont("Consolas", 8))

        for timestamp_sec, label_class in self._markers:
            if self._view_start_sec <= timestamp_sec <= self._view_start_sec + self._view_duration_sec:
                x = self._time_to_x(timestamp_sec)

                # Marker line
                painter.setPen(QPen(self.COLOR_LABEL_MARKER, 2))
                painter.drawLine(x, 0, x, h)

                # Label text
                painter.setPen(self.COLOR_LABEL_MARKER)
                painter.drawText(x + 3, 12, label_class[:8])

    def _draw_playhead(self, painter: QPainter, h: int):
        """Draw playback position indicator."""
        if self._view_start_sec <= self._playhead_sec <= self._view_start_sec + self._view_duration_sec:
            x = self._time_to_x(self._playhead_sec)
            painter.setPen(QPen(self.COLOR_PLAYHEAD, 2))
            painter.drawLine(x, 0, x, h)

            # Triangle indicator at top
            painter.setBrush(QBrush(self.COLOR_PLAYHEAD))
            painter.drawPolygon([
                QPointF(x - 5, 0),
                QPointF(x + 5, 0),
                QPointF(x, 8)
            ])

    def _draw_time_labels(self, painter: QPainter, w: int, h: int):
        """Draw time labels at bottom."""
        painter.setPen(self.COLOR_TEXT)
        painter.setFont(QFont("Consolas", 9))

        # Start time
        painter.drawText(5, h - 5, f"{self._view_start_sec:.1f}s")

        # End time
        end_text = f"{self._view_start_sec + self._view_duration_sec:.1f}s"
        painter.drawText(w - 50, h - 5, end_text)

        # Center time
        center_time = self._view_start_sec + self._view_duration_sec / 2
        painter.drawText(w // 2 - 20, h - 5, f"{center_time:.1f}s")

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for selection."""
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = True
            self._is_selecting = True
            self._selection_start_sec = self._x_to_time(event.x())
            self._selection_end_sec = self._selection_start_sec
            self.update()
        elif event.button() == Qt.MiddleButton:
            # Start panning
            self._drag_start_x = event.x()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for selection."""
        if self._is_selecting:
            self._selection_end_sec = self._x_to_time(event.x())
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release for selection."""
        if event.button() == Qt.LeftButton and self._is_selecting:
            self._is_selecting = False
            self._mouse_pressed = False

            # Emit signal if selection is valid
            selection = self.get_selection()
            if selection and selection[1] - selection[0] > 0.01:
                self.selection_changed.emit(selection[0], selection[1])
            else:
                # Click without drag - emit position
                self.position_clicked.emit(self._x_to_time(event.x()))
                self.clear_selection()

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()


class WaveformTimelineWidget(QWidget):
    """
    Complete waveform timeline widget with controls.

    Features:
    - Waveform display with zoom/scroll
    - Zoom controls (+/-)
    - Horizontal scrollbar
    - Selection info display
    - Integration with ML Training panel
    """

    # Signals
    segment_selected = pyqtSignal(float, float)  # start_sec, end_sec
    timestamp_clicked = pyqtSignal(float)  # timestamp in seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        """Build the widget UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Title and controls row
        controls_row = QHBoxLayout()

        title = QLabel(tr('waveform_timeline') if callable(tr) else "Waveform Timeline")
        title.setStyleSheet("font-weight: bold; color: #00DDFF;")
        controls_row.addWidget(title)

        controls_row.addStretch()

        # Selection info
        self.selection_label = QLabel(tr('no_selection') if callable(tr) else "No selection")
        self.selection_label.setStyleSheet("color: #888888; font-family: monospace;")
        controls_row.addWidget(self.selection_label)

        controls_row.addStretch()

        # Zoom controls
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setFixedSize(28, 28)
        zoom_out_btn.setToolTip(tr('zoom_out') if callable(tr) else "Zoom Out")
        zoom_out_btn.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                color: #00DDFF;
                border: 1px solid #444;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #3a3a3a; }
        """)
        zoom_out_btn.clicked.connect(self._on_zoom_out)
        controls_row.addWidget(zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: #888888; min-width: 40px; text-align: center;")
        controls_row.addWidget(self.zoom_label)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(28, 28)
        zoom_in_btn.setToolTip(tr('zoom_in') if callable(tr) else "Zoom In")
        zoom_in_btn.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                color: #00DDFF;
                border: 1px solid #444;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #3a3a3a; }
        """)
        zoom_in_btn.clicked.connect(self._on_zoom_in)
        controls_row.addWidget(zoom_in_btn)

        layout.addLayout(controls_row)

        # Waveform display
        self.waveform = WaveformDisplay()
        self.waveform.selection_changed.connect(self._on_selection_changed)
        self.waveform.position_clicked.connect(self._on_position_clicked)
        layout.addWidget(self.waveform)

        # Horizontal scrollbar
        self.scrollbar = QScrollBar(Qt.Horizontal)
        self.scrollbar.setStyleSheet("""
            QScrollBar:horizontal {
                background: #1a1a1a;
                height: 12px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background: #444;
                min-width: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #555;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                width: 0;
            }
        """)
        self.scrollbar.valueChanged.connect(self._on_scroll)
        layout.addWidget(self.scrollbar)

        self.setLayout(layout)

    def set_audio_data(self, audio_data: np.ndarray, sample_rate: int):
        """Set audio data for visualization."""
        self.waveform.set_audio_data(audio_data, sample_rate)
        self._update_scrollbar()
        self._update_zoom_label()

    def set_markers(self, markers: list):
        """Set label markers."""
        self.waveform.set_markers(markers)

    def set_playhead(self, timestamp_sec: float):
        """Set playback position."""
        self.waveform.set_playhead(timestamp_sec)

    def get_selection(self):
        """Get current selection."""
        return self.waveform.get_selection()

    def clear_selection(self):
        """Clear selection."""
        self.waveform.clear_selection()
        self.selection_label.setText(tr('no_selection') if callable(tr) else "No selection")

    def _on_zoom_in(self):
        """Handle zoom in button."""
        self.waveform.zoom_in()
        self._update_scrollbar()
        self._update_zoom_label()

    def _on_zoom_out(self):
        """Handle zoom out button."""
        self.waveform.zoom_out()
        self._update_scrollbar()
        self._update_zoom_label()

    def _on_scroll(self, value: int):
        """Handle scrollbar movement."""
        if self.scrollbar.maximum() > 0:
            ratio = value / self.scrollbar.maximum()
            self.waveform.scroll_to(ratio)

    def _update_scrollbar(self):
        """Update scrollbar range based on zoom level."""
        if self.waveform._duration_sec > 0:
            visible_ratio = self.waveform._view_duration_sec / self.waveform._duration_sec
            if visible_ratio < 1.0:
                self.scrollbar.setEnabled(True)
                self.scrollbar.setMaximum(1000)
                self.scrollbar.setPageStep(int(visible_ratio * 1000))

                # Update scrollbar position
                if self.waveform._duration_sec > self.waveform._view_duration_sec:
                    pos_ratio = self.waveform._view_start_sec / (
                        self.waveform._duration_sec - self.waveform._view_duration_sec
                    )
                    self.scrollbar.setValue(int(pos_ratio * 1000))
            else:
                self.scrollbar.setEnabled(False)
                self.scrollbar.setMaximum(0)
        else:
            self.scrollbar.setEnabled(False)

    def _update_zoom_label(self):
        """Update zoom level display."""
        if self.waveform._duration_sec > 0:
            zoom_percent = int(100 / self.waveform._zoom_level)
            self.zoom_label.setText(f"{zoom_percent}%")
        else:
            self.zoom_label.setText("100%")

    def _on_selection_changed(self, start_sec: float, end_sec: float):
        """Handle selection change."""
        duration = end_sec - start_sec
        self.selection_label.setText(
            f"{start_sec:.2f}s - {end_sec:.2f}s ({duration:.2f}s)"
        )
        self.segment_selected.emit(start_sec, end_sec)

    def _on_position_clicked(self, timestamp_sec: float):
        """Handle position click."""
        self.timestamp_clicked.emit(timestamp_sec)
