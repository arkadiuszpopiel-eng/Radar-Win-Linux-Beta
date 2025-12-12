"""
RadarSuite v4.2.0 - Constants Module
All application constants extracted for maintainability (FIX 9)

FIXED v4.2.0: ARC Raiders-specific optimizations
- 48 kHz sample rate (FMOD + UE5 standard)
- Enhanced detection categories
- MFCC and spectral features
"""

# ============================================================================
# VERSION (FIXED v4.2.0: Centralized in version.py)
# ============================================================================

# Import version from centralized version.py
try:
    from version import __version_full__ as VERSION
except ImportError:
    # Fallback if version.py not found (shouldn't happen)
    VERSION = "v4.2.0-ARC-Raiders"

# ============================================================================
# CONSTANTS (FIXED v3.5.0: Extracted magic numbers)
# ============================================================================

# Audio (FIXED v4.2.0: ARC Raiders / FMOD + UE5 standard)
SAMPLE_RATE = 48000  # Hz - 48 kHz standard for FMOD + UE5 (console/PC)
BLOCK_SIZE = 2048    # Samples per block (~42.7 ms @ 48 kHz)
CHANNELS = 2         # Stereo (downmix from 5.1/7.1)

# Performance
TICK_INTERVAL_MS = 50        # Main loop @ 20 FPS
GAME_SCAN_INTERVAL_MS = 5000  # Scan games every 5s
AUDIO_SCAN_INTERVAL_MS = 2000 # Scan audio every 2s
STARTUP_DELAY_MS = 500        # Initial scan delay
STARTUP_AUDIO_DELAY_MS = 1000 # Audio scan delay

# Detection
ENERGY_THRESHOLD = 0.001         # Minimum energy for detection (FIXED v4.1.1: increased 100x to reduce noise)
LOCALIZATION_MIN_CONFIDENCE = 30  # Minimum confidence for target tracking (FIXED v4.1.1)
RADAR_ROTATION_DEG = 4.0         # Degrees per frame

# FIXED v4.2.0: Target confidence thresholds (normalized 0-100%)
TARGET_CONFIDENCE_ALGORITHM_MIN = 30.0  # Minimum confidence to create target (30%)
TARGET_CONFIDENCE_UI_MIN = 50.0         # Minimum confidence to show in UI (50%)
TARGET_CONFIDENCE_THREAT_MIN = 70.0     # Minimum confidence for threat classification (70%)

# FIXED v4.2.0: Radar orientation configuration
RADAR_ORIENTATION_MODE = "player_up"  # "north_up" or "player_up" (head-up mode for ARC Raiders)
RADAR_DEBUG_ORIENTATION = False  # Enable debug logging for orientation calculations

# Worker threads
MAX_WORKERS = 3              # Thread pool size
DETECTION_TIMEOUT_SEC = 5.0  # Worker shutdown timeout
CLEANUP_INTERVAL_SEC = 10.0  # Future cleanup interval

# Audio levels (dBFS)
AUDIO_LEVEL_LOUD = -20      # Green
AUDIO_LEVEL_MEDIUM = -40    # Yellow
AUDIO_LEVEL_LOW = -60       # Orange

# Recording (FIXED v3.5.0: Buffering to reduce I/O)
RECORDING_BUFFER_SIZE = 20   # Blocks before flush (1 sec @ 20 FPS)
RECORDING_FLUSH_INTERVAL = 1.0  # Seconds between flushes

# UI
TOAST_DURATION_MS = 3000     # Default toast display time
TOAST_MAX_COUNT = 3          # Max concurrent toasts

# ============================================================================
# ARC RAIDERS DETECTION PARAMETERS (FIXED v4.2.0)
# ============================================================================

# Transient Detection
TRANSIENT_WINDOW_MS = 10         # Short window for transient detection (ms)
TRANSIENT_THRESHOLD_RATIO = 3.0  # Peak/RMS ratio for transient
TRANSIENT_ATTACK_MS = 20         # Attack time for envelope detection

# Shot Detection (close/distant)
SHOT_CLOSE_DISTANCE_M = 30       # Threshold for close shot (meters)
SHOT_FREQ_MIN_HZ = 200           # Minimum frequency for shot detection
SHOT_FREQ_MAX_HZ = 8000          # Maximum frequency for shot detection
SHOT_BASS_THRESHOLD = 0.3        # Bass energy ratio for explosions

# Footstep Detection (walk/run + surface type)
FOOTSTEP_FREQ_MIN_HZ = 100       # Minimum frequency for footsteps
FOOTSTEP_FREQ_MAX_HZ = 800       # Maximum frequency for footsteps
FOOTSTEP_WALK_INTERVAL_S = 0.6   # Average interval for walking (seconds)
FOOTSTEP_RUN_INTERVAL_S = 0.3    # Average interval for running (seconds)
FOOTSTEP_INTERVAL_TOLERANCE = 0.15  # Tolerance for interval detection

# Surface Type Detection
SURFACE_METAL_FREQ_PEAK_HZ = 400    # Metal surface peak frequency
SURFACE_DIRT_FREQ_PEAK_HZ = 200     # Dirt/earth surface peak frequency
SURFACE_SNOW_FREQ_PEAK_HZ = 150     # Snow surface peak frequency

# Machine Detection (ARC machines - idle/patrol/search/combat)
MACHINE_DETECTION_WINDOW_S = 2.0     # Window for machine state detection
MACHINE_MODULATION_THRESHOLD = 0.1   # Modulation depth threshold
MACHINE_BASS_MIN_HZ = 50             # Machine bass minimum frequency
MACHINE_BASS_MAX_HZ = 300            # Machine bass maximum frequency

# Equipment/Backpack Detection
EQUIPMENT_FREQ_MIN_HZ = 300          # Equipment rustle minimum frequency
EQUIPMENT_FREQ_MAX_HZ = 4000         # Equipment rustle maximum frequency
EQUIPMENT_SPECTRAL_FLATNESS = 0.3    # Spectral flatness threshold

# Spectral Feature Parameters (MFCC)
MFCC_NUM_COEFFS = 13                 # Number of MFCC coefficients
MEL_NUM_BANDS = 40                   # Number of mel bands
MEL_FREQ_MIN_HZ = 20                 # Minimum mel frequency
MEL_FREQ_MAX_HZ = 8000               # Maximum mel frequency

# Classification Thresholds
CLASSIFICATION_CONFIDENCE_MIN = 50   # Minimum confidence for classification
NIGHT_MODE_COMPRESSION_RATIO = 4.0   # Simulated Night Mode compression
