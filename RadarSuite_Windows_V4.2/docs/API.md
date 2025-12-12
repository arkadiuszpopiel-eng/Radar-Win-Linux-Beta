# RadarSuite V4.2.1 - API Documentation

## Architecture Overview

RadarSuite is a real-time audio detection and spatial tracking system built with PyQt5. The application uses a modular architecture with clear separation of concerns:

```
RadarSuite_Windows_V4.2/
├── app/
│   ├── core/           # Core functionality (config, DI, logging, translations)
│   ├── audio/          # Audio capture and processing
│   ├── detection/      # Sound detection algorithms
│   ├── ml/             # Machine learning models
│   ├── tracking/       # Target tracking and threat assessment
│   ├── widgets/        # UI components (radar, spectrum, panels)
│   ├── ui/             # UI builders
│   ├── utils/          # Utilities (game detection, audio scanner)
│   ├── hardware/       # Hardware-specific support (GPU, Sound Blaster)
│   └── main.py         # Application entry point
└── build_tools/        # PyInstaller spec files
```

## Key Modules

### 1. Core Modules (`core/`)

#### `core/constants.py`
Application-wide constants (sample rate, block size, thresholds, etc.)

```python
# Example usage
from core import SAMPLE_RATE, BLOCK_SIZE, CHANNELS

# Audio configuration
SAMPLE_RATE = 48000  # 48 kHz (FMOD/UE5 standard)
BLOCK_SIZE = 2048    # ~42.7 ms @ 48 kHz
CHANNELS = 2         # Stereo
```

#### `core/config.py`
Configuration management with persistence

```python
from core.config import config

# Get configuration value
sample_rate = config.get('audio.sample_rate', default=48000)

# Set configuration value
config.set('detection.profile', 'ARC Raiders')

# Save configuration
config.save()
```

#### `core/logger.py`
Centralized logging system

```python
from core.logger import log

log("Application started", "INFO")
log("Detection failed: no audio", "WARNING")
log("Fatal error occurred", "ERROR")
```

#### `core/translations.py`
Multi-language support (EN/PL)

```python
from core.translations import tr, set_language, get_language

# Set language
set_language('pl')  # 'en' or 'pl'

# Translate key
button_text = tr('start')  # Returns "START" (EN) or "START" (PL)
tab_name = tr('tab_radar_view')  # Returns "Radar View" or "Widok Radaru"
```

#### `core/export_import.py` (NEW v4.2.1)
Configuration and ML model export/import

```python
from core.export_import import get_export_import_manager

manager = get_export_import_manager()

# Export configuration
export_path = manager.export_configuration(
    output_path=None,  # Auto-generate filename
    include_models=True,
    include_training_data=False
)

# Import configuration
results = manager.import_configuration(
    import_path="radarsuite_config_20251207_120000.zip",
    overwrite_existing=True
)

# List available exports
exports = manager.list_exports()
```

---

### 2. Audio Modules (`audio/`)

#### `audio/engine.py`
Main audio engine with sounddevice/soundcard backends

```python
from audio import AudioEngine

# Initialize audio engine
audio = AudioEngine()

# Start audio capture
audio.start()

# Get latest audio block
block = audio.get_latest_block()  # Returns numpy array (samples x channels)

# Stop audio
audio.stop()
```

#### `audio/cache.py`
FFT caching for performance optimization

```python
from audio.cache import AudioProcessingCache

# Create cache
cache = AudioProcessingCache(max_size=5)

# Compute FFT (cached)
result = cache.compute_fft(block, sample_rate=48000)
# Returns: {'fft_data', 'freqs', 'power', 'mono', 'windowed', 'timestamp'}

# Get cache statistics
stats = cache.get_stats()  # {'hits', 'misses', 'hit_rate', 'size'}

# Memory optimization (NEW v4.2.1)
memory_bytes = cache.get_memory_usage()
cache.cleanup_old_entries(max_age_seconds=300)
cache.clear()  # Clear all cached data
```

#### `audio/voice_detector.py`
Human voice detection with spectral analysis

```python
from audio import HumanVoiceDetector

detector = HumanVoiceDetector(sample_rate=48000)

result = detector.detect(audio_block)
# Returns: {'is_voice', 'confidence', 'pitch_hz', 'formants', ...}
```

---

### 3. Detection Modules (`detection/`)

#### `detection/footstep.py`
Human footstep detection with surface type classification

```python
from detection import HumanFootstepDetector

detector = HumanFootstepDetector(sample_rate=48000)

result = detector.analyze_footstep(audio_block, sample_rate=48000)
# Returns: {
#   'is_human_step': bool,
#   'confidence': float,
#   'gait_type': 'WALK' | 'RUN',
#   'surface': 'metal' | 'dirt' | 'snow' | 'concrete' | 'wood',
#   'distance_m': float
# }
```

#### `detection/shot.py`
Shot/explosion detection with distance estimation

```python
from detection import ShotDetector

detector = ShotDetector(sample_rate=48000)

result = detector.detect(audio_block)
# Returns: {
#   'type': 'close_shot' | 'distant_shot' | 'explosion',
#   'weapon_type': 'rifle' | 'pistol' | 'shotgun' | 'sniper' | 'explosive',
#   'distance_estimate': float,  # meters
#   'confidence': float
# }
```

#### `detection/machine.py`
ARC machine state detection (idle/patrol/search/combat)

```python
from detection import ARCMachineDetector

detector = ARCMachineDetector(sample_rate=48000)

result = detector.detect(audio_block)
# Returns: {
#   'state': 'idle' | 'patrol' | 'search' | 'combat',
#   'confidence': float,
#   'modulation_depth': float
# }
```

#### `detection/spectral.py`
Spectral feature extraction (MFCC, centroid, rolloff, flatness)

```python
from detection import SpectralFeatureExtractor

extractor = SpectralFeatureExtractor(sample_rate=48000)

# Extract all features
features = extractor.extract_all_features(audio_block)
# Returns: {
#   'mfcc': ndarray,           # 13 MFCC coefficients
#   'spectral_centroid': float,
#   'spectral_rolloff': float,
#   'spectral_flatness': float,
#   'band_energy_ratio': dict  # {'bass', 'mid', 'high'}
# }
```

---

### 4. Machine Learning Modules (`ml/`)

#### `ml/detector.py`
ML-based sound classification (YAMNet integration)

```python
from ml import get_ml_detector

detector = get_ml_detector()

# Check if ML is available
if detector.is_ml_enabled:
    result = detector.predict(audio_block)
    # Returns: {'class', 'confidence', 'probabilities'}
```

#### `ml/training/` (NEW v4.2.1)
ML training pipeline for custom models

```python
from ml.training import SessionManager, LabeledRecorder, ModelTrainer

# Create training session
session_manager = SessionManager()
session = session_manager.create_session(game="ARC Raiders")

# Record audio with labels
recorder = LabeledRecorder(session_manager)
recorder.start_recording()
recorder.add_label("WALK", timestamp=5.2)
recorder.add_label("SHOT", timestamp=8.7)
recorder.stop_recording()

# Train model
trainer = ModelTrainer(session_manager)
trainer.train_from_session(session.session_id)
```

---

### 5. Tracking Modules (`tracking/`)

#### `tracking/target.py`
Multi-target tracking with Kalman filtering

```python
from tracking import Target

# Create target
target = Target(
    x=10.5, y=20.3,
    target_type="FOOTSTEP",
    confidence=0.85
)

# Update target position
target.update(x=11.2, y=20.8, confidence=0.90)

# Get target info
info = target.get_info()
# Returns: {'x', 'y', 'type', 'confidence', 'age', 'velocity', ...}
```

#### `tracking/threat.py`
Threat level assessment

```python
from tracking import ThreatAssessor

assessor = ThreatAssessor()

threat_level = assessor.assess_threat(target)
# Returns: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
```

---

### 6. Widget Modules (`widgets/`)

#### `widgets/radar.py`
Military-style 2D and 3D radar displays

```python
from widgets.radar import MilitaryHUDRadar, Military3DRadar

# 2D Radar
radar_2d = MilitaryHUDRadar()
radar_2d.add_target(x=10, y=20, target_type="WALK", confidence=0.9)
radar_2d.update()

# 3D Radar (OpenGL)
radar_3d = Military3DRadar()
radar_3d.add_target(x=10, y=20, z=5, target_type="SHOT")
```

#### `widgets/spectrum.py`
Spectrum/waterfall/waveform visualization

```python
from widgets.spectrum import (
    MilitarySpectrumWidget,
    MilitaryWaterfallWidget,
    MilitaryWaveformWidget
)

# FFT Spectrum
spectrum = MilitarySpectrumWidget()
spectrum.update_from_cache(fft_result)

# Waterfall (spectrogram)
waterfall = MilitaryWaterfallWidget()
waterfall.push_row(power_row)

# Waveform
waveform = MilitaryWaveformWidget()
waveform.update_waveform(audio_block)
```

#### `widgets/ml_waveform.py` (NEW v4.2.1)
Advanced waveform widget for ML training with labeling

```python
from widgets.ml_waveform import MLWaveformWidget

widget = MLWaveformWidget()

# Load audio
widget.load_audio(audio_data, sample_rate=48000)

# Zoom/pan
widget.zoom_in()
widget.zoom_out()
widget.zoom_reset()

# Add label markers
widget.set_current_label_class("FOOTSTEP")
widget.add_label_marker(time=5.2, label_class="FOOTSTEP")

# Get all labels
labels = widget.get_all_labels()
# Returns: [{'time', 'label_class', 'description'}, ...]

# Signals
widget.label_added.connect(on_label_added)
widget.label_removed.connect(on_label_removed)
```

#### `widgets/detection_panel.py`
Detection configuration panel

```python
from widgets import DetectionPanel

panel = DetectionPanel()

# Access controls
profile = panel.profile_combo.currentText()
walk_enabled = panel.walk_enable.isChecked()
sensitivity = panel.walk_sens.value()
```

#### `widgets/device_panel.py`
Audio device selection and configuration

```python
from widgets import DevicePanel

panel = DevicePanel(audio_engine)

# Refresh devices
panel.refresh_devices()

# Get selected device
device_index = panel.device_combo.currentIndex()
```

---

### 7. Utilities (`utils/`)

#### `utils/game_detector.py`
Detect running games and engines

```python
from utils import GameDetector

detector = GameDetector()

# Scan for games
games = detector.detect_games()
# Returns: [{'name', 'process', 'engine', 'audio_profile'}, ...]

# Scan for launchers
launchers = detector.detect_launchers()
```

#### `utils/audio_scanner.py`
Scan and monitor audio sources

```python
from utils import AudioScanner

scanner = AudioScanner()

# Scan active sources
active_sources = scanner.get_active_sources()
inactive_sources = scanner.get_inactive_sources()
```

---

## Common Workflows

### Workflow 1: Audio Detection Pipeline

```python
# 1. Initialize components
from audio import AudioEngine
from audio.cache import AudioProcessingCache
from detection import HumanFootstepDetector, ShotDetector
from tracking import Target

audio = AudioEngine()
cache = AudioProcessingCache()
footstep_detector = HumanFootstepDetector()
shot_detector = ShotDetector()

# 2. Start audio capture
audio.start()

# 3. Process audio in loop
while True:
    # Get audio block
    block = audio.get_latest_block()

    # Compute FFT (cached)
    fft_result = cache.compute_fft(block, sample_rate=48000)

    # Detect footsteps
    footstep_result = footstep_detector.analyze_footstep(block)
    if footstep_result['is_human_step']:
        print(f"Footstep: {footstep_result['gait_type']} on {footstep_result['surface']}")

    # Detect shots
    shot_result = shot_detector.detect(block)
    if shot_result:
        print(f"Shot: {shot_result['type']} at ~{shot_result['distance_estimate']}m")

# 4. Cleanup
audio.stop()
cache.clear()
```

### Workflow 2: ML Training Session

```python
from ml.training import SessionManager, LabeledRecorder
from widgets.ml_waveform import MLWaveformWidget

# 1. Create session
session_manager = SessionManager()
session = session_manager.create_session(game="ARC Raiders", profile="SB Z SE")

# 2. Record audio
recorder = LabeledRecorder(session_manager)
recorder.start_recording()

# ... user adds labels via UI ...

recorder.stop_recording()

# 3. Visualize and label
widget = MLWaveformWidget()
widget.load_audio(recorder.get_audio_data(), sample_rate=48000)

# User adds labels via mouse clicks
widget.label_added.connect(lambda t, c: recorder.add_label(c, timestamp=t))

# 4. Export labeled data
labels = widget.get_all_labels()
session_manager.save_labels(session.session_id, labels)
```

### Workflow 3: Configuration Export/Import

```python
from core.export_import import get_export_import_manager

manager = get_export_import_manager()

# Export on main PC
export_path = manager.export_configuration(
    include_models=True,
    include_training_data=False
)
print(f"Exported to: {export_path}")

# Import on different PC
results = manager.import_configuration(
    import_path=export_path,
    overwrite_existing=True
)

if results['success']:
    print(f"Imported: {results['models_imported']} models")
```

---

## Performance Optimization

### Memory Management (NEW v4.2.1)

```python
from audio.cache import AudioProcessingCache

cache = AudioProcessingCache(max_size=5)

# Monitor memory usage
memory_mb = cache.get_memory_usage() / (1024 * 1024)
print(f"Cache using {memory_mb:.2f} MB")

# Cleanup old entries (older than 5 minutes)
cache.cleanup_old_entries(max_age_seconds=300)

# Full cache clear
cache.clear()
```

### GPU Acceleration

```python
from hardware.gpu import GPUAccelerator

gpu = GPUAccelerator()

if gpu.is_available():
    # FFT acceleration
    fft_result = gpu.fft_optimized(audio_signal)
```

---

## Internationalization (i18n)

All UI strings should use the translation system:

```python
from core.translations import tr

# Good ✅
button = QPushButton(tr('start'))
label = QLabel(tr('detection_profile'))

# Bad ❌
button = QPushButton("START")  # Hardcoded
```

Available translation keys: See `core/translations.py` for full list.

---

## Error Handling

Use centralized logging for all errors:

```python
from core.logger import log

try:
    result = detector.detect(audio_block)
except Exception as e:
    log(f"Detection failed: {e}", "ERROR")
```

---

## Version History

- **v4.2.1** (2025-12-07): Layout fixes, translations, ML waveform widget, export/import, memory optimization
- **v4.2.0** (2025-11-28): MFCC, spectral features, shot/surface detection, ML training
- **v4.1.2**: Adaptive noise floor, type-aware tracking
- **v4.0.0**: Split Windows/Linux versions
- **v3.5.0**: Modularization, GPU acceleration

---

## Support

For issues or questions:
- See `README_V4.2.md` for features
- Check `REFACTORING_PLAN.md` for architecture
- Review `WORK_SUMMARY_V4.2.md` for implementation details
