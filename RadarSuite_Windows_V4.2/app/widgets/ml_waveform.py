"""
RadarSuite v4.2.1 - ML Training Waveform Widget
Advanced waveform visualization with zoom, pan, labeling for ML training

Features:
- Zoom in/out with mouse wheel or buttons
- Pan/scroll with horizontal scrollbar
- Click to add label markers
- Drag to select time regions
- Playback position indicator
- Multi-track display (stereo channels)
"""

import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QScrollBar, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QColor

# FIXED v4.2.1-k0003: Corrected imports to use absolute paths
# These rely on main.py adding app/ to sys.path
try:
    from app.core.logger import log
except ImportError:
    def log(msg, level="INFO"):
        print(f"[{level}] {msg}")


class LabelMarker(pg.InfiniteLine):
    """
    Draggable vertical line representing a labeled event in audio.
    """

    # Signal emitted when marker is moved
    moved = pyqtSignal(object, float)  # (marker, new_time)
    clicked = pyqtSignal(object)  # (marker)

    def __init__(self, time, label_class, description="", color=(255, 200, 0)):
        """
        Initialize label marker.

        Args:
            time: Time position in seconds
            label_class: Label class name (e.g., "WALK", "RUN", "SHOT")
            description: Optional description
            color: RGB color tuple
        """
        super().__init__(
            pos=time,
            angle=90,
            movable=True,
            pen=pg.mkPen(color=color, width=2, style=Qt.DashLine)
        )
        self.time = time
        self.label_class = label_class
        self.description = description
        self.color = color

        # Text label
        self.label = pg.TextItem(
            text=label_class,
            color=color,
            anchor=(0.5, 1)
        )
        self.label.setPos(time, 0)

        # Connect position change signal
        self.sigPositionChanged.connect(self._on_position_changed)

    def _on_position_changed(self, line):
        """Handle marker drag."""
        new_time = line.value()
        self.time = new_time
        self.label.setPos(new_time, 0)
        self.moved.emit(self, new_time)

    def mouseClickEvent(self, ev):
        """Handle marker click."""
        if ev.button() == Qt.LeftButton:
            self.clicked.emit(self)
        super().mouseClickEvent(ev)


class SelectionRegion(pg.LinearRegionItem):
    """
    Draggable time region for marking audio segments.
    """

    # Signals
    region_changed = pyqtSignal(object, float, float)  # (region, start, end)

    def __init__(self, start_time, end_time, label_class="", color=(0, 255, 100, 50)):
        """
        Initialize selection region.

        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            label_class: Label class name
            color: RGBA color tuple (with alpha)
        """
        super().__init__(
            values=(start_time, end_time),
            movable=True,
            brush=pg.mkBrush(color)
        )
        self.label_class = label_class

        # Connect region change signal
        self.sigRegionChanged.connect(self._on_region_changed)

    def _on_region_changed(self, region):
        """Handle region drag/resize."""
        start, end = region.getRegion()
        self.region_changed.emit(self, start, end)


class MLWaveformWidget(QWidget):
    """
    Advanced waveform widget for ML training with zoom, pan, labeling.

    Signals:
        label_added(time, label_class)
        label_removed(marker)
        region_selected(start_time, end_time)
    """

    # Signals
    label_added = pyqtSignal(float, str)  # (time, label_class)
    label_removed = pyqtSignal(object)  # (marker)
    region_selected = pyqtSignal(float, float)  # (start, end)
    playback_position_changed = pyqtSignal(float)  # (time)

    def __init__(self, parent=None):
        super().__init__(parent)
        log("MLWaveformWidget.__init__", "INFO")

        # Data
        self.audio_data = None  # Full audio data (samples x channels)
        self.sample_rate = 48000
        self.duration = 0.0
        self.current_label_class = "FOOTSTEP"  # Default label class

        # Markers and regions
        self.markers = []  # List of LabelMarker objects
        self.regions = []  # List of SelectionRegion objects

        # Playback position
        self.playback_line = None

        # Zoom/Pan state
        self.zoom_level = 1.0  # 1.0 = show all, >1.0 = zoomed in
        self.view_start = 0.0  # Start time of current view (seconds)
        self.view_end = 10.0  # End time of current view (seconds)

        self._build_ui()

    def _build_ui(self):
        """Build the widget UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar with zoom controls
        toolbar = self._build_toolbar()
        layout.addLayout(toolbar)

        # Waveform plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#0a0a0a")
        self.plot_widget.setLabel('left', 'AMPLITUDE', color='#00DDFF', size='10pt')
        self.plot_widget.setLabel('bottom', 'TIME (seconds)', color='#00DDFF', size='10pt')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setYRange(-1.0, 1.0)
        self.plot_widget.setXRange(0, 10.0)

        # Waveform curves
        self.left_curve = self.plot_widget.plot(pen=pg.mkPen(color=(0, 221, 255), width=1))
        self.right_curve = self.plot_widget.plot(pen=pg.mkPen(color=(255, 150, 0), width=1))

        # Playback position indicator
        self.playback_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color=(255, 0, 0), width=2),
            movable=False
        )
        self.plot_widget.addItem(self.playback_line)

        # Enable mouse interaction for labeling
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_clicked)

        layout.addWidget(self.plot_widget)

        # Horizontal scrollbar for panning
        self.scrollbar = QScrollBar(Qt.Horizontal)
        self.scrollbar.setMinimum(0)
        self.scrollbar.setMaximum(1000)
        self.scrollbar.setValue(0)
        self.scrollbar.valueChanged.connect(self._on_scroll)
        layout.addWidget(self.scrollbar)

        self.setLayout(layout)

    def _build_toolbar(self) -> QHBoxLayout:
        """Build toolbar with zoom and label controls."""
        toolbar = QHBoxLayout()

        # Zoom controls
        self.zoom_in_btn = QPushButton("🔍 Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("🔍 Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar.addWidget(self.zoom_out_btn)

        self.zoom_reset_btn = QPushButton("↔️ Fit All")
        self.zoom_reset_btn.clicked.connect(self.zoom_reset)
        toolbar.addWidget(self.zoom_reset_btn)

        toolbar.addWidget(QLabel("|"))

        # Label controls
        toolbar.addWidget(QLabel("Label:"))
        self.label_display = QLabel(self.current_label_class)
        self.label_display.setStyleSheet(
            "background: #00aa00; color: white; padding: 5px; font-weight: bold; border-radius: 3px;"
        )
        toolbar.addWidget(self.label_display)

        self.clear_markers_btn = QPushButton("🗑️ Clear All")
        self.clear_markers_btn.clicked.connect(self.clear_all_markers)
        toolbar.addWidget(self.clear_markers_btn)

        toolbar.addStretch()

        # Info label
        self.info_label = QLabel("No audio loaded")
        self.info_label.setStyleSheet("color: #888;")
        toolbar.addWidget(self.info_label)

        return toolbar

    def load_audio(self, audio_data, sample_rate=48000):
        """
        Load audio data for visualization and labeling.

        Args:
            audio_data: NumPy array (samples x channels) or (samples,)
            sample_rate: Sample rate in Hz
        """
        log(f"MLWaveformWidget.load_audio: shape={audio_data.shape}, sr={sample_rate}", "INFO")

        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.duration = len(audio_data) / sample_rate

        # Reset view
        self.view_start = 0.0
        self.view_end = self.duration
        self.zoom_level = 1.0

        # Update scrollbar
        self.scrollbar.setEnabled(True)
        self.scrollbar.setValue(0)

        # Update display
        self._update_waveform_display()
        self.info_label.setText(f"Duration: {self.duration:.2f}s | SR: {sample_rate} Hz")

    def _update_waveform_display(self):
        """Update waveform display for current view range."""
        if self.audio_data is None:
            return

        # Calculate sample indices for current view
        start_sample = int(self.view_start * self.sample_rate)
        end_sample = int(self.view_end * self.sample_rate)
        start_sample = max(0, start_sample)
        end_sample = min(len(self.audio_data), end_sample)

        if start_sample >= end_sample:
            return

        # Extract view data
        view_data = self.audio_data[start_sample:end_sample]

        # Downsample for display if needed (max 10000 points for performance)
        max_points = 10000
        if len(view_data) > max_points:
            step = len(view_data) // max_points
            view_data = view_data[::step]
        else:
            step = 1

        # Time array for X axis
        time_array = np.arange(start_sample, start_sample + len(view_data) * step, step) / self.sample_rate

        # Handle stereo/mono
        if view_data.ndim == 2 and view_data.shape[1] >= 2:
            left = view_data[:, 0]
            right = view_data[:, 1]
            self.left_curve.setData(time_array[:len(left)], left)
            self.right_curve.setData(time_array[:len(right)], right)
        else:
            mono = view_data.ravel()
            self.left_curve.setData(time_array[:len(mono)], mono)
            self.right_curve.setData([], [])

        # Update plot range
        self.plot_widget.setXRange(self.view_start, self.view_end, padding=0)

    def zoom_in(self):
        """Zoom in (show less time, more detail)."""
        self.zoom_level *= 1.5
        self._apply_zoom()

    def zoom_out(self):
        """Zoom out (show more time, less detail)."""
        self.zoom_level /= 1.5
        if self.zoom_level < 1.0:
            self.zoom_level = 1.0
        self._apply_zoom()

    def zoom_reset(self):
        """Reset zoom to show entire waveform."""
        self.zoom_level = 1.0
        self.view_start = 0.0
        self.view_end = self.duration
        self._update_waveform_display()

    def _apply_zoom(self):
        """Apply current zoom level centered on current view."""
        if self.duration == 0:
            return

        # Calculate new view duration
        view_duration = self.duration / self.zoom_level

        # Keep view centered on current center
        view_center = (self.view_start + self.view_end) / 2.0
        self.view_start = view_center - view_duration / 2.0
        self.view_end = view_center + view_duration / 2.0

        # Clamp to valid range
        if self.view_start < 0:
            self.view_start = 0
            self.view_end = view_duration
        if self.view_end > self.duration:
            self.view_end = self.duration
            self.view_start = self.duration - view_duration

        self._update_waveform_display()

    def _on_scroll(self, value):
        """Handle scrollbar movement."""
        if self.duration == 0:
            return

        # Map scrollbar value (0-1000) to time position
        scroll_ratio = value / 1000.0
        view_duration = self.view_end - self.view_start

        self.view_start = scroll_ratio * (self.duration - view_duration)
        self.view_end = self.view_start + view_duration

        self._update_waveform_display()

    def _on_mouse_clicked(self, event):
        """Handle mouse click on plot for adding labels."""
        # Get click position in plot coordinates
        pos = event.scenePos()
        mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        click_time = mouse_point.x()

        # Only add marker if click is within audio duration
        if 0 <= click_time <= self.duration:
            self.add_label_marker(click_time, self.current_label_class)

    def add_label_marker(self, time, label_class, description=""):
        """
        Add a label marker at specified time.

        Args:
            time: Time position in seconds
            label_class: Label class name
            description: Optional description
        """
        # Choose color based on label class
        color_map = {
            "WALK": (0, 200, 255),
            "RUN": (255, 150, 0),
            "SHOT": (255, 0, 0),
            "FOOTSTEP": (0, 255, 100),
            "VOICE": (200, 0, 255),
            "EXPLOSION": (255, 255, 0),
        }
        color = color_map.get(label_class, (255, 200, 0))

        # Create marker
        marker = LabelMarker(time, label_class, description, color)
        marker.clicked.connect(self._on_marker_clicked)
        marker.moved.connect(self._on_marker_moved)

        # Add to plot and list
        self.plot_widget.addItem(marker)
        self.plot_widget.addItem(marker.label)
        self.markers.append(marker)

        # Emit signal
        self.label_added.emit(time, label_class)

        log(f"Added label: {label_class} at {time:.2f}s", "INFO")

    def _on_marker_clicked(self, marker):
        """Handle marker click (could open edit dialog)."""
        log(f"Marker clicked: {marker.label_class} at {marker.time:.2f}s", "INFO")

    def _on_marker_moved(self, marker, new_time):
        """Handle marker drag."""
        log(f"Marker moved: {marker.label_class} to {new_time:.2f}s", "INFO")

    def remove_marker(self, marker):
        """Remove a label marker."""
        if marker in self.markers:
            self.plot_widget.removeItem(marker)
            self.plot_widget.removeItem(marker.label)
            self.markers.remove(marker)
            self.label_removed.emit(marker)

    def clear_all_markers(self):
        """Clear all label markers."""
        for marker in self.markers[:]:  # Copy list to avoid modification during iteration
            self.remove_marker(marker)
        log("All markers cleared", "INFO")

    def set_current_label_class(self, label_class):
        """Set the label class for next marker."""
        self.current_label_class = label_class
        self.label_display.setText(label_class)

    def set_playback_position(self, time):
        """Update playback position indicator."""
        self.playback_line.setValue(time)
        self.playback_position_changed.emit(time)

    def get_all_labels(self):
        """
        Get all labels as a list of dicts.

        Returns:
            List of {time, label_class, description} dicts
        """
        return [
            {
                "time": marker.time,
                "label_class": marker.label_class,
                "description": marker.description
            }
            for marker in self.markers
        ]
