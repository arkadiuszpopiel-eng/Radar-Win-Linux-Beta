"""Configuration management module."""

import json
import os
from pathlib import Path
from typing import Any, Dict


class Config:
    """Configuration manager for the YOLO detection system."""

    def __init__(self, config_path: str = None):
        """Initialize configuration.

        Args:
            config_path: Path to config file. If None, uses default.
        """
        if config_path is None:
            # Use default config
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "default_config.json"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file.

        Returns:
            Configuration dictionary.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return json.load(f)

    def save(self, path: str = None):
        """Save current configuration to file.

        Args:
            path: Path to save config. If None, uses current config_path.
        """
        save_path = Path(path) if path else self.config_path
        with open(save_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., 'model.confidence_threshold')
            default: Default value if key not found.

        Returns:
            Configuration value.
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., 'model.confidence_threshold')
            value: Value to set.
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def __getitem__(self, key: str) -> Any:
        """Get top-level configuration section.

        Args:
            key: Section name.

        Returns:
            Configuration section.
        """
        return self.config[key]

    def __setitem__(self, key: str, value: Any):
        """Set top-level configuration section.

        Args:
            key: Section name.
            value: Section value.
        """
        self.config[key] = value
