"""
RadarSuite v4.2.1-k0008 - Centralized Path Management

FIXED v4.2.1-k0008: Unified log and report directory structure
- All logs go to: log/ (dev) or <exe_dir>/log/ (production)
- All reports go to: raport/ (dev) or <exe_dir>/raport/ (production)
- Automatic directory creation on import
- Compatible with PyInstaller frozen executables
"""

import sys
from pathlib import Path


def get_app_root() -> Path:
    """
    Get application root directory

    Returns:
        Path: Root directory of the application
            - PyInstaller (frozen EXE): directory containing the executable
            - Development mode: repository root directory
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller frozen executable
        # sys.executable points to the .exe file
        return Path(sys.executable).resolve().parent
    else:
        # Development mode
        # This file is in app/core/paths.py, so go up 2 levels to reach root
        return Path(__file__).resolve().parent.parent.parent


# ============================================================================
# CENTRAL DIRECTORY DEFINITIONS
# ============================================================================

# Application root directory
APP_ROOT = get_app_root()

# Log directory - all runtime logs, self-test logs, build logs
LOG_DIR = APP_ROOT / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Report directory - all reports, summaries, diagnostic reports
REPORT_DIR = APP_ROOT / "raport"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Legacy paths (for reference/migration)
LEGACY_SUPER_LOG = APP_ROOT / "super_log.txt"


# ============================================================================
# COMMON LOG FILES
# ============================================================================

SUPER_LOG_FILE = LOG_DIR / "super_log.txt"
BUILD_LOG_FILE = LOG_DIR / "build_windows.log"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_selftest_log_path(timestamp: str) -> Path:
    """
    Get path for self-test log file

    Args:
        timestamp: Timestamp string (e.g., "20251209_143052")

    Returns:
        Path: Full path to self-test log file
    """
    return LOG_DIR / f"selftest_{timestamp}.log"


def get_selftest_report_path(timestamp: str) -> Path:
    """
    Get path for self-test report file

    Args:
        timestamp: Timestamp string (e.g., "20251209_143052")

    Returns:
        Path: Full path to self-test report file
    """
    return REPORT_DIR / f"selftest_report_{timestamp}.txt"


def get_ml_training_report_path(profile_name: str) -> Path:
    """
    Get path for ML training report

    Args:
        profile_name: Name of ML training profile

    Returns:
        Path: Full path to ML training report
    """
    return REPORT_DIR / f"ml_training_{profile_name}.json"


def cleanup_legacy_log() -> None:
    """
    One-time cleanup of legacy super_log.txt from repository root

    If old super_log.txt exists in root, move it to log/ as legacy file
    """
    if LEGACY_SUPER_LOG.exists() and LEGACY_SUPER_LOG.is_file():
        try:
            # Move to log directory with legacy prefix
            legacy_destination = LOG_DIR / "legacy_super_log_v2.3.0.txt"

            # Avoid overwriting if legacy file already exists
            if not legacy_destination.exists():
                import shutil
                shutil.move(str(LEGACY_SUPER_LOG), str(legacy_destination))

                # Log the migration (but carefully - logger might not be initialized yet)
                try:
                    from .logger import log
                    log(f"Migrated legacy super_log.txt to {legacy_destination}", "INFO")
                except:
                    # If logger not ready, just print
                    print(f"[paths.py] Migrated legacy super_log.txt to {legacy_destination}")
            else:
                # Legacy file already exists, just remove the old one
                LEGACY_SUPER_LOG.unlink()
        except Exception as e:
            # Silent fail - this is just cleanup
            print(f"[paths.py] Could not migrate legacy super_log.txt: {e}")


# ============================================================================
# AUTO-INITIALIZATION
# ============================================================================

# Run legacy cleanup on module import (one-time operation)
cleanup_legacy_log()


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'get_app_root',
    'APP_ROOT',
    'LOG_DIR',
    'REPORT_DIR',
    'SUPER_LOG_FILE',
    'BUILD_LOG_FILE',
    'get_selftest_log_path',
    'get_selftest_report_path',
    'get_ml_training_report_path',
]
