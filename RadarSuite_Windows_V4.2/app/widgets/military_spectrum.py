"""
RadarSuite v3.5.0 - Military Sci-Fi HUD Spectrum Panels
LIVE SPECTRUM / WATERFALL / WAVEFORM with Walk/Run/Shot indicators
"""

import math
import time
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                         QLinearGradient, QPainterPath, QPolygonF)

from core import log


# =============================================================================
# TARGET STATE (shared with radar)
# =============================================================================

class SignalState:
    """Signal classification states"""
    UNKNOWN = 0
    WALK = 1
    RUN = 2
    SHOT = 3

    LABELS = {
        UNKNOWN: "???",
        WALK: "WALK",
        RUN: "RUN",
        SHOT: "SHOT"
    }

    COLORS = {
        UNKNOWN: QColor(100, 100, 100),
        WALK: QColor(0, 200, 100),      # Green
        RUN: QColor(255, 200, 0),       # Yellow/Orange
        SHOT: QColor(255, 50, 50)       # Red
    }

    # Frequency ranges for classification (Hz)
    FREQ_RANGES = {
        WALK: (100, 400),    # Low frequency footsteps
        RUN: (300, 800),     # Higher frequency, faster impacts
        SHOT: (800, 4000)    # High frequency impulses
    }


# =============================================================================
# MILITARY LIVE SPECTRUM WIDGET
# =============================================================================

class MilitarySpectrumWidget(QWidget):
    """
    Ultra-readable military signal analysis interface - LIVE SPECTRUM

    Features:
    - Wide frequency spectrum display with neon bars
    - Thin grid overlay
    - Peak markers with frequency and dB labels
    - WALK/RUN/SHOT tags with icons
    - Live indicator with red dot
    - Side panels with bandwidth, peak, noise floor data
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        log("MilitarySpectrumWidget.__init__", "INFO")

        self.setMinimumSize(600, 300)
        self.setStyleSheet("background-color: #030508;")

        # Colors
        self.COLOR_BG = QColor(3, 5, 8)
        self.COLOR_GRID = QColor(0, 60, 80, 40)
        self.COLOR_GRID_MAJOR = QColor(0, 80, 100, 60)
        self.COLOR_SPECTRUM = QColor(0, 255, 150)
        self.COLOR_SPECTRUM_FILL = QColor(0, 255, 150, 40)
        self.COLOR_AVG = QColor(0, 180, 255)
        self.COLOR_TEXT = QColor(0, 200, 150)
        self.COLOR_TEXT_DIM = QColor(0, 120, 100)
        self.COLOR_ACCENT = QColor(0, 255, 200)
        self.COLOR_WALK = QColor(0, 200, 100)
        self.COLOR_RUN = QColor(255, 200, 0)
        self.COLOR_SHOT = QColor(255, 50, 50)

        # Fonts
        self.FONT_MAIN = QFont("Consolas", 9)
        self.FONT_LABEL = QFont("Consolas", 8)
        self.FONT_STATUS = QFont("Consolas", 10, QFont.Bold)
        self.FONT_TITLE = QFont("Consolas", 11, QFont.Bold)
        self.FONT_SMALL = QFont("Consolas", 7)

        # Spectrum data
        self.freqs = np.linspace(20, 10000, 512)
        self.spectrum_data = np.full(512, -80.0)
        self.avg_data = np.full(512, -80.0)
        self.avg_buffer = []
        self.avg_size = 30

        # Peak detection
        self.peaks = []  # List of {freq, db, state}
        self.peak_threshold = -60  # dB

        # Stats
        self.bandwidth = "20-10kHz"
        self.peak_freq = 0
        self.peak_db = -80
        self.noise_floor = -80

        # Animation
        self.live_blink = True
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._toggle_blink)
        self.blink_timer.start(500)

    def _toggle_blink(self):
        """Toggle live indicator"""
        self.live_blink = not self.live_blink
        self.update()

    def update_spectrum(self, freqs, power_db):
        """Update spectrum data"""
        try:
            if len(power_db) != len(self.spectrum_data):
                # Resample
                self.spectrum_data = np.interp(
                    np.linspace(0, len(power_db), len(self.spectrum_data)),
                    np.arange(len(power_db)),
                    power_db
                )
                self.freqs = np.linspace(freqs[0] if len(freqs) > 0 else 20,
                                         freqs[-1] if len(freqs) > 0 else 10000,
                                         len(self.spectrum_data))
            else:
                self.spectrum_data = power_db.copy()
                self.freqs = freqs.copy()

            # Update average
            self.avg_buffer.append(self.spectrum_data.copy())
            if len(self.avg_buffer) > self.avg_size:
                self.avg_buffer.pop(0)
            self.avg_data = np.mean(self.avg_buffer, axis=0)

            # Detect peaks and classify
            self._detect_peaks()

            # Update stats
            self.peak_db = np.max(self.spectrum_data)
            peak_idx = np.argmax(self.spectrum_data)
            self.peak_freq = self.freqs[peak_idx] if peak_idx < len(self.freqs) else 0
            self.noise_floor = np.percentile(self.spectrum_data, 10)

            self.update()
        except Exception as e:
            log(f"MilitarySpectrum update error: {e}", "ERROR")

    def update_from_cache(self, fft_result):
        """Update from cached FFT result"""
        try:
            freqs = fft_result['freqs']
            power_linear = fft_result['power']
            power_db = 20 * np.log10(power_linear + 1e-10)
            self.update_spectrum(freqs, power_db)
        except Exception as e:
            log(f"MilitarySpectrum cache update error: {e}", "ERROR")

    def _detect_peaks(self):
        """Detect and classify signal peaks"""
        self.peaks = []

        # Find local maxima above threshold
        for i in range(2, len(self.spectrum_data) - 2):
            if (self.spectrum_data[i] > self.peak_threshold and
                self.spectrum_data[i] > self.spectrum_data[i-1] and
                self.spectrum_data[i] > self.spectrum_data[i+1] and
                self.spectrum_data[i] > self.spectrum_data[i-2] and
                self.spectrum_data[i] > self.spectrum_data[i+2]):

                freq = self.freqs[i]
                db = self.spectrum_data[i]

                # Classify based on frequency range and intensity
                state = SignalState.UNKNOWN
                if db > -30:  # High intensity = likely shot
                    if freq > 500:
                        state = SignalState.SHOT
                    elif freq > 250:
                        state = SignalState.RUN
                    else:
                        state = SignalState.WALK
                elif db > -50:
                    if 300 <= freq <= 800:
                        state = SignalState.RUN
                    elif 100 <= freq <= 400:
                        state = SignalState.WALK

                self.peaks.append({'freq': freq, 'db': db, 'state': state, 'idx': i})

        # Limit to top 5 peaks
        self.peaks = sorted(self.peaks, key=lambda x: x['db'], reverse=True)[:5]

    def paintEvent(self, event):
        """Paint the military spectrum display"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(0, 0, w, h, self.COLOR_BG)

        # Margins for spectrum area
        margin_left = 80
        margin_right = 100
        margin_top = 50
        margin_bottom = 40

        spec_x = margin_left
        spec_y = margin_top
        spec_w = w - margin_left - margin_right
        spec_h = h - margin_top - margin_bottom

        # Draw grid
        self._draw_grid(painter, spec_x, spec_y, spec_w, spec_h)

        # Draw spectrum
        self._draw_spectrum(painter, spec_x, spec_y, spec_w, spec_h)

        # Draw peaks with WALK/RUN/SHOT markers
        self._draw_peaks(painter, spec_x, spec_y, spec_w, spec_h)

        # Draw axes labels
        self._draw_axes(painter, spec_x, spec_y, spec_w, spec_h)

        # Draw LIVE indicator
        self._draw_live_indicator(painter)

        # Draw side panels
        self._draw_left_panel(painter, spec_y, spec_h)
        self._draw_right_panel(painter, w, spec_y, spec_h)

        # Draw title
        self._draw_title(painter, w)

    def _draw_grid(self, painter, x, y, w, h):
        """Draw thin grid"""
        # Vertical lines (frequency)
        painter.setPen(QPen(self.COLOR_GRID, 1))
        num_v_lines = 10
        for i in range(num_v_lines + 1):
            lx = x + (w * i / num_v_lines)
            painter.drawLine(int(lx), y, int(lx), y + h)

        # Horizontal lines (dB)
        num_h_lines = 8
        for i in range(num_h_lines + 1):
            ly = y + (h * i / num_h_lines)
            if i % 2 == 0:
                painter.setPen(QPen(self.COLOR_GRID_MAJOR, 1))
            else:
                painter.setPen(QPen(self.COLOR_GRID, 1))
            painter.drawLine(x, int(ly), x + w, int(ly))

        # Border
        painter.setPen(QPen(self.COLOR_GRID_MAJOR, 2))
        painter.drawRect(x, y, w, h)

    def _draw_spectrum(self, painter, x, y, w, h):
        """Draw spectrum bars and curve"""
        if len(self.spectrum_data) == 0:
            return

        # Create path for filled area
        path = QPainterPath()
        path.moveTo(x, y + h)

        # Draw bars
        bar_width = max(1, w / len(self.spectrum_data))

        for i, db in enumerate(self.spectrum_data):
            # Normalize to 0-1 range (-80 to 0 dB)
            normalized = max(0, min(1, (db + 80) / 80))
            bar_h = normalized * h
            bx = x + (i / len(self.spectrum_data)) * w

            # Add to path
            path.lineTo(bx, y + h - bar_h)

        path.lineTo(x + w, y + h)
        path.closeSubpath()

        # Fill with gradient
        gradient = QLinearGradient(x, y + h, x, y)
        gradient.setColorAt(0, QColor(0, 100, 80, 20))
        gradient.setColorAt(0.5, QColor(0, 200, 150, 60))
        gradient.setColorAt(1, QColor(0, 255, 200, 100))
        painter.fillPath(path, gradient)

        # Draw curve line
        painter.setPen(QPen(self.COLOR_SPECTRUM, 2))
        for i in range(1, len(self.spectrum_data)):
            db1 = self.spectrum_data[i-1]
            db2 = self.spectrum_data[i]
            n1 = max(0, min(1, (db1 + 80) / 80))
            n2 = max(0, min(1, (db2 + 80) / 80))
            x1 = x + ((i-1) / len(self.spectrum_data)) * w
            x2 = x + (i / len(self.spectrum_data)) * w
            y1 = y + h - n1 * h
            y2 = y + h - n2 * h
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Draw average line
        painter.setPen(QPen(self.COLOR_AVG, 1, Qt.DashLine))
        for i in range(1, len(self.avg_data)):
            db1 = self.avg_data[i-1]
            db2 = self.avg_data[i]
            n1 = max(0, min(1, (db1 + 80) / 80))
            n2 = max(0, min(1, (db2 + 80) / 80))
            x1 = x + ((i-1) / len(self.avg_data)) * w
            x2 = x + (i / len(self.avg_data)) * w
            y1 = y + h - n1 * h
            y2 = y + h - n2 * h
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_peaks(self, painter, x, y, w, h):
        """Draw peak markers with WALK/RUN/SHOT icons"""
        for peak in self.peaks:
            freq = peak['freq']
            db = peak['db']
            state = peak['state']

            # Calculate position
            freq_ratio = np.log10(freq / 20) / np.log10(10000 / 20) if freq > 20 else 0
            freq_ratio = min(1, max(0, (freq - 20) / (10000 - 20)))  # Linear for simplicity
            px = x + freq_ratio * w
            normalized = max(0, min(1, (db + 80) / 80))
            py = y + h - normalized * h

            # Get color based on state
            color = SignalState.COLORS.get(state, self.COLOR_TEXT)
            label = SignalState.LABELS.get(state, "")

            # Draw peak marker
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(px) - 4, int(py) - 4, 8, 8)

            # Draw vertical line to bottom
            painter.setPen(QPen(color, 1, Qt.DashLine))
            painter.drawLine(int(px), int(py), int(px), y + h)

            # Draw frequency/dB label
            painter.setFont(self.FONT_SMALL)
            painter.setPen(QPen(self.COLOR_TEXT, 1))
            freq_text = f"{freq:.0f}Hz"
            db_text = f"{db:.0f}dB"
            painter.drawText(int(px) - 20, int(py) - 25, freq_text)
            painter.drawText(int(px) - 15, int(py) - 15, db_text)

            # Draw state icon and label
            if state != SignalState.UNKNOWN:
                self._draw_state_icon(painter, int(px) + 15, int(py) - 20, state)
                painter.setFont(self.FONT_LABEL)
                painter.setPen(QPen(color, 1))
                painter.drawText(int(px) + 30, int(py) - 12, label)

    def _draw_state_icon(self, painter, x, y, state):
        """Draw WALK/RUN/SHOT icon"""
        color = SignalState.COLORS.get(state, self.COLOR_TEXT)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)

        if state == SignalState.WALK:
            # Walking figure icon
            # Head
            painter.drawEllipse(x + 4, y, 6, 6)
            # Body
            painter.drawLine(x + 7, y + 6, x + 7, y + 14)
            # Arms
            painter.drawLine(x + 3, y + 9, x + 11, y + 9)
            # Legs (walking pose)
            painter.drawLine(x + 7, y + 14, x + 3, y + 20)
            painter.drawLine(x + 7, y + 14, x + 11, y + 20)

        elif state == SignalState.RUN:
            # Running figure icon
            # Head
            painter.drawEllipse(x + 6, y, 6, 6)
            # Body (leaning forward)
            painter.drawLine(x + 9, y + 6, x + 5, y + 14)
            # Arms (running pose)
            painter.drawLine(x + 2, y + 7, x + 12, y + 11)
            # Legs (running stride)
            painter.drawLine(x + 5, y + 14, x, y + 20)
            painter.drawLine(x + 5, y + 14, x + 12, y + 18)

        elif state == SignalState.SHOT:
            # Bullet/projectile icon
            painter.setBrush(QBrush(color))
            # Bullet shape
            path = QPainterPath()
            path.moveTo(x, y + 10)
            path.lineTo(x + 5, y + 6)
            path.lineTo(x + 15, y + 10)
            path.lineTo(x + 5, y + 14)
            path.closeSubpath()
            painter.drawPath(path)
            # Trail lines
            painter.setPen(QPen(color, 1))
            painter.drawLine(x - 5, y + 8, x - 2, y + 10)
            painter.drawLine(x - 5, y + 10, x - 2, y + 10)
            painter.drawLine(x - 5, y + 12, x - 2, y + 10)

    def _draw_axes(self, painter, x, y, w, h):
        """Draw axis labels"""
        painter.setFont(self.FONT_LABEL)
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))

        # Frequency labels
        freq_labels = ['20', '100', '500', '1k', '2k', '5k', '10k']
        freq_values = [20, 100, 500, 1000, 2000, 5000, 10000]
        for label, freq in zip(freq_labels, freq_values):
            ratio = (freq - 20) / (10000 - 20)
            lx = x + ratio * w
            painter.drawText(int(lx) - 10, y + h + 15, label)

        # dB labels
        db_labels = ['0', '-20', '-40', '-60', '-80']
        for i, label in enumerate(db_labels):
            ly = y + (i / 4) * h
            painter.drawText(x - 35, int(ly) + 4, label)

        # Axis titles
        painter.setFont(self.FONT_MAIN)
        painter.setPen(QPen(self.COLOR_TEXT, 1))
        painter.drawText(x + w // 2 - 30, y + h + 35, "Frequency (Hz)")

        painter.save()
        painter.translate(15, y + h // 2 + 30)
        painter.rotate(-90)
        painter.drawText(0, 0, "Power (dB)")
        painter.restore()

    def _draw_live_indicator(self, painter):
        """Draw LIVE indicator with blinking red dot"""
        painter.setFont(self.FONT_STATUS)

        # Red dot
        if self.live_blink:
            painter.setBrush(QBrush(QColor(255, 0, 0)))
        else:
            painter.setBrush(QBrush(QColor(100, 0, 0)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(15, 12, 10, 10)

        # LIVE text
        painter.setPen(QPen(self.COLOR_TEXT, 1))
        painter.drawText(30, 22, "LIVE")

    def _draw_title(self, painter, w):
        """Draw panel title"""
        painter.setFont(self.FONT_TITLE)
        painter.setPen(QPen(self.COLOR_ACCENT, 1))
        painter.drawText(w // 2 - 50, 25, "LIVE SPECTRUM")

    def _draw_left_panel(self, painter, y, h):
        """Draw left info panel"""
        panel_x = 5
        panel_y = y + 20

        painter.setFont(self.FONT_LABEL)
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))

        # Bandwidth
        painter.drawText(panel_x, panel_y, "BANDWIDTH")
        painter.setPen(QPen(self.COLOR_TEXT, 1))
        painter.drawText(panel_x, panel_y + 12, self.bandwidth)

        # Peak
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))
        painter.drawText(panel_x, panel_y + 35, "PEAK")
        painter.setPen(QPen(self.COLOR_ACCENT, 1))
        painter.drawText(panel_x, panel_y + 47, f"{self.peak_freq:.0f}Hz")
        painter.drawText(panel_x, panel_y + 59, f"{self.peak_db:.1f}dB")

        # Noise floor
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))
        painter.drawText(panel_x, panel_y + 82, "FLOOR")
        painter.setPen(QPen(self.COLOR_TEXT, 1))
        painter.drawText(panel_x, panel_y + 94, f"{self.noise_floor:.1f}dB")

    def _draw_right_panel(self, painter, w, y, h):
        """Draw right info panel with legend"""
        panel_x = w - 90
        panel_y = y + 20

        painter.setFont(self.FONT_LABEL)
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))
        painter.drawText(panel_x, panel_y, "SIGNALS")

        # Legend
        legend_items = [
            (SignalState.WALK, "WALK", self.COLOR_WALK),
            (SignalState.RUN, "RUN", self.COLOR_RUN),
            (SignalState.SHOT, "SHOT", self.COLOR_SHOT),
        ]

        for i, (state, label, color) in enumerate(legend_items):
            ly = panel_y + 20 + i * 25
            self._draw_state_icon(painter, panel_x, ly, state)
            painter.setFont(self.FONT_LABEL)
            painter.setPen(QPen(color, 1))
            painter.drawText(panel_x + 25, ly + 12, label)


# =============================================================================
# MILITARY WATERFALL WIDGET
# =============================================================================

class MilitaryWaterfallWidget(QWidget):
    """
    Futuristic military signal analysis - WATERFALL display

    Features:
    - Vertical waterfall (spectrogram over time)
    - Frequency axis horizontal, time vertical
    - Color-coded intensity (green/cyan/yellow)
    - WALK/RUN/SHOT markers on signal bands
    - Time scale on left, frequency scale on bottom
    - Legend panel with color and icon guide
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        log("MilitaryWaterfallWidget.__init__", "INFO")

        self.setMinimumSize(600, 350)
        self.setStyleSheet("background-color: #030508;")

        # Colors
        self.COLOR_BG = QColor(3, 5, 8)
        self.COLOR_GRID = QColor(0, 60, 80, 30)
        self.COLOR_TEXT = QColor(0, 200, 150)
        self.COLOR_TEXT_DIM = QColor(0, 120, 100)
        self.COLOR_ACCENT = QColor(0, 255, 200)

        # Fonts
        self.FONT_MAIN = QFont("Consolas", 9)
        self.FONT_LABEL = QFont("Consolas", 8)
        self.FONT_STATUS = QFont("Consolas", 10, QFont.Bold)
        self.FONT_TITLE = QFont("Consolas", 11, QFont.Bold)
        self.FONT_SMALL = QFont("Consolas", 7)

        # Waterfall data
        self.num_rows = 100
        self.num_cols = 256
        self.waterfall_data = np.full((self.num_rows, self.num_cols), -80.0)
        self.row_idx = 0

        # Signal markers: list of {row, col_start, col_end, state}
        self.markers = []

        # Frequency range
        self.freq_min = 20
        self.freq_max = 10000

        # Time scale (seconds per row)
        self.time_per_row = 0.05  # 50ms per row

        # Color map (dark to bright: green -> cyan -> yellow)
        self.colormap = self._create_colormap()

    def _create_colormap(self):
        """Create military-style colormap"""
        colormap = []
        for i in range(256):
            if i < 64:
                # Dark green
                r = 0
                g = int(i * 0.5)
                b = int(i * 0.3)
            elif i < 128:
                # Green to cyan
                t = (i - 64) / 64
                r = 0
                g = int(32 + t * 150)
                b = int(20 + t * 100)
            elif i < 192:
                # Cyan to yellow-green
                t = (i - 128) / 64
                r = int(t * 200)
                g = int(182 + t * 55)
                b = int(120 - t * 100)
            else:
                # Yellow to bright
                t = (i - 192) / 64
                r = int(200 + t * 55)
                g = int(237 + t * 18)
                b = int(20 + t * 30)
            colormap.append(QColor(r, g, b))
        return colormap

    def push_row(self, spectrum_db):
        """Add new row to waterfall"""
        try:
            # Roll data down
            self.waterfall_data = np.roll(self.waterfall_data, 1, axis=0)

            # Resample if needed
            if len(spectrum_db) != self.num_cols:
                row = np.interp(
                    np.linspace(0, len(spectrum_db), self.num_cols),
                    np.arange(len(spectrum_db)),
                    spectrum_db
                )
            else:
                row = spectrum_db.copy()

            self.waterfall_data[0, :] = row

            # Detect and mark signals
            self._detect_signals(row)

            # Age markers
            self._age_markers()

            self.update()
        except Exception as e:
            log(f"MilitaryWaterfall push_row error: {e}", "ERROR")

    def _detect_signals(self, row):
        """Detect signals in new row and classify"""
        threshold = -50

        # Find peaks in this row
        in_signal = False
        signal_start = 0
        signal_max = -80
        signal_max_col = 0

        for i, db in enumerate(row):
            if db > threshold:
                if not in_signal:
                    in_signal = True
                    signal_start = i
                    signal_max = db
                    signal_max_col = i
                else:
                    if db > signal_max:
                        signal_max = db
                        signal_max_col = i
            else:
                if in_signal:
                    # End of signal - classify
                    freq = self.freq_min + (signal_max_col / self.num_cols) * (self.freq_max - self.freq_min)
                    state = self._classify_signal(freq, signal_max)

                    if state != SignalState.UNKNOWN:
                        self.markers.append({
                            'row': 0,
                            'col_start': signal_start,
                            'col_end': i,
                            'col_peak': signal_max_col,
                            'state': state,
                            'db': signal_max
                        })
                    in_signal = False

    def _classify_signal(self, freq, db):
        """Classify signal based on frequency and intensity"""
        if db > -30:
            if freq > 500:
                return SignalState.SHOT
            elif freq > 250:
                return SignalState.RUN
            else:
                return SignalState.WALK
        elif db > -45:
            if 300 <= freq <= 800:
                return SignalState.RUN
            elif 100 <= freq <= 400:
                return SignalState.WALK
        return SignalState.UNKNOWN

    def _age_markers(self):
        """Age markers and remove old ones"""
        new_markers = []
        for m in self.markers:
            m['row'] += 1
            if m['row'] < self.num_rows:
                new_markers.append(m)
        self.markers = new_markers

    def paintEvent(self, event):
        """Paint the waterfall display"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(0, 0, w, h, self.COLOR_BG)

        # Margins
        margin_left = 60
        margin_right = 100
        margin_top = 45
        margin_bottom = 50

        wf_x = margin_left
        wf_y = margin_top
        wf_w = w - margin_left - margin_right
        wf_h = h - margin_top - margin_bottom

        # Draw waterfall
        self._draw_waterfall(painter, wf_x, wf_y, wf_w, wf_h)

        # Draw grid overlay
        self._draw_grid(painter, wf_x, wf_y, wf_w, wf_h)

        # Draw signal markers
        self._draw_markers(painter, wf_x, wf_y, wf_w, wf_h)

        # Draw axes
        self._draw_axes(painter, wf_x, wf_y, wf_w, wf_h)

        # Draw title
        self._draw_title(painter, w)

        # Draw legend panel
        self._draw_legend(painter, w, wf_y, wf_h)

    def _draw_waterfall(self, painter, x, y, w, h):
        """Draw the waterfall image"""
        cell_w = w / self.num_cols
        cell_h = h / self.num_rows

        for row in range(self.num_rows):
            for col in range(self.num_cols):
                db = self.waterfall_data[row, col]
                # Normalize to 0-255
                norm = int(max(0, min(255, (db + 80) / 80 * 255)))
                color = self.colormap[norm]

                cx = x + col * cell_w
                cy = y + row * cell_h
                painter.fillRect(int(cx), int(cy), int(cell_w) + 1, int(cell_h) + 1, color)

    def _draw_grid(self, painter, x, y, w, h):
        """Draw thin grid overlay"""
        painter.setPen(QPen(self.COLOR_GRID, 1))

        # Vertical lines
        for i in range(11):
            lx = x + (w * i / 10)
            painter.drawLine(int(lx), y, int(lx), y + h)

        # Horizontal lines
        for i in range(11):
            ly = y + (h * i / 10)
            painter.drawLine(x, int(ly), x + w, int(ly))

        # Border
        painter.setPen(QPen(QColor(0, 100, 120, 100), 2))
        painter.drawRect(x, y, w, h)

    def _draw_markers(self, painter, x, y, w, h):
        """Draw WALK/RUN/SHOT markers on waterfall"""
        cell_w = w / self.num_cols
        cell_h = h / self.num_rows

        for m in self.markers:
            state = m['state']
            row = m['row']
            col_peak = m['col_peak']

            color = SignalState.COLORS.get(state, self.COLOR_TEXT)
            label = SignalState.LABELS.get(state, "")

            # Position
            mx = x + col_peak * cell_w
            my = y + row * cell_h

            # Draw marker outline
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.NoBrush)

            # Draw bracket around signal
            bracket_w = (m['col_end'] - m['col_start']) * cell_w
            painter.drawRect(int(x + m['col_start'] * cell_w), int(my) - 2,
                           int(bracket_w), int(cell_h) + 4)

            # Draw state icon (only for recent markers)
            if row < 20:
                # Icon position
                icon_x = int(mx) + 5
                icon_y = int(my) - 15
                self._draw_state_icon(painter, icon_x, icon_y, state)

                # Label
                painter.setFont(self.FONT_SMALL)
                painter.setPen(QPen(color, 1))
                painter.drawText(icon_x + 18, icon_y + 10, label)

    def _draw_state_icon(self, painter, x, y, state):
        """Draw WALK/RUN/SHOT icon"""
        color = SignalState.COLORS.get(state, self.COLOR_TEXT)
        painter.setPen(QPen(color, 1))
        painter.setBrush(Qt.NoBrush)

        if state == SignalState.WALK:
            # Walking figure (small)
            painter.drawEllipse(x + 3, y, 4, 4)
            painter.drawLine(x + 5, y + 4, x + 5, y + 10)
            painter.drawLine(x + 2, y + 6, x + 8, y + 6)
            painter.drawLine(x + 5, y + 10, x + 2, y + 14)
            painter.drawLine(x + 5, y + 10, x + 8, y + 14)

        elif state == SignalState.RUN:
            # Running figure (small)
            painter.drawEllipse(x + 4, y, 4, 4)
            painter.drawLine(x + 6, y + 4, x + 4, y + 10)
            painter.drawLine(x + 1, y + 5, x + 9, y + 8)
            painter.drawLine(x + 4, y + 10, x, y + 14)
            painter.drawLine(x + 4, y + 10, x + 9, y + 12)

        elif state == SignalState.SHOT:
            # Bullet (small)
            painter.setBrush(QBrush(color))
            path = QPainterPath()
            path.moveTo(x, y + 7)
            path.lineTo(x + 4, y + 4)
            path.lineTo(x + 12, y + 7)
            path.lineTo(x + 4, y + 10)
            path.closeSubpath()
            painter.drawPath(path)

    def _draw_axes(self, painter, x, y, w, h):
        """Draw axis labels"""
        painter.setFont(self.FONT_LABEL)
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))

        # Frequency labels (bottom)
        freq_labels = ['20', '1k', '2k', '4k', '6k', '8k', '10k']
        freq_positions = [0, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
        for label, pos in zip(freq_labels, freq_positions):
            lx = x + pos * w
            painter.drawText(int(lx) - 10, y + h + 18, label)

        # Time labels (left)
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))
        time_labels = ['NOW', '-1s', '-2s', '-3s', '-4s', '-5s']
        for i, label in enumerate(time_labels):
            ly = y + (i / 5) * h
            painter.drawText(x - 50, int(ly) + 4, label)

        # Axis titles
        painter.setFont(self.FONT_MAIN)
        painter.setPen(QPen(self.COLOR_TEXT, 1))
        painter.drawText(x + w // 2 - 30, y + h + 40, "Frequency (Hz)")

        painter.save()
        painter.translate(12, y + h // 2 + 15)
        painter.rotate(-90)
        painter.drawText(0, 0, "Time")
        painter.restore()

    def _draw_title(self, painter, w):
        """Draw panel title"""
        painter.setFont(self.FONT_TITLE)
        painter.setPen(QPen(self.COLOR_ACCENT, 1))
        painter.drawText(w // 2 - 40, 25, "WATERFALL")

        # Subtitle
        painter.setFont(self.FONT_LABEL)
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))
        painter.drawText(w // 2 - 50, 38, "Signal History")

    def _draw_legend(self, painter, w, y, h):
        """Draw legend panel"""
        panel_x = w - 90
        panel_y = y + 10

        painter.setFont(self.FONT_LABEL)
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))
        painter.drawText(panel_x, panel_y, "LEGEND")

        # Color scale
        scale_y = panel_y + 15
        scale_h = 60
        for i in range(scale_h):
            norm = int(255 * i / scale_h)
            color = self.colormap[norm]
            painter.fillRect(panel_x, scale_y + scale_h - i, 20, 1, color)

        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))
        painter.drawText(panel_x + 25, scale_y + 5, "0dB")
        painter.drawText(panel_x + 25, scale_y + scale_h, "-80dB")

        # Signal icons
        icon_y = scale_y + scale_h + 20
        legend_items = [
            (SignalState.WALK, "WALK"),
            (SignalState.RUN, "RUN"),
            (SignalState.SHOT, "SHOT"),
        ]

        for i, (state, label) in enumerate(legend_items):
            ly = icon_y + i * 20
            self._draw_state_icon(painter, panel_x, ly, state)
            color = SignalState.COLORS.get(state, self.COLOR_TEXT)
            painter.setFont(self.FONT_SMALL)
            painter.setPen(QPen(color, 1))
            painter.drawText(panel_x + 18, ly + 10, label)


# =============================================================================
# MILITARY WAVEFORM WIDGET
# =============================================================================

class MilitaryWaveformWidget(QWidget):
    """
    Ultra-readable WAVEFORM panel - military sci-fi HUD style

    Features:
    - Oscilloscope-style waveform display
    - Thin grid, neon lines
    - Time markers on horizontal axis
    - Amplitude scale on vertical axis
    - Top bar with gain, trigger, sample rate
    - WALK/RUN/SHOT segment markers with icons
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        log("MilitaryWaveformWidget.__init__", "INFO")

        self.setMinimumSize(600, 300)
        self.setStyleSheet("background-color: #030508;")

        # Colors
        self.COLOR_BG = QColor(3, 5, 8)
        self.COLOR_GRID = QColor(0, 60, 80, 40)
        self.COLOR_GRID_MAJOR = QColor(0, 80, 100, 60)
        self.COLOR_WAVE_L = QColor(0, 255, 180)
        self.COLOR_WAVE_R = QColor(0, 200, 255)
        self.COLOR_RMS = QColor(255, 200, 0)
        self.COLOR_TEXT = QColor(0, 200, 150)
        self.COLOR_TEXT_DIM = QColor(0, 120, 100)
        self.COLOR_ACCENT = QColor(0, 255, 200)

        # Fonts
        self.FONT_MAIN = QFont("Consolas", 9)
        self.FONT_LABEL = QFont("Consolas", 8)
        self.FONT_STATUS = QFont("Consolas", 10, QFont.Bold)
        self.FONT_TITLE = QFont("Consolas", 11, QFont.Bold)
        self.FONT_SMALL = QFont("Consolas", 7)

        # Waveform data
        self.buffer_size = 2048
        self.left_channel = np.zeros(self.buffer_size)
        self.right_channel = np.zeros(self.buffer_size)
        self.rms_envelope = np.zeros(self.buffer_size)

        # Signal segments: list of {start_idx, end_idx, state}
        self.segments = []

        # Parameters
        self.gain = 1.0
        self.trigger_level = 0.1
        self.sample_rate = 48000

        # Amplitude range
        self.amp_max = 1.0

    def update_waveform(self, data):
        """Update waveform from audio data"""
        try:
            if data is None or len(data) == 0:
                return

            if data.ndim == 2 and data.shape[1] >= 2:
                left = data[:, 0]
                right = data[:, 1]
            else:
                left = data.ravel()
                right = left.copy()

            # Resample to buffer size
            if len(left) > self.buffer_size:
                step = len(left) // self.buffer_size
                self.left_channel = left[::step][:self.buffer_size]
                self.right_channel = right[::step][:self.buffer_size]
            elif len(left) < self.buffer_size:
                self.left_channel = np.pad(left, (0, self.buffer_size - len(left)), 'constant')
                self.right_channel = np.pad(right, (0, self.buffer_size - len(right)), 'constant')
            else:
                self.left_channel = left.copy()
                self.right_channel = right.copy()

            # Calculate RMS envelope
            window_size = 50
            mono = (self.left_channel + self.right_channel) / 2
            self.rms_envelope = np.sqrt(np.convolve(mono**2,
                                        np.ones(window_size)/window_size,
                                        mode='same'))

            # Detect segments
            self._detect_segments()

            # Update amplitude range
            self.amp_max = max(np.max(np.abs(self.left_channel)),
                             np.max(np.abs(self.right_channel)), 0.1)

            self.update()
        except Exception as e:
            log(f"MilitaryWaveform update error: {e}", "ERROR")

    def _detect_segments(self):
        """Detect WALK/RUN/SHOT segments in waveform"""
        self.segments = []

        # Analyze RMS envelope for activity
        threshold_low = 0.02
        threshold_med = 0.08
        threshold_high = 0.2

        in_segment = False
        segment_start = 0
        segment_max = 0

        for i, rms in enumerate(self.rms_envelope):
            if rms > threshold_low:
                if not in_segment:
                    in_segment = True
                    segment_start = i
                    segment_max = rms
                else:
                    segment_max = max(segment_max, rms)
            else:
                if in_segment:
                    # End of segment - classify
                    state = SignalState.UNKNOWN
                    if segment_max > threshold_high:
                        state = SignalState.SHOT
                    elif segment_max > threshold_med:
                        state = SignalState.RUN
                    elif segment_max > threshold_low:
                        state = SignalState.WALK

                    if state != SignalState.UNKNOWN:
                        self.segments.append({
                            'start': segment_start,
                            'end': i,
                            'state': state,
                            'max_rms': segment_max
                        })
                    in_segment = False

    def paintEvent(self, event):
        """Paint the waveform display"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(0, 0, w, h, self.COLOR_BG)

        # Margins
        margin_left = 60
        margin_right = 30
        margin_top = 60
        margin_bottom = 45

        wv_x = margin_left
        wv_y = margin_top
        wv_w = w - margin_left - margin_right
        wv_h = h - margin_top - margin_bottom

        # Draw grid
        self._draw_grid(painter, wv_x, wv_y, wv_w, wv_h)

        # Draw waveforms
        self._draw_waveforms(painter, wv_x, wv_y, wv_w, wv_h)

        # Draw segment markers
        self._draw_segments(painter, wv_x, wv_y, wv_w, wv_h)

        # Draw axes
        self._draw_axes(painter, wv_x, wv_y, wv_w, wv_h)

        # Draw title bar
        self._draw_title_bar(painter, w)

        # Draw parameter panel
        self._draw_params(painter, wv_x, wv_y, wv_w)

    def _draw_grid(self, painter, x, y, w, h):
        """Draw thin grid"""
        # Center line
        painter.setPen(QPen(self.COLOR_GRID_MAJOR, 1))
        center_y = y + h // 2
        painter.drawLine(x, center_y, x + w, center_y)

        # Other horizontal lines
        painter.setPen(QPen(self.COLOR_GRID, 1))
        for i in range(1, 5):
            dy = (h // 2) * i / 4
            painter.drawLine(x, int(center_y - dy), x + w, int(center_y - dy))
            painter.drawLine(x, int(center_y + dy), x + w, int(center_y + dy))

        # Vertical lines
        for i in range(11):
            lx = x + (w * i / 10)
            if i == 5:
                painter.setPen(QPen(self.COLOR_GRID_MAJOR, 1))
            else:
                painter.setPen(QPen(self.COLOR_GRID, 1))
            painter.drawLine(int(lx), y, int(lx), y + h)

        # Border
        painter.setPen(QPen(self.COLOR_GRID_MAJOR, 2))
        painter.drawRect(x, y, w, h)

    def _draw_waveforms(self, painter, x, y, w, h):
        """Draw waveform curves"""
        center_y = y + h // 2
        scale = (h / 2) / self.amp_max

        # Left channel (cyan-green)
        painter.setPen(QPen(self.COLOR_WAVE_L, 1))
        for i in range(1, len(self.left_channel)):
            x1 = x + ((i - 1) / len(self.left_channel)) * w
            x2 = x + (i / len(self.left_channel)) * w
            y1 = center_y - self.left_channel[i - 1] * scale
            y2 = center_y - self.left_channel[i] * scale
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Right channel (blue-cyan)
        painter.setPen(QPen(self.COLOR_WAVE_R, 1))
        for i in range(1, len(self.right_channel)):
            x1 = x + ((i - 1) / len(self.right_channel)) * w
            x2 = x + (i / len(self.right_channel)) * w
            y1 = center_y - self.right_channel[i - 1] * scale
            y2 = center_y - self.right_channel[i] * scale
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # RMS envelope (yellow dashed)
        painter.setPen(QPen(self.COLOR_RMS, 2, Qt.DashLine))
        for i in range(1, len(self.rms_envelope)):
            x1 = x + ((i - 1) / len(self.rms_envelope)) * w
            x2 = x + (i / len(self.rms_envelope)) * w
            y1 = center_y - self.rms_envelope[i - 1] * scale
            y2 = center_y - self.rms_envelope[i] * scale
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_segments(self, painter, x, y, w, h):
        """Draw WALK/RUN/SHOT segment markers"""
        for seg in self.segments:
            state = seg['state']
            start = seg['start']
            end = seg['end']

            color = SignalState.COLORS.get(state, self.COLOR_TEXT)
            label = SignalState.LABELS.get(state, "")

            # Segment boundaries
            x1 = x + (start / len(self.left_channel)) * w
            x2 = x + (end / len(self.left_channel)) * w
            mid_x = (x1 + x2) / 2

            # Draw segment highlight
            painter.setPen(Qt.NoPen)
            highlight_color = QColor(color)
            highlight_color.setAlpha(30)
            painter.setBrush(QBrush(highlight_color))
            painter.drawRect(int(x1), y, int(x2 - x1), h)

            # Draw boundary lines
            painter.setPen(QPen(color, 1, Qt.DashLine))
            painter.drawLine(int(x1), y, int(x1), y + h)
            painter.drawLine(int(x2), y, int(x2), y + h)

            # Draw icon and label above segment
            icon_x = int(mid_x) - 10
            icon_y = y - 35
            self._draw_state_icon(painter, icon_x, icon_y, state)

            # Label
            painter.setFont(self.FONT_LABEL)
            painter.setPen(QPen(color, 1))
            painter.drawText(icon_x + 20, icon_y + 12, label)

            # Connecting line
            painter.setPen(QPen(color, 1))
            painter.drawLine(int(mid_x), icon_y + 20, int(mid_x), y)

    def _draw_state_icon(self, painter, x, y, state):
        """Draw WALK/RUN/SHOT icon"""
        color = SignalState.COLORS.get(state, self.COLOR_TEXT)
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)

        if state == SignalState.WALK:
            painter.drawEllipse(x + 4, y, 6, 6)
            painter.drawLine(x + 7, y + 6, x + 7, y + 14)
            painter.drawLine(x + 3, y + 9, x + 11, y + 9)
            painter.drawLine(x + 7, y + 14, x + 3, y + 20)
            painter.drawLine(x + 7, y + 14, x + 11, y + 20)

        elif state == SignalState.RUN:
            painter.drawEllipse(x + 6, y, 6, 6)
            painter.drawLine(x + 9, y + 6, x + 5, y + 14)
            painter.drawLine(x + 2, y + 7, x + 12, y + 11)
            painter.drawLine(x + 5, y + 14, x, y + 20)
            painter.drawLine(x + 5, y + 14, x + 12, y + 18)

        elif state == SignalState.SHOT:
            painter.setBrush(QBrush(color))
            path = QPainterPath()
            path.moveTo(x, y + 10)
            path.lineTo(x + 5, y + 6)
            path.lineTo(x + 15, y + 10)
            path.lineTo(x + 5, y + 14)
            path.closeSubpath()
            painter.drawPath(path)
            painter.setPen(QPen(color, 1))
            painter.drawLine(x - 5, y + 8, x - 2, y + 10)
            painter.drawLine(x - 5, y + 10, x - 2, y + 10)
            painter.drawLine(x - 5, y + 12, x - 2, y + 10)

    def _draw_axes(self, painter, x, y, w, h):
        """Draw axis labels"""
        painter.setFont(self.FONT_LABEL)
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))

        # Time labels (samples converted to ms)
        time_ms = (self.buffer_size / self.sample_rate) * 1000
        time_labels = ['0', f'{time_ms/4:.0f}', f'{time_ms/2:.0f}',
                       f'{3*time_ms/4:.0f}', f'{time_ms:.0f}']
        for i, label in enumerate(time_labels):
            lx = x + (i / 4) * w
            painter.drawText(int(lx) - 10, y + h + 18, f"{label}ms")

        # Amplitude labels
        amp_labels = [f'{self.amp_max:.2f}', f'{self.amp_max/2:.2f}', '0',
                      f'-{self.amp_max/2:.2f}', f'-{self.amp_max:.2f}']
        for i, label in enumerate(amp_labels):
            ly = y + (i / 4) * h
            painter.drawText(x - 55, int(ly) + 4, label)

        # Axis titles
        painter.setFont(self.FONT_MAIN)
        painter.setPen(QPen(self.COLOR_TEXT, 1))
        painter.drawText(x + w // 2 - 30, y + h + 38, "Time (ms)")

        painter.save()
        painter.translate(12, y + h // 2 + 30)
        painter.rotate(-90)
        painter.drawText(0, 0, "Amplitude")
        painter.restore()

    def _draw_title_bar(self, painter, w):
        """Draw title bar"""
        painter.setFont(self.FONT_TITLE)
        painter.setPen(QPen(self.COLOR_ACCENT, 1))
        painter.drawText(w // 2 - 40, 22, "WAVEFORM")

    def _draw_params(self, painter, x, y, w):
        """Draw parameter bar"""
        params_y = y - 25

        painter.setFont(self.FONT_LABEL)

        # Gain
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))
        painter.drawText(x, params_y, "GAIN")
        painter.setPen(QPen(self.COLOR_TEXT, 1))
        painter.drawText(x + 35, params_y, f"{self.gain:.1f}x")

        # Trigger
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))
        painter.drawText(x + 90, params_y, "TRIG")
        painter.setPen(QPen(self.COLOR_TEXT, 1))
        painter.drawText(x + 125, params_y, f"{self.trigger_level:.2f}")

        # Sample rate
        painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))
        painter.drawText(x + 180, params_y, "SR")
        painter.setPen(QPen(self.COLOR_TEXT, 1))
        painter.drawText(x + 200, params_y, f"{self.sample_rate/1000:.0f}kHz")

        # Legend
        legend_x = x + w - 200
        legend_items = [
            ("L", self.COLOR_WAVE_L),
            ("R", self.COLOR_WAVE_R),
            ("RMS", self.COLOR_RMS),
        ]
        for i, (label, color) in enumerate(legend_items):
            lx = legend_x + i * 50
            painter.setPen(QPen(color, 2))
            painter.drawLine(lx, int(params_y) - 3, lx + 15, int(params_y) - 3)
            painter.setPen(QPen(self.COLOR_TEXT_DIM, 1))
            painter.drawText(lx + 20, params_y, label)
