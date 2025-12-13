"""
RadarSuite v4.2.0 - Core Module
Essential application components

FIXED v4.2.0: ARC Raiders-specific constants and features
"""

# Constants
from .constants import (
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
    # ARC Raiders constants (v4.2.0)
    TRANSIENT_WINDOW_MS,
    TRANSIENT_THRESHOLD_RATIO,
    TRANSIENT_ATTACK_MS,
    SHOT_CLOSE_DISTANCE_M,
    SHOT_FREQ_MIN_HZ,
    SHOT_FREQ_MAX_HZ,
    SHOT_BASS_THRESHOLD,
    FOOTSTEP_FREQ_MIN_HZ,
    FOOTSTEP_FREQ_MAX_HZ,
    FOOTSTEP_WALK_INTERVAL_S,
    FOOTSTEP_RUN_INTERVAL_S,
    FOOTSTEP_INTERVAL_TOLERANCE,
    SURFACE_METAL_FREQ_PEAK_HZ,
    SURFACE_DIRT_FREQ_PEAK_HZ,
    SURFACE_SNOW_FREQ_PEAK_HZ,
    MACHINE_DETECTION_WINDOW_S,
    MACHINE_MODULATION_THRESHOLD,
    MACHINE_BASS_MIN_HZ,
    MACHINE_BASS_MAX_HZ,
    EQUIPMENT_FREQ_MIN_HZ,
    EQUIPMENT_FREQ_MAX_HZ,
    EQUIPMENT_SPECTRAL_FLATNESS,
    MFCC_NUM_COEFFS,
    MEL_NUM_BANDS,
    MEL_FREQ_MIN_HZ,
    MEL_FREQ_MAX_HZ,
    CLASSIFICATION_CONFIDENCE_MIN,
    NIGHT_MODE_COMPRESSION_RATIO,
)

# Paths (v4.2.1-k0008 - centralized directory management)
from .paths import (
    APP_ROOT,
    LOG_DIR,
    REPORT_DIR,
    SUPER_LOG_FILE,
    get_selftest_log_path,
    get_selftest_report_path,
    get_ml_training_report_path,
)

# Version metadata / build identification
from .version import get_build_id

# Logger
from .logger import (
    ThreadSafeLogger,
    log,
    ROOT,
    SUPER_LOG,
)

# Config
from .config import ConfigManager

# Translations
from .translations import (
    TRANSLATIONS,
    current_language,
    tr,
    set_language,
    get_language,
)

# Dependency Injection (Point 11 - v3.5.0)
from .di import (
    ServiceContainer,
    get_container,
    configure_services,
)

# Error Handler (v4.2.0 - Punkt 7)
from .error_handler import (
    RadarSuiteError,
    AudioError,
    DetectionError,
    ConfigurationError,
    UIError,
    ErrorSeverity,
    handle_errors,
    safe_call,
    log_and_suppress,
    ErrorContext,
    ErrorReporter,
    get_error_reporter,
    report_error,
    get_error_summary,
)

# Performance Profiler (v4.2.0 - Punkt 9)
from .profiler import (
    PerformanceProfiler,
    get_profiler,
    profile,
    measure,
    timed,
)

__all__ = [
    # Constants
    'VERSION',
    'SAMPLE_RATE',
    'BLOCK_SIZE',
    'CHANNELS',
    'TICK_INTERVAL_MS',
    'GAME_SCAN_INTERVAL_MS',
    'AUDIO_SCAN_INTERVAL_MS',
    'STARTUP_DELAY_MS',
    'STARTUP_AUDIO_DELAY_MS',
    'ENERGY_THRESHOLD',
    'LOCALIZATION_MIN_CONFIDENCE',
    'RADAR_ROTATION_DEG',
    'MAX_WORKERS',
    'DETECTION_TIMEOUT_SEC',
    'CLEANUP_INTERVAL_SEC',
    'AUDIO_LEVEL_LOUD',
    'AUDIO_LEVEL_MEDIUM',
    'AUDIO_LEVEL_LOW',
    'RECORDING_BUFFER_SIZE',
    'RECORDING_FLUSH_INTERVAL',
    'TOAST_DURATION_MS',
    'TOAST_MAX_COUNT',

    # Paths (v4.2.1-k0008)
    'APP_ROOT',
    'LOG_DIR',
    'REPORT_DIR',
    'SUPER_LOG_FILE',
    'get_selftest_log_path',
    'get_selftest_report_path',
    'get_ml_training_report_path',

    # Logger
    'ThreadSafeLogger',
    'log',
    'ROOT',
    'SUPER_LOG',

    # Config
    'ConfigManager',

    # Translations
    'TRANSLATIONS',
    'current_language',
    'tr',
    'set_language',
    'get_language',

    # Dependency Injection
    'ServiceContainer',
    'get_container',
    'configure_services',

    # Error Handler (v4.2.0)
    'RadarSuiteError',
    'AudioError',
    'DetectionError',
    'ConfigurationError',
    'UIError',
    'ErrorSeverity',
    'handle_errors',
    'safe_call',
    'log_and_suppress',
    'ErrorContext',
    'ErrorReporter',
    'get_error_reporter',
    'report_error',
    'get_error_summary',

    # Performance Profiler (v4.2.0)
    'PerformanceProfiler',
    'get_profiler',
    'profile',
    'measure',
    'timed',
]
