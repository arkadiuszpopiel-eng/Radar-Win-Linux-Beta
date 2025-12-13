"""
RadarSuite v4.2.1 - Spectrum Widgets
Enhanced with Military-themed styling for HUD consistency
"""

import numpy as np
import pyqtgraph as pg
try:
    import pyqtgraph.opengl as gl
except ImportError:
    gl = None
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSlider, QCheckBox, QSpinBox, QGroupBox, QFormLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPalette

from core import log, tr, TOAST_DURATION_MS, TOAST_MAX_COUNT


class SpectrumWidget(pg.PlotWidget):
    """Real-time FFT spectrum analyzer"""

    def __init__(self):
        super().__init__()
        log("SpectrumWidget.__init__", "INFO")

        self.setBackground("#050505")
        self.setLabel('left', 'Power', units='dB')
        self.setLabel('bottom', 'Frequency', units='Hz')
        self.setXRange(20, 10000, padding=0)
        self.setYRange(-80, 0, padding=0)
        self.showGrid(x=True, y=True, alpha=0.25)

        self.spectrum_curve = self.plot(pen=pg.mkPen(color=(0, 255, 0), width=2))
        self.avg_curve = self.plot(pen=pg.mkPen(color=(255, 255, 0), width=1))

        self.freqs = None
        self.avg_buffer = []
        self.avg_size = 30

    def update_fft(self, data):
        """Update spectrum from audio data (computes FFT - legacy method)"""
        try:
            if data.ndim == 2:
                mono = np.mean(data, axis=1)
            else:
                mono = data.ravel()

            window = np.hanning(len(mono))
            windowed = mono * window

            fft_data = np.fft.rfft(windowed)
            freqs = np.fft.rfftfreq(len(mono), d=1.0/48000)

            power = 20 * np.log10(np.abs(fft_data) + 1e-10)

            self.spectrum_curve.setData(freqs, power)

            self.avg_buffer.append(power)
            if len(self.avg_buffer) > self.avg_size:
                self.avg_buffer.pop(0)

            avg_power = np.mean(self.avg_buffer, axis=0)
            self.avg_curve.setData(freqs, avg_power)

        except Exception as e:
            log(f"Error in update_fft: {e}", "ERROR")

    def update_from_cache(self, fft_result):
        """
        Update spectrum from cached FFT result (PERFORMANCE OPTIMIZATION)

        FIXED v3.5.0: Eliminates duplicate FFT computation

        Args:
            fft_result: Dict with keys 'fft_data', 'freqs', 'power'
        """
        try:
            freqs = fft_result['freqs']
            power_linear = fft_result['power']

            # Convert to dB
            power = 20 * np.log10(power_linear + 1e-10)

            self.spectrum_curve.setData(freqs, power)

            self.avg_buffer.append(power)
            if len(self.avg_buffer) > self.avg_size:
                self.avg_buffer.pop(0)

            avg_power = np.mean(self.avg_buffer, axis=0)
            self.avg_curve.setData(freqs, avg_power)

        except Exception as e:
            log(f"Error in update_from_cache: {e}", "ERROR")


# ============================================================================
# WATERFALL WIDGET
# ============================================================================


class WaterfallWidget(pg.PlotWidget):
    """Waterfall display (spectrogram over time)"""

    def __init__(self):
        super().__init__()
        log("WaterfallWidget.__init__", "INFO")

        self.setBackground("#050505")
        self.setLabel('left', 'Time')
        self.setLabel('bottom', 'Frequency', units='Hz')

        self.img = pg.ImageItem()
        self.addItem(self.img)

        colormap = pg.colormap.get('viridis')
        self.img.setLookupTable(colormap.getLookupTable())

        self.data = np.zeros((100, 512))
        self.row_idx = 0

    def push_row(self, row):
        """Add new row to waterfall"""
        try:
            self.data = np.roll(self.data, 1, axis=0)

            if len(row) != self.data.shape[1]:
                row = np.interp(
                    np.linspace(0, len(row), self.data.shape[1]),
                    np.arange(len(row)),
                    row
                )

            self.data[0, :] = row

            self.img.setImage(self.data.T, autoLevels=False, levels=(-80, 0))

        except Exception as e:
            log(f"Error in push_row: {e}", "ERROR")


# ============================================================================
# WAVEFORM WIDGET (v3.1.2 - Audio Input Visualization)
# ============================================================================


class WaveformWidget(pg.PlotWidget):
    """
    Real-time audio waveform display
    Shows raw audio signal to help debug input issues
    Displays both left and right channels with RMS envelope
    """

    def __init__(self):
        super().__init__()
        log("WaveformWidget.__init__", "INFO")

        self.setBackground("#050505")
        self.setLabel('left', 'Amplitude')
        self.setLabel('bottom', 'Samples')
        self.setYRange(-1.0, 1.0, padding=0)
        self.showGrid(x=True, y=True, alpha=0.25)

        # Waveform curves
        self.left_curve = self.plot(pen=pg.mkPen(color=(0, 200, 255), width=1))
        self.right_curve = self.plot(pen=pg.mkPen(color=(255, 100, 0), width=1))
        self.rms_curve = self.plot(pen=pg.mkPen(color=(0, 255, 0), width=2, style=Qt.DashLine))

        # Buffer for display
        self.buffer_size = 2048
        self.x_data = np.arange(self.buffer_size)

        # Add legend
        legend = self.addLegend()
        legend.addItem(self.left_curve, "Left Channel")
        legend.addItem(self.right_curve, "Right Channel")
        legend.addItem(self.rms_curve, "RMS Level")

    def update_waveform(self, data):
        """Update waveform display from audio data"""
        try:
            if data is None or len(data) == 0:
                return

            # Handle stereo/mono data
            if data.ndim == 2 and data.shape[1] >= 2:
                left = data[:, 0]
                right = data[:, 1]

                # Downsample if needed for display
                if len(left) > self.buffer_size:
                    step = len(left) // self.buffer_size
                    left = left[::step][:self.buffer_size]
                    right = right[::step][:self.buffer_size]
                elif len(left) < self.buffer_size:
                    # Pad with zeros
                    left = np.pad(left, (0, self.buffer_size - len(left)), 'constant')
                    right = np.pad(right, (0, self.buffer_size - len(right)), 'constant')

                # Calculate RMS envelope (moving average)
                window_size = 50
                rms_left = np.sqrt(np.convolve(left**2, np.ones(window_size)/window_size, mode='same'))
                rms_right = np.sqrt(np.convolve(right**2, np.ones(window_size)/window_size, mode='same'))
                rms_avg = (rms_left + rms_right) / 2.0

                # Update curves
                self.left_curve.setData(self.x_data[:len(left)], left)
                self.right_curve.setData(self.x_data[:len(right)], right)
                self.rms_curve.setData(self.x_data[:len(rms_avg)], rms_avg)

            else:
                # Mono data
                mono = data.ravel()

                if len(mono) > self.buffer_size:
                    step = len(mono) // self.buffer_size
                    mono = mono[::step][:self.buffer_size]
                elif len(mono) < self.buffer_size:
                    mono = np.pad(mono, (0, self.buffer_size - len(mono)), 'constant')

                # Calculate RMS
                window_size = 50
                rms = np.sqrt(np.convolve(mono**2, np.ones(window_size)/window_size, mode='same'))

                self.left_curve.setData(self.x_data[:len(mono)], mono)
                self.right_curve.setData([], [])  # Hide right channel for mono
                self.rms_curve.setData(self.x_data[:len(rms)], rms)

            # Auto-scale Y axis based on data
            max_val = max(np.max(np.abs(data)), 0.1)  # Minimum 0.1 for visibility
            self.setYRange(-max_val * 1.1, max_val * 1.1)

        except Exception as e:
            log(f"Error in update_waveform: {e}", "ERROR")


# ============================================================================
# MILITARY-THEMED WIDGETS (v4.2.1)
# Enhanced styling for HUD consistency with Military Radar
# ============================================================================


class MilitarySpectrumWidget(SpectrumWidget):
    """
    Military-themed FFT Spectrum Analyzer.
    Enhanced styling with cyan/green military HUD colors.
    """

    def __init__(self):
        super().__init__()
        log("MilitarySpectrumWidget.__init__", "INFO")

        # Military HUD styling
        self.setBackground("#0a0a0a")
        self.setLabel('left', 'POWER', units='dB', **{'color': '#00DDFF', 'font-size': '10pt'})
        self.setLabel('bottom', 'FREQUENCY', units='Hz', **{'color': '#00DDFF', 'font-size': '10pt'})

        # Update curves with military colors
        self.spectrum_curve.setPen(pg.mkPen(color=(0, 255, 100), width=2))  # Bright green
        self.avg_curve.setPen(pg.mkPen(color=(0, 221, 255), width=1, style=Qt.DashLine))  # Cyan

        # Grid styling
        self.showGrid(x=True, y=True, alpha=0.3)
        self.getAxis('left').setPen(pg.mkPen(color='#00DDFF', width=1))
        self.getAxis('bottom').setPen(pg.mkPen(color='#00DDFF', width=1))


class MilitaryWaterfallWidget(WaterfallWidget):
    """
    Military-themed Waterfall (Spectrogram).
    Enhanced styling with military HUD colors.
    """

    def __init__(self):
        super().__init__()
        log("MilitaryWaterfallWidget.__init__", "INFO")

        # Military HUD styling
        self.setBackground("#0a0a0a")
        self.setLabel('left', 'TIME', **{'color': '#00DDFF', 'font-size': '10pt'})
        self.setLabel('bottom', 'FREQUENCY', units='Hz', **{'color': '#00DDFF', 'font-size': '10pt'})

        # Use military-themed colormap (green-cyan gradient)
        try:
            # Create custom colormap: dark -> green -> cyan
            colors = [
                (0, 0, 0),      # Black
                (0, 50, 0),     # Dark green
                (0, 150, 0),    # Green
                (0, 255, 100),  # Bright green
                (0, 221, 255),  # Cyan
            ]
            positions = [0.0, 0.25, 0.5, 0.75, 1.0]
            colormap = pg.ColorMap(positions, colors)
            self.img.setLookupTable(colormap.getLookupTable())
        except Exception as e:
            log(f"Failed to set custom colormap: {e}", "WARNING")

        # Grid styling
        self.getAxis('left').setPen(pg.mkPen(color='#00DDFF', width=1))
        self.getAxis('bottom').setPen(pg.mkPen(color='#00DDFF', width=1))


class MilitaryWaveformWidget(WaveformWidget):
    """
    Military-themed Waveform Display.
    Enhanced styling with military HUD colors.
    """

    def __init__(self):
        super().__init__()
        log("MilitaryWaveformWidget.__init__", "INFO")

        # Military HUD styling
        self.setBackground("#0a0a0a")
        self.setLabel('left', 'AMPLITUDE', **{'color': '#00DDFF', 'font-size': '10pt'})
        self.setLabel('bottom', 'SAMPLES', **{'color': '#00DDFF', 'font-size': '10pt'})

        # Update curves with military colors
        self.left_curve.setPen(pg.mkPen(color=(0, 221, 255), width=1))  # Cyan
        self.right_curve.setPen(pg.mkPen(color=(255, 150, 0), width=1))  # Orange
        self.rms_curve.setPen(pg.mkPen(color=(0, 255, 100), width=2, style=Qt.DashLine))  # Green

        # Grid styling
        self.showGrid(x=True, y=True, alpha=0.3)
        self.getAxis('left').setPen(pg.mkPen(color='#00DDFF', width=1))
        self.getAxis('bottom').setPen(pg.mkPen(color='#00DDFF', width=1))


