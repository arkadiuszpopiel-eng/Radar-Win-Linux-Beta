"""
RadarSuite v3.5.0 - Device_Panel Widgets
"""

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QComboBox, QSlider, QCheckBox, QSpinBox, QGroupBox,
                             QFormLayout, QFrame, QStyledItemDelegate, QScrollArea,
                             QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPalette, QFont

from core import log, tr, TOAST_DURATION_MS, TOAST_MAX_COUNT


class DeviceItemDelegate(QStyledItemDelegate):
    """Custom delegate for coloring device items based on status"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_device_index = -1
        self.device_statuses = {}  # {index: 'active'|'inactive'|'selected'}
        self.device_names = {}  # {index: device_name} for Sound Blaster detection

    def paint(self, painter, option, index):
        # Get device status and name
        status = self.device_statuses.get(index.row(), 'inactive')
        device_name = self.device_names.get(index.row(), '').lower()

        # Detect device type
        is_soundblaster = any(sb in device_name for sb in [
            'sound blaster', 'soundblaster', 'sb z', 'sb-z', 'creative'
        ])
        is_realtek = any(rt in device_name for rt in [
            'realtek', 'high definition audio', 'hd audio'
        ])

        # Set background color based on status and device type
        if status == 'active' or index.row() == self.active_device_index:
            if is_soundblaster:
                # Sound Blaster Z SE - dark green with cyan tint
                painter.fillRect(option.rect, QColor(0, 60, 40))
                painter.fillRect(option.rect.x(), option.rect.y(),
                               3, option.rect.height(), QColor(0, 200, 150))
            elif is_realtek:
                # Realtek/Laptop - blue tint
                painter.fillRect(option.rect, QColor(20, 40, 80))
                painter.fillRect(option.rect.x(), option.rect.y(),
                               3, option.rect.height(), QColor(100, 150, 255))
            else:
                # General active device - bright/light green
                painter.fillRect(option.rect, QColor(0, 100, 0))
                painter.fillRect(option.rect.x(), option.rect.y(),
                               3, option.rect.height(), QColor(0, 255, 0))

        # Call default painting
        super().paint(painter, option, index)

    def set_device_info(self, index, name, is_active):
        """Store device info for coloring"""
        self.device_names[index] = name
        self.device_statuses[index] = 'active' if is_active else 'inactive'


class DevicePanel(QWidget):
    """Device selection and configuration panel with scroll support"""

    def __init__(self, audio_engine):
        super().__init__()
        self.audio = audio_engine
        self.game_detector = None  # Will be set externally
        log("DevicePanel.__init__", "INFO")

        # Main layout for the panel
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for responsive scaling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #444;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #0a0;
            }
        """)

        # Container widget for scroll area content
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(scroll_content)

        # Device selection
        device_group = QGroupBox(tr('audio_device'))
        device_layout = QVBoxLayout()

        self.device_combo = QComboBox()
        # Add custom delegate for coloring
        self.device_delegate = DeviceItemDelegate(self.device_combo)
        self.device_combo.setItemDelegate(self.device_delegate)
        # Style the combo box
        self.device_combo.setStyleSheet("""
            QComboBox {
                background-color: #1a1a1a;
                color: white;
                border: 2px solid #333;
                border-radius: 5px;
                padding: 5px;
                font-size: 10pt;
            }
            QComboBox:hover {
                border: 2px solid #0a0;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: white;
                selection-background-color: #006600;
            }
        """)
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)

        self.select_device_label = QLabel(tr('select_device'))
        device_layout.addWidget(self.select_device_label)
        device_layout.addWidget(self.device_combo)

        # Current device status indicator
        self.device_status_frame = QFrame()
        self.device_status_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        status_frame_layout = QHBoxLayout(self.device_status_frame)
        status_frame_layout.setContentsMargins(5, 2, 5, 2)

        self.device_status_led = QLabel("●")
        self.device_status_led.setStyleSheet("color: #666; font-size: 14pt;")
        status_frame_layout.addWidget(self.device_status_led)

        self.device_status_text = QLabel("No device selected")
        self.device_status_text.setStyleSheet("color: #888; font-size: 9pt;")
        status_frame_layout.addWidget(self.device_status_text)
        status_frame_layout.addStretch()

        device_layout.addWidget(self.device_status_frame)

        self.refresh_btn = QPushButton(tr('refresh_devices'))
        self.refresh_btn.clicked.connect(self.refresh_devices)
        device_layout.addWidget(self.refresh_btn)

        device_group.setLayout(device_layout)
        layout.addWidget(device_group)

        # Audio settings
        settings_group = QGroupBox(tr('audio_settings'))
        settings_layout = QFormLayout()

        self.samplerate_combo = QComboBox()
        self.samplerate_combo.addItems(['44100', '48000', '96000'])
        self.samplerate_combo.setCurrentText('48000')
        settings_layout.addRow(tr('sample_rate'), self.samplerate_combo)

        self.blocksize_combo = QComboBox()
        self.blocksize_combo.addItems(['512', '1024', '2048', '4096'])
        self.blocksize_combo.setCurrentText('2048')
        settings_layout.addRow(tr('block_size'), self.blocksize_combo)

        self.channels_combo = QComboBox()
        self.channels_combo.addItems(['1', '2', '6', '8'])
        self.channels_combo.setCurrentText('2')
        settings_layout.addRow(tr('channels'), self.channels_combo)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Mode selection
        mode_group = QGroupBox(tr('mode'))
        mode_layout = QVBoxLayout()

        self.test_mode = QCheckBox(tr('test_mode'))
        mode_layout.addWidget(self.test_mode)

        self.loopback_mode = QCheckBox(tr('loopback_mode'))
        self.loopback_mode.toggled.connect(self.on_loopback_toggled)
        mode_layout.addWidget(self.loopback_mode)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Audio Enhancements (v3.1.2 - Auto-gain for quiet audio)
        enhance_group = QGroupBox("🎚️ Audio Enhancements")
        enhance_layout = QVBoxLayout()

        # Auto-gain checkbox
        self.auto_gain_enable = QCheckBox("Enable Auto-Gain (boost quiet audio)")
        self.auto_gain_enable.setToolTip("Automatically amplify quiet audio signals for better detection")
        self.auto_gain_enable.setChecked(False)
        enhance_layout.addWidget(self.auto_gain_enable)

        # Manual gain slider
        gain_slider_layout = QHBoxLayout()
        gain_slider_layout.addWidget(QLabel(tr('manual_gain')))
        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(1, 100)  # 1x to 100x gain
        self.gain_slider.setValue(1)  # Default 1x (no gain)
        self.gain_slider.setEnabled(True)  # Enabled by default (auto-gain is off)
        # FIXED v4.2.1: Smooth scrolling for gain slider
        self.gain_slider.setSingleStep(1)
        self.gain_slider.setPageStep(10)
        self.gain_slider.setTracking(True)
        gain_slider_layout.addWidget(self.gain_slider)
        self.gain_label = QLabel("1x")
        self.gain_slider.valueChanged.connect(lambda v: self.gain_label.setText(f"{v}x"))
        gain_slider_layout.addWidget(self.gain_label)
        enhance_layout.addLayout(gain_slider_layout)

        # Connect auto-gain checkbox to disable manual slider
        self.auto_gain_enable.toggled.connect(lambda checked: self.gain_slider.setEnabled(not checked))

        # Noise gate threshold
        noise_gate_layout = QHBoxLayout()
        noise_gate_layout.addWidget(QLabel(tr('noise_gate')))
        self.noise_gate_slider = QSlider(Qt.Horizontal)
        self.noise_gate_slider.setRange(0, 100)
        self.noise_gate_slider.setValue(5)  # Default -60 dB
        self.noise_gate_slider.setToolTip(tr('noise_gate_tooltip'))
        # FIXED v4.2.1: Smooth scrolling for noise gate slider
        self.noise_gate_slider.setSingleStep(1)
        self.noise_gate_slider.setPageStep(10)
        self.noise_gate_slider.setTracking(True)
        noise_gate_layout.addWidget(self.noise_gate_slider)
        self.noise_gate_label = QLabel("-60dB")
        self.noise_gate_slider.valueChanged.connect(
            lambda v: self.noise_gate_label.setText(f"-{80-v}dB")
        )
        noise_gate_layout.addWidget(self.noise_gate_label)
        enhance_layout.addLayout(noise_gate_layout)

        enhance_group.setLayout(enhance_layout)
        layout.addWidget(enhance_group)

        # Presets
        preset_group = QGroupBox(tr('presets'))
        preset_layout = QVBoxLayout()

        self.sb_btn = QPushButton(tr('sb_preset'))
        self.sb_btn.clicked.connect(self.apply_sb_preset)
        self.sb_btn.setToolTip("Sound Blaster Z SE: 48kHz, 2048 block, 2ch")
        preset_layout.addWidget(self.sb_btn)

        # Laptop/Realtek preset
        self.realtek_btn = QPushButton("💻 Laptop (Realtek)")
        self.realtek_btn.clicked.connect(self.apply_realtek_preset)
        self.realtek_btn.setToolTip("Realtek Audio: 44.1kHz, 1024 block, 2ch - optimized for laptops")
        preset_layout.addWidget(self.realtek_btn)

        # Generic USB preset
        self.usb_btn = QPushButton("🎧 USB Audio")
        self.usb_btn.clicked.connect(self.apply_usb_preset)
        self.usb_btn.setToolTip("USB Audio: 48kHz, 512 block, 2ch - low latency")
        preset_layout.addWidget(self.usb_btn)

        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # Game Detection (v3.0) - Enhanced with process details
        self.game_group = QGroupBox("🎮 Game Detection")
        game_layout = QVBoxLayout()

        # Detection status with LED
        detection_status_layout = QHBoxLayout()
        self.game_detection_led = QLabel("●")
        self.game_detection_led.setStyleSheet("color: #666; font-size: 14pt;")
        detection_status_layout.addWidget(self.game_detection_led)
        self.game_detection_status = QLabel("Scanning...")
        self.game_detection_status.setStyleSheet("font-size: 10pt; font-weight: bold; color: #888;")
        detection_status_layout.addWidget(self.game_detection_status)
        detection_status_layout.addStretch()
        game_layout.addLayout(detection_status_layout)

        # Process details frame
        self.process_frame = QFrame()
        self.process_frame.setStyleSheet("""
            QFrame {
                background-color: #0a0a0a;
                border: 1px solid #333;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        process_frame_layout = QVBoxLayout(self.process_frame)
        process_frame_layout.setSpacing(2)
        process_frame_layout.setContentsMargins(8, 5, 8, 5)

        # Process name
        self.process_name_label = QLabel("Process: —")
        self.process_name_label.setStyleSheet("font-size: 9pt; color: #aaa; font-family: monospace;")
        process_frame_layout.addWidget(self.process_name_label)

        # PID
        self.process_pid_label = QLabel("PID: —")
        self.process_pid_label.setStyleSheet("font-size: 9pt; color: #888; font-family: monospace;")
        process_frame_layout.addWidget(self.process_pid_label)

        # Memory usage
        self.process_memory_label = QLabel("Memory: —")
        self.process_memory_label.setStyleSheet("font-size: 9pt; color: #888; font-family: monospace;")
        process_frame_layout.addWidget(self.process_memory_label)

        # Window title
        self.process_window_label = QLabel("Window: —")
        self.process_window_label.setStyleSheet("font-size: 9pt; color: #888; font-family: monospace;")
        self.process_window_label.setWordWrap(True)
        process_frame_layout.addWidget(self.process_window_label)

        game_layout.addWidget(self.process_frame)

        # Audio initialization status
        self.audio_init_frame = QFrame()
        self.audio_init_frame.setStyleSheet("""
            QFrame {
                background-color: #0a0a0a;
                border: 1px solid #333;
                border-radius: 5px;
                padding: 3px;
            }
        """)
        audio_init_layout = QHBoxLayout(self.audio_init_frame)
        audio_init_layout.setContentsMargins(8, 3, 8, 3)

        self.audio_init_led = QLabel("●")
        self.audio_init_led.setStyleSheet("color: #666; font-size: 12pt;")
        audio_init_layout.addWidget(self.audio_init_led)

        self.audio_init_label = QLabel("Audio: Not initialized")
        self.audio_init_label.setStyleSheet("font-size: 9pt; color: #888;")
        audio_init_layout.addWidget(self.audio_init_label)
        audio_init_layout.addStretch()

        game_layout.addWidget(self.audio_init_frame)

        # Games list (shows all known games, highlights active)
        games_header = QLabel("🎯 Games:")
        games_header.setStyleSheet("font-size: 9pt; font-weight: bold; color: #aaa; margin-top: 5px;")
        game_layout.addWidget(games_header)

        self.games_list_label = QLabel("—")
        self.games_list_label.setStyleSheet("font-size: 9pt; color: #666;")
        self.games_list_label.setWordWrap(True)
        self.games_list_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        game_layout.addWidget(self.games_list_label)

        # Engines list (shows all known engines, highlights active)
        engines_header = QLabel("⚙️ Engines:")
        engines_header.setStyleSheet("font-size: 9pt; font-weight: bold; color: #aaa; margin-top: 3px;")
        game_layout.addWidget(engines_header)

        self.engines_list_label = QLabel("—")
        self.engines_list_label.setStyleSheet("font-size: 9pt; color: #666;")
        self.engines_list_label.setWordWrap(True)
        self.engines_list_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        game_layout.addWidget(self.engines_list_label)

        # Launchers list (shows all known launchers, highlights active)
        launchers_header = QLabel("🚀 Launchers:")
        launchers_header.setStyleSheet("font-size: 9pt; font-weight: bold; color: #aaa; margin-top: 3px;")
        game_layout.addWidget(launchers_header)

        self.launchers_list_label = QLabel("—")
        self.launchers_list_label.setStyleSheet("font-size: 9pt; color: #666;")
        self.launchers_list_label.setWordWrap(True)
        self.launchers_list_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        game_layout.addWidget(self.launchers_list_label)

        self.game_group.setLayout(game_layout)
        layout.addWidget(self.game_group)

        # Audio Sources (v3.0)
        self.sources_group = QGroupBox("🔊 Audio Sources")
        sources_layout = QVBoxLayout()

        # Active sources label
        self.active_sources_label = QLabel("Active: 0")
        self.active_sources_label.setStyleSheet("font-size: 9pt; font-weight: bold; color: #00FF00;")
        sources_layout.addWidget(self.active_sources_label)

        # Active sources list (compact)
        self.active_sources_list = QLabel("—")
        self.active_sources_list.setStyleSheet("font-size: 9pt; color: #00DD00;")
        self.active_sources_list.setWordWrap(True)
        self.active_sources_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sources_layout.addWidget(self.active_sources_list)

        # Inactive sources label
        self.inactive_sources_label = QLabel("Inactive: 0")
        self.inactive_sources_label.setStyleSheet("font-size: 9pt; font-weight: bold; color: #FF6666;")
        sources_layout.addWidget(self.inactive_sources_label)

        # Inactive sources list (compact)
        self.inactive_sources_list = QLabel("—")
        self.inactive_sources_list.setStyleSheet("font-size: 9pt; color: #DD6666;")
        self.inactive_sources_list.setWordWrap(True)
        self.inactive_sources_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sources_layout.addWidget(self.inactive_sources_list)

        self.sources_group.setLayout(sources_layout)
        layout.addWidget(self.sources_group)

        # Status
        status_group = QGroupBox(tr('status'))
        status_layout = QVBoxLayout()

        self.rms_label = QLabel(f"{tr('rms')} --- dBFS")
        status_layout.addWidget(self.rms_label)

        self.backend_label = QLabel(f"{tr('backend')} sounddevice")
        status_layout.addWidget(self.backend_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        layout.addStretch()

        # Set scroll content and add scroll area to main layout
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Set minimum width for proper display
        self.setMinimumWidth(280)

        self.refresh_devices()

    def refresh_devices(self):
        """Refresh device list"""
        self.device_combo.clear()
        self.device_delegate.device_names.clear()
        self.device_delegate.device_statuses.clear()

        devices = self.audio.list_devices()

        idx = 0
        for dev in devices:
            if dev['type'] in ['input', 'loopback']:
                label = f"{dev['name']} ({dev['channels']}ch, {dev['samplerate']}Hz) [{dev['backend']}]"
                self.device_combo.addItem(label, dev)

                # Store device info in delegate for coloring
                is_active = dev.get('is_default', False) or dev['type'] == 'loopback'
                self.device_delegate.set_device_info(idx, dev['name'], is_active)
                idx += 1

        log(f"Refreshed devices: found {len(devices)}", "INFO")

    def apply_settings(self):
        """Apply current settings to audio engine"""
        self.audio.sample_rate = int(self.samplerate_combo.currentText())
        self.audio.blocksize = int(self.blocksize_combo.currentText())
        self.audio.channels = int(self.channels_combo.currentText())

        dev_data = self.device_combo.currentData()
        if dev_data:
            if dev_data['backend'] == 'sounddevice':
                self.audio.device = dev_data['index']
                self.audio.use_loopback = False
                self.backend_label.setText(f"{tr('backend')} sounddevice")
            else:
                self.audio.use_loopback = True
                self.backend_label.setText(f"{tr('backend')} soundcard (loopback)")

        log(f"Applied settings: SR={self.audio.sample_rate}, BS={self.audio.blocksize}, CH={self.audio.channels}", "INFO")

    def apply_sb_preset(self):
        """Apply Sound Blaster Z SE preset"""
        self.samplerate_combo.setCurrentText('48000')
        self.blocksize_combo.setCurrentText('2048')
        self.channels_combo.setCurrentText('2')
        # Try to auto-select Sound Blaster device
        self._auto_select_device(['sound blaster', 'soundblaster', 'sb z', 'creative'])
        log("Applied SB Z SE preset", "INFO")

    def apply_realtek_preset(self):
        """Apply Laptop/Realtek preset - optimized for integrated audio"""
        self.samplerate_combo.setCurrentText('44100')
        self.blocksize_combo.setCurrentText('1024')
        self.channels_combo.setCurrentText('2')
        # Try to auto-select Realtek device
        self._auto_select_device(['realtek', 'high definition audio', 'hd audio'])
        log("Applied Realtek/Laptop preset", "INFO")

    def apply_usb_preset(self):
        """Apply USB Audio preset - low latency for external devices"""
        self.samplerate_combo.setCurrentText('48000')
        self.blocksize_combo.setCurrentText('512')
        self.channels_combo.setCurrentText('2')
        # Try to auto-select USB device
        self._auto_select_device(['usb', 'external', 'headset'])
        log("Applied USB Audio preset", "INFO")

    def _auto_select_device(self, keywords):
        """Auto-select device matching any of the keywords"""
        for i in range(self.device_combo.count()):
            dev_data = self.device_combo.itemData(i)
            if dev_data:
                name_lower = dev_data['name'].lower()
                if any(kw in name_lower for kw in keywords):
                    self.device_combo.setCurrentIndex(i)
                    log(f"Auto-selected device: {dev_data['name']}", "INFO")
                    return
        log(f"No device found matching: {keywords}", "DEBUG")

    def on_loopback_toggled(self, checked):
        """Handle loopback mode toggle"""
        if checked:
            self.audio.use_loopback = True
            self.backend_label.setText(f"{tr('backend')} soundcard (loopback)")
        else:
            self.audio.use_loopback = False
            self.backend_label.setText(f"{tr('backend')} sounddevice")

    def set_audio_scanner(self, scanner):
        """Set reference to audio scanner for device tracking"""
        self.audio_scanner = scanner

    def on_device_changed(self, index):
        """Handle device selection change"""
        if index >= 0:
            self.device_delegate.active_device_index = index
            dev_data = self.device_combo.currentData()
            if dev_data:
                # Update status indicator
                self.device_status_led.setStyleSheet("color: #0f0; font-size: 14pt;")
                self.device_status_text.setText(f"Selected: {dev_data['name'][:30]}...")
                self.device_status_text.setStyleSheet("color: #0f0; font-size: 9pt;")
                log(f"Device selected: {dev_data['name']}", "INFO")

                # Notify audio scanner of selected device
                if hasattr(self, 'audio_scanner') and self.audio_scanner:
                    self.audio_scanner.set_selected_device(dev_data['name'], dev_data.get('index', -1))

            self.device_combo.update()

    def update_game_detection_info(self, game_info, scan_result=None):
        """Update game detection panel with process details and lists"""
        if game_info and game_info.get('detected'):
            # Game detected - show green
            self.game_detection_led.setStyleSheet("color: #0f0; font-size: 14pt;")
            self.game_detection_status.setText(tr('game_detected'))
            self.game_detection_status.setStyleSheet("font-size: 10pt; font-weight: bold; color: #0f0;")

            # Update process details
            self.process_name_label.setText(f"{tr('process')}: {game_info.get('process_name', '—')}")
            self.process_name_label.setStyleSheet("font-size: 9pt; color: #0f0; font-family: monospace;")

            self.process_pid_label.setText(f"{tr('pid')}: {game_info.get('pid', '—')}")
            self.process_pid_label.setStyleSheet("font-size: 9pt; color: #0dd; font-family: monospace;")

            memory_mb = game_info.get('memory_mb', 0)
            self.process_memory_label.setText(f"{tr('memory')}: {memory_mb:.1f} MB")
            self.process_memory_label.setStyleSheet("font-size: 9pt; color: #dd0; font-family: monospace;")

            window = game_info.get('window_title', '—')
            if len(window) > 40:
                window = window[:40] + "..."
            self.process_window_label.setText(f"{tr('window')}: {window}")

        else:
            # No game detected - show gray
            self.game_detection_led.setStyleSheet("color: #666; font-size: 14pt;")
            self.game_detection_status.setText(tr('no_game_detected'))
            self.game_detection_status.setStyleSheet("font-size: 10pt; font-weight: bold; color: #888;")

            self.process_name_label.setText(f"{tr('process')}: —")
            self.process_name_label.setStyleSheet("font-size: 9pt; color: #888; font-family: monospace;")
            self.process_pid_label.setText(f"{tr('pid')}: —")
            self.process_pid_label.setStyleSheet("font-size: 9pt; color: #888; font-family: monospace;")
            self.process_memory_label.setText(f"{tr('memory')}: —")
            self.process_memory_label.setStyleSheet("font-size: 9pt; color: #888; font-family: monospace;")
            self.process_window_label.setText(f"{tr('window')}: —")

        # Update lists if scan_result provided
        if scan_result:
            self._update_detection_lists(scan_result)

    def _update_detection_lists(self, scan_result):
        """Update games, engines, launchers lists with highlighting"""
        active_games = scan_result.get('games', [])
        active_engines = scan_result.get('engines', [])
        active_launchers = scan_result.get('launchers', [])

        # Get all known items from game detector
        if self.game_detector:
            known = self.game_detector.get_all_known_items()
            all_games = known.get('all_games', [])
            all_engines = known.get('all_engines', [])
            all_launchers = known.get('all_launchers', [])
        else:
            all_games = active_games
            all_engines = active_engines
            all_launchers = active_launchers

        # Build HTML for games list
        games_html = self._build_list_html(all_games, active_games, limit=12)
        self.games_list_label.setText(games_html)

        # Build HTML for engines list
        engines_html = self._build_list_html(all_engines, active_engines, limit=8)
        self.engines_list_label.setText(engines_html)

        # Build HTML for launchers list
        launchers_html = self._build_list_html(all_launchers, active_launchers, limit=6)
        self.launchers_list_label.setText(launchers_html)

    def _build_list_html(self, all_items, active_items, limit=10):
        """Build HTML string with active items highlighted in green"""
        if not all_items:
            return "—"

        # Sort: active items first, then alphabetically
        sorted_items = sorted(all_items, key=lambda x: (x not in active_items, x))

        # Limit items shown
        display_items = sorted_items[:limit]
        remaining = len(sorted_items) - limit

        parts = []
        for item in display_items:
            if item in active_items:
                # Active - bright green with indicator
                parts.append(f'<span style="color: #0f0; font-weight: bold;">● {item}</span>')
            else:
                # Inactive - gray
                parts.append(f'<span style="color: #555;">{item}</span>')

        html = ', '.join(parts)
        if remaining > 0:
            html += f' <span style="color: #444;">+{remaining} more</span>'

        return html

    def update_audio_init_status(self, is_initialized, is_receiving_audio=False):
        """Update audio initialization status indicator"""
        if is_initialized and is_receiving_audio:
            # Fully working - green
            self.audio_init_led.setStyleSheet("color: #0f0; font-size: 12pt;")
            self.audio_init_label.setText("Audio: ✓ Receiving audio data")
            self.audio_init_label.setStyleSheet("font-size: 9pt; color: #0f0;")
        elif is_initialized:
            # Initialized but no audio - yellow
            self.audio_init_led.setStyleSheet("color: #dd0; font-size: 12pt;")
            self.audio_init_label.setText("Audio: ✓ Initialized (no signal)")
            self.audio_init_label.setStyleSheet("font-size: 9pt; color: #dd0;")
        else:
            # Not initialized - red
            self.audio_init_led.setStyleSheet("color: #f00; font-size: 12pt;")
            self.audio_init_label.setText("Audio: ✗ Not initialized")
            self.audio_init_label.setStyleSheet("font-size: 9pt; color: #f00;")

    def set_game_detector(self, detector):
        """Set reference to game detector for updates"""
        self.game_detector = detector

    def update_device_activity(self, active_device_names):
        """Update device activity status for highlighting

        Args:
            active_device_names: List of device names that are currently active
        """
        active_lower = [name.lower() for name in active_device_names]

        for idx, name in self.device_delegate.device_names.items():
            is_active = any(active in name.lower() or name.lower() in active
                          for active in active_lower)
            self.device_delegate.device_statuses[idx] = 'active' if is_active else 'inactive'

        # Force redraw of combo box
        self.device_combo.update()

    def update_translations(self):
        """Update UI translations"""
        # Update group box titles
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and isinstance(item.widget(), QGroupBox):
                gb = item.widget()
                # Get the translation key based on current title
                if 'Audio Device' in gb.title() or 'Urządzenie Audio' in gb.title():
                    gb.setTitle(tr('audio_device'))
                elif 'Audio Settings' in gb.title() or 'Ustawienia Audio' in gb.title():
                    gb.setTitle(tr('audio_settings'))
                elif 'Mode' in gb.title() or 'Tryb' in gb.title():
                    gb.setTitle(tr('mode'))
                elif 'Presets' in gb.title() or 'Presety' in gb.title():
                    gb.setTitle(tr('presets'))
                elif 'Status' in gb.title():
                    gb.setTitle(tr('status'))

        # Update labels and buttons
        self.select_device_label.setText(tr('select_device'))
        self.refresh_btn.setText(tr('refresh_devices'))
        self.test_mode.setText(tr('test_mode'))
        self.loopback_mode.setText(tr('loopback_mode'))
        self.sb_btn.setText(tr('sb_preset'))

        # Update backend label
        if self.audio.use_loopback:
            self.backend_label.setText(f"{tr('backend')} soundcard (loopback)")
        else:
            self.backend_label.setText(f"{tr('backend')} sounddevice")


# ============================================================================
# SOUND CLASSIFIER (Module 7 - v3.2.0)
# ============================================================================





