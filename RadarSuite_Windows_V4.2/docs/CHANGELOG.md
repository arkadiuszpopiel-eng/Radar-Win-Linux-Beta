# Changelog - RadarSuite

All notable changes to RadarSuite documented here.

---

## [4.2.0] - 2025-12-01

### Added
- **Parallel Detection Processing** - DetectionWorker now actively used (prevents UI freezing)
- **Explicit Error Handling** - DetectionResult class with success/error states
- **Backpressure Protection** - Worker rejects tasks when overloaded (2x pool size limit)
- **Timeout Protection** - 1-second timeout on detection.result() calls
- **Professional Documentation** - Complete docs/ directory with 9 comprehensive guides
- **Refactoring Plan** - Documented god object extraction strategy (REFACTORING_PLAN.md)

### Changed
- **DetectionWorker** - Refactored with thread-safe cleanup (replaces recursive Timer)
- **main.py Header** - Reduced from 147 lines to 12 lines (92% reduction)
- **Detection Flow** - Now uses worker.submit_detection() instead of direct panel.analyze()
- **Classification Flow** - Now uses worker.submit_classification() for parallel processing

### Fixed
- **CRITICAL** - UI freezing during detection (detection now runs in worker threads)
- **CRITICAL** - Memory leak from recursive Timer cleanup (replaced with thread + Event)
- **CRITICAL** - Exception masking in DetectionWorker (explicit DetectionResult)
- **CRITICAL** - Hardcoded max_workers=3 (now uses MAX_WORKERS from constants)
- **Thread Safety** - DetectionWorker cleanup now thread-safe with proper locking

### Technical Details

**DetectionWorker Improvements:**
```python
class DetectionResult:
    """V4.2.0: Explicit success/error handling"""
    success: bool
    data: Any
    error: Optional[str]

class DetectionWorker:
    MAX_ACTIVE_FUTURES_MULTIPLIER = 2  # Backpressure protection

    def _start_cleanup_thread(self):
        """V4.2.0: Safe cleanup (replaces recursive Timer)"""
        # Daemon thread with Event-based shutdown
```

**Integration (main.py):**
```python
# V4.2.0: Parallel detection
future = self.detection_worker.submit_detection(...)
if future:
    result = future.result(timeout=1.0)
    if result.success:
        events = result.data['events']
```

**Documentation:**
- `docs/README.md` - Project overview
- `docs/INSTALLATION.md` - Complete setup guide
- `docs/USAGE.md` - Feature walkthrough
- `docs/ARCHITECTURE.md` - System design
- `docs/MODULES.md` - API reference
- `docs/CONFIGURATION.md` - Parameter tuning
- `docs/BUILD.md` - Build instructions
- `docs/CHANGELOG.md` - This file
- `docs/KNOWN_ISSUES.md` - Limitations

---

## [4.1.2] - 2025-11-25

### Added
- **Adaptive Noise Floor** - Auto-adjusts detection thresholds based on ambient noise
- **Type-Aware Target Matching** - Distinguishes walk/run/shot for tracking
- **Detached Window Cleanup** - Proper cleanup of stale targets (max_age_seconds=3.0)

### Changed
- **Detection Type Classification** - Improved walk vs run distinction
- **Radar Display** - All targets shown, not just primary (multi-target support)
- **2D Radar** - TargetState mapping (WALK, RUN, SHOT, UNKNOWN)

### Fixed
- **Target Tracking** - Low-confidence localizations filtered (<30 confidence)
- **Radar Chaos** - Reduced by filtering unreliable position estimates
- **Stale Targets** - Defensive cleanup every frame (3-second max age)

---

## [4.1.0] - 2025-11-22

### Added
- **Thread-Safe TargetTracker** - `threading.Lock` protection for concurrent access
- **RMS-Based Detection** - More stable than peak-based detection
- **History Copy on Export** - Prevents concurrent modification errors

### Changed
- **Frequency Bands** - Optimized for ARC Raiders:
  - Walk: 40-250 Hz (was 20-200)
  - Run: 200-1200 Hz (was 200-1500)
  - Shot: 1500-8000 Hz (was 1500-6000)
- **Detection Thresholds** - Lowered for better sensitivity:
  - Walk: 0.03 (was 0.04)
  - Run: 0.025 (was 0.03)
  - Shot: 0.05 (was 0.06)

### Fixed
- **CRITICAL** - Duplicate `toggle_start_stop` function (renamed to `toggle_start_stop_shortcut`)
- **CRITICAL** - `setup_shortcuts` using wrong `self.tabs` → `self.main_tabs`
- **Thread Safety** - Race conditions in TargetTracker.update(), get_active_targets(), clear()

### Removed
- Dead code in main.py (duplicate function)

---

## [3.5.3] - 2025-11-15

### Fixed
- Language switching EN/PL with `get_language()` function
- Engine detection with game-to-engine mapping
- `MilitaryHUDRadar.update_sweep` and `update_target` methods
- Game detector connection to DevicePanel
- Audio status "Not initialized" display
- Detection from `mean()` to `max()` for frequency band power (later reverted to RMS in 4.1.0)
- Detection thresholds lowered
- `sp_signal` not defined in classifier.py
- `add_target` TypeError - parameter order
- `re` not defined in launcher.py
- Numpy array truth value ambiguity
- COM initialization error 0x800401f0
- Speaker.recorder() doesn't exist error
- numpy.fromstring deprecation (pyaudiowpatch fallback)

---

## [3.5.0] - 2025-11-10

### Added
- **Complete Testing Suite** - 250+ unit tests with pytest
- **Dependency Injection** - IoC container for testability
- **Toast Notifications** - User feedback system
- **Platform-Specific Builds** - Separate Windows/Linux build scripts
- **Thread-Safe Cache** - AudioProcessingCache with proper locking

### Changed
- **Modularization** - Clean separation: core, audio, detection, tracking, utils, hardware, widgets
- **Relative Imports** - Fixed ModuleNotFoundError issues
- **Type Safety** - Consistent interfaces across modules

### Fixed
- **CRITICAL** - ModuleNotFoundError in main.py (relative imports)
- **CRITICAL** - Missing imports in 15+ modules (time, numpy, deque)
- **CRITICAL** - Thread-safe cache operations
- **Memory Leak** - DetectionWorker cleanup (partially fixed, fully resolved in 4.2.0)

---

## [3.4.1] - 2025-11-05

### Added
- **Gaming Platform Integration** - Steam, Epic, GOG, Battle.net, EA App detection
- **Steam AppID Detection** - Automatic game identification via Steam AppID
- **Epic Games Integration** - -epicapp= parameter detection
- **Launcher Audio Filtering** - Ignores audio from Steam/Discord/Spotify
- **Platform Status Display** - Live launcher status in Tab 3

### Technical Details
- 5 platforms supported (priority: Steam/Epic high, GOG/Battle.net medium, EA low)
- Steam AppID database for 10+ popular games
- Audio blacklist for 15+ processes (launchers, VoIP, browsers)
- Regex parsing for Steam AppID and Epic parameters

---

## [3.4.0] - 2025-11-01

### Added
- **MODULE 12: Performance Optimization**
- **FFT Caching** - Compute once, reuse 4x (eliminates redundant calculations)
- **Performance Monitoring** - Real-time FPS, CPU, memory, latency
- **Multi-threading** - Worker pool for parallel detection (3 threads)
- **Stats Display** - Live FPS and latency in toolbar

### Performance Improvements
- 4x reduction in FFT computations (was: 4/frame, now: 1/frame)
- Real-time metrics tracking
- Latency: <10ms audio-to-radar update (target achieved!)

---

## [3.3.1] - 2025-10-28

### Added
- **Enhanced Game Detection** - Process name, exe path, command line scanning
- **6 New Games** - Destiny 2, Hunt Showdown, The Cycle, Marauders, etc.
- **Improved Patterns** - More detection patterns per game

### Fixed
- **ARC Raiders Detection** - Now detects PioneerGame.exe correctly

---

## [3.3.0] - 2025-10-25

### Added
- **MODULE 8: Threat Priority System** - Ranks targets by danger level
  - Scoring: weapon type + distance + direction + confidence
  - Weapon threats: sniper(100) > explosion(90) > rifle(85) > pistol(70)
  - Direction factor: rear = 1.3x, front = 0.8x
  - Distance factor: <20m = 1.5x, >50m = 0.5x
  - Categories: CRITICAL/HIGH/MEDIUM/LOW
- **MODULE 9: Audio Recording** - WAV + JSON metadata export
  - ⏺ REC button in toolbar
  - 16-bit quality, timestamped filenames
  - Metadata: detections, positions, performance metrics

---

## [3.2.0] - 2025-10-20

### Added
- **MODULE 6: 3D Sound Localization** - ITD + ILD analysis
  - ITD: Cross-correlation for precise azimuth
  - ILD: Volume difference for angle estimation
  - Combined: 70% ITD + 30% ILD
  - Confidence scoring
- **MODULE 7: Sound Classification** - Weapon/vehicle identification
  - 8 types: rifle, pistol, shotgun, sniper, car, helicopter, explosion, grenade
  - Spectral fingerprinting
  - Confidence scoring

---

## [3.1.2] - 2025-10-15

### Added
- **Waveform Widget** - Visual audio signal display
- **Auto-Gain** - Automatic amplification (target -20 dBFS)
- **Manual Gain** - 1x to 100x slider
- **Noise Gate** - Threshold-based noise blocking

---

## [3.1.1] - 2025-10-12

### Fixed
- **CRITICAL** - Added error handling to tick() (prevents application freeze)
- **Quick Setup** - Now properly restarts audio stream
- .gitignore preserves build_tools/*.spec
- More sensitive default thresholds (35, 35, 45)
- Energy threshold lowered 10x for better sensitivity

---

## [3.1.0] - 2025-10-10

### Added
- **Modern Tabbed Interface** - 4 tabs: Radar, Detection, Game Detection, Analysis
- **Real-time Audio Monitoring** - Color-coded level feedback
- **Quick Setup Button** - One-click game audio configuration
- **Auto-Suggestion** - Loopback mode when games detected
- **Live Stats Toolbar** - Targets, audio level, FPS

---

## [3.0.5] - 2025-10-05

### Added
- **Multi-Target Tracking** - Up to 3 simultaneous targets
- **3D Sphere Radar** - Elevation detection
- **Game Detection** - ARC Raiders, Tarkov, CS2, Valorant
- **Human Voice Detection** - Formant analysis, pitch, breathing
- **Footstep Pattern Recognition** - Cadence, L-R, surface, gait

---

## Version History Summary

```
4.2.0 (2025-12-01) - Parallel processing, explicit error handling, professional docs
4.1.2 (2025-11-25) - Adaptive noise floor, type-aware tracking
4.1.0 (2025-11-22) - Thread safety, RMS detection, optimized bands
3.5.3 (2025-11-15) - Bug fixes, language switching
3.5.0 (2025-11-10) - Testing suite, DI container, modularization
3.4.1 (2025-11-05) - Gaming platform integration
3.4.0 (2025-11-01) - Performance optimization (Module 12)
3.3.1 (2025-10-28) - Enhanced game detection
3.3.0 (2025-10-25) - Threat priority, audio recording
3.2.0 (2025-10-20) - 3D localization, classification
3.1.2 (2025-10-15) - Audio processing UI
3.1.1 (2025-10-12) - Critical stability fixes
3.1.0 (2025-10-10) - Modern UI
3.0.5 (2025-10-05) - Foundation release
```

---

## Semantic Versioning

RadarSuite follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** (4.x.x) - Breaking changes, major architecture shifts
- **MINOR** (x.2.x) - New features, backward-compatible
- **PATCH** (x.x.0) - Bug fixes, backward-compatible

**Current:** 4.2.0 (MINOR release - new parallel processing features)

---

**RadarSuite** - Continuous improvement for tactical audio intelligence.
