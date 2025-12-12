# Module Reference - RadarSuite V4.2.0

Complete API documentation for all modules.

---

## Table of Contents

1. [Core Modules](#core-modules)
2. [Audio Modules](#audio-modules)
3. [Detection Modules](#detection-modules)
4. [Tracking Modules](#tracking-modules)
5. [Utility Modules](#utility-modules)
6. [Hardware Modules](#hardware-modules)
7. [Widget Modules](#widget-modules)

---

## Core Modules

### `core/constants.py`

Centralized application constants.

**Exports:**
```python
# Version
VERSION: str                      # Current version (from version.py)

# Audio
SAMPLE_RATE: int                  # 48000 Hz
BLOCK_SIZE: int                   # 2048 samples
CHANNELS: int                     # 2 (stereo)

# Performance
TICK_INTERVAL_MS: int             # 50 ms (20 FPS)
GAME_SCAN_INTERVAL_MS: int        # 5000 ms
AUDIO_SCAN_INTERVAL_MS: int       # 2000 ms

# Detection
ENERGY_THRESHOLD: float           # 0.001
LOCALIZATION_MIN_CONFIDENCE: int  # 30
RADAR_ROTATION_DEG: float         # 4.0

# Worker threads
MAX_WORKERS: int                  # 3
DETECTION_TIMEOUT_SEC: float      # 5.0
CLEANUP_INTERVAL_SEC: float       # 10.0

# ARC Raiders specific
TRANSIENT_WINDOW_MS: int          # 10
SHOT_CLOSE_DISTANCE_M: int        # 30
FOOTSTEP_WALK_INTERVAL_S: float   # 0.6
MACHINE_DETECTION_WINDOW_S: float # 2.0
```

### `core/config.py`

Configuration persistence.

**Class: ConfigManager**
```python
def load() -> dict:
    """Load configuration from %APPDATA%/RadarSuite/config.json"""

def save(config: dict) -> None:
    """Save configuration to disk"""

def get_default() -> dict:
    """Get default configuration"""
```

**Example:**
```python
from core.config import ConfigManager

manager = ConfigManager()
config = manager.load()
print(config['audio']['sample_rate'])  # 48000
```

### `core/di.py`

Dependency Injection container.

**Class: ServiceContainer**
```python
def register(name: str, instance: Any) -> None:
    """Register service instance"""

def get(name: str) -> Any:
    """Resolve service by name"""

def has(name: str) -> bool:
    """Check if service registered"""
```

**Example:**
```python
from core.di import ServiceContainer

container = ServiceContainer()
container.register('audio_engine', AudioEngine())
engine = container.get('audio_engine')
```

### `core/logger.py`

Centralized logging.

**Functions:**
```python
def log(message: str, level: str = "INFO") -> None:
    """
    Log message with level (DEBUG, INFO, WARNING, ERROR)
    Outputs to console + log file
    """
```

**Example:**
```python
from core.logger import log

log("Detection started", "INFO")
log("Error in FFT computation", "ERROR")
```

---

## Audio Modules

### `audio/engine.py`

Audio I/O abstraction.

**Class: AudioEngine**
```python
def __init__(sample_rate: int = 48000, block_size: int = 2048):
    """Initialize audio engine"""

def start(device_id: int, loopback: bool = False) -> None:
    """Start audio capture"""

def stop() -> None:
    """Stop audio capture"""

def read() -> np.ndarray:
    """Read audio block (shape: [block_size, channels])"""

@property
def is_running() -> bool:
    """Check if audio capture active"""
```

**Example:**
```python
from audio.engine import AudioEngine

engine = AudioEngine(sample_rate=48000, block_size=2048)
engine.start(device_id=0, loopback=True)

block = engine.read()  # Shape: (2048, 2)
engine.stop()
```

### `audio/cache.py`

FFT result caching for performance.

**Class: AudioProcessingCache**
```python
def __init__(max_size: int = 5, gpu_accelerator=None):
    """Initialize cache with max size"""

def compute_fft(block: np.ndarray, sample_rate: int) -> dict:
    """
    Compute or retrieve cached FFT
    Returns: {'fft': np.ndarray, 'freqs': np.ndarray, 'power': np.ndarray}
    """

def clear() -> None:
    """Clear all cached FFT results"""
```

**Thread safety:** Uses `threading.Lock` for concurrent access

**Example:**
```python
from audio.cache import AudioProcessingCache

cache = AudioProcessingCache(max_size=5)
fft_result = cache.compute_fft(block, 48000)
print(fft_result['fft'].shape)  # (1025,) for 2048 samples
```

### `audio/classifier.py`

Sound classification (weapon types).

**Class: SoundClassifier**
```python
def classify_sound(block: np.ndarray, sample_rate: int, fft_cache=None) -> dict:
    """
    Classify sound type
    Returns: {
        'type': str,           # 'rifle', 'pistol', 'shotgun', 'sniper', etc.
        'confidence': float,   # 0-100
        'details': dict        # Additional classification data
    }
    """
```

**Example:**
```python
from audio.classifier import SoundClassifier

classifier = SoundClassifier()
result = classifier.classify_sound(block, 48000)
print(f"{result['type']} with {result['confidence']}% confidence")
```

### `audio/recorder.py`

Audio session recording.

**Class: AudioRecorder**
```python
def __init__(sample_rate: int = 48000):
    """Initialize recorder"""

def start_recording(filename: str) -> None:
    """Start recording to WAV file"""

def add_block(block: np.ndarray) -> None:
    """Add audio block to recording"""

def stop_recording() -> dict:
    """
    Stop recording and save metadata
    Returns: {'duration': float, 'size': int, 'blocks': int}
    """
```

**Example:**
```python
from audio.recorder import AudioRecorder

recorder = AudioRecorder(sample_rate=48000)
recorder.start_recording("session_001.wav")

# During audio capture loop
recorder.add_block(block)

# When done
metadata = recorder.stop_recording()
print(f"Recorded {metadata['duration']:.1f} seconds")
```

---

## Detection Modules

### `detection/worker.py`

Parallel detection processing (V4.2.0 refactored).

**Class: DetectionResult**
```python
def __init__(success: bool, data: Any = None, error: Optional[str] = None):
    """Detection result with explicit error handling"""

@property
def success() -> bool:
    """True if detection succeeded"""

@property
def data() -> Any:
    """Detection data (only if success=True)"""

@property
def error() -> Optional[str]:
    """Error message (only if success=False)"""
```

**Class: DetectionWorker**
```python
MAX_ACTIVE_FUTURES_MULTIPLIER = 2  # Backpressure limit

def __init__(max_workers: int = MAX_WORKERS):
    """Initialize worker pool"""

def submit_detection(det_panel, block, sample_rate, fft_cache) -> Optional[Future]:
    """
    Submit detection task to worker pool
    Returns: Future[DetectionResult] or None (if rejected due to backpressure)
    """

def submit_classification(classifier, block, sample_rate, fft_cache) -> Optional[Future]:
    """
    Submit classification task to worker pool
    Returns: Future[DetectionResult] or None
    """

def shutdown(timeout: float = DETECTION_TIMEOUT_SEC) -> None:
    """Shutdown worker pool with timeout"""

@property
def is_shutdown() -> bool:
    """Check if worker pool shut down"""

def get_active_task_count() -> int:
    """Get number of active tasks"""
```

**Example (V4.2.0):**
```python
from detection.worker import DetectionWorker

worker = DetectionWorker(max_workers=3)

# Submit detection task
future = worker.submit_detection(det_panel, block, 48000, fft_cache)

if future:
    try:
        result = future.result(timeout=1.0)
        if result.success:
            events = result.data['events']
            bands = result.data['bands']
        else:
            log(f"Detection failed: {result.error}", "WARNING")
    except TimeoutError:
        log("Detection timed out", "WARNING")
else:
    log("Worker rejected task (backpressure)", "DEBUG")

# Shutdown when done
worker.shutdown(timeout=5.0)
```

### `detection/footstep.py`

Footstep detection with surface type classification.

**Class: HumanFootstepDetector**
```python
def analyze_footstep(block: np.ndarray, sample_rate: int) -> dict:
    """
    Analyze footstep sound
    Returns: {
        'is_human_step': bool,
        'gait_type': str,         # 'walk', 'run', or 'unknown'
        'surface': str,           # 'metal', 'dirt', 'snow', 'concrete', 'wood'
        'distance_m': float,
        'confidence': float       # 0-100
    }
    """

def classify_surface_type(spectral_centroid: float) -> str:
    """
    Classify surface from spectral centroid
    Returns: 'metal', 'dirt', 'snow', 'concrete', or 'wood'
    """
```

**Example:**
```python
from detection.footstep import HumanFootstepDetector

detector = HumanFootstepDetector(sample_rate=48000)
result = detector.analyze_footstep(block, 48000)

if result['is_human_step']:
    print(f"{result['gait_type']} on {result['surface']}, {result['distance_m']:.1f}m away")
```

### `detection/shot.py`

Shot/explosion detection with weapon classification.

**Class: ShotDetector**
```python
def detect(block: np.ndarray, sample_rate: int = 48000) -> Optional[dict]:
    """
    Detect shot/explosion
    Returns: {
        'type': str,              # 'close_shot', 'distant_shot', 'explosion'
        'weapon_type': str,       # 'rifle', 'pistol', 'shotgun', 'sniper', 'explosive'
        'distance_estimate': float,  # meters
        'confidence': float       # 0-100
    } or None if no shot detected
    """

def detect_transient(block: np.ndarray) -> bool:
    """Detect sharp transient (indicative of gunshot)"""

def classify_shot_type(block: np.ndarray, fft_data: np.ndarray) -> str:
    """Classify as 'close_shot', 'distant_shot', or 'explosion'"""
```

**Example:**
```python
from detection.shot import ShotDetector

detector = ShotDetector(sample_rate=48000)
result = detector.detect(block)

if result:
    print(f"{result['weapon_type']} at ~{result['distance_estimate']}m")
```

### `detection/machine.py`

ARC machine state detection.

**Class: ARCMachineDetector**
```python
def detect(block: np.ndarray, sample_rate: int = 48000) -> Optional[dict]:
    """
    Detect ARC machine state
    Returns: {
        'state': str,             # 'idle', 'patrol', 'search', 'combat'
        'confidence': float,      # 0-100
        'modulation_depth': float # 0-1
    } or None if no machine detected
    """

def extract_bass_envelope(block: np.ndarray) -> np.ndarray:
    """Extract bass frequency envelope (50-300 Hz)"""

def analyze_modulation(envelope: np.ndarray) -> float:
    """Compute temporal modulation depth"""

def classify_machine_state(modulation_depth: float) -> str:
    """
    Classify machine state from modulation:
    - idle: 5-15% (steady hum)
    - patrol: 15-30% (rhythmic movement)
    - search: 30-50% (irregular scanning)
    - combat: 50-100% (aggressive)
    """
```

### `detection/spectral.py`

Spectral feature extraction (MFCC, centroid, etc.).

**Class: SpectralFeatureExtractor**
```python
def __init__(sample_rate: int = 48000, n_mfcc: int = 13, n_mels: int = 40):
    """Initialize with sample rate and MFCC parameters"""

def extract_mfcc(block: np.ndarray) -> np.ndarray:
    """
    Extract MFCC coefficients
    Returns: np.ndarray of shape (n_mfcc,)
    """

def extract_spectral_centroid(fft_data: np.ndarray, freqs: np.ndarray) -> float:
    """Compute spectral centroid (center of mass of spectrum)"""

def extract_spectral_rolloff(fft_data: np.ndarray, freqs: np.ndarray) -> float:
    """Compute 85% rolloff frequency"""

def extract_spectral_flatness(fft_data: np.ndarray) -> float:
    """Compute flatness (0=tonal, 1=noise)"""

def extract_band_energy_ratio(fft_data: np.ndarray, freqs: np.ndarray,
                               band_low: float, band_high: float) -> float:
    """Compute energy ratio in frequency band"""

def extract_all_features(block: np.ndarray) -> dict:
    """
    Extract all spectral features
    Returns: {
        'mfcc': np.ndarray,
        'centroid': float,
        'rolloff': float,
        'flatness': float
    }
    """
```

---

## Tracking Modules

### `tracking/tracker.py`

Multi-target tracking with temporal filtering.

**Class: TargetTracker**
```python
def __init__(max_targets: int = 3, decay_frames: int = 60):
    """Initialize tracker (max 3 targets, 60 frame decay = 3 sec @ 20 FPS)"""

def update(detections: List[dict]) -> List[dict]:
    """
    Update tracker with new detections
    Args: detections = [{'angle': float, 'distance': float, 'type': str, ...}, ...]
    Returns: List of active targets with IDs
    """

def get_active_targets() -> List[dict]:
    """Get currently tracked targets"""

def clear() -> None:
    """Reset all targets"""
```

**Thread safety:** Uses `threading.Lock`

**Example:**
```python
from tracking.tracker import TargetTracker

tracker = TargetTracker(max_targets=3)

# Each frame
detections = [
    {'angle': 45, 'distance': 25, 'type': 'walk', 'elevation': 0}
]
active_targets = tracker.update(detections)

for target in active_targets:
    print(f"T{target['id']}: {target['type']} at {target['angle']}° / {target['distance']}m")
```

### `tracking/threat.py`

Threat priority ranking.

**Class: ThreatPrioritySystem**
```python
def rank_targets(targets: List[dict]) -> List[dict]:
    """
    Rank targets by threat level
    Modifies each target dict to add 'threat_score' and 'threat_level'
    Returns: Sorted list (highest threat first)
    """

def calculate_threat_score(target: dict) -> float:
    """
    Calculate individual threat score
    Formula: weapon_score × distance_factor × direction_factor + confidence
    """
```

**Scoring constants:**
```python
WEAPON_SCORES = {
    'sniper': 100, 'explosion': 90, 'rifle': 85, 'pistol': 70,
    'shotgun': 75, 'walk': 50, 'run': 55, 'unknown': 30
}

THREAT_CATEGORIES = {
    'CRITICAL': 150,  # Red
    'HIGH': 100,      # Orange
    'MEDIUM': 50,     # Yellow
    'LOW': 0          # Green
}
```

---

## Utility Modules

### `utils/performance.py`

Performance monitoring.

**Class: PerformanceMonitor**
```python
def start_frame() -> None:
    """Mark start of frame"""

def end_frame() -> None:
    """Mark end of frame and compute metrics"""

def get_fps() -> float:
    """Get current FPS"""

def get_latency_ms() -> float:
    """Get frame latency in milliseconds"""

def get_cpu_percent() -> float:
    """Get CPU usage percentage"""

def get_memory_mb() -> float:
    """Get memory usage in MB"""
```

### `utils/game_detector.py`

Game process detection.

**Class: GameProcessDetector**
```python
def scan_processes() -> dict:
    """
    Scan for running games
    Returns: {
        'has_games': bool,
        'games': List[str],      # Game names
        'processes': List[str]   # Process names
    }
    """
```

**Supported games (partial list):**
- ARC Raiders (PioneerGame.exe)
- Escape from Tarkov (EscapeFromTarkov.exe)
- Counter-Strike 2 (cs2.exe)
- VALORANT (VALORANT.exe)
- Hunt: Showdown (Hunt.exe)

### `utils/launcher.py`

Gaming platform launcher detection.

**Class: PlatformLauncherDetector**
```python
def scan_platforms() -> dict:
    """
    Scan for gaming platform launchers
    Returns: {
        'steam': bool,
        'epic': bool,
        'gog': bool,
        'battlenet': bool,
        'ea_app': bool
    }
    """

def detect_game_from_launcher(games: List[str]) -> Optional[dict]:
    """
    Detect game launched from platform
    Returns: {
        'game': str,
        'platform': str,
        'appid': Optional[str]  # Steam AppID if applicable
    }
    """
```

### `utils/audio_scanner.py`

Audio source scanning.

**Class: AudioSourceScanner**
```python
def __init__(platform_detector: PlatformLauncherDetector):
    """Initialize with platform detector"""

def scan_audio_sources() -> List[dict]:
    """
    Scan for active audio sources
    Returns: [{
        'name': str,
        'process': str,
        'is_game': bool,
        'is_filtered': bool  # VoIP, music, browser filtered out
    }, ...]
    """
```

---

## Hardware Modules

### `hardware/gpu.py`

GPU acceleration (NVIDIA CUDA).

**Class: GPUAccelerator**
```python
def __init__(enable_gpu: bool = True):
    """Initialize GPU (auto-detect CUDA)"""

@property
def is_available() -> bool:
    """Check if GPU available"""

def fft_gpu(data: np.ndarray) -> np.ndarray:
    """GPU-accelerated FFT (fallback to CPU if unavailable)"""
```

### `hardware/soundblaster.py`

Sound Blaster Z SE optimizations.

**Class: SoundBlasterOptimizer**
```python
def detect() -> bool:
    """Detect Sound Blaster Z SE hardware"""

def optimize() -> dict:
    """Apply optimizations, returns config dict"""
```

---

## Widget Modules

### `widgets/radar.py`

Radar visualization widgets.

**Class: MilitaryHUDRadar** (2D)
```python
def add_target(target_id: int, angle: float, distance: float,
               state: TargetState, speed: float, label: str) -> None:
    """Add target to radar"""

def clear_targets() -> None:
    """Remove all targets"""

def update_sweep(angle: float) -> None:
    """Update radar sweep line"""

def cleanup_stale_targets(max_age_seconds: float) -> None:
    """Remove targets older than max_age"""
```

**Class: Military3DRadar**
```python
def add_target(target_id: int, angle: float, distance: float, elevation: float) -> None:
    """Add target to 3D radar"""

def clear_targets() -> None:
    """Remove all targets"""
```

### `widgets/led.py`

LED directional overlay.

**Class: LEDOverlay**
```python
def update(targets: List[dict]) -> None:
    """Update LED indicators for targets"""

def set_opacity(opacity: float) -> None:
    """Set overlay opacity (0.0-1.0)"""
```

---

**RadarSuite V4.2.0** - Complete module API reference.
