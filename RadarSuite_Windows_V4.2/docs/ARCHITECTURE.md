# Architecture - RadarSuite V4.2.0

System architecture, design patterns, and component interaction.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Threading Model](#threading-model)
6. [Design Patterns](#design-patterns)
7. [Module Dependencies](#module-dependencies)

---

## System Overview

RadarSuite follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│              Presentation Layer                  │ ← PyQt5 GUI
│  (MainWindow, Widgets, Radar, LED, Panels)      │
├─────────────────────────────────────────────────┤
│           Application Layer                      │ ← Business Logic
│  (Detection, Classification, Tracking, Threat)  │
├─────────────────────────────────────────────────┤
│              Service Layer                       │ ← Audio/Hardware
│  (AudioEngine, DetectionWorker, GPU, Cache)     │
├─────────────────────────────────────────────────┤
│               Core Layer                         │ ← Foundation
│  (Constants, Config, DI Container, Logger)      │
└─────────────────────────────────────────────────┘
```

**Key principles:**
- **Dependency Injection** - Loose coupling via IoC container
- **Single Responsibility** - Each module has one clear purpose
- **Thread Safety** - Explicit locking for shared resources
- **Explicit Error Handling** - No silent failures

---

## Architecture Diagram

### High-Level Component View

```
┌────────────┐
│   User     │
│  (Gamer)   │
└─────┬──────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│                    MainWindow (GUI)                      │
│  ┌───────────┬──────────────┬───────────┬────────────┐ │
│  │  Radar    │  Detection   │   Game    │  Analysis  │ │
│  │   Tab     │   & Audio    │ Detection │    Tab     │ │
│  └───────────┴──────────────┴───────────┴────────────┘ │
└──────┬─────────────┬────────────────┬──────────────────┘
       │             │                │
       ▼             ▼                ▼
┌─────────────┐ ┌──────────────┐ ┌─────────────────┐
│   Radar     │ │   Detection  │ │  Performance    │
│  Widgets    │ │    Panel     │ │   Monitor       │
└─────────────┘ └──────────────┘ └─────────────────┘
       │             │                │
       ▼             ▼                ▼
┌──────────────────────────────────────────────────────┐
│              Application Controller                   │
│                   (tick loop)                         │
└──────────┬───────────────────────────┬────────────────┘
           │                           │
           ▼                           ▼
    ┌─────────────┐            ┌──────────────────┐
    │   Target    │            │  DetectionWorker │
    │  Tracker    │            │  (ThreadPool)    │
    └─────────────┘            └─────────┬────────┘
           │                             │
           ▼                             ▼
    ┌─────────────┐            ┌──────────────────┐
    │   Threat    │            │ Detection Panel  │
    │  Priority   │            │   (analyze)      │
    └─────────────┘            └──────────────────┘
                                        │
                ┌───────────────────────┼─────────────────────┐
                ▼                       ▼                     ▼
       ┌──────────────┐       ┌──────────────┐     ┌──────────────┐
       │  Footstep    │       │     Shot     │     │   Machine    │
       │  Detector    │       │   Detector   │     │   Detector   │
       └──────────────┘       └──────────────┘     └──────────────┘
                │                      │                    │
                └──────────────────────┼────────────────────┘
                                       ▼
                            ┌──────────────────────┐
                            │  Spectral Feature    │
                            │     Extractor        │
                            └──────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │   FFT Cache          │
                            │ (AudioProcessing)    │
                            └──────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │   Audio Engine       │
                            │  (sounddevice/       │
                            │   pyaudiowpatch)     │
                            └──────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │   Audio Hardware     │
                            │ (Microphone/Loopback)│
                            └──────────────────────┘
```

---

## Core Components

### 1. Presentation Layer

#### MainWindow (`app/main.py`)
**Responsibility:** Primary application window and coordinator

**Key methods:**
- `__init__()` - Initialize UI and dependencies
- `tick()` - Main update loop (20 FPS)
- `_process_detection_and_tracking()` - Coordinate detection pipeline
- `_update_ui_elements()` - Update radar, LED, and panels
- `start()` / `stop()` - Lifecycle management

**Dependencies:** All subsystems (via DI container or direct creation)

**Status:** God object (1,670 lines) - **refactoring planned** (see REFACTORING_PLAN.md)

#### Widgets (`app/widgets/`)
- `MilitaryHUDRadar` - 2D tactical radar visualization
- `Military3DRadar` - 3D sphere radar with elevation
- `DetectionPanel` - Audio analysis UI
- `DevicePanel` - Audio device configuration
- `LEDOverlay` - Directional indicators

### 2. Application Layer

#### DetectionPanel (`app/widgets/detection_panel.py`)
**Responsibility:** Audio analysis and event detection

**Key methods:**
- `analyze(block, sample_rate, fft_cache)` - Main detection entry point
  - Returns: `(events, bands)` where `events = {'walk': bool, 'run': bool, 'shot': bool}`
- `_detect_walk()`, `_detect_run()`, `_detect_shot()` - Individual detectors

#### TargetTracker (`app/tracking/tracker.py`)
**Responsibility:** Multi-target tracking with temporal filtering

**Key methods:**
- `update(detections)` - Update tracker with new detections
- `get_active_targets()` - Get currently tracked targets
- `clear()` - Reset all targets

**Thread safety:** Uses `threading.Lock` for concurrent access

#### ThreatPrioritySystem (`app/tracking/threat.py`)
**Responsibility:** Rank targets by tactical threat level

**Algorithm:**
```python
threat_score = weapon_score × distance_factor × direction_factor + confidence

Categories:
- CRITICAL: score > 150 (red)
- HIGH: 100-150 (orange)
- MEDIUM: 50-100 (yellow)
- LOW: < 50 (green)
```

### 3. Service Layer

#### DetectionWorker (`app/detection/worker.py`)
**Responsibility:** Parallel detection processing via thread pool

**V4.2.0 improvements:**
- Explicit error handling via `DetectionResult` class
- Backpressure protection (rejects tasks when overloaded)
- Safe cleanup thread (replaces recursive Timer)
- Timeout protection on `.result()` calls

**Key methods:**
- `submit_detection(det_panel, block, sample_rate, fft_cache)` → `Future[DetectionResult]`
- `submit_classification(classifier, block, sample_rate, fft_cache)` → `Future[DetectionResult]`
- `shutdown(timeout)` - Clean shutdown with timeout

#### AudioEngine (`app/audio/engine.py`)
**Responsibility:** Audio I/O abstraction

**Modes:**
- **Microphone** - `sounddevice` for direct capture
- **Loopback** - `pyaudiowpatch` for WASAPI loopback (Windows)

**Configuration:**
- Sample rate: 48000 Hz
- Block size: 2048 samples
- Channels: Stereo (downmix from 5.1/7.1)

#### AudioProcessingCache (`app/audio/cache.py`)
**Responsibility:** FFT result caching (4x performance improvement)

**Thread safety:** Uses `threading.Lock` for cache operations

**V3.5.0 fix:** Thread-safe cache operations prevent race conditions

### 4. Core Layer

#### ServiceContainer (`app/core/di.py`)
**Responsibility:** Dependency Injection container

**Registration:**
```python
container = ServiceContainer()
container.register('audio_engine', AudioEngine())
container.register('detection_worker', DetectionWorker(max_workers=3))
```

**Resolution:**
```python
audio_engine = container.get('audio_engine')
```

#### Constants (`app/core/constants.py`)
**Centralized configuration** for all magic numbers

**Categories:**
- Audio (sample rate, block size, channels)
- Performance (FPS, scan intervals, delays)
- Detection (thresholds, frequency ranges)
- ARC Raiders specific (shot detection, footstep, machine)

#### ConfigManager (`app/core/config.py`)
**Responsibility:** Persist user preferences

**Storage:** `%APPDATA%\RadarSuite\config.json`

---

## Data Flow

### Detection Pipeline (Complete Flow)

```
[Audio Hardware] (48 kHz stereo)
       │
       ▼
[AudioEngine.read()] → audio block (2048 samples)
       │
       ▼
[MainWindow.tick()] ← Main update loop (20 FPS)
       │
       ├─→ [apply_audio_processing()] → gain + noise gate
       │         │
       │         ▼
       ├─→ [FFTCache.compute_fft()] → cached FFT result
       │         │
       │         ▼
       ├─→ [DetectionWorker.submit_detection()] → Future
       │         │
       │         ├─→ [Thread Pool] → DetectionPanel.analyze()
       │         │         │
       │         │         ├─→ _detect_walk() → band energy (40-250 Hz)
       │         │         ├─→ _detect_run() → band energy (200-1200 Hz)
       │         │         └─→ _detect_shot() → band energy (1500-8000 Hz)
       │         │         │
       │         │         └─→ return {'walk': bool, 'run': bool, 'shot': bool}
       │         │
       │         └─→ DetectionResult(success=True, data={'events': ..., 'bands': ...})
       │
       ├─→ [future.result(timeout=1.0)] → events, bands
       │         │
       │         ▼
       ├─→ [compute_precise_location_3d()] → angle, distance, elevation
       │         │
       │         ▼
       ├─→ [DetectionWorker.submit_classification()] → Future
       │         │
       │         └─→ [SoundClassifier.classify_sound()] → weapon type
       │         │
       │         └─→ DetectionResult(success=True, data={'type': 'rifle', 'confidence': 85})
       │
       ├─→ [future.result(timeout=1.0)] → sound_class
       │         │
       │         ▼
       ├─→ [TargetTracker.update(detections)] → active_targets (T1, T2, T3)
       │         │
       │         ▼
       ├─→ [ThreatPrioritySystem.rank_targets()] → sorted by threat
       │         │
       │         ▼
       └─→ [_update_ui_elements()] → Update radar, LED, panels
              │
              ├─→ [Radar2D.add_target()] → Draw target markers
              ├─→ [Radar3D.add_target()] → Draw 3D spheres
              └─→ [LEDOverlay.update()] → Show directional indicators
```

### Error Handling Flow (V4.2.0)

```
[DetectionWorker.submit_detection()]
       │
       ├─→ Check backpressure
       │   │
       │   ├─→ OK → Submit to thread pool → Future
       │   └─→ OVERLOAD → Return None
       │
       ▼
[future.result(timeout=1.0)]
       │
       ├─→ SUCCESS → DetectionResult(success=True, data={...})
       ├─→ TIMEOUT → TimeoutError → Log warning + use defaults
       ├─→ EXCEPTION → DetectionResult(success=False, error="...")
       │
       ▼
[if result.success]
       │
       ├─→ TRUE → Use result.data
       └─→ FALSE → Log error + use fallback defaults
```

---

## Threading Model

### Thread Types

#### 1. Main (GUI) Thread
**Runs:** PyQt5 event loop
**Responsibilities:**
- UI updates
- User input handling
- Timer callbacks (`tick()` every 50 ms)

**Critical:** Never block! Offload heavy work to worker threads.

#### 2. Detection Worker Threads (Pool of 3)
**Type:** `ThreadPoolExecutor(max_workers=3)`
**Responsibilities:**
- FFT computation
- Detection analysis
- Classification

**V4.2.0 improvement:** Explicit error handling prevents silent failures

#### 3. Cleanup Thread (DetectionWorker)
**Type:** Daemon thread
**Responsibilities:**
- Cleanup completed futures every 10 seconds
- Runs until shutdown event set

**V4.2.0 improvement:** Replaced recursive Timer (memory leak fix)

#### 4. Audio Capture Thread
**Type:** Callback thread (sounddevice)
**Responsibilities:**
- Read audio blocks from hardware
- Push to main thread queue

### Thread Safety

**Shared resources protected by locks:**

```python
# TargetTracker
self._lock = threading.Lock()

def update(self, detections):
    with self._lock:
        # Thread-safe update logic
        ...
```

**FFT Cache:**
```python
# AudioProcessingCache
self._lock = threading.Lock()

def compute_fft(self, block, sample_rate):
    with self._lock:
        # Thread-safe cache access
        ...
```

**DetectionWorker:**
```python
self._futures_lock = threading.Lock()
self.shutdown_event = threading.Event()

def _cleanup_done_futures(self):
    with self._futures_lock:
        # Thread-safe cleanup
        ...
```

---

## Design Patterns

### 1. Dependency Injection (IoC Container)

**Purpose:** Loose coupling, easier testing

**Implementation:**
```python
# app/core/di.py
class ServiceContainer:
    def register(self, name, instance):
        self._services[name] = instance

    def get(self, name):
        return self._services[name]

# Usage in MainWindow
def __init__(self, container=None):
    if container:
        self._inject_dependencies(container)  # DI mode
    else:
        self._create_dependencies()  # Legacy mode
```

### 2. Result Object Pattern

**Purpose:** Explicit success/error states

**Implementation:**
```python
# app/detection/worker.py
class DetectionResult:
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

    def __bool__(self):
        return self.success
```

**Usage:**
```python
result = future.result()
if result.success:
    events = result.data['events']
else:
    log(f"Detection failed: {result.error}")
```

### 3. Worker Pool Pattern

**Purpose:** Parallel processing without UI blocking

**Implementation:**
```python
from concurrent.futures import ThreadPoolExecutor

class DetectionWorker:
    def __init__(self, max_workers=3):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit_detection(self, det_panel, block, sample_rate, fft_cache):
        return self._executor.submit(
            self._run_detection, det_panel, block, sample_rate, fft_cache
        )
```

### 4. Facade Pattern (Planned)

**Purpose:** Simplify MainWindow god object

**Implementation (future):**
```python
class ApplicationController:
    """Facade for tick loop coordination"""

    def tick(self):
        self._update_radar()
        self._process_audio()
        self._update_ui()
```

---

## Module Dependencies

### Dependency Graph

```
main.py
├── core/
│   ├── constants.py (no deps)
│   ├── logger.py (no deps)
│   ├── config.py → constants
│   ├── di.py (no deps)
│   └── version.py (no deps)
│
├── audio/
│   ├── engine.py → constants, logger
│   ├── cache.py → constants, logger, hardware/gpu
│   ├── classifier.py → constants, logger
│   ├── recorder.py → constants, logger
│   └── voice_detector.py → constants, logger
│
├── detection/
│   ├── worker.py → constants, logger
│   ├── footstep.py → constants, logger, detection/spectral
│   ├── shot.py → constants, logger, detection/spectral
│   ├── machine.py → constants, logger
│   └── spectral.py → constants, logger
│
├── tracking/
│   ├── tracker.py → constants, logger
│   └── threat.py → constants, logger
│
├── utils/
│   ├── performance.py → constants, logger
│   ├── game_detector.py → constants, logger
│   ├── launcher.py → constants, logger
│   └── audio_scanner.py → constants, logger
│
├── hardware/
│   ├── gpu.py → constants, logger
│   └── soundblaster.py → constants, logger
│
└── widgets/
    ├── radar.py → constants, logger
    ├── led.py → constants, logger
    ├── panels.py → constants, logger
    └── detachable.py → constants, logger
```

**Key principle:** All modules depend on `core/` (constants, logger), but not on each other (loose coupling).

---

## Performance Characteristics

### Latency Budget (Total: ~50 ms)

```
Audio Capture:      ~10 ms (hardware + driver)
FFT Computation:    ~5 ms (with caching)
Detection:          ~8 ms (parallel workers)
UI Update:          ~5 ms (PyQt rendering)
Overhead:           ~2 ms (thread switching, locks)
──────────────────────────────────────────
Total:              ~30 ms actual (20 ms target margin)
```

### Memory Footprint

```
Python Runtime:     ~80 MB
PyQt5 Libraries:    ~60 MB
NumPy Arrays:       ~20 MB (audio buffers + FFT)
Audio Cache:        ~10 MB (5 cached FFTs)
Application Code:   ~5 MB
──────────────────────────────────────────
Total:              ~175 MB typical
```

### CPU Usage

```
Idle (not detecting):   ~5-10%
Active (detecting):     ~12-20%
Heavy load (3 targets): ~25-35%
```

**Note:** With GPU acceleration, CPU drops to ~8-12% during active detection.

---

## V4.2.0 Refactoring Summary

### MainWindow God Object Refactoring

**Before:** `MainWindow` - 2,136 LOC (god object)
**After:** `MainWindow` - 1,767 LOC (-17%)

#### Extracted Components

##### 1. UIBuilder (`app/ui/builder.py`) - 470 LOC
**Responsibility:** Complete UI construction extracted from `create_ui()`

```python
class UIBuilder:
    def __init__(self, main_window: "MainWindow") -> None
    def build(self) -> None
    def _create_main_tabs(self) -> None
    def _build_radar_tab(self) -> None
    def _build_detection_tab(self) -> None
    def _build_game_detection_tab(self) -> None
    def _build_analysis_tab(self) -> None
    def _build_toolbar(self) -> None
    def _build_statusbar(self) -> None
```

##### 2. AudioProcessor (`app/audio/processor.py`) - 377 LOC
**Responsibility:** Audio signal processing and 3D localization

```python
class AudioProcessor:
    def apply_processing(block, auto_gain, manual_gain, noise_gate_db) -> np.ndarray
    def compute_orientation(block) -> Tuple[float, float]
    def compute_location_3d(block) -> Dict[str, float]
    def compute_elevation(block) -> float
```

##### 3. ConfigManager Enhancements (`app/core/config.py`)
**New methods for v4.2.0:**

```python
def get(section: str, key: str, default=None)  # Convenience getter
def set(section: str, key: str, value) -> ConfigDict  # Convenience setter
def save_window_state(window, config=None) -> ConfigDict  # Persist geometry
def restore_window_state(window, config=None) -> None  # Restore geometry
```

### New Core Modules (Punkt 7, 9)

##### ErrorReporter (`app/core/error_handler.py`)
**Centralized error tracking with statistics:**

```python
class ErrorReporter:
    def report(error, context, severity) -> None
    def get_summary() -> dict  # {total, by_type, by_severity, recent}
    def get_error_rate(window_seconds) -> float
    def clear() -> None
```

##### PerformanceProfiler (`app/core/profiler.py`)
**Execution time measurement and bottleneck detection:**

```python
class PerformanceProfiler:
    @profile("operation_name")  # Decorator
    def measure("name")  # Context manager
    def get_report() -> dict  # {slowest, most_called, total_time}
    def get_bottlenecks(threshold_ms) -> List[dict]
```

### Type Hints Added (Punkt 6)

All extracted modules now have comprehensive type hints:
- `ConfigManager`: Type aliases (`ConfigDict`, `SchemaDict`)
- `UIBuilder`: `TYPE_CHECKING` forward references
- `AudioProcessor`: Full numpy/scipy type annotations

---

## Next Steps

- **[Module Reference](MODULES.md)** - Detailed API for each module
- **[Configuration](CONFIGURATION.md)** - Tuning parameters
- **[Refactoring Plan](../REFACTORING_PLAN.md)** - Future architecture improvements

---

**RadarSuite V4.2.0** - Well-architected audio intelligence system.
