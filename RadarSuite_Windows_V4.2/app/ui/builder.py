"""
UIBuilder - Extracted UI construction logic from MainWindow
RadarSuite V4.2 - Refactoring Phase 1

This module handles all UI widget creation, reducing MainWindow complexity.
All widgets are assigned to self.main.widget_name for backward compatibility.
"""

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox,
    QLabel, QPushButton, QCheckBox, QSlider, QToolBar, QStatusBar,
    QSizePolicy, QScrollArea, QTextEdit
)
from PyQt5.QtCore import Qt

# Support both packaged execution (app.*) and direct script execution
try:
    from ..widgets.radar import MilitaryHUDRadar, Military3DRadar
    from ..widgets.spectrum import (
        MilitarySpectrumWidget,
        MilitaryWaterfallWidget,
        MilitaryWaveformWidget,
    )
    from ..widgets.led import LedOverlayWidget
    from ..widgets.detection_panel import DetectionPanel
    from ..widgets.device_panel import DevicePanel
    from ..core.constants import VERSION
    from ..core.translations import tr
except ImportError:
    # Standalone script execution (e.g., python main.py)
    from widgets.radar import MilitaryHUDRadar, Military3DRadar
    from widgets.spectrum import (
        MilitarySpectrumWidget,
        MilitaryWaterfallWidget,
        MilitaryWaveformWidget,
    )
    from widgets.led import LedOverlayWidget
    from widgets.detection_panel import DetectionPanel
    from widgets.device_panel import DevicePanel

    try:
        from core.constants import VERSION
    except ImportError:
        # Minimal fallback when constants.py cannot be resolved
        from version import __version__ as VERSION

    from core.translations import tr

# ML Training Panel (v4.2.0 - Roadmap Item 1)
# FIXED v4.2.1-k0003: Corrected import order to match rest of file
# Try relative imports first (package mode), then absolute (standalone mode)
try:
    from ..widgets.ml_training_panel import MLTrainingPanel
    from ..widgets.ml_quick_overlay import MLQuickRecordOverlay
    from ..ml.training import RecordingController
    ML_TRAINING_AVAILABLE = True
    ML_TRAINING_ERROR = None
    ML_TRAINING_ERROR_TRACE = ""
except Exception:
    try:
        from widgets.ml_training_panel import MLTrainingPanel
        from widgets.ml_quick_overlay import MLQuickRecordOverlay
        from ml.training import RecordingController
        ML_TRAINING_AVAILABLE = True
        ML_TRAINING_ERROR = None
        ML_TRAINING_ERROR_TRACE = ""
    except Exception as exc:  # ImportError or missing optional deps
        import traceback

        ML_TRAINING_AVAILABLE = False
        ML_TRAINING_ERROR = exc
        ML_TRAINING_ERROR_TRACE = traceback.format_exc()

if TYPE_CHECKING:
    from ..main import MainWindow


class UIBuilder:
    """
    Builds the complete UI for MainWindow.

    Extracts ~360 LOC from MainWindow.create_ui() into organized methods.
    All widgets are assigned to main window instance for backward compatibility.
    """

    # Style constants
    TAB_WIDGET_STYLE = """
        QTabWidget::pane {
            border: 1px solid #333;
            background: #0a0a0a;
        }
        QTabBar::tab {
            background: #1a1a1a;
            color: #aaa;
            padding: 10px 20px;
            margin: 2px;
            border: 1px solid #333;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: #2a2a2a;
            color: #0ff;
            border-bottom: 2px solid #0ff;
        }
        QTabBar::tab:hover {
            background: #252525;
            color: #0dd;
        }
    """

    TOOLBAR_STYLE = """
        QToolBar {
            background: #1a1a1a;
            border-bottom: 1px solid #333;
            padding: 5px;
        }
    """

    STATUSBAR_STYLE = """
        QStatusBar {
            background: #1a1a1a;
            color: #aaa;
            border-top: 1px solid #333;
        }
    """

    START_BTN_STYLE = """
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
    """

    RECORD_BTN_STYLE = """
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
        QPushButton:disabled {
            background: #555555;
            color: #888888;
        }
    """

    QUICK_SETUP_BTN_STYLE = """
        QPushButton {
            background: #0066aa;
            color: white;
            font-weight: bold;
            padding: 10px;
            border-radius: 4px;
            font-size: 10pt;
            margin: 10px;
        }
        QPushButton:hover {
            background: #0088cc;
        }
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize UIBuilder with reference to MainWindow.

        Args:
            main_window: MainWindow instance - all widgets will be assigned here
        """
        self.main: "MainWindow" = main_window

    def build(self) -> None:
        """
        Build the complete UI. Main entry point.

        Creates all tabs, toolbar, and statusbar.
        """
        # Main tab widget
        self._create_main_tabs()

        # Build each tab
        self._build_radar_tab()
        self._build_detection_tab()
        self._build_game_detection_tab()
        self._build_analysis_tab()
        self._build_ml_training_tab()  # v4.2.0: ML Training Tab

        # Toolbar and statusbar
        self._build_toolbar()
        self._build_statusbar()

        # Setup keyboard shortcuts
        self.main.setup_shortcuts()

    def _create_main_tabs(self) -> None:
        """Create main tab widget and set as central widget."""
        self.main.main_tabs = QTabWidget()
        self.main.main_tabs.setStyleSheet(self.TAB_WIDGET_STYLE)
        self.main.setCentralWidget(self.main.main_tabs)

    def _build_radar_tab(self) -> None:
        """Build Tab 1: Radar View (Main tactical display)."""
        radar_tab = QWidget()
        radar_layout = QVBoxLayout()
        radar_layout.setContentsMargins(5, 5, 5, 5)

        # Radar sub-tabs (2D/3D)
        self.main.radar_tabs = QTabWidget()
        self.main.radar_tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #222; }")

        # 2D Radar - Military HUD Style
        self.main.radar_widget = MilitaryHUDRadar()
        self.main.radar_tabs.addTab(self.main.radar_widget, f"🎯 {tr('military_hud')}")

        # 3D Radar - Military Wallhack HUD Style
        self.main.radar_3d_widget = Military3DRadar()
        self.main.radar_tabs.addTab(self.main.radar_3d_widget, f"🌐 {tr('3d_wallhack')}")

        radar_layout.addWidget(self.main.radar_tabs)

        # Radar controls (compact bottom panel)
        radar_controls = self._build_radar_controls()
        radar_layout.addLayout(radar_controls)

        radar_tab.setLayout(radar_layout)
        self.main.main_tabs.addTab(radar_tab, f"🎯 {tr('tab_radar_view')}")

    def _build_radar_controls(self) -> QHBoxLayout:
        """Build radar control panel (detach, frameless, opacity)."""
        radar_controls = QHBoxLayout()

        self.main.detach_radar_btn = QPushButton(f"⬜ {tr('detach_radar')}")
        self.main.detach_radar_btn.setCheckable(True)
        self.main.detach_radar_btn.clicked.connect(self.main.toggle_detach_radar)
        radar_controls.addWidget(self.main.detach_radar_btn)

        self.main.radar_frameless_btn = QCheckBox(tr('frameless_mode'))
        self.main.radar_frameless_btn.toggled.connect(self.main.toggle_radar_frameless)
        radar_controls.addWidget(self.main.radar_frameless_btn)

        radar_controls.addWidget(QLabel(tr('opacity')))
        self.main.radar_alpha = QSlider(Qt.Horizontal)
        self.main.radar_alpha.setRange(0, 100)
        self.main.radar_alpha.setValue(100)
        self.main.radar_alpha.setMaximumWidth(150)
        self.main.radar_alpha.valueChanged.connect(self.main.update_radar_alpha)
        radar_controls.addWidget(self.main.radar_alpha)
        radar_controls.addStretch()

        return radar_controls

    def _build_detection_tab(self) -> None:
        """Build Tab 2: Detection & Audio."""
        detection_tab = QWidget()
        detection_layout = QVBoxLayout()
        detection_layout.setContentsMargins(5, 5, 5, 5)

        # Scrollable container to ensure responsive layout on small widths/DPI
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(12)

        # Left: Detection panel
        self.main.det_panel = DetectionPanel()
        container_layout.addWidget(self.main.det_panel, 3)

        # Right: Device/Audio panel
        self.main.dev_panel = DevicePanel(self.main.audio)
        self.main.dev_panel.set_audio_scanner(self.main.audio_scanner)
        self.main.dev_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        container_layout.addWidget(self.main.dev_panel, 2)

        container.setLayout(container_layout)
        scroll_area.setWidget(container)

        detection_layout.addWidget(scroll_area)
        detection_tab.setLayout(detection_layout)
        self.main.main_tabs.addTab(detection_tab, f"🔊 {tr('tab_detection_audio')}")

    def _build_game_detection_tab(self) -> None:
        """Build Tab 3: Game Detection."""
        game_tab = QWidget()
        game_layout = QVBoxLayout()
        game_layout.setContentsMargins(10, 10, 10, 10)

        # Game detection section
        game_group = self._build_game_group()
        game_layout.addWidget(game_group)

        # Platform Launchers section
        platform_group = self._build_platform_group()
        game_layout.addWidget(platform_group)

        # Audio sources section
        sources_group = self._build_audio_sources_group()
        game_layout.addWidget(sources_group)

        game_layout.addStretch()
        game_tab.setLayout(game_layout)
        self.main.main_tabs.addTab(game_tab, f"🎮 {tr('tab_game_detection')}")

    def _build_game_group(self) -> QGroupBox:
        """Build Active Games & Engines group."""
        game_group = QGroupBox(tr('game_group_title'))
        game_group_layout = QVBoxLayout()

        self.main.detected_games_label = QLabel(tr('scanning_games'))
        self.main.detected_games_label.setStyleSheet(
            "font-size: 11pt; color: #888888; padding: 10px;"
        )
        self.main.detected_games_label.setWordWrap(True)
        game_group_layout.addWidget(self.main.detected_games_label)

        self.main.detected_engines_label = QLabel(tr('no_engines'))
        self.main.detected_engines_label.setStyleSheet(
            "font-size: 10pt; color: #888888; padding: 5px;"
        )
        self.main.detected_engines_label.setWordWrap(True)
        game_group_layout.addWidget(self.main.detected_engines_label)

        # Quick Setup button
        self.main.quick_setup_btn = QPushButton(tr('quick_setup'))
        self.main.quick_setup_btn.setStyleSheet(self.QUICK_SETUP_BTN_STYLE)
        self.main.quick_setup_btn.clicked.connect(self.main.quick_setup_game_audio)
        game_group_layout.addWidget(self.main.quick_setup_btn)

        game_group.setLayout(game_group_layout)
        return game_group

    def _build_platform_group(self) -> QGroupBox:
        """Build Gaming Platform Launchers group."""
        platform_group = QGroupBox(tr('platform_group_title'))
        platform_layout = QVBoxLayout()

        self.main.detected_platforms_label = QLabel(tr('scanning_launchers'))
        self.main.detected_platforms_label.setStyleSheet(
            "font-size: 10pt; color: #888888; padding: 5px;"
        )
        self.main.detected_platforms_label.setWordWrap(True)
        platform_layout.addWidget(self.main.detected_platforms_label)

        self.main.launcher_game_label = QLabel(tr('launchers_placeholder'))
        self.main.launcher_game_label.setStyleSheet(
            "font-size: 9pt; color: #00DDFF; padding: 5px;"
        )
        self.main.launcher_game_label.setWordWrap(True)
        platform_layout.addWidget(self.main.launcher_game_label)

        platform_group.setLayout(platform_layout)
        return platform_group

    def _build_audio_sources_group(self) -> QGroupBox:
        """Build Audio Sources Monitor group."""
        sources_group = QGroupBox(tr('audio_sources_group'))
        sources_layout = QVBoxLayout()

        # Active sources
        active_label = QLabel(tr('active_sources'))
        active_label.setStyleSheet("font-weight: bold; color: #00FF00; font-size: 10pt;")
        sources_layout.addWidget(active_label)

        self.main.active_sources_label = QLabel(tr('scanning_sources').format(count=0))
        self.main.active_sources_label.setStyleSheet(
            "font-size: 9pt; color: #00DD00; padding: 5px;"
        )
        sources_layout.addWidget(self.main.active_sources_label)

        self.main.active_sources_list = QLabel(tr('sources_placeholder'))
        self.main.active_sources_list.setStyleSheet(
            "font-size: 8pt; color: #00DD00; padding: 5px;"
        )
        self.main.active_sources_list.setWordWrap(True)
        self.main.active_sources_list.setMaximumHeight(120)
        sources_layout.addWidget(self.main.active_sources_list)

        # Inactive sources
        inactive_label = QLabel("INACTIVE SOURCES:")
        inactive_label.setStyleSheet(
            "font-weight: bold; color: #FF6666; font-size: 10pt; margin-top: 10px;"
        )
        sources_layout.addWidget(inactive_label)

        self.main.inactive_sources_label = QLabel("Inactive: 0")
        self.main.inactive_sources_label.setStyleSheet(
            "font-size: 9pt; color: #DD6666; padding: 5px;"
        )
        sources_layout.addWidget(self.main.inactive_sources_label)

        self.main.inactive_sources_list = QLabel("—")
        self.main.inactive_sources_list.setStyleSheet(
            "font-size: 8pt; color: #DD6666; padding: 5px;"
        )
        self.main.inactive_sources_list.setWordWrap(True)
        self.main.inactive_sources_list.setMaximumHeight(80)
        sources_layout.addWidget(self.main.inactive_sources_list)

        sources_group.setLayout(sources_layout)
        return sources_group

    def _build_analysis_tab(self) -> None:
        """Build Tab 4: Analysis (Spectrum, Waterfall, LED)."""
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout()
        analysis_layout.setContentsMargins(5, 5, 5, 5)

        # Spectrum & Waterfall & Waveform tabs
        spectrum_waterfall_tabs = QTabWidget()

        self.main.spectrum = MilitarySpectrumWidget()
        spectrum_waterfall_tabs.addTab(self.main.spectrum, f"📡 {tr('live_spectrum')}")

        self.main.waterfall = MilitaryWaterfallWidget()
        spectrum_waterfall_tabs.addTab(self.main.waterfall, f"🌊 {tr('waterfall').upper()}")

        self.main.waveform = MilitaryWaveformWidget()
        spectrum_waterfall_tabs.addTab(self.main.waveform, f"〰️ {tr('waveform').upper()}")

        analysis_layout.addWidget(spectrum_waterfall_tabs, 3)

        # LED Alert section
        led_group = self._build_led_group()
        analysis_layout.addWidget(led_group, 1)

        analysis_tab.setLayout(analysis_layout)
        self.main.main_tabs.addTab(analysis_tab, f"📊 {tr('tab_analysis')}")

    def _build_led_group(self) -> QGroupBox:
        """Build LED Edge Alert group with controls."""
        led_group = QGroupBox(f"⚡ {tr('led_alert')}")
        led_layout = QVBoxLayout()

        self.main.led_widget = LedOverlayWidget()
        self.main.led_widget.setMinimumHeight(100)
        led_layout.addWidget(self.main.led_widget)

        # LED controls
        led_controls = QHBoxLayout()

        self.main.detach_led_btn = QPushButton(f"⬜ {tr('detach_led')}")
        self.main.detach_led_btn.setCheckable(True)
        self.main.detach_led_btn.clicked.connect(self.main.toggle_detach_led)
        led_controls.addWidget(self.main.detach_led_btn)

        self.main.led_frameless_btn = QCheckBox("Frameless")
        self.main.led_frameless_btn.toggled.connect(self.main.toggle_led_frameless)
        led_controls.addWidget(self.main.led_frameless_btn)

        led_controls.addWidget(QLabel("Opacity:"))
        self.main.led_alpha = QSlider(Qt.Horizontal)
        self.main.led_alpha.setRange(0, 100)
        self.main.led_alpha.setValue(80)
        self.main.led_alpha.setMaximumWidth(150)
        self.main.led_alpha.valueChanged.connect(self.main.update_led_alpha)
        led_controls.addWidget(self.main.led_alpha)
        led_controls.addStretch()

        led_layout.addLayout(led_controls)
        led_group.setLayout(led_layout)
        return led_group

    def _build_toolbar(self) -> None:
        """Build main toolbar with Start, Record, Language controls."""
        toolbar = QToolBar()
        toolbar.setStyleSheet(self.TOOLBAR_STYLE)
        self.main.addToolBar(toolbar)

        # Start/Stop button
        self.main.start_btn = QPushButton(f"▶ {tr('start')}")
        self.main.start_btn.setStyleSheet(self.START_BTN_STYLE)
        self.main.start_btn.clicked.connect(self.main.toggle_start_stop)
        toolbar.addWidget(self.main.start_btn)

        toolbar.addSeparator()

        # Recording controls
        self.main.record_btn = QPushButton(f"⏺ {tr('rec')}")
        self.main.record_btn.setStyleSheet(self.RECORD_BTN_STYLE)
        self.main.record_btn.clicked.connect(self.main.toggle_recording)
        self.main.record_btn.setEnabled(False)
        toolbar.addWidget(self.main.record_btn)

        self.main.record_duration_label = QLabel("0:00")
        self.main.record_duration_label.setStyleSheet(
            "color: #ff0000; font-family: monospace; font-weight: bold;"
        )
        toolbar.addWidget(self.main.record_duration_label)

        toolbar.addSeparator()

        # Language switcher
        toolbar.addWidget(QLabel("🌍"))
        self.main.lang_btn = QPushButton("🇬🇧 EN")
        self.main.lang_btn.setCheckable(True)
        self.main.lang_btn.setToolTip("Click to switch language / Kliknij aby zmienić język")
        self.main.lang_btn.clicked.connect(self.main.toggle_language)
        toolbar.addWidget(self.main.lang_btn)

        toolbar.addSeparator()

        # Self-test trigger
        self.main.test_btn = QPushButton(tr('self_test'))
        self.main.test_btn.setToolTip(tr('self_test_title'))
        self.main.test_btn.clicked.connect(self.main.launch_self_test)
        toolbar.addWidget(self.main.test_btn)

        toolbar.addSeparator()

        # Quick stats
        self.main.toolbar_stats_label = QLabel("Targets: 0 | FPS: 20")
        self.main.toolbar_stats_label.setStyleSheet(
            "color: #0dd; padding: 5px; font-family: monospace;"
        )
        toolbar.addWidget(self.main.toolbar_stats_label)

        # Spacer to push version to right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)

        # Version label
        version_label = QLabel(f"v{VERSION}")
        version_label.setStyleSheet("color: #666; padding: 5px; font-size: 9pt;")
        toolbar.addWidget(version_label)

    def _build_ml_training_tab(self) -> None:
        """Build Tab 5: ML Training (v4.2.0 - Roadmap Item 1)."""
        if not ML_TRAINING_AVAILABLE:
            # Create placeholder tab if ML training is not available and surface the reason.
            placeholder = QWidget()
            layout = QVBoxLayout()
            label = QLabel(f"🧠 {tr('ml_training_unavailable_title')}")
            label.setStyleSheet("font-size: 12pt; color: #888888; padding: 10px;")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)

            error_hint = QLabel(
                tr('ml_training_dependency_hint').format(error=str(ML_TRAINING_ERROR))
            )
            error_hint.setWordWrap(True)
            error_hint.setStyleSheet("color: #AAAAAA; padding: 0 15px 5px 15px;")
            layout.addWidget(error_hint)

            install_hint = QLabel(tr('ml_training_install_hint'))
            install_hint.setWordWrap(True)
            install_hint.setStyleSheet("color: #AAAAAA; padding: 0 15px 10px 15px;")
            layout.addWidget(install_hint)

            if ML_TRAINING_ERROR_TRACE:
                trace_box = QTextEdit()
                trace_box.setReadOnly(True)
                trace_box.setText(ML_TRAINING_ERROR_TRACE)
                trace_box.setStyleSheet("font-family: monospace; font-size: 8pt; color: #CCCCCC;")
                layout.addWidget(trace_box)

            placeholder.setLayout(layout)
            self.main.main_tabs.addTab(placeholder, f"🧠 {tr('tab_ml_training')}")
            self.main.ml_training_panel = None
            return

        controller = getattr(self.main, 'recording_controller', None)
        if controller is None:
            try:
                controller = RecordingController()
            except Exception as exc:
                controller = None
                ML_TRAINING_ERROR_TRACE = str(exc)
        self.main.recording_controller = controller

        def launch_overlay():
            if controller is None:
                return
            overlay = getattr(self.main, 'ml_quick_overlay', None)
            if overlay is None:
                overlay = MLQuickRecordOverlay(
                    controller,
                    config_manager=getattr(self.main, 'config_manager', None)
                )
                self.main.ml_quick_overlay = overlay
            overlay.show()
            overlay.raise_()
            overlay.activateWindow()

        self.main.ml_training_panel = MLTrainingPanel(
            recording_controller=controller,
            overlay_launcher=launch_overlay,
        )
        self.main.main_tabs.addTab(self.main.ml_training_panel, f"🧠 {tr('tab_ml_training')}")

    def _build_statusbar(self) -> None:
        """Build status bar."""
        self.main.status_bar = QStatusBar()
        self.main.status_bar.setStyleSheet(self.STATUSBAR_STYLE)
        self.main.setStatusBar(self.main.status_bar)
        self.main.status_bar.showMessage(f"✓ {tr('ready')} - All systems operational")

        # Permanent build ID indicator for user-side verification
        build_label = QLabel(self.main.build_id)
        build_label.setStyleSheet("color: #7aa2f7; font-weight: bold;")
        self.main.status_bar.addPermanentWidget(build_label)
        self.main.build_label = build_label
