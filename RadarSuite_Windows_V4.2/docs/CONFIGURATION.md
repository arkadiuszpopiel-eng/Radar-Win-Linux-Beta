# Configuration Reference - RadarSuite V4.2.0

Complete reference for all configuration parameters and tuning.

---

## Table of Contents

1. [Configuration Files](#configuration-files)
2. [Audio Parameters](#audio-parameters)
3. [Detection Parameters](#detection-parameters)
4. [Performance Parameters](#performance-parameters)
5. [ARC Raiders Specific](#arc-raiders-specific)
6. [Advanced Tuning](#advanced-tuning)

---

## Configuration Files

### User Configuration

**Location:** `%APPDATA%\RadarSuite\config.json`

**Structure:**
```json
{
  "audio": {
    "sample_rate": 48000,
    "block_size": 2048,
    "loopback": true,
    "device_id": 0
  },
  "detection": {
    "thresholds": {
      "walk": 35,
      "run": 35,
      "shot": 45
    }
  },
  "performance": {
    "use_gpu": true,
    "max_workers": 3
  },
  "ui": {
    "language": "en",
    "radar_opacity": 0.9,
    "led_opacity": 0.8
  }
}
```

### Application Constants

**Location:** `app/core/constants.py`

**Edit this file** to change system-wide defaults.

---

## Audio Parameters

### Sample Rate

**Parameter:** `SAMPLE_RATE`
**Default:** `48000` Hz
**Range:** `44100`, `48000`, `96000`

**Recommendation:** **48000 Hz** (FMOD/UE5 standard for ARC Raiders)

**Impact:**
- **44100 Hz:** Lower CPU, slightly worse quality
- **48000 Hz:** Optimal for gaming (native rate)
- **96000 Hz:** Higher quality, 2x CPU usage (not recommended)

**Edit:**
```python
# app/core/constants.py
SAMPLE_RATE = 48000  # Change to 44100 if CPU limited
```

### Block Size

**Parameter:** `BLOCK_SIZE`
**Default:** `2048` samples
**Range:** `512`, `1024`, `2048`, `4096`

**Latency calculation:**
```
Latency (ms) = (BLOCK_SIZE / SAMPLE_RATE) × 1000
2048 / 48000 × 1000 = 42.7 ms
```

**Trade-offs:**
```
Smaller block (512):  Lower latency (10.7 ms), higher CPU
Medium block (1024):  Moderate (21.3 ms), balanced
Larger block (2048):  Higher latency (42.7 ms), lower CPU
```

**Recommendation:** **2048** (good balance)

### Channels

**Parameter:** `CHANNELS`
**Default:** `2` (stereo)
**Range:** `1` (mono), `2` (stereo)

**Note:** 5.1/7.1 automatically downmixed to stereo by audio engine.

---

## Detection Parameters

### Energy Threshold

**Parameter:** `ENERGY_THRESHOLD`
**Default:** `0.001`
**Range:** `0.0001` (very sensitive) to `0.01` (less sensitive)

**Purpose:** Minimum audio energy to trigger detection

**Tuning:**
- **Too low (<0.0001):** False positives from noise
- **Optimal (0.001):** Good balance
- **Too high (>0.01):** Miss quiet footsteps

### Localization Confidence

**Parameter:** `LOCALIZATION_MIN_CONFIDENCE`
**Default:** `30`
**Range:** `0` to `100`

**Purpose:** Minimum confidence for 3D position tracking

**Tuning:**
- **Low (10-20):** More targets tracked (noisier radar)
- **Medium (30-40):** Balanced
- **High (50-70):** Only high-confidence targets (cleaner radar)

### Detection Thresholds (User Configurable)

#### Walk Threshold

**UI Control:** Tab 2 → Walk Threshold Slider
**Default:** `35`
**Range:** `0` to `100`

**Frequency band:** `40-250 Hz`
**RMS threshold:** `0.03`

**Tuning:**
- **Quiet environment:** `20-30`
- **Normal:** `30-40`
- **Noisy:** `50-60`

#### Run Threshold

**UI Control:** Tab 2 → Run Threshold Slider
**Default:** `35`
**Range:** `0` to `100`

**Frequency band:** `200-1200 Hz`
**RMS threshold:** `0.025`

**Tuning:**
- **Quiet:** `20-30`
- **Normal:** `30-40`
- **Noisy:** `50-60`

#### Shot Threshold

**UI Control:** Tab 2 → Shot Threshold Slider
**Default:** `45`
**Range:** `0` to `100`

**Frequency band:** `1500-8000 Hz`
**RMS threshold:** `0.05`

**Tuning:**
- **Quiet:** `30-40`
- **Normal:** `40-50`
- **Noisy:** `60-70`

---

## Performance Parameters

### Worker Threads

**Parameter:** `MAX_WORKERS`
**Default:** `3`
**Range:** `1` to `8`

**Purpose:** Thread pool size for parallel detection

**Tuning based on CPU:**
```
Dual-core:    MAX_WORKERS = 2
Quad-core:    MAX_WORKERS = 3 (default)
6-core:       MAX_WORKERS = 4
8+ core:      MAX_WORKERS = 5-6
```

**Impact:**
- **Too few (1-2):** Detection may lag, lower FPS
- **Optimal (3-4):** Good balance
- **Too many (>6):** Diminishing returns, overhead increases

### Cleanup Interval

**Parameter:** `CLEANUP_INTERVAL_SEC`
**Default:** `10.0` seconds
**Range:** `5.0` to `60.0`

**Purpose:** Frequency of future cleanup in DetectionWorker

**Tuning:**
- **Shorter (5s):** More cleanup overhead, lower memory
- **Longer (30s):** Less overhead, higher memory

**Recommendation:** **10.0** (good balance)

### Detection Timeout

**Parameter:** `DETECTION_TIMEOUT_SEC`
**Default:** `5.0` seconds
**Range:** `1.0` to `10.0`

**Purpose:** Timeout for worker shutdown

**Impact:**
- **Shorter (1-2s):** Faster shutdown, may interrupt tasks
- **Longer (5-10s):** Cleaner shutdown, slower exit

### Tick Interval

**Parameter:** `TICK_INTERVAL_MS`
**Default:** `50` ms (20 FPS)
**Range:** `33` ms (30 FPS) to `100` ms (10 FPS)

**Purpose:** Main update loop frequency

**FPS calculation:**
```
FPS = 1000 / TICK_INTERVAL_MS
50 ms = 20 FPS
33 ms = 30 FPS
100 ms = 10 FPS
```

**Tuning:**
- **30 FPS (33 ms):** Smoother radar, higher CPU
- **20 FPS (50 ms):** Balanced (default)
- **10 FPS (100 ms):** Lower CPU, choppier radar

---

## ARC Raiders Specific

### Shot Detection

#### Close Shot Distance

**Parameter:** `SHOT_CLOSE_DISTANCE_M`
**Default:** `30` meters
**Range:** `20` to `50`

**Purpose:** Threshold for classifying shots as "close" vs "distant"

**Impact:**
- **Shorter (<30m):** More shots classified as "distant"
- **Longer (>30m):** More shots classified as "close"

#### Shot Frequency Range

**Parameters:**
```python
SHOT_FREQ_MIN_HZ = 200   # Minimum
SHOT_FREQ_MAX_HZ = 8000  # Maximum
```

**Purpose:** Frequency band for shot detection

**Tuning:** Generally don't modify (optimized for gunshot spectrum)

#### Shot Bass Threshold

**Parameter:** `SHOT_BASS_THRESHOLD`
**Default:** `0.3` (30% bass energy)
**Range:** `0.2` to `0.5`

**Purpose:** Classify explosions (high bass) vs gunshots (mid-high)

**Tuning:**
- **Lower (0.2):** More sounds classified as explosions
- **Higher (0.5):** Stricter explosion detection

### Footstep Detection

#### Walk Interval

**Parameter:** `FOOTSTEP_WALK_INTERVAL_S`
**Default:** `0.6` seconds
**Range:** `0.4` to `0.8`

**Purpose:** Expected interval between walk footsteps

**Calculation:**
```
Walk cadence = 1 / 0.6 = 1.67 steps/second
```

#### Run Interval

**Parameter:** `FOOTSTEP_RUN_INTERVAL_S`
**Default:** `0.3` seconds
**Range:** `0.2` to `0.4`

**Purpose:** Expected interval between run footsteps

**Calculation:**
```
Run cadence = 1 / 0.3 = 3.33 steps/second
```

#### Interval Tolerance

**Parameter:** `FOOTSTEP_INTERVAL_TOLERANCE`
**Default:** `0.15` seconds
**Range:** `0.1` to `0.2`

**Purpose:** Tolerance for natural gait variation

**Example:**
```
Walk: 0.6 ± 0.15 = 0.45 to 0.75 seconds OK
Run:  0.3 ± 0.15 = 0.15 to 0.45 seconds OK
```

#### Surface Type Peaks

**Parameters:**
```python
SURFACE_METAL_FREQ_PEAK_HZ = 400
SURFACE_DIRT_FREQ_PEAK_HZ = 200
SURFACE_SNOW_FREQ_PEAK_HZ = 150
```

**Purpose:** Expected spectral centroid for surface types

**Tuning:** Based on game sound design (don't modify unless game audio changes)

### Machine Detection

#### Detection Window

**Parameter:** `MACHINE_DETECTION_WINDOW_S`
**Default:** `2.0` seconds
**Range:** `1.0` to `5.0`

**Purpose:** Analysis window for machine state detection

**Tuning:**
- **Shorter (1s):** Faster state changes, less reliable
- **Longer (3-5s):** More stable, slower to respond

#### Modulation Threshold

**Parameter:** `MACHINE_MODULATION_THRESHOLD`
**Default:** `0.1` (10%)
**Range:** `0.05` to `0.2`

**Purpose:** Minimum modulation to detect machine

**Tuning:**
- **Lower (0.05):** Detect quieter machines
- **Higher (0.2):** Only loud, obvious machines

---

## Advanced Tuning

### GPU Acceleration

**Configuration:**
```json
{
  "performance": {
    "use_gpu": true
  }
}
```

**Requirements:**
- NVIDIA GPU with CUDA support
- CuPy installed (`pip install cupy-cuda11x`)

**Impact:**
- **Enabled:** ~40% faster FFT computation
- **Disabled:** CPU-only (works fine, slightly slower)

### Night Mode (Enhanced Sensitivity)

**Not in UI - requires code edit**

**Edit:** `app/core/constants.py`
```python
# Add these lines
NIGHT_MODE_ENABLED = True
COMPRESSION_RATIO = 4.0  # 4:1 compression

# Adjust thresholds
ENERGY_THRESHOLD = 0.0005  # Lower for better sensitivity
```

**Effect:**
- Quiet sounds (footsteps) boosted
- Loud sounds (explosions) reduced
- Better competitive balance

### Custom Frequency Bands

**Edit:** Detection panel or constants

**Example - Optimize for specific game:**
```python
# For game with lower-pitched footsteps
FOOTSTEP_FREQ_MIN_HZ = 80   # Lower from 100
FOOTSTEP_FREQ_MAX_HZ = 600  # Lower from 800

# For game with high-pitched gunshots
SHOT_FREQ_MIN_HZ = 1000     # Raise from 200
SHOT_FREQ_MAX_HZ = 12000    # Raise from 8000
```

### Radar Behavior

#### Rotation Speed

**Parameter:** `RADAR_ROTATION_DEG`
**Default:** `4.0` degrees per frame
**Range:** `0.0` to `10.0`

**Purpose:** Cosmetic radar sweep rotation

**Tuning:**
- **0.0:** No rotation
- **2.0:** Slow rotation
- **4.0:** Medium (default)
- **8.0:** Fast rotation

#### Orientation Mode

**Parameter:** `RADAR_ORIENTATION_MODE`
**Default:** `"player_up"` (head-up mode)
**Options:** `"north_up"`, `"player_up"`

**Effect:**
```
north_up:   0° always points north (map mode)
player_up:  0° always points forward (FPS mode)
```

**Recommendation:** **"player_up"** for ARC Raiders

---

## Configuration Best Practices

### For Competitive Play

```json
{
  "audio": {
    "sample_rate": 48000,
    "loopback": true
  },
  "detection": {
    "thresholds": {
      "walk": 25,    // More sensitive
      "run": 25,     // More sensitive
      "shot": 35     // More sensitive
    }
  },
  "performance": {
    "use_gpu": true,
    "max_workers": 4  // If 6+ core CPU
  }
}
```

### For Low-End Systems

```json
{
  "audio": {
    "sample_rate": 44100,  // Lower rate
    "block_size": 2048
  },
  "detection": {
    "thresholds": {
      "walk": 40,
      "run": 40,
      "shot": 50
    }
  },
  "performance": {
    "use_gpu": false,  // CPU-only
    "max_workers": 2   // Fewer threads
  }
}
```

**Edit tick interval:**
```python
# app/core/constants.py
TICK_INTERVAL_MS = 100  # 10 FPS instead of 20
```

### For Maximum Accuracy

```json
{
  "audio": {
    "sample_rate": 48000,
    "block_size": 2048
  },
  "detection": {
    "thresholds": {
      "walk": 30,
      "run": 30,
      "shot": 40
    }
  }
}
```

**Edit constants:**
```python
# app/core/constants.py
LOCALIZATION_MIN_CONFIDENCE = 50  # Higher confidence only
ENERGY_THRESHOLD = 0.002          # Slightly less sensitive
```

---

## Configuration Validation

After editing configuration, validate with:

```python
from core.config import ConfigManager

manager = ConfigManager()
config = manager.load()

# Check values
assert 44100 <= config['audio']['sample_rate'] <= 96000
assert 0 <= config['detection']['thresholds']['walk'] <= 100
assert 1 <= config['performance']['max_workers'] <= 8

print("Configuration valid!")
```

---

**RadarSuite V4.2.0** - Optimized configuration for peak performance.
