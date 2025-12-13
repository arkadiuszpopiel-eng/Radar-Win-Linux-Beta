"""
RadarSuite v4.2.0 - Configuration Manager
ADDED v3.5.0: Auto-save/restore user settings
FIXED v3.5.0: Schema validation to prevent corrupt config
ENHANCED v4.2.0: Type hints, window state persistence
"""

import sys
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .constants import VERSION
from .logger import log

# Type aliases for clarity
ConfigDict = Dict[str, Any]
SchemaDict = Dict[str, Dict[str, Any]]


# ============================================================================
# CONFIG MANAGER (Phase 4 - v3.5.0)
# ============================================================================

class ConfigManager:
    """
    Persistent settings manager for Windows/Linux

    Windows: %APPDATA%/RadarSuite/config.json
    Linux: ~/.config/RadarSuite/config.json

    ADDED v3.5.0: Auto-save/restore user settings
    FIXED v3.5.0: Schema validation to prevent corrupt config
    Optimized for Windows 11 Pro 64-bit
    """

    # FIXED v3.5.0: Config schema for validation
    CONFIG_SCHEMA = {
        "audio": {
            "device": {"type": (type(None), int, str), "required": False},
            "sample_rate": {"type": int, "values": [8000, 16000, 22050, 44100, 48000, 96000]},
            "block_size": {"type": int, "range": (128, 8192)},
            "channels": {"type": int, "values": [1, 2]},
            "loopback": {"type": bool},
            "gain": {"type": (int, float), "range": (0.1, 100.0)},
            "auto_gain": {"type": bool},
            "noise_gate": {"type": (int, float), "range": (-120.0, 0.0)}
        },
        "detection": {
            "walk_threshold": {"type": (int, float), "range": (0, 100)},
            "run_threshold": {"type": (int, float), "range": (0, 100)},
            "shot_threshold": {"type": (int, float), "range": (0, 100)},
            "walk_enabled": {"type": bool},
            "run_enabled": {"type": bool},
            "shot_enabled": {"type": bool}
        },
        "ui": {
            "language": {"type": str, "values": ["en", "pl"]},
            "radar_alpha": {"type": int, "range": (0, 100)},
            "led_alpha": {"type": int, "range": (0, 100)},
            "window_x": {"type": int},
            "window_y": {"type": int},
            "window_width": {"type": int, "range": (800, 4000)},
            "window_height": {"type": int, "range": (600, 3000)},
            "window_maximized": {"type": bool}
        },
        "ml_overlay": {
            "x": {"type": (type(None), int)},
            "y": {"type": (type(None), int)},
            "width": {"type": int, "range": (120, 800)},
            "height": {"type": int, "range": (120, 800)},
            "opacity": {"type": (int, float), "range": (0.3, 1.0)},
            "frameless": {"type": bool},
            "size_preset": {"type": str, "values": ["small", "medium", "large"]},
            "visible": {"type": bool}
        },
        "performance": {
            "use_gpu": {"type": bool},
            "max_workers": {"type": int, "range": (1, 16)}
        }
    }

    def __init__(self):
        # Determine config path based on OS
        if sys.platform == 'win32':
            # Windows: %APPDATA%/RadarSuite
            config_base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        else:
            # Linux/Mac: ~/.config/RadarSuite
            config_base = Path.home() / '.config'

        self.config_dir = config_base / 'RadarSuite'
        self.config_file = self.config_dir / 'config.json'

        # Create directory if not exists
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating config directory: {e}")

        self.default_config = {
            "audio": {
                "device": None,
                "sample_rate": 48000,
                "block_size": 2048,
                "channels": 2,
                "loopback": False,
                "gain": 1.0,
                "auto_gain": False,
                "noise_gate": -60.0
            },
            "detection": {
                "walk_threshold": 35,
                "run_threshold": 35,
                "shot_threshold": 45,
                "walk_enabled": True,
                "run_enabled": True,
                "shot_enabled": True
            },
            "ui": {
                "language": "en",
                "radar_alpha": 100,
                "led_alpha": 80,
                "window_x": 100,
                "window_y": 100,
                "window_width": 1400,
                "window_height": 900,
                "window_maximized": False
            },
            "ml_overlay": {
                "x": 200,
                "y": 200,
                "width": 300,
                "height": 200,
                "opacity": 0.9,
                "frameless": True,
                "size_preset": "medium",
                "visible": False
            },
            "performance": {
                "use_gpu": True,  # AMD OpenCL for RX 7900 GRE
                "max_workers": 4
            },
            "version": VERSION
        }

    def _validate_value(self, key: str, value: Any, schema: Dict[str, Any]) -> Tuple[bool, Optional[Any]]:
        """
        Validate single value against schema (FIXED v3.5.0)

        Returns: (is_valid: bool, validated_value)
        """
        # Type check
        expected_types = schema.get("type", type(None))
        if not isinstance(expected_types, tuple):
            expected_types = (expected_types,)

        if not isinstance(value, expected_types):
            log(f"Config validation: Invalid type for '{key}': {type(value).__name__}, expected {expected_types}", "WARNING")
            return False, None

        # Values check (whitelist)
        if "values" in schema:
            if value not in schema["values"]:
                log(f"Config validation: Invalid value for '{key}': {value}, allowed: {schema['values']}", "WARNING")
                return False, None

        # Range check
        if "range" in schema:
            min_val, max_val = schema["range"]
            if not (min_val <= value <= max_val):
                log(f"Config validation: Value '{key}'={value} out of range {min_val}-{max_val}", "WARNING")
                return False, None

        return True, value

    def _validate_config(self, user_config: ConfigDict) -> ConfigDict:
        """
        Validate user config against schema (FIXED v3.5.0)

        Returns validated config dict (invalid values are skipped)
        """
        validated = {}

        for section, section_schema in self.CONFIG_SCHEMA.items():
            if section not in user_config:
                continue  # Section missing, will use defaults

            validated[section] = {}

            for key, value_schema in section_schema.items():
                if key not in user_config[section]:
                    continue  # Key missing, will use default

                user_value = user_config[section][key]

                # Validate value
                is_valid, validated_value = self._validate_value(
                    f"{section}.{key}",
                    user_value,
                    value_schema
                )

                if is_valid:
                    validated[section][key] = validated_value
                # Else: skip invalid value, will use default

        return validated

    def load(self) -> ConfigDict:
        """Load settings from disk (FIXED v3.5.0: with validation)"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)

                # FIXED v3.5.0: Validate before merge
                validated_config = self._validate_config(user_config)

                # Merge with defaults (validated values override defaults)
                merged = self._merge_configs(self.default_config, validated_config)
                merged['version'] = VERSION

                log(f"Config loaded: {len(validated_config)} sections validated", "INFO")
                return merged
            else:
                log("Config file not found, using defaults", "INFO")
                return self.default_config.copy()

        except json.JSONDecodeError as e:
            log(f"Invalid JSON in config file: {e}", "ERROR")
            return self.default_config.copy()
        except Exception as e:
            log(f"Error loading settings: {e}", "ERROR")
            return self.default_config.copy()

    def save(self, config: ConfigDict) -> None:
        """Save settings to disk"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            config['version'] = VERSION

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving settings: {e}")

    def _merge_configs(self, default: ConfigDict, user: ConfigDict) -> ConfigDict:
        """Recursively merge user config with defaults"""
        merged = default.copy()

        for key, value in user.items():
            if key in merged:
                if isinstance(value, dict) and isinstance(merged[key], dict):
                    merged[key] = self._merge_configs(merged[key], value)
                else:
                    merged[key] = value
            else:
                merged[key] = value

        return merged

    # ========================================================================
    # CONVENIENCE METHODS (v4.2.0 - ConfigManager Enhancement)
    # ========================================================================

    def get(self, section: str, key: str, default=None):
        """
        Get a config value with dotted path support.

        Args:
            section: Config section (e.g., 'audio', 'ui')
            key: Key within section (e.g., 'device', 'language')
            default: Default value if not found

        Returns:
            Config value or default

        Example:
            config_manager.get('ui', 'language', 'en')
        """
        config = self.load()
        return config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value, config: dict = None):
        """
        Set a config value and optionally save.

        Args:
            section: Config section
            key: Key within section
            value: Value to set
            config: Config dict to modify (if None, loads current config)

        Returns:
            Modified config dict
        """
        if config is None:
            config = self.load()

        if section not in config:
            config[section] = {}

        config[section][key] = value
        return config

    def save_window_state(self, window, config: dict = None):
        """
        Save window geometry and state to config (v4.2.0).

        Args:
            window: QMainWindow instance
            config: Config dict to modify (if None, loads current)

        Returns:
            Modified config dict
        """
        if config is None:
            config = self.load()

        if 'ui' not in config:
            config['ui'] = {}

        # Get geometry
        geo = window.geometry()
        config['ui']['window_x'] = geo.x()
        config['ui']['window_y'] = geo.y()
        config['ui']['window_width'] = geo.width()
        config['ui']['window_height'] = geo.height()
        config['ui']['window_maximized'] = window.isMaximized()

        log(f"Window state saved: {geo.width()}x{geo.height()} at ({geo.x()}, {geo.y()})", "DEBUG")
        return config

    def restore_window_state(self, window, config: dict = None):
        """
        Restore window geometry and state from config (v4.2.0).

        Args:
            window: QMainWindow instance
            config: Config dict to read from (if None, loads current)

        Note:
            - Validates geometry is within screen bounds
            - Falls back to defaults if invalid
        """
        if config is None:
            config = self.load()

        ui_config = config.get('ui', {})

        # Get saved values with defaults
        x = ui_config.get('window_x', 100)
        y = ui_config.get('window_y', 100)
        width = ui_config.get('window_width', 1400)
        height = ui_config.get('window_height', 900)
        maximized = ui_config.get('window_maximized', False)

        # Validate bounds (ensure window is visible)
        try:
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            if screen:
                screen_geo = screen.availableGeometry()
                # Ensure window is at least partially visible
                x = max(0, min(x, screen_geo.width() - 100))
                y = max(0, min(y, screen_geo.height() - 100))
                width = min(width, screen_geo.width())
                height = min(height, screen_geo.height())
        except Exception as e:
            log(f"Could not validate screen bounds: {e}", "WARNING")

        # Apply geometry
        window.setGeometry(x, y, width, height)

        # Restore maximized state
        if maximized:
            window.showMaximized()

        log(f"Window state restored: {width}x{height} at ({x}, {y}), maximized={maximized}", "DEBUG")
