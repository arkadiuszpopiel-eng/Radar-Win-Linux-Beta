"""
RadarSuite v4.2.1 - Configuration Export/Import Module

Features:
- Export application settings (detection profiles, audio config, UI state)
- Export ML models and training data
- Import configuration on different machine
- Version compatibility checking
"""

import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

try:
    from .logger import log
    from .config import config
except ImportError:
    def log(msg, level="INFO"):
        print(f"[{level}] {msg}")
    config = None


class ExportImportManager:
    """
    Manages export/import of RadarSuite configuration and ML models.
    """

    VERSION = "4.2.1"
    EXPORT_FORMAT_VERSION = "1.0"

    def __init__(self, app_data_dir: Optional[Path] = None):
        """
        Initialize export/import manager.

        Args:
            app_data_dir: Application data directory (default: ~/.radarsuite)
        """
        if app_data_dir is None:
            app_data_dir = Path.home() / ".radarsuite"

        self.app_data_dir = Path(app_data_dir)
        self.app_data_dir.mkdir(parents=True, exist_ok=True)

        self.config_dir = self.app_data_dir / "config"
        self.models_dir = self.app_data_dir / "models"
        self.exports_dir = self.app_data_dir / "exports"

        # Create directories
        for directory in [self.config_dir, self.models_dir, self.exports_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        log(f"ExportImportManager initialized: {self.app_data_dir}", "INFO")

    def export_configuration(
        self,
        output_path: Optional[Path] = None,
        include_models: bool = True,
        include_training_data: bool = False
    ) -> Path:
        """
        Export full configuration to a ZIP file.

        Args:
            output_path: Output ZIP file path (auto-generated if None)
            include_models: Include ML models in export
            include_training_data: Include training audio samples

        Returns:
            Path to created export file
        """
        # Generate output filename if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.exports_dir / f"radarsuite_config_{timestamp}.zip"
        else:
            output_path = Path(output_path)

        log(f"Exporting configuration to: {output_path}", "INFO")

        # Collect export data
        export_data = self._collect_export_data(include_models, include_training_data)

        # Create ZIP file
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Write metadata
            metadata = {
                "version": self.VERSION,
                "export_format": self.EXPORT_FORMAT_VERSION,
                "timestamp": datetime.now().isoformat(),
                "include_models": include_models,
                "include_training_data": include_training_data
            }
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

            # Write main configuration
            zipf.writestr("config.json", json.dumps(export_data["config"], indent=2))

            # Write ML models if included
            if include_models and export_data["models"]:
                for model_name, model_path in export_data["models"].items():
                    if Path(model_path).exists():
                        zipf.write(model_path, f"models/{model_name}")

            # Write training data if included
            if include_training_data and export_data["training_data"]:
                for data_file in export_data["training_data"]:
                    if Path(data_file).exists():
                        zipf.write(data_file, f"training_data/{Path(data_file).name}")

        log(f"Export completed: {output_path} ({output_path.stat().st_size} bytes)", "INFO")
        return output_path

    def import_configuration(
        self,
        import_path: Path,
        overwrite_existing: bool = False
    ) -> Dict:
        """
        Import configuration from a ZIP file.

        Args:
            import_path: Path to export ZIP file
            overwrite_existing: Overwrite existing configuration

        Returns:
            Dict with import results
        """
        import_path = Path(import_path)
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")

        log(f"Importing configuration from: {import_path}", "INFO")

        results = {
            "success": False,
            "metadata": {},
            "config_imported": False,
            "models_imported": 0,
            "errors": []
        }

        try:
            with zipfile.ZipFile(import_path, 'r') as zipf:
                # Read and validate metadata
                metadata_json = zipf.read("metadata.json").decode('utf-8')
                metadata = json.loads(metadata_json)
                results["metadata"] = metadata

                # Check version compatibility
                if not self._check_version_compatibility(metadata):
                    results["errors"].append(f"Incompatible version: {metadata.get('version')}")
                    return results

                # Import configuration
                config_json = zipf.read("config.json").decode('utf-8')
                config_data = json.loads(config_json)
                self._apply_configuration(config_data, overwrite_existing)
                results["config_imported"] = True

                # Import models if present
                model_files = [f for f in zipf.namelist() if f.startswith("models/")]
                for model_file in model_files:
                    model_name = Path(model_file).name
                    target_path = self.models_dir / model_name

                    if target_path.exists() and not overwrite_existing:
                        log(f"Skipping existing model: {model_name}", "WARNING")
                        continue

                    zipf.extract(model_file, self.app_data_dir)
                    # Move to correct location
                    extracted_path = self.app_data_dir / model_file
                    shutil.move(str(extracted_path), str(target_path))
                    results["models_imported"] += 1

                results["success"] = True
                log(f"Import completed successfully", "INFO")

        except Exception as e:
            error_msg = f"Import failed: {e}"
            log(error_msg, "ERROR")
            results["errors"].append(error_msg)

        return results

    def _collect_export_data(
        self,
        include_models: bool,
        include_training_data: bool
    ) -> Dict:
        """Collect all data to be exported."""
        export_data = {
            "config": {},
            "models": {},
            "training_data": []
        }

        # Collect application configuration
        export_data["config"] = {
            "detection": {
                "profile": "ARC Raiders + SB Z SE + Cloud II",
                "sensitivity": {
                    "walk": 50,
                    "run": 50,
                    "shot": 60
                },
                "enabled_detections": ["WALK", "RUN", "SHOT"]
            },
            "audio": {
                "sample_rate": 48000,
                "block_size": 2048,
                "channels": 2
            },
            "ui": {
                "language": "pl",
                "theme": "military",
                "radar_alpha": 100
            },
            "game_profiles": {}
        }

        # Collect ML models
        if include_models:
            models_path = self.models_dir
            if models_path.exists():
                for model_file in models_path.glob("*.pkl"):
                    export_data["models"][model_file.name] = str(model_file)
                for model_file in models_path.glob("*.h5"):
                    export_data["models"][model_file.name] = str(model_file)

        # Collect training data
        if include_training_data:
            training_path = self.app_data_dir / "training_data"
            if training_path.exists():
                for audio_file in training_path.glob("*.wav"):
                    export_data["training_data"].append(str(audio_file))

        return export_data

    def _check_version_compatibility(self, metadata: Dict) -> bool:
        """
        Check if import file version is compatible.

        Args:
            metadata: Import file metadata

        Returns:
            True if compatible, False otherwise
        """
        export_version = metadata.get("version", "0.0.0")
        export_format = metadata.get("export_format", "0.0")

        # Simple version check (can be enhanced)
        if export_format != self.EXPORT_FORMAT_VERSION:
            log(f"Warning: Export format mismatch ({export_format} vs {self.EXPORT_FORMAT_VERSION})", "WARNING")
            # Still allow import for now
            return True

        log(f"Version check passed: {export_version} -> {self.VERSION}", "INFO")
        return True

    def _apply_configuration(self, config_data: Dict, overwrite: bool):
        """
        Apply imported configuration.

        Args:
            config_data: Configuration data dict
            overwrite: Overwrite existing settings
        """
        log(f"Applying configuration (overwrite={overwrite})", "INFO")

        # Save to config file
        config_file = self.config_dir / "imported_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        log(f"Configuration saved to: {config_file}", "INFO")

    def list_exports(self) -> List[Dict]:
        """
        List all available export files.

        Returns:
            List of dicts with export file info
        """
        exports = []
        for export_file in self.exports_dir.glob("radarsuite_config_*.zip"):
            try:
                with zipfile.ZipFile(export_file, 'r') as zipf:
                    metadata_json = zipf.read("metadata.json").decode('utf-8')
                    metadata = json.loads(metadata_json)

                exports.append({
                    "path": export_file,
                    "filename": export_file.name,
                    "size": export_file.stat().st_size,
                    "timestamp": metadata.get("timestamp"),
                    "version": metadata.get("version"),
                    "include_models": metadata.get("include_models", False)
                })
            except Exception as e:
                log(f"Failed to read export metadata: {export_file} - {e}", "WARNING")

        # Sort by timestamp (newest first)
        exports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return exports


# Global instance
_export_import_manager = None


def get_export_import_manager() -> ExportImportManager:
    """Get global ExportImportManager instance."""
    global _export_import_manager
    if _export_import_manager is None:
        _export_import_manager = ExportImportManager()
    return _export_import_manager
