"""Quick always-on-top recording overlay for ML Training.

Provides lightweight controls and a mini equalizer so users can capture
training samples while the main window is minimized.
"""
from __future__ import annotations

import typing
from typing import Optional
import copy

import numpy as np
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
    QComboBox,
    QCheckBox,
    QSizePolicy,
)

from app.core.logger import log
from app.core.translations import tr
from app.ml.training import RecordingController, RecordingState

if typing.TYPE_CHECKING:  # pragma: no cover
    from app.core.config import ConfigManager


class MiniEqualizerWidget(QWidget):
    """Simple bar-based audio visualizer for the overlay."""

    def __init__(self, bar_count: int = 12, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.bar_count = bar_count
        self._levels = np.zeros(self.bar_count)
        self._target_level = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def set_level(self, level: float) -> None:
        self._target_level = max(0.0, min(1.0, level))

    def _tick(self):
        # Exponential smoothing for each bar with slight variance
        decay = 0.15
        rise = 0.35
        jitter = np.linspace(0.8, 1.2, self.bar_count)
        for i in range(self.bar_count):
            target = self._target_level * jitter[i]
            if target > self._levels[i]:
                self._levels[i] = self._levels[i] + rise * (target - self._levels[i])
            else:
                self._levels[i] = max(0.0, self._levels[i] - decay * (self._levels[i] - target))
        self.update()

    def paintEvent(self, event):  # pragma: no cover - Qt paint
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = self.width()
        height = self.height()
        bar_width = max(4, width / (self.bar_count * 1.3))
        gap = bar_width * 0.3
        for i in range(self.bar_count):
            level = min(1.0, self._levels[i])
            bar_height = level * height
            x = i * (bar_width + gap)
            y = height - bar_height
            color = QColor(0, int(200 + 55 * level), int(120 + 80 * level))
            painter.fillRect(x, y, bar_width, bar_height, color)


class MLQuickRecordOverlay(QWidget):
    """Top-level always-on-top overlay for quick ML recording."""

    def __init__(
        self,
        controller: RecordingController,
        config_manager: Optional["ConfigManager"] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent, Qt.Tool | Qt.WindowStaysOnTopHint)
        self.controller = controller
        self.config_manager = config_manager

        self._drag_position: Optional[QPoint] = None
        self._frameless = True
        self._opacity = 1.0
        self._size_preset = "medium"
        self._config_data: dict = {}
        self._dirty = False
        self._state_loaded = False
        self._save_debounce = QTimer(self)
        self._save_debounce.setSingleShot(True)
        self._save_debounce.timeout.connect(self._persist_state)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_timer_label)
        self._timer.start(200)

        self._build_ui()
        self._apply_window_flags()
        self._load_state()

        self.controller.add_state_listener(self._on_state_change)
        self.controller.add_level_listener(self._on_level)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.setWindowTitle(tr("ml_overlay_title"))
        self.setMinimumSize(220, 160)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        self.title_label = QLabel(tr("ml_overlay_title"))
        header.addWidget(self.title_label)
        header.addStretch()
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedWidth(26)
        self.close_btn.clicked.connect(self.close)
        header.addWidget(self.close_btn)
        layout.addLayout(header)

        self.equalizer = MiniEqualizerWidget()
        self.equalizer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.equalizer)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton(tr("start"))
        self.stop_btn = QPushButton(tr("stop"))
        self.save_btn = QPushButton(tr("save"))
        self.new_btn = QPushButton(tr("new"))
        for btn in (self.start_btn, self.stop_btn, self.save_btn, self.new_btn):
            btn.setMinimumHeight(28)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.new_btn)
        layout.addLayout(btn_row)

        controls = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(int(self._opacity * 100))
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        controls.addWidget(QLabel(tr("opacity")))
        controls.addWidget(self.opacity_slider)
        layout.addLayout(controls)

        extras = QHBoxLayout()
        self.frameless_checkbox = QCheckBox(tr("frameless_mode"))
        self.frameless_checkbox.setChecked(True)
        self.frameless_checkbox.stateChanged.connect(self._toggle_frameless)
        extras.addWidget(self.frameless_checkbox)

        self.size_combo = QComboBox()
        self.size_combo.addItems([tr("size_small"), tr("size_medium"), tr("size_large")])
        self.size_combo.currentIndexChanged.connect(self._apply_size_preset)
        extras.addWidget(self.size_combo)

        layout.addLayout(extras)

        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.timer_label)

        self.setLayout(layout)

        self.start_btn.clicked.connect(self._start_recording)
        self.stop_btn.clicked.connect(self._stop_recording)
        self.save_btn.clicked.connect(self._save_session)
        self.new_btn.clicked.connect(self._new_session)

        self._update_buttons(self.controller.state)

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------
    def _load_state(self) -> None:
        if not self.config_manager or self._state_loaded:
            return
        loaded = self.config_manager.load()
        self._config_data = loaded if isinstance(loaded, dict) else {}
        overlay_cfg = self._config_data.get("ml_overlay", {})
        self._frameless = overlay_cfg.get("frameless", True)
        self._opacity = overlay_cfg.get("opacity", 1.0)
        self._size_preset = overlay_cfg.get("size_preset", "medium")

        self.opacity_slider.setValue(int(self._opacity * 100))
        self.frameless_checkbox.setChecked(self._frameless)
        preset_index = {"small": 0, "medium": 1, "large": 2}.get(self._size_preset, 1)
        self.size_combo.setCurrentIndex(preset_index)
        self._apply_window_flags()
        self._apply_size_preset(save_immediately=False)

        x = overlay_cfg.get("x")
        y = overlay_cfg.get("y")
        w = overlay_cfg.get("width")
        h = overlay_cfg.get("height")
        if all(v is not None for v in (x, y, w, h)):
            self.setGeometry(x, y, w, h)
        self.setWindowOpacity(self._opacity)

        if overlay_cfg.get("visible", False):
            self.show()
        self._state_loaded = True

    def _update_config(self) -> None:
        if not self.config_manager:
            return
        if not self._config_data:
            self._config_data = copy.deepcopy(self.config_manager.default_config)
        overlay_cfg = self._config_data.setdefault("ml_overlay", {})
        geo = self.geometry()
        overlay_cfg.update(
            {
                "x": geo.x(),
                "y": geo.y(),
                "width": geo.width(),
                "height": geo.height(),
                "opacity": self._opacity,
                "frameless": self._frameless,
                "size_preset": self._size_preset,
                "visible": self.isVisible(),
            }
        )
        self._dirty = True
        # Debounce disk writes to avoid log spam and UI stalls
        self._save_debounce.start(750)

    def _persist_state(self) -> None:
        if not self.config_manager or not self._dirty:
            return
        try:
            self.config_manager.save(self._config_data)
            self._dirty = False
        except Exception as exc:  # pragma: no cover - disk IO
            log(f"Overlay state persist failed: {exc}", "WARNING")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _apply_window_flags(self) -> None:
        flags = Qt.Tool | Qt.WindowStaysOnTopHint
        if self._frameless:
            flags |= Qt.FramelessWindowHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, self._frameless)
        self.show()

    def _on_state_change(self, state: RecordingState) -> None:
        self._update_buttons(state)

    def _on_level(self, level: float) -> None:
        self.equalizer.set_level(level)

    def _start_recording(self):
        if not self.controller.start_recording():
            log("Overlay: unable to start recording", "WARNING")
        self._update_buttons(self.controller.state)

    def _stop_recording(self):
        self.controller.stop_recording()
        self._update_buttons(self.controller.state)

    def _save_session(self):
        if self.controller.last_session:
            log(f"Overlay: session already saved {self.controller.last_session.session_id}", "INFO")
        elif self.controller.state.is_recording:
            self.controller.stop_recording()
        else:
            log("Overlay: no session to save", "WARNING")
        self._update_buttons(self.controller.state)

    def _new_session(self):
        self.controller.discard_recording()
        self.equalizer.set_level(0.0)
        self.timer_label.setText("00:00")
        self._update_buttons(self.controller.state)

    def _on_opacity_changed(self, value: int):
        self._opacity = max(0.3, min(1.0, value / 100))
        self.setWindowOpacity(self._opacity)
        self._update_config()

    def _toggle_frameless(self, state: int):
        self._frameless = state == Qt.Checked
        self._apply_window_flags()
        self._update_config()

    def _apply_size_preset(self, save_immediately: bool = True):
        index = self.size_combo.currentIndex()
        presets = {0: (220, 160), 1: (300, 200), 2: (380, 240)}
        w, h = presets.get(index, presets[1])
        self._size_preset = ["small", "medium", "large"][index]
        self.resize(w, h)
        if save_immediately:
            self._update_config()

    def _update_timer_label(self):
        elapsed = int(self.controller.state.elapsed_sec)
        mins, secs = divmod(elapsed, 60)
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")

    def _update_buttons(self, state: RecordingState):
        self.start_btn.setEnabled(not state.is_recording)
        self.stop_btn.setEnabled(state.is_recording)
        self.save_btn.setEnabled(not state.is_recording and bool(self.controller.last_session))
        self.new_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Dragging support for frameless mode
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):  # pragma: no cover - GUI interaction
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):  # pragma: no cover - GUI interaction
        if self._drag_position and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            self._update_config()
            event.accept()

    def mouseReleaseEvent(self, event):  # pragma: no cover - GUI interaction
        self._drag_position = None

    def resizeEvent(self, event):  # pragma: no cover
        super().resizeEvent(event)
        self._update_config()

    def closeEvent(self, event):  # pragma: no cover
        self._update_config()
        self._persist_state()
        super().closeEvent(event)
