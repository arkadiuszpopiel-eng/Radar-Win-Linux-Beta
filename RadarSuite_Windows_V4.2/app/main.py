"""
RadarSuite v4.2.0 - Main Application
Real-time audio detection and spatial tracking system for gaming

Architecture:
- PyQt5 GUI with multi-threaded audio processing
- Real-time FFT analysis and sound classification
- 3D spatial localization (ITD/ILD) with multi-target tracking
- Worker pool for parallel detection processing

For changelog and feature details, see CHANGELOG.md
"""

# ============================================================================
# STANDARD LIBRARY IMPORTS
# ============================================================================
import sys
import os
import queue
import time
import math
import threading
import re
from typing import Optional
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from collections import deque

# ============================================================================
# THIRD-PARTY IMPORTS
# ============================================================================
import numpy as np

# FIXED v3.5.3: Add numpy compatibility shim BEFORE importing soundcard
# soundcard uses deprecated numpy.fromstring which was removed in numpy 2.0
if not hasattr(np, 'fromstring'):
    np.fromstring = np.frombuffer

from scipy import signal as sp_signal
import psutil

import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QDockWidget, QTabWidget, QPushButton, QLabel, QComboBox,
    QSlider, QCheckBox, QToolBar, QStatusBar, QSpinBox, QGroupBox,
    QFormLayout, QMessageBox, QAction, QSizePolicy, QFileDialog,
    QDialog, QDialogButtonBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QElapsedTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPalette

# ============================================================================
# MODULE IMPORTS - Deterministic package imports
# ============================================================================
from app.core import (
    APP_ROOT,
    LOG_DIR,
    REPORT_DIR,
    VERSION,
    SAMPLE_RATE,
    BLOCK_SIZE,
    CHANNELS,
    TICK_INTERVAL_MS,
    GAME_SCAN_INTERVAL_MS,
    AUDIO_SCAN_INTERVAL_MS,
    STARTUP_DELAY_MS,
    STARTUP_AUDIO_DELAY_MS,
    ENERGY_THRESHOLD,
    LOCALIZATION_MIN_CONFIDENCE,
    RADAR_ROTATION_DEG,
    MAX_WORKERS,
    DETECTION_TIMEOUT_SEC,
    CLEANUP_INTERVAL_SEC,
    AUDIO_LEVEL_LOUD,
    AUDIO_LEVEL_MEDIUM,
    AUDIO_LEVEL_LOW,
    RECORDING_BUFFER_SIZE,
    RECORDING_FLUSH_INTERVAL,
    TOAST_DURATION_MS,
    TOAST_MAX_COUNT,
    ThreadSafeLogger,
    log,
    SUPER_LOG_FILE,
    ConfigManager,
    TRANSLATIONS,
    current_language,
    tr,
    set_language,
    get_language,
    get_build_id,
)
from app.core.export_import import ExportImportManager
from app.hardware import GPUAccelerator, SoundBlasterOptimizer
from app.utils import (
    PerformanceMonitor,
    GameProcessDetector,
    PlatformLauncherDetector,
    AudioSourceScanner,
)
from app.tracking import Target, TargetTracker, ThreatPrioritySystem
from app.detection import DetectionWorker, HumanFootstepDetector
from app.audio import (
    AudioProcessingCache,
    AudioEngine,
    SoundClassifier,
    AudioRecorder,
    HumanVoiceDetector,
    AudioProcessor,
)
from app.widgets import (
    ToastNotification,
    DetachableRadarWidget,
    RadarWidget,
    MilitaryHUDRadar,
    Military3DRadar,
    Radar3DWidget,
    DetachableLedWidget,
    LedOverlayWidget,
    SpectrumWidget,
    WaterfallWidget,
    WaveformWidget,
    MilitarySpectrumWidget,
    MilitaryWaterfallWidget,
    MilitaryWaveformWidget,
    DevicePanel,
    DetectionPanel,
)
from app.ui import UIBuilder
from app.diagnostics import SelfTestRunner

# ============================================================================
# CONFIG MANAGER - Imported from core module
# ============================================================================

# ============================================================================
# TRANSLATIONS - Imported from core module
# ============================================================================

# ============================================================================
# PATHS AND LOGGING (ENHANCED v3.5.0 - Thread-safe logging)
# ============================================================================

import logging
import logging.handlers

ROOT = APP_ROOT
SUPER_LOG = SUPER_LOG_FILE


# ThreadSafeLogger - Imported from core module


def apply_dark_theme(app: QApplication):
    """Apply dark theme to application"""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(25, 25, 35))
    palette.setColor(QPalette.WindowText, QColor(220, 220, 230))
    palette.setColor(QPalette.Base, QColor(18, 18, 28))
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 40))
    palette.setColor(QPalette.ToolTipBase, QColor(50, 50, 60))
    palette.setColor(QPalette.ToolTipText, QColor(220, 220, 230))
    palette.setColor(QPalette.Text, QColor(220, 220, 230))
    palette.setColor(QPalette.Button, QColor(45, 45, 55))
    palette.setColor(QPalette.ButtonText, QColor(220, 220, 230))
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

    app.setPalette(palette)

    stylesheet = """
        QMainWindow { background-color: #191923; }
        QWidget { background-color: #191923; color: #DCDCE6; }
        QDockWidget { background-color: #191923; color: #DCDCE6; }
        QDockWidget::title { background-color: #2D2D37; padding: 5px; }
        QPushButton {
            background-color: #2D2D37;
            color: #DCDCE6;
            border: 1px solid #2A82DA;
            border-radius: 3px;
            padding: 5px 15px;
            min-width: 80px;
        }
        QPushButton:hover { background-color: #2A82DA; }
        QPushButton:pressed { background-color: #1A5AA0; }
        QPushButton:checked { background-color: #2A82DA; }
        QComboBox, QSpinBox {
            background-color: #121218;
            color: #DCDCE6;
            border: 1px solid #2A82DA;
            border-radius: 3px;
            padding: 3px;
        }
        QSlider::groove:horizontal {
            background: #121218;
            height: 6px;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #2A82DA;
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }
        QLabel { color: #DCDCE6; background: transparent; }
        QGroupBox {
            border: 1px solid #2A82DA;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
            color: #2A82DA;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
        }
        QCheckBox { color: #DCDCE6; }
    """
    app.setStyleSheet(stylesheet)


# ============================================================================
# PERFORMANCE OPTIMIZATION (Module 12 - v3.4.0)
# ============================================================================











class _RadarDetachWindow(QMainWindow):
    """Thin wrapper that re-attaches the radar when closed."""

    def __init__(self, on_close, parent=None):
        super().__init__(parent)
        self._on_close = on_close

    def closeEvent(self, event):  # pragma: no cover - GUI interaction
        if self._on_close:
            self._on_close()
        event.accept()


class MainWindow(QMainWindow):
    """
    Main application window

    Point 11 - v3.5.0: Dependency Injection support
    Can receive dependencies via container or create them directly (backward compatible)
    """

    def __init__(self, container=None):
        super().__init__()
        log("MainWindow.__init__", "INFO")

        self.setWindowTitle(f"{tr('app_title')} {VERSION}")
        # NOTE: Window geometry is restored from config after dependencies are loaded

        # State
        self.is_running = False
        self.radar_angle = 0.0
        self.test_phase = 0.0

        # Build identifier for diagnostics (hash + UTC timestamp)
        self.build_id = get_build_id()
        log(f"BUILD_ID: {self.build_id}", "INFO")

        # Detachable windows
        self.detached_radar = None
        self.detached_led = None
        self.radar_window = None
        self.radar_placeholder = None

        # Point 11 - v3.5.0: Dependency Injection
        if container is not None:
            log("MainWindow: Using DI container for dependencies", "INFO")
            self._inject_dependencies(container)
        else:
            log("MainWindow: Creating dependencies directly (legacy mode)", "INFO")
            self._create_dependencies()

        # Configuration
        self.config = self.config_manager.load()

        # Restore window geometry from config (v4.2.0)
        self.config_manager.restore_window_state(self, self.config)

        # Toast notification system (v3.5.0 - Phase 7)
        self.toast = ToastNotification()

        self.create_ui()

        # Connect game detector to DevicePanel (FIXED v3.5.2)
        self.dev_panel.set_game_detector(self.game_detector)

        # Main update timer (20 FPS) - FIXED v3.5.0: Use constant
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(TICK_INTERVAL_MS)

        # Game detection timer (scan every 5 seconds) - FIXED v3.5.0: Use constant
        self.game_scan_timer = QTimer()
        self.game_scan_timer.timeout.connect(self.scan_games)
        self.game_scan_timer.start(GAME_SCAN_INTERVAL_MS)

        # Audio source scan timer (scan every 2 seconds) - FIXED v3.5.0: Use constant
        self.audio_scan_timer = QTimer()
        self.audio_scan_timer.timeout.connect(self.scan_audio_sources)
        self.audio_scan_timer.start(AUDIO_SCAN_INTERVAL_MS)

        # Initial scans (v3.0) - FIXED v3.5.0: Use constants
        QTimer.singleShot(STARTUP_DELAY_MS, self.scan_games)
        QTimer.singleShot(STARTUP_AUDIO_DELAY_MS, self.scan_audio_sources)

        # GUI freeze watchdog (diagnostic mode)
        self._ui_watchdog_elapsed = QElapsedTimer()
        self._ui_watchdog_elapsed.start()
        self._ui_watchdog = QTimer(self)
        self._ui_watchdog.setInterval(250)
        self._ui_watchdog.timeout.connect(self._ui_watchdog_tick)
        self._ui_watchdog.start()

    def _inject_dependencies(self, container):
        """
        Inject dependencies from DI container (Point 11 - v3.5.0)

        Args:
            container: ServiceContainer with registered dependencies
        """
        # Core
        self.config_manager = container.get('config_manager')

        # Hardware
        self.gpu_accelerator = container.get('gpu')
        self.sb_optimizer = container.get('soundblaster')

        # Audio
        self.fft_cache = container.get('audio_cache')
        self.audio = container.get('audio_engine')
        self.sound_classifier = container.get('sound_classifier')
        self.audio_recorder = container.get('audio_recorder')
        # v4.2.0: AudioProcessor - create locally if not in container
        self.audio_processor = container.get('audio_processor') if container.has('audio_processor') else AudioProcessor(sample_rate=SAMPLE_RATE)

        # Detection
        self.detection_worker = container.get('detection_worker')

        # Tracking
        self.target_tracker = container.get('target_tracker')
        self.threat_system = container.get('threat_system')

        # Utils
        self.perf_monitor = container.get('performance_monitor')
        self.game_detector = container.get('game_detector')
        self.platform_detector = container.get('launcher_detector')
        self.audio_scanner = container.get('audio_scanner')

    def _create_dependencies(self):
        """
        Create dependencies directly (legacy mode)
        Backward compatible with pre-DI code
        """
        # Configuration manager (v3.5.0 - Phase 4)
        self.config_manager = ConfigManager()
        config = self.config_manager.load()

        # Performance optimization (Module 12 - v3.4.0)
        use_gpu = config.get('performance', {}).get('use_gpu', True)
        self.gpu_accelerator = GPUAccelerator(enable_gpu=use_gpu)

        # Sound Blaster Z SE optimization (v3.5.0 - Phase 6)
        self.sb_optimizer = SoundBlasterOptimizer()

        # Audio services
        self.fft_cache = AudioProcessingCache(max_size=5, gpu_accelerator=self.gpu_accelerator)
        self.audio = AudioEngine()
        self.sound_classifier = SoundClassifier()
        self.audio_recorder = AudioRecorder(sample_rate=48000)
        self.audio_processor = AudioProcessor(sample_rate=SAMPLE_RATE)  # v4.2.0: Extracted algorithms

        # Detection
        self.detection_worker = DetectionWorker(max_workers=MAX_WORKERS)

        # Tracking
        self.target_tracker = TargetTracker(max_targets=3)
        self.threat_system = ThreatPrioritySystem()

        # Utils
        self.perf_monitor = PerformanceMonitor()
        self.game_detector = GameProcessDetector()
        self.platform_detector = PlatformLauncherDetector()
        self.audio_scanner = AudioSourceScanner(platform_detector=self.platform_detector)

    def create_ui(self):
        """
        Create modern tabbed UI (v4.2.0 - Refactored with UIBuilder).

        Delegates UI construction to UIBuilder class, reducing MainWindow complexity.
        All widgets are still accessible via self.widget_name for backward compatibility.
        """
        ui_builder = UIBuilder(self)
        ui_builder.build()

    def toggle_language(self):
        """Toggle between EN and PL (FIXED v3.5.2: Use get_language function)"""
        current_lang = get_language()

        if current_lang == 'en':
            set_language('pl')
        else:
            set_language('en')

        log(f"Language changed to: {get_language()}", "INFO")
        self.update_ui_translations()

    def update_ui_translations(self):
        """Update all UI text with current language (FIXED v3.5.2: Use get_language function)"""
        lang = get_language()

        # Main window
        self.setWindowTitle(f"{tr('app_title')} {VERSION}")

        # Start/Stop button
        if not self.is_running:
            self.start_btn.setText("▶ START")
        else:
            self.start_btn.setText("⏹ STOP")

        # Status bar
        if not self.is_running:
            self.status_bar.showMessage("✓ Ready - All systems operational" if lang == 'en' else "✓ Gotowy - Wszystkie systemy sprawne")
        else:
            self.status_bar.showMessage("● RUNNING - Detection active" if lang == 'en' else "● DZIAŁA - Detekcja aktywna")

        if hasattr(self, 'test_btn'):
            self.test_btn.setText(tr('self_test'))
            self.test_btn.setToolTip(tr('self_test_title'))

    def launch_self_test(self):
        """Run internal self-test and show summary dialog."""
        lang = get_language()
        if hasattr(self, 'test_btn'):
            self.test_btn.setEnabled(False)

        def worker():
            error: Optional[Exception] = None
            results = []
            report_path = None
            try:
                runner = SelfTestRunner(config_manager=self.config_manager)
                results, report_path = runner.run_quick()
            except Exception as exc:  # pragma: no cover - defensive
                error = exc

            def finish():
                if hasattr(self, 'test_btn'):
                    self.test_btn.setEnabled(True)
                if error:
                    QMessageBox.critical(self, tr('self_test_title'), str(error))
                    return
                failed = [r for r in results if not r.success]
                if failed:
                    msg = f"{tr('self_test_failure')}\n{tr('self_test_report').format(path=report_path)}"
                    QMessageBox.warning(self, tr('self_test_title'), msg)
                else:
                    msg = f"{tr('self_test_success')}\n{tr('self_test_report').format(path=report_path)}"
                    QMessageBox.information(self, tr('self_test_title'), msg)

            QTimer.singleShot(0, finish)

        threading.Thread(target=worker, daemon=True).start()

        # Update language button to show current language
        if hasattr(self, 'lang_btn'):
            self.lang_btn.setText("🇬🇧 EN" if lang == 'en' else "🇵🇱 PL")
            self.lang_btn.setChecked(lang == 'pl')

        # Update panels
        self.dev_panel.update_translations()
        self.det_panel.update_translations()

        # Update detached windows titles
        if self.detached_radar:
            self.detached_radar.setWindowTitle(f"{tr('radar')} - RadarSuite {VERSION}")

        if self.detached_led:
            self.detached_led.setWindowTitle(f"{tr('led_alert')} - RadarSuite {VERSION}")

    # ========================================================================
    # EXPORT/IMPORT METHODS (v4.2.1 - ZADANIE 5)
    # ========================================================================

    def show_export_dialog(self):
        """Show export dialog for configuration/models/sessions."""
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('export') if callable(tr) else "Export")
        dialog.setMinimumWidth(350)

        layout = QVBoxLayout()

        # Export type selection
        group = QGroupBox(tr('export') if callable(tr) else "Export Type")
        group_layout = QVBoxLayout()

        self._export_type_group = QButtonGroup()

        radio_config = QRadioButton(tr('export_config_file') if callable(tr) else "Configuration")
        radio_config.setChecked(True)
        self._export_type_group.addButton(radio_config, 0)
        group_layout.addWidget(radio_config)

        radio_model = QRadioButton(tr('export_ml_model') if callable(tr) else "ML Model")
        self._export_type_group.addButton(radio_model, 1)
        group_layout.addWidget(radio_model)

        radio_session = QRadioButton(tr('export_session') if callable(tr) else "Training Session")
        self._export_type_group.addButton(radio_session, 2)
        group_layout.addWidget(radio_session)

        group.setLayout(group_layout)
        layout.addWidget(group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            export_type = self._export_type_group.checkedId()
            self._perform_export(export_type)

    def _perform_export(self, export_type: int):
        """Perform the export operation."""
        export_manager = ExportImportManager(
            config_manager=self.config_manager
        )

        if export_type == 0:  # Configuration
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                tr('save_file_as') if callable(tr) else "Save Configuration",
                "",
                export_manager.get_file_filter("config")
            )
            if file_path:
                config = self.config_manager.load()
                result = export_manager.export_config(config, file_path)
                if result.success:
                    QMessageBox.information(
                        self,
                        tr('success'),
                        f"{tr('export_success')}\n{result.file_path}"
                    )
                else:
                    QMessageBox.warning(self, tr('error'), result.error_message)

        elif export_type == 1:  # ML Model
            # Find available models
            models_dir = ROOT / "models"
            if not models_dir.exists():
                QMessageBox.warning(
                    self,
                    tr('warning'),
                    "No models directory found."
                )
                return

            model_files = list(models_dir.glob("*.pkl"))
            if not model_files:
                QMessageBox.warning(
                    self,
                    tr('warning'),
                    "No trained models found in models directory."
                )
                return

            # Simple selection - use first model for now
            # TODO: Add model selection dialog
            model_path = str(model_files[0])

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                tr('save_file_as') if callable(tr) else "Save Model",
                "",
                export_manager.get_file_filter("model")
            )
            if file_path:
                result = export_manager.export_model(model_path, file_path)
                if result.success:
                    QMessageBox.information(
                        self,
                        tr('success'),
                        f"{tr('export_success')}\n{result.file_path}"
                    )
                else:
                    QMessageBox.warning(self, tr('error'), result.error_message)

        elif export_type == 2:  # Session
            QMessageBox.information(
                self,
                tr('warning'),
                "Session export requires ML Training panel.\nUse ML Training tab to manage sessions."
            )

    def show_import_dialog(self):
        """Show import dialog for configuration/models/sessions."""
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('import') if callable(tr) else "Import")
        dialog.setMinimumWidth(350)

        layout = QVBoxLayout()

        # Import type selection
        group = QGroupBox(tr('import') if callable(tr) else "Import Type")
        group_layout = QVBoxLayout()

        self._import_type_group = QButtonGroup()

        radio_config = QRadioButton(tr('import_config_file') if callable(tr) else "Configuration")
        radio_config.setChecked(True)
        self._import_type_group.addButton(radio_config, 0)
        group_layout.addWidget(radio_config)

        radio_model = QRadioButton(tr('import_ml_model') if callable(tr) else "ML Model")
        self._import_type_group.addButton(radio_model, 1)
        group_layout.addWidget(radio_model)

        radio_session = QRadioButton(tr('import_session') if callable(tr) else "Training Session")
        self._import_type_group.addButton(radio_session, 2)
        group_layout.addWidget(radio_session)

        group.setLayout(group_layout)
        layout.addWidget(group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            import_type = self._import_type_group.checkedId()
            self._perform_import(import_type)

    def _perform_import(self, import_type: int):
        """Perform the import operation."""
        export_manager = ExportImportManager(
            config_manager=self.config_manager
        )

        if import_type == 0:  # Configuration
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                tr('select_file') if callable(tr) else "Select Configuration File",
                "",
                export_manager.get_file_filter("config")
            )
            if file_path:
                result, config = export_manager.import_config(file_path)
                if result.success and config:
                    # Apply configuration
                    self.config_manager.save(config)
                    self._apply_imported_config(config)

                    msg = tr('import_success')
                    if result.warnings:
                        msg += "\n\nWarnings:\n" + "\n".join(result.warnings)

                    QMessageBox.information(self, tr('success'), msg)
                else:
                    QMessageBox.warning(self, tr('error'), result.error_message)

        elif import_type == 1:  # ML Model
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                tr('select_file') if callable(tr) else "Select Model File",
                "",
                export_manager.get_file_filter("model")
            )
            if file_path:
                models_dir = ROOT / "models"
                models_dir.mkdir(parents=True, exist_ok=True)

                result, model_path = export_manager.import_model(file_path, str(models_dir))
                if result.success:
                    msg = f"{tr('import_success')}\nModel: {model_path}"
                    if result.warnings:
                        msg += "\n\nWarnings:\n" + "\n".join(result.warnings)

                    QMessageBox.information(self, tr('success'), msg)
                else:
                    QMessageBox.warning(self, tr('error'), result.error_message)

        elif import_type == 2:  # Session
            QMessageBox.information(
                self,
                tr('warning'),
                "Session import requires ML Training panel.\nUse ML Training tab to manage sessions."
            )

    def _apply_imported_config(self, config: dict):
        """Apply imported configuration to UI and settings."""
        log("Applying imported configuration", "INFO")

        # Audio settings
        audio_cfg = config.get('audio', {})
        if hasattr(self, 'dev_panel'):
            if 'gain' in audio_cfg:
                self.dev_panel.gain_slider.setValue(int(audio_cfg['gain'] * 10))
            if 'noise_gate' in audio_cfg:
                self.dev_panel.noise_gate_slider.setValue(int(audio_cfg['noise_gate']))
            if 'auto_gain' in audio_cfg:
                self.dev_panel.auto_gain_check.setChecked(audio_cfg['auto_gain'])

        # Detection settings
        detection_cfg = config.get('detection', {})
        if hasattr(self, 'det_panel'):
            if 'walk_threshold' in detection_cfg:
                self.det_panel.walk_sens.setValue(int(detection_cfg['walk_threshold']))
            if 'run_threshold' in detection_cfg:
                self.det_panel.run_sens.setValue(int(detection_cfg['run_threshold']))
            if 'shot_threshold' in detection_cfg:
                self.det_panel.shot_sens.setValue(int(detection_cfg['shot_threshold']))
            if 'walk_enabled' in detection_cfg:
                self.det_panel.detect_walk_check.setChecked(detection_cfg['walk_enabled'])
            if 'run_enabled' in detection_cfg:
                self.det_panel.detect_run_check.setChecked(detection_cfg['run_enabled'])
            if 'shot_enabled' in detection_cfg:
                self.det_panel.detect_shot_check.setChecked(detection_cfg['shot_enabled'])

        # UI settings
        ui_cfg = config.get('ui', {})
        if 'language' in ui_cfg:
            set_language(ui_cfg['language'])
            self.update_ui_translations()

        log("Configuration applied successfully", "INFO")

    def setup_shortcuts(self):
        """
        Setup keyboard shortcuts (v3.5.0 - Phase 8)

        Shortcuts:
            Ctrl+S: Start/Stop
            Ctrl+R: Reset radar
            Ctrl+1/2/3/4: Switch tabs
            Space: Quick mute (toggle audio)
            F11: Fullscreen
        """
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence

        # Ctrl+S: Start/Stop
        shortcut_startstop = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_startstop.activated.connect(self.toggle_start_stop_shortcut)

        # Ctrl+R: Reset radar
        shortcut_reset = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_reset.activated.connect(self.reset_radar)

        # Ctrl+1: Switch to Radar tab (FIXED v4.1.0: was self.tabs, now self.main_tabs)
        shortcut_tab1 = QShortcut(QKeySequence("Ctrl+1"), self)
        shortcut_tab1.activated.connect(lambda: self.main_tabs.setCurrentIndex(0))

        # Ctrl+2: Switch to Detection tab
        shortcut_tab2 = QShortcut(QKeySequence("Ctrl+2"), self)
        shortcut_tab2.activated.connect(lambda: self.main_tabs.setCurrentIndex(1))

        # Ctrl+3: Switch to Game Detection tab
        shortcut_tab3 = QShortcut(QKeySequence("Ctrl+3"), self)
        shortcut_tab3.activated.connect(lambda: self.main_tabs.setCurrentIndex(2))

        # Ctrl+4: Switch to Analysis tab
        shortcut_tab4 = QShortcut(QKeySequence("Ctrl+4"), self)
        shortcut_tab4.activated.connect(lambda: self.main_tabs.setCurrentIndex(3) if self.main_tabs.count() > 3 else None)

        # Space: Quick mute toggle
        shortcut_mute = QShortcut(QKeySequence("Space"), self)
        shortcut_mute.activated.connect(self.quick_mute_toggle)

        # F11: Fullscreen toggle
        shortcut_fullscreen = QShortcut(QKeySequence("F11"), self)
        shortcut_fullscreen.activated.connect(self.toggle_fullscreen)

        log("Keyboard shortcuts initialized", "INFO")

    def toggle_start_stop_shortcut(self):
        """Toggle start/stop via keyboard shortcut (with toast notification)"""
        if self.is_running:
            self.stop()
            self.toast.show_toast("Audio detection stopped", "info", 2000)
        else:
            self.start()
            self.toast.show_toast("Audio detection started", "success", 2000)

    def reset_radar(self):
        """Reset radar display"""
        # Reset radar angle
        self.radar_angle = 0.0
        self.toast.show_toast("Radar reset", "info", 1500)
        log("Radar reset via keyboard shortcut", "INFO")

    def quick_mute_toggle(self):
        """Quick mute toggle (Space key)"""
        # Stop/start audio without changing UI state
        if self.is_running:
            self.audio.stop()
            self.toast.show_toast("Audio muted", "warning", 1500)
            log("Audio muted via keyboard shortcut", "INFO")
        else:
            self.audio.start()
            self.toast.show_toast("Audio unmuted", "success", 1500)
            log("Audio unmuted via keyboard shortcut", "INFO")

    def toggle_fullscreen(self):
        """Toggle fullscreen mode (F11)"""
        if self.isFullScreen():
            self.showNormal()
            self.toast.show_toast("Exited fullscreen", "info", 1500)
        else:
            self.showFullScreen()
            self.toast.show_toast("Entered fullscreen (F11 to exit)", "info", 2000)

    def _ui_watchdog_tick(self):
        """Detect long event-loop stalls and surface diagnostic context."""
        if not self._ui_watchdog_elapsed.isValid():
            self._ui_watchdog_elapsed.start()

        elapsed = self._ui_watchdog_elapsed.elapsed()
        self._ui_watchdog_elapsed.restart()
        delay = elapsed - self._ui_watchdog.interval()
        if delay > 1500:
            recording_state = getattr(self, 'recording_controller', None)
            is_recording = False
            elapsed_sec = 0.0
            if recording_state is not None:
                try:
                    state = recording_state.state
                    is_recording = bool(state.is_recording)
                    elapsed_sec = float(state.elapsed_sec)
                except Exception:
                    pass

            overlay = getattr(self, 'ml_quick_overlay', None)
            overlay_visible = bool(overlay and overlay.isVisible())

            log(
                f"GUI_STALL detected: {int(delay)} ms | recording={is_recording} "
                f"(elapsed={elapsed_sec:.2f}s) | overlay_visible={overlay_visible} | "
                f"threads={threading.active_count()}",
                "WARNING",
            )

    def update_radar_alpha(self, value):
        """Update radar opacity"""
        opacity = value / 100.0

        if self.detached_radar:
            self.detached_radar.set_opacity(opacity)

    def update_led_alpha(self, value):
        """Update LED opacity"""
        opacity = value / 100.0

        if self.detached_led:
            self.detached_led.set_opacity(opacity)
        else:
            self.led_widget.global_alpha = opacity

    def _safe_update_detached_radar(self, method_name, *args):
        """
        Safely update detached radar (FIXED v4.1.2: Updated for MinimalRadarWidget)

        Prevents AttributeError when detached_radar or detached_radar.radar_widget is None

        Args:
            method_name: Method name to call on detached_radar.radar_widget
            *args: Arguments to pass to method
        """
        if not self.detached_radar:
            return

        if not hasattr(self.detached_radar, 'radar_widget'):
            log(f"Detached radar missing 'radar_widget' attribute", "WARNING")
            return

        if self.detached_radar.radar_widget is None:
            log(f"Detached radar.radar_widget is None", "WARNING")
            return

        try:
            method = getattr(self.detached_radar.radar_widget, method_name)
            method(*args)
        except AttributeError as e:
            log(f"Method '{method_name}' not found on detached radar: {e}", "WARNING")
        except Exception as e:
            log(f"Error updating detached radar.{method_name}: {e}", "ERROR")

    def _ensure_detached_radar(self):
        if self.detached_radar is None:
            self.detached_radar = DetachableRadarWidget()

    def _handle_radar_window_closed(self):
        if self.detach_radar_btn.isChecked():
            self.detach_radar_btn.setChecked(False)
        self._attach_radar()

    def _detach_radar(self):
        self._ensure_detached_radar()
        if self.radar_window is None:
            self.radar_window = _RadarDetachWindow(self._handle_radar_window_closed, self)
            self.radar_window.setWindowTitle(f"{tr('radar')} - {VERSION}")
        if self.radar_window.centralWidget() is None:
            self.radar_window.setCentralWidget(self.detached_radar)
        self.detached_radar.set_opacity(self.radar_alpha.value() / 100.0)
        self.radar_window.show()
        self.radar_window.raise_()
        log("Radar detached", "INFO")

    def _attach_radar(self):
        if self.radar_window:
            self.radar_window.hide()
            if self.radar_window.centralWidget():
                self.radar_window.takeCentralWidget()
        if self.detached_radar:
            self.detached_radar.hide()
            self.detached_radar.setParent(None)
        if hasattr(self, 'detach_radar_btn') and self.detach_radar_btn.isChecked():
            self.detach_radar_btn.setChecked(False)
        log("Radar attached", "INFO")

    def toggle_detach_radar(self, checked):
        """Toggle radar detachment without duplicating widgets."""
        if checked:
            self._detach_radar()
        else:
            self._attach_radar()

    def toggle_detach_led(self, checked):
        """Toggle LED detachment"""
        if checked:
            # Create detached LED
            self.detached_led = DetachableLedWidget()
            self.detached_led.set_opacity(self.led_alpha.value() / 100.0)
            self.detached_led.show()
            log("LED detached", "INFO")
        else:
            # Close detached LED
            if self.detached_led:
                self.detached_led.close()
                self.detached_led = None
            log("LED attached", "INFO")

    def toggle_radar_frameless(self, checked):
        """Toggle radar frameless mode"""
        if self.detached_radar:
            self.detached_radar.set_frameless(checked)

    def toggle_led_frameless(self, checked):
        """Toggle LED frameless mode"""
        if self.detached_led:
            self.detached_led.set_frameless(checked)

    def toggle_start_stop(self):
        """Toggle audio capture"""
        if not self.is_running:
            self.start()
        else:
            self.stop()

    def toggle_recording(self):
        """Toggle audio recording (Module 9 - v3.3.0)"""
        if not self.audio_recorder.is_recording:
            # Start recording
            self.audio_recorder.start_recording()
            self.record_btn.setText("⏹ STOP REC")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background: #00aa00;
                    color: white;
                    font-weight: bold;
                    padding: 8px 15px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #00cc00;
                }
            """)
            log("Recording started", "INFO")
        else:
            # Stop recording and save
            self.audio_recorder.stop_recording()

            # Generate filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"RadarSuite_Recording_{timestamp}.wav"

            # Save to file
            if self.audio_recorder.save_to_wav(filename):
                self.status_bar.showMessage(f"✓ Recording saved: {filename}")
            else:
                self.status_bar.showMessage("❌ Failed to save recording")

            # Reset button
            self.record_btn.setText("⏺ REC")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background: #aa0000;
                    color: white;
                    font-weight: bold;
                    padding: 8px 15px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #cc0000;
                }
            """)

            log(f"Recording saved to {filename}", "INFO")

    def start(self):
        """Start audio capture"""
        log("Starting audio capture", "INFO")

        self.dev_panel.apply_settings()
        self.audio.start()

        self.is_running = True
        self.record_btn.setEnabled(True)  # Enable recording when audio starts

        # Update audio status indicator (FIXED v3.5.3)
        self.dev_panel.update_audio_init_status(True, False)
        self.start_btn.setText("⏹ STOP")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #aa0000;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: #cc0000;
            }
        """)
        self.status_bar.showMessage("● RUNNING - Detection active" if get_language() == 'en' else "● DZIAŁA - Detekcja aktywna")

    def stop(self):
        """Stop audio capture"""
        log("Stopping audio capture", "INFO")

        self.audio.stop()

        self.is_running = False

        # Update audio status indicator (FIXED v3.5.3)
        self.dev_panel.update_audio_init_status(False, False)

        # FIXED v3.5.3: Reset detection labels and clear radars on stop
        self.det_panel.reset_detection()
        self.radar_widget.update_target(None, None)
        self.radar_3d_widget.clear_targets()
        self.target_tracker.clear()
        self.dev_panel.rms_label.setText("RMS: --- dBFS")

        self.start_btn.setText("▶ START")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #00aa00;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: #00cc00;
            }
        """)
        self.status_bar.showMessage("✓ Stopped - Ready to start" if get_language() == 'en' else "✓ Zatrzymano - Gotowy do startu")

    def _update_radar_sweep(self):
        """
        Update radar sweep angle and all radar widgets (FIXED v3.5.0: Helper method)
        """
        self.radar_angle = (self.radar_angle + RADAR_ROTATION_DEG) % 360.0
        self.radar_widget.update_sweep(self.radar_angle)
        self.radar_3d_widget.update_sweep(self.radar_angle)
        self._safe_update_detached_radar('update_sweep', self.radar_angle)

    def _acquire_audio_block(self):
        """
        Acquire audio block from test mode or real audio input (FIXED v3.5.0: Helper method)

        Returns:
            Audio block (numpy array) or None if not available
        """
        if self.dev_panel.test_mode.isChecked():
            return self.generate_test_block()
        else:
            # FIXED v3.5.3: Avoid numpy array truth value ambiguity
            block = self.audio.read_block(0.0)
            if block is not None:
                return block
            # FIXED v4.2.1-k0004: Use thread-safe getter
            return self.audio.get_last_block()

    def _update_recording(self, block):
        """
        Update audio recording and duration display (FIXED v3.5.0: Helper method)

        Args:
            block: Audio block to record
        """
        if self.audio_recorder.is_recording:
            self.audio_recorder.add_block(block)
            duration = self.audio_recorder.get_duration()
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            self.record_duration_label.setText(f"{minutes}:{seconds:02d}")

    def _process_audio_visualizations(self, block, fft_result):
        """
        Update spectrum, waterfall, and waveform visualizations (FIXED v3.5.0: Helper method)

        Args:
            block: Audio block (numpy array)
            fft_result: Cached FFT computation result
        """
        # Update spectrum with cached FFT (eliminates duplicate computation)
        self.spectrum.update_from_cache(fft_result)
        self.waveform.update_waveform(block)

        # Update waterfall with cached FFT power
        power = 20 * np.log10(fft_result['power'] + 1e-10)
        self.waterfall.push_row(power)

    def _process_audio_level_monitoring(self, energy):
        """
        Monitor and display audio levels with color coding (FIXED v3.5.0: Helper method)

        Args:
            energy: Audio energy (RMS)
        """
        if energy > 0:
            rms_db = 20 * np.log10(energy + 1e-10)
            self.dev_panel.rms_label.setText(f"{tr('rms')} {rms_db:.1f} dBFS")

            # Color-coded audio level indicator
            if rms_db > AUDIO_LEVEL_LOUD:
                level_color = "#00FF00"  # Green - loud
                level_status = "🔊 LOUD"
            elif rms_db > AUDIO_LEVEL_MEDIUM:
                level_color = "#FFFF00"  # Yellow - medium
                level_status = "🔉 OK"
            elif rms_db > AUDIO_LEVEL_LOW:
                level_color = "#FF8800"  # Orange - quiet
                level_status = "🔈 LOW"
            else:
                level_color = "#FF0000"  # Red - very quiet
                level_status = "🔇 SILENT"

            self.dev_panel.rms_label.setStyleSheet(f"color: {level_color}; font-weight: bold; font-size: 10pt;")
        else:
            self.dev_panel.rms_label.setText(f"{tr('rms')} --- dBFS (NO AUDIO!)")
            self.dev_panel.rms_label.setStyleSheet("color: #FF0000; font-weight: bold; font-size: 10pt;")

    def _process_detection_and_tracking(self, block, fft_result, energy):
        """
        Perform detection, 3D localization, classification, and tracking (FIXED v3.5.0: Helper method)
        FIXED v4.2.0: Use DetectionWorker for parallel processing with proper error handling

        Args:
            block: Audio block (numpy array)
            fft_result: Cached FFT computation result
            energy: Audio energy (RMS)

        Returns:
            Tuple of (events, bands, active_targets)
        """
        # FIXED v4.2.0: Use DetectionWorker for parallel detection (offload from main thread)
        detection_future = self.detection_worker.submit_detection(
            self.det_panel, block, self.audio.sample_rate, fft_result
        )

        # Handle detection result
        if detection_future:
            try:
                # Wait for detection to complete (max 1 second)
                detection_result = detection_future.result(timeout=1.0)

                if detection_result.success:
                    events = detection_result.data['events']
                    bands = detection_result.data['bands']
                else:
                    # Detection failed - log and use defaults
                    log(f"Detection worker returned error: {detection_result.error}", "WARNING")
                    events = {'walk': False, 'run': False, 'shot': False}
                    bands = {}
            except TimeoutError:
                log("Detection worker timed out (>1s) - skipping frame", "WARNING")
                events = {'walk': False, 'run': False, 'shot': False}
                bands = {}
            except Exception as e:
                log(f"Unexpected error getting detection result: {e}", "ERROR")
                events = {'walk': False, 'run': False, 'shot': False}
                bands = {}
        else:
            # Worker rejected task (backpressure or shutdown)
            log("DetectionWorker rejected task (backpressure or shutdown)", "DEBUG")
            events = {'walk': False, 'run': False, 'shot': False}
            bands = {}

        # Multi-target tracking
        has_detection = events.get('walk', False) or events.get('run', False) or events.get('shot', False)

        # Prepare detections for tracker
        detections = []
        if has_detection and energy > ENERGY_THRESHOLD:
            # Use precise 3D localization (Module 6)
            location_3d = self.compute_precise_location_3d(block, self.audio.sample_rate)

            # FIXED v4.1.1: Filter low-confidence localizations to reduce radar chaos
            if location_3d['confidence'] < LOCALIZATION_MIN_CONFIDENCE:
                # Skip low-confidence detections
                return events, bands, self.target_tracker.get_active_targets()

            angle = location_3d['angle']
            distance = location_3d['distance']
            elevation = location_3d['elevation']

            # FIXED v4.2.0: Use DetectionWorker for parallel classification
            classification_future = self.detection_worker.submit_classification(
                self.sound_classifier, block, self.audio.sample_rate, fft_result
            )

            # Handle classification result
            if classification_future:
                try:
                    # Wait for classification to complete (max 1 second)
                    classification_result = classification_future.result(timeout=1.0)

                    if classification_result.success:
                        sound_class = classification_result.data
                    else:
                        log(f"Classification worker returned error: {classification_result.error}", "WARNING")
                        sound_class = {'type': 'unknown', 'confidence': 0, 'details': {}}
                except TimeoutError:
                    log("Classification worker timed out (>1s) - using unknown", "WARNING")
                    sound_class = {'type': 'unknown', 'confidence': 0, 'details': {}}
                except Exception as e:
                    log(f"Unexpected error getting classification result: {e}", "ERROR")
                    sound_class = {'type': 'unknown', 'confidence': 0, 'details': {}}
            else:
                # Worker rejected task
                log("DetectionWorker rejected classification task", "DEBUG")
                sound_class = {'type': 'unknown', 'confidence': 0, 'details': {}}

            # FIXED v4.1.2: Improved detection type classification
            # Prioritize classification, but distinguish walk vs run
            if sound_class['confidence'] > 50:
                target_type = sound_class['type']
            elif events.get('shot', False):
                target_type = 'shot'
            elif events.get('run', False):
                target_type = 'run'  # FIXED: Distinguish run from walk
            elif events.get('walk', False):
                target_type = 'walk'  # FIXED: Keep walk separate
            else:
                target_type = 'unknown'

            detections.append({
                'angle': angle,
                'distance': distance,
                'elevation': elevation,
                'type': target_type,
                'sound_class': sound_class['type'],
                'class_confidence': sound_class['confidence']
            })

        # Update tracker
        active_targets = self.target_tracker.update(detections)

        # Rank targets by threat priority (Module 8)
        if active_targets:
            active_targets = self.threat_system.rank_targets(active_targets)

        return events, bands, active_targets

    def _map_target_type_to_state(self, target_type):
        """
        FIXED v4.1.2: Map target type string to TargetState enum for 2D radar display

        Args:
            target_type: String type ('walk', 'run', 'shot', 'rifle', 'unknown', etc.)

        Returns:
            TargetState constant (WALK, RUN, SHOT, or UNKNOWN)
        """
        from widgets.radar import TargetState

        # FIXED v4.1.2: Map detection types to radar states with proper walk/run distinction
        if target_type in ['walk', 'footstep']:
            return TargetState.WALK
        elif target_type == 'run':
            return TargetState.RUN
        elif target_type in ['shot', 'rifle', 'pistol', 'shotgun', 'sniper']:
            return TargetState.SHOT
        else:
            return TargetState.UNKNOWN

    def _update_ui_elements(self, active_targets, events, bands, energy, balance):
        """
        Update all UI elements: radars, LEDs, toolbar stats (FIXED v3.5.0: Helper method)

        Args:
            active_targets: List of tracked targets
            events: Detection events dictionary
            bands: Frequency bands data
            energy: Audio energy (RMS)
            balance: L/R audio balance
        """
        # FIXED v4.1.2: Update radars with all active targets (threat-ranked)
        if active_targets:
            # Update 3D radar (supports multiple targets)
            self.radar_3d_widget.clear_targets()
            for target in active_targets:
                # FIXED v3.5.3: Correct parameter order for add_target
                self.radar_3d_widget.add_target(
                    target['id'],           # target_id
                    target['angle'],        # angle
                    target['distance'],     # distance
                    target['elevation']     # elevation
                )

            # FIXED v4.1.2: Update 2D radar with ALL targets, not just primary
            self.radar_widget.clear_targets()
            for target in active_targets:
                # Map target type to TargetState for 2D radar display
                target_state = self._map_target_type_to_state(target['type'])
                self.radar_widget.add_target(
                    target['id'],           # target_id
                    target['angle'],        # angle
                    target['distance'],     # distance
                    state=target_state,     # state (WALK/RUN/SHOT/UNKNOWN)
                    speed=0,                # speed (not yet calculated)
                    label=f"T{target['id']}" # label
                )

            # Update detached radar if exists
            if self.detached_radar:
                self.detached_radar.radar_widget.clear_targets()
                for target in active_targets:
                    target_state = self._map_target_type_to_state(target['type'])
                    self.detached_radar.radar_widget.add_target(
                        target['id'], target['angle'], target['distance'],
                        state=target_state, speed=0, label=f"T{target['id']}"
                    )

            # FIXED v4.2.0: Defensive cleanup of stale targets from radar UI
            # This catches any targets that weren't properly removed by the tracker
            self.radar_widget.cleanup_stale_targets(max_age_seconds=3.0)
            if self.detached_radar:
                self.detached_radar.radar_widget.cleanup_stale_targets(max_age_seconds=3.0)
        else:
            # FIXED v4.2.1: Clear all radars when no active_targets (was incorrectly tied to detached_radar check)
            self.radar_widget.clear_targets()
            self.radar_3d_widget.clear_targets()
            if self.detached_radar:
                self.detached_radar.radar_widget.clear_targets()

        # Update LED overlays
        self.led_widget.update_from_events(events, bands, energy, balance)
        if self.detached_led:
            self.detached_led.led_overlay.update_from_events(events, bands, energy, balance)

        # Update toolbar stats with real performance metrics
        target_count = len(active_targets) if active_targets else 0
        if energy > 0:
            rms_db = 20 * np.log10(energy + 1e-10)
            audio_indicator = "🔊" if rms_db > -40 else "🔉" if rms_db > -60 else "🔇"
        else:
            audio_indicator = "❌"
            rms_db = -100

        # Performance monitoring - end frame and update stats
        self.perf_monitor.end_frame()
        self.perf_monitor.update()
        perf_stats = self.perf_monitor.get_stats()

        self.toolbar_stats_label.setText(
            f"Targets: {target_count} | Audio: {audio_indicator} {rms_db:.0f}dB | FPS: {perf_stats['fps']:.1f} | Latency: {perf_stats['latency_ms']:.1f}ms"
        )

    def tick(self):
        """
        Main update loop (FIXED v3.5.0: Refactored with helper methods)

        Performance optimizations:
        - Module 12 (v3.4.0): Cached FFT computation
        - v3.5.0: Split into focused helper methods for maintainability
        """
        try:
            # Start performance monitoring
            self.perf_monitor.start_frame()

            # 1. Update radar sweep
            self._update_radar_sweep()

            # 2. Acquire and process audio block
            block = self._acquire_audio_block()
            if block is None:
                # FIXED v3.5.3: Update UI even when no audio block
                if hasattr(self, 'audio_scanner') and self.audio_scanner:
                    self.audio_scanner.report_audio_activity(False)
                # Update status to show no audio
                self.dev_panel.update_audio_init_status(self.is_running, False)
                self.dev_panel.rms_label.setText("RMS: --- dBFS")
                self.perf_monitor.end_frame()
                return
            block = self.apply_audio_processing(block)

            # 2b. Report audio activity to scanner (v3.5.1)
            if hasattr(self, 'audio_scanner') and self.audio_scanner:
                has_audio = np.max(np.abs(block)) > 0.001  # Check if there's actual audio
                self.audio_scanner.report_audio_activity(has_audio)

            # 2c. Update audio status indicator (FIXED v3.5.3)
            has_audio_signal = np.max(np.abs(block)) > 0.001
            self.dev_panel.update_audio_init_status(True, has_audio_signal)

            # 3. Update recording
            self._update_recording(block)

            # 3b. FIXED v4.2.1: Feed audio to ML Training panel for labeled recording
            if hasattr(self, 'ml_training_panel') and self.ml_training_panel is not None:
                self.ml_training_panel.feed_audio(block)

            # 4. Compute FFT once and cache (Module 12 - eliminates 4 redundant computations!)
            fft_result = self.fft_cache.compute_fft(block, self.audio.sample_rate)

            # 5. Update audio visualizations
            self._process_audio_visualizations(block, fft_result)

            # 6. Compute energy and balance
            energy, balance = self.compute_orientation(block)

            # 7. Monitor audio levels
            self._process_audio_level_monitoring(energy)

            # 8. Detection, classification, and tracking
            events, bands, active_targets = self._process_detection_and_tracking(block, fft_result, energy)

            # 9. Update UI elements (radars, LEDs, toolbar stats)
            self._update_ui_elements(active_targets, events, bands, energy, balance)

        except Exception as e:
            # CRITICAL ERROR HANDLING: Prevent application freeze if tick() crashes
            log(f"CRITICAL ERROR in tick(): {e}", "ERROR")
            import traceback
            log(traceback.format_exc(), "ERROR")
            # Don't crash - just skip this frame and continue running

    def apply_audio_processing(self, block):
        """
        Apply audio enhancements: auto-gain, manual gain, noise gate (v4.2.0 - delegates to AudioProcessor)

        Args:
            block: Audio data (numpy array)

        Returns:
            Processed audio block
        """
        try:
            if block is None or len(block) == 0:
                return block

            # Get parameters from UI
            noise_gate_value = self.dev_panel.noise_gate_slider.value()
            noise_gate_db = -80 + noise_gate_value  # Convert slider (0-100) to dB (-80 to -20)
            auto_gain = self.dev_panel.auto_gain_enable.isChecked()
            manual_gain = float(self.dev_panel.gain_slider.value())

            # Delegate to AudioProcessor (v4.2.0)
            processed = self.audio_processor.apply_processing(
                block,
                auto_gain=auto_gain,
                manual_gain=manual_gain,
                noise_gate_db=noise_gate_db
            )

            # Update UI label for auto-gain display
            if auto_gain and processed is not None:
                current_rms = np.sqrt(np.mean(block ** 2)) + 1e-10
                target_rms = 0.1
                gain_applied = min(100.0, max(1.0, target_rms / current_rms))
                self.dev_panel.gain_label.setText(f"AUTO: {gain_applied:.1f}x")

            return processed

        except Exception as e:
            log(f"Error in apply_audio_processing: {e}", "ERROR")
            return block

    def compute_orientation(self, block):
        """
        Compute energy and L/R balance (v4.2.0 - delegates to AudioProcessor)
        """
        return self.audio_processor.compute_orientation(block)

    def compute_precise_location_3d(self, block, sample_rate):
        """
        Advanced 3D sound localization using ITD and ILD (Module 6 - v3.2.0)

        Uses:
        - ITD (Interaural Time Difference): Cross-correlation between L/R channels
        - ILD (Interaural Level Difference): Volume difference between L/R channels
        - Frequency analysis for elevation

        Returns: dict with angle, distance, elevation, confidence
        """
        try:
            if block is None or len(block) == 0:
                return {'angle': 0, 'distance': 50, 'elevation': 0, 'confidence': 0}

            # Ensure stereo
            if block.ndim != 2 or block.shape[1] < 2:
                return {'angle': 0, 'distance': 50, 'elevation': 0, 'confidence': 0}

            left = block[:, 0]
            right = block[:, 1]

            # === ITD (Time Difference) using Cross-Correlation ===
            # Cross-correlate left and right channels
            correlation = np.correlate(left, right, mode='full')
            center = len(correlation) // 2

            # Find peak correlation (time delay)
            # Limit search to ±1ms (realistic head size)
            max_delay_samples = int(0.001 * sample_rate)  # 1ms
            search_range = slice(center - max_delay_samples, center + max_delay_samples)
            local_corr = correlation[search_range]

            if len(local_corr) > 0:
                peak_idx = np.argmax(np.abs(local_corr))
                time_delay_samples = peak_idx - max_delay_samples

                # Convert time delay to azimuth angle
                # Speed of sound: 343 m/s, head diameter: ~0.18m
                # Max ITD: ~0.52ms (90° left/right)
                max_itd_seconds = 0.00052
                max_itd_samples = max_itd_seconds * sample_rate

                if max_itd_samples > 0:
                    # Normalize time delay to angle (-90° to +90°)
                    angle_from_itd = (time_delay_samples / max_itd_samples) * 90.0
                    angle_from_itd = np.clip(angle_from_itd, -90, 90)
                else:
                    angle_from_itd = 0
            else:
                angle_from_itd = 0

            # === ILD (Level Difference) ===
            rms_left = np.sqrt(np.mean(left ** 2)) + 1e-10
            rms_right = np.sqrt(np.mean(right ** 2)) + 1e-10

            # ILD in dB
            ild_db = 20 * np.log10(rms_right / rms_left)

            # Typical ILD range: ±20 dB for ±90°
            angle_from_ild = (ild_db / 20.0) * 90.0
            angle_from_ild = np.clip(angle_from_ild, -90, 90)

            # === Combine ITD and ILD for robust angle estimation ===
            # ITD is more reliable for low frequencies, ILD for high frequencies
            # Weight: 70% ITD, 30% ILD (ITD is generally more accurate)
            angle_combined = 0.7 * angle_from_itd + 0.3 * angle_from_ild

            # FIXED v4.2.0: Player-centric radar transformation
            # TODO: Get player yaw from game (requires hooks/memory reading)
            # For now, assume player facing North (yaw = 0)
            # When player yaw is available, subtract it from angle_radar
            player_yaw = 0.0  # Placeholder - will be replaced with actual game data

            # Convert to radar coordinates (0° = forward, 90° = right, 180° = back, 270° = left)
            # Relative to sound source
            angle_radar = 90.0 + angle_combined  # Center at front (90°)

            # Transform to player-centric coordinates
            # If player faces East (yaw=90°), sounds from North should appear on left
            angle_radar = (angle_radar - player_yaw) % 360.0

            # === Distance Estimation ===
            total_energy = (rms_left + rms_right) / 2.0

            # Inverse square law approximation
            # Reference: 0.1 RMS = 10m, 0.01 RMS = 100m
            if total_energy > 0:
                distance = np.clip(10.0 / total_energy, 5.0, 100.0)
            else:
                distance = 50.0

            # === Elevation from frequency content ===
            elevation = self.compute_elevation(block, sample_rate)

            # === Confidence Score ===
            # Based on signal strength and stereo correlation
            signal_strength = total_energy / 0.1  # Normalized to 0.1 = 100%
            correlation_quality = np.max(np.abs(local_corr)) if len(local_corr) > 0 else 0

            confidence = min(100.0, signal_strength * 50 + correlation_quality * 50)

            return {
                'angle': angle_radar,
                'distance': distance,
                'elevation': elevation,
                'confidence': confidence,
                'itd_angle': angle_from_itd,
                'ild_angle': angle_from_ild,
                'ild_db': ild_db
            }

        except Exception as e:
            log(f"Error in compute_precise_location_3d: {e}", "ERROR")
            return {'angle': 0, 'distance': 50, 'elevation': 0, 'confidence': 0}

    def compute_elevation(self, block, sample_rate):
        """
        Estimate elevation angle from frequency content (v3.0.4 - Module 4)

        High frequencies (>2000 Hz) suggest sound from above (positive elevation)
        Low frequencies (<500 Hz) suggest sound from below (negative elevation)
        Mid frequencies suggest horizontal plane (0 elevation)

        Returns: Elevation angle in degrees (-45 to +45)
        """
        try:
            # Convert to mono if stereo
            if block.ndim == 2:
                mono = np.mean(block, axis=1)
            else:
                mono = block.ravel()

            # Compute FFT
            fft_data = np.fft.rfft(mono * np.hanning(len(mono)))
            freqs = np.fft.rfftfreq(len(mono), 1.0 / sample_rate)
            power = np.abs(fft_data) ** 2

            # Define frequency bands
            low_mask = (freqs >= 50) & (freqs < 500)    # Low freq = below
            mid_mask = (freqs >= 500) & (freqs < 2000)  # Mid freq = horizontal
            high_mask = (freqs >= 2000) & (freqs < 8000) # High freq = above

            # Compute energy in each band
            low_energy = np.sum(power[low_mask]) if np.any(low_mask) else 0
            mid_energy = np.sum(power[mid_mask]) if np.any(mid_mask) else 0
            high_energy = np.sum(power[high_mask]) if np.any(high_mask) else 0

            total_energy = low_energy + mid_energy + high_energy

            if total_energy < 1e-10:
                return 0.0

            # Calculate elevation bias (-1 = below, 0 = horizontal, +1 = above)
            elevation_bias = (high_energy - low_energy) / total_energy

            # Map to elevation angle (-45° to +45°)
            elevation_deg = elevation_bias * 45.0

            # Clamp to reasonable range
            elevation_deg = max(-45.0, min(45.0, elevation_deg))

            return elevation_deg

        except Exception as e:
            log(f"Error in compute_elevation: {e}", "ERROR")
            return 0.0

    def generate_test_block(self):
        """Generate synthetic test audio (FIXED v3.5.3: Stronger signals for detection)"""
        duration = self.audio.blocksize / self.audio.sample_rate
        t = np.linspace(self.test_phase, self.test_phase + duration, self.audio.blocksize)
        self.test_phase += duration

        # Stronger test signals for reliable detection (FIXED v3.5.3)
        # Walk: 80 Hz (low frequency footsteps)
        walk = 0.3 * np.sin(2 * np.pi * 80 * t)

        # Run: 420 Hz (mid frequency running)
        run = 0.4 * np.sin(2 * np.pi * 420 * t)

        # Shot: 2200 Hz every 2 seconds (high frequency gunshot)
        shot = np.zeros_like(t)
        if int(self.test_phase) % 2 == 0 and (self.test_phase % 2) < 0.15:
            shot = 0.5 * np.sin(2 * np.pi * 2200 * t)

        mono = walk + run + shot

        # Stereo with slight L/R imbalance for direction detection
        left = mono * 0.85
        right = mono * 1.15

        stereo = np.column_stack([left, right]).astype(np.float32)

        return stereo

    def quick_setup_game_audio(self):
        """Quick setup for game audio capture (v3.1.0 - Fixed to restart audio when running)"""
        log("Quick Setup: Enabling game audio capture", "INFO")

        try:
            # Remember if we were running
            was_running = self.is_running

            # Stop audio if running (to apply new settings)
            if self.is_running:
                log("Quick Setup: Stopping audio to apply new settings", "INFO")
                self.stop()

            # Enable loopback mode
            self.dev_panel.loopback_mode.setChecked(True)

            # Try to find and select a loopback device
            found_loopback = False
            for i in range(self.dev_panel.device_combo.count()):
                device_name = self.dev_panel.device_combo.itemText(i).lower()
                if 'loopback' in device_name or 'speaker' in device_name or 'output' in device_name:
                    self.dev_panel.device_combo.setCurrentIndex(i)
                    log(f"Quick Setup: Selected device: {self.dev_panel.device_combo.itemText(i)}", "INFO")
                    found_loopback = True
                    break

            # Apply settings
            self.dev_panel.apply_settings()

            # Restart audio if it was running before
            if was_running:
                log("Quick Setup: Restarting audio with new settings", "INFO")
                self.start()

            # Show success message
            if found_loopback:
                self.status_bar.showMessage(
                    "✓ Quick Setup Complete! Loopback mode enabled. Press START to capture game audio." if get_language() == 'en'
                    else "✓ Szybka konfiguracja zakończona! Tryb loopback włączony. Naciśnij START aby przechwycić dźwięk."
                )
            else:
                self.status_bar.showMessage(
                    "⚠ Loopback mode enabled, but no loopback device found. Check Tab 2 settings." if get_language() == 'en'
                    else "⚠ Tryb loopback włączony, ale nie znaleziono urządzenia. Sprawdź ustawienia w Zakładce 2."
                )

            # Switch to Detection & Audio tab to see settings
            self.main_tabs.setCurrentIndex(1)

        except Exception as e:
            log(f"Error in quick_setup_game_audio: {e}", "ERROR")
            import traceback
            log(traceback.format_exc(), "ERROR")
            self.status_bar.showMessage(
                "❌ Quick Setup failed - please configure manually (Tab 2)" if get_language() == 'en'
                else "❌ Szybka konfiguracja nie powiodła się - skonfiguruj ręcznie (Zakładka 2)"
            )

    def scan_games(self):
        """
        Scan for running games and update UI (v3.4.1 - z integracją platform gaming)

        FIXED v4.2.0: Reduced logging spam - only log on changes
        """
        try:
            game_data = self.game_detector.scan_processes()

            # Skanuj platformy gaming (v3.4.1)
            platform_data = self.platform_detector.scan_platforms()

            # Inteligentna detekcja przez launchery (v3.4.1)
            launcher_game = self.platform_detector.detect_game_from_launcher(game_data['games'])

            # FIXED v4.2.0: Only log when game state changes
            current_games = set(game_data.get('games', []))
            if not hasattr(self, '_last_detected_games'):
                self._last_detected_games = set()

            # Update game detection labels in Tab 3
            if game_data['has_games']:
                games_text = ", ".join(game_data['games'][:5])
                if len(game_data['games']) > 5:
                    games_text += f" (+{len(game_data['games']) - 5} more)"

                # Dodaj informację o platformie jeśli wykryto
                if launcher_game:
                    platform_name = launcher_game['platform']
                    games_text += f" 🔹 via {platform_name}"

                self.detected_games_label.setText(f"🎮 {games_text}")
                self.detected_games_label.setStyleSheet("font-size: 11pt; color: #00FF00; font-weight: bold; padding: 10px;")

                # FIXED v4.2.0: Only log when games change
                if current_games != self._last_detected_games:
                    log(f"Game detection changed: {games_text}", "INFO")

                # AUTO-SUGGESTION: Enable loopback when game detected (v3.1.0)
                if not self.dev_panel.loopback_mode.isChecked():
                    # Only log once when first game detected
                    if not self._last_detected_games and current_games:
                        log("Game detected! Auto-suggesting loopback mode for game audio capture", "INFO")
                    # Show subtle hint in status bar
                    if not self.is_running:
                        self.status_bar.showMessage(
                            "💡 Tip: Enable LOOPBACK mode (Tab 2) to capture game audio!" if get_language() == 'en'
                            else "💡 Wskazówka: Włącz tryb LOOPBACK (Zakładka 2) aby przechwycić dźwięk z gry!"
                        )
            else:
                self.detected_games_label.setText("No games detected")
                self.detected_games_label.setStyleSheet("font-size: 11pt; color: #888888; padding: 10px;")

            self._last_detected_games = current_games

            if game_data['engines']:
                engines_text = ", ".join(game_data['engines'][:3])
                if len(game_data['engines']) > 3:
                    engines_text += f" (+{len(game_data['engines']) - 3} more)"
                self.detected_engines_label.setText(f"⚙️ Engines: {engines_text}")
                self.detected_engines_label.setStyleSheet("font-size: 10pt; color: #00DDFF; padding: 5px;")
            else:
                self.detected_engines_label.setText("No engines detected")
                self.detected_engines_label.setStyleSheet("font-size: 10pt; color: #888888; padding: 5px;")

            # Aktualizuj informacje o platformach (v3.4.1)
            if platform_data['has_platforms']:
                platforms_list = []
                for p in platform_data['platforms']:
                    status_icon = "✅" if p['status'] == 'running' else "❌"
                    platforms_list.append(f"{status_icon} {p['name']}")

                platforms_text = ", ".join(platforms_list)
                self.detected_platforms_label.setText(platforms_text)
                self.detected_platforms_label.setStyleSheet("font-size: 10pt; color: #00FF00; padding: 5px;")
            else:
                self.detected_platforms_label.setText("No launchers detected")
                self.detected_platforms_label.setStyleSheet("font-size: 10pt; color: #888888; padding: 5px;")

            # Aktualizuj informacje o grze przez launcher (v3.4.1)
            if launcher_game:
                game_info = f"🎯 {launcher_game['name']}"
                if 'appid' in launcher_game:
                    game_info += f" (AppID: {launcher_game['appid']})"
                game_info += f"\n   Platform: {launcher_game['platform']}"
                game_info += f"\n   Process: {launcher_game['process']}"
                self.launcher_game_label.setText(game_info)
                self.launcher_game_label.setStyleSheet("font-size: 9pt; color: #00FFAA; padding: 5px; font-weight: bold;")
            else:
                self.launcher_game_label.setText("—")
                self.launcher_game_label.setStyleSheet("font-size: 9pt; color: #888888; padding: 5px;")

            # Update DevicePanel Game Detection section (FIXED v3.5.2)
            detailed_info = self.game_detector.get_detailed_game_info()
            self.dev_panel.update_game_detection_info(detailed_info, game_data)

        except Exception as e:
            log(f"Error in scan_games: {e}", "ERROR")

    def scan_audio_sources(self):
        """Scan audio sources and update UI (v3.5.1 - Fixed proper status display)"""
        try:
            sources_data = self.audio_scanner.scan_audio_sources()
            is_receiving = sources_data.get('is_receiving', False)

            # Update active/selected sources
            active_count = len(sources_data['active'])

            if active_count > 0:
                # Show "RECEIVING" or "SELECTED" based on actual audio activity
                status_text = "RECEIVING" if is_receiving else "SELECTED"
                status_color = "#00FF00" if is_receiving else "#FFAA00"
                self.active_sources_label.setText(f"{status_text}: {active_count}")
                self.active_sources_label.setStyleSheet(f"font-size: 9pt; font-weight: bold; color: {status_color};")

                active_list = []
                for i, src in enumerate(sources_data['active'][:5]):
                    name = src['name'][:45] + "..." if len(src['name']) > 45 else src['name']
                    icon = "📡" if is_receiving else "✓"
                    active_list.append(f"{icon} {name}")

                if len(sources_data['active']) > 5:
                    active_list.append(f"   (+{len(sources_data['active']) - 5} more)")

                self.active_sources_list.setText("\n".join(active_list))
                self.active_sources_list.setStyleSheet(f"font-size: 9pt; color: {status_color};")
            else:
                self.active_sources_label.setText("NO DEVICE SELECTED")
                self.active_sources_label.setStyleSheet("font-size: 9pt; font-weight: bold; color: #FF6666;")
                self.active_sources_list.setText("Select a device in Tab 2")
                self.active_sources_list.setStyleSheet("font-size: 9pt; color: #888;")

            # Update available (inactive) sources
            inactive_count = len(sources_data['inactive'])
            self.inactive_sources_label.setText(f"Available: {inactive_count}")
            self.inactive_sources_label.setStyleSheet("font-size: 9pt; font-weight: bold; color: #888;")

            if inactive_count > 0:
                inactive_list = []
                for i, src in enumerate(sources_data['inactive'][:3]):
                    name = src['name'][:45] + "..." if len(src['name']) > 45 else src['name']
                    inactive_list.append(f"○ {name}")

                if len(sources_data['inactive']) > 3:
                    inactive_list.append(f"   (+{len(sources_data['inactive']) - 3} more)")

                self.inactive_sources_list.setText("\n".join(inactive_list))
                self.inactive_sources_list.setStyleSheet("font-size: 9pt; color: #666;")
            else:
                self.inactive_sources_list.setText("—")
                self.inactive_sources_list.setStyleSheet("font-size: 9pt; color: #666;")

        except Exception as e:
            log(f"Error in scan_audio_sources: {e}", "ERROR")

    def closeEvent(self, event):
        """
        Handle window close - Enhanced cleanup

        ENHANCED v3.5.0: Thread-safe shutdown with timeout
        """
        log("Application closing - starting cleanup", "INFO")

        # Stop audio first
        self.stop()

        # Shutdown worker threads with timeout (v3.5.0)
        if hasattr(self, 'detection_worker'):
            try:
                self.detection_worker.shutdown(timeout=DETECTION_TIMEOUT_SEC)  # FIXED v3.5.0: Use constant
                log("Detection worker shutdown complete", "INFO")
            except Exception as e:
                log(f"Error shutting down detection worker: {e}", "ERROR")

        # Stop all timers
        if hasattr(self, 'timer'):
            self.timer.stop()

        if hasattr(self, 'game_scan_timer'):
            self.game_scan_timer.stop()

        if hasattr(self, 'audio_scan_timer'):
            self.audio_scan_timer.stop()

        # Stop toast notification timer (v3.5.0)
        if hasattr(self, 'toast') and hasattr(self.toast, 'animation_timer'):
            self.toast.animation_timer.stop()
            self.toast.close()

        # Close detached windows
        if self.detached_radar:
            try:
                self.detached_radar.close()
            except Exception as e:
                log(f"Error closing detached radar: {e}", "WARNING")

        if self.detached_led:
            try:
                self.detached_led.close()
            except Exception as e:
                log(f"Error closing detached LED: {e}", "WARNING")

        # Save configuration (v3.5.0, enhanced v4.2.0 with window state)
        if hasattr(self, 'config_manager'):
            try:
                # Save window geometry before saving config (v4.2.0)
                self.config = self.config_manager.save_window_state(self, self.config)
                self.config_manager.save(self.config)
                log("Configuration saved successfully", "INFO")
            except Exception as e:
                log(f"Error saving configuration: {e}", "WARNING")

        log("Application cleanup complete", "INFO")
        event.accept()


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """
    Main entry point

    Point 11 - v3.5.0: Uses Dependency Injection for clean architecture
    """
    log("=" * 80, "INFO")
    log(f"RadarSuite Final {VERSION} - Starting", "INFO")
    log("=" * 80, "INFO")

    log(f"Python: {sys.version}", "INFO")
    log(f"NumPy: {np.__version__}", "INFO")
    log(f"pyqtgraph: {pg.__version__}", "INFO")

    # Lazy check for optional audio backends to avoid crashes when PortAudio is missing
    try:
        import sounddevice  # noqa: F401
        log("sounddevice import OK", "INFO")
    except Exception as e:
        log(f"sounddevice import failed (audio will be disabled until resolved): {e}", "WARN")

    try:
        import soundcard  # noqa: F401
        log("soundcard import OK", "INFO")
    except Exception as e:
        log(f"soundcard import failed (loopback disabled): {e}", "WARN")

    app = QApplication(sys.argv)
    app.setApplicationName("RadarSuite Final")
    app.setOrganizationName("RadarSuite")

    apply_dark_theme(app)

    # Point 11 - v3.5.0: Configure Dependency Injection
    from core import configure_services, ConfigManager

    log("Configuring Dependency Injection container...", "INFO")
    config_mgr = ConfigManager()
    config = config_mgr.load()

    container = configure_services(config)
    log(f"DI: {len(container.get_registered_services())} services registered", "INFO")

    # Create main window with DI
    window = MainWindow(container=container)
    window.show()

    log("Main window shown, entering event loop", "INFO")

    exit_code = app.exec_()

    log(f"Application exited with code: {exit_code}", "INFO")
    log("=" * 80, "INFO")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
