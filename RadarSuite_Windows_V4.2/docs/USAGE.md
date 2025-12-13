# Usage Guide - RadarSuite V4.2.0

Complete user guide for all features and workflows.

---

## Table of Contents

1. [Quick Start Workflow](#quick-start-workflow)
2. [Interface Overview](#interface-overview)
3. [Tab 1: Radar View](#tab-1-radar-view)
4. [Tab 2: Detection & Audio](#tab-2-detection--audio)
5. [Tab 3: Game Detection](#tab-3-game-detection)
6. [Tab 4: Analysis](#tab-4-analysis)
7. [Keyboard Shortcuts](#keyboard-shortcuts)
8. [Detection Modes](#detection-modes)
9. [Recording Sessions](#recording-sessions)
10. [Advanced Features](#advanced-features)
11. [Tips & Best Practices](#tips--best-practices)

---

## Quick Start Workflow

### Scenario 1: Capture Game Audio (ARC Raiders)

```
1. Launch ARC Raiders
2. Launch RadarSuite
3. Click "Quick Setup" button (auto-configures loopback)
4. Press START (or Ctrl+S)
5. Play game → Radar shows footsteps, shots, machines
```

### Scenario 2: Test with Microphone

```
1. Tab 2 → Device → Select microphone
2. Tab 2 → Loopback Mode → UNCHECK
3. Tab 2 → Press "Apply"
4. Press START
5. Speak/clap/make noise → Radar shows detections
```

### Scenario 3: Test Mode (No Audio Input)

```
1. Tab 2 → Enable "Test Mode"
2. Press START
3. Synthetic test signals generated
4. Walk (80 Hz), Run (420 Hz), Shot (2200 Hz) displayed on radar
```

---

## Interface Overview

### Main Window Layout

```
┌─────────────────────────────────────────────────────┐
│ [RadarSuite V4.2.0]                      [_][□][X] │
│ ─────────────────────────────────────────────────── │
│ Toolbar: [START] [⏺REC] [🔊] [EN/PL] [Detach] ... │
│ ─────────────────────────────────────────────────── │
│ ┌─────────────────────────────────────────────────┐ │
│ │ ┌─────┬─────────────────┬──────────┬─────────┐ │ │
│ │ │ Tab1│ Tab2            │ Tab3     │ Tab4    │ │ │
│ │ │Radar│Detection & Audio│Game Detec│Analysis │ │ │
│ │ └─────┴─────────────────┴──────────┴─────────┘ │ │
│ │                                                 │ │
│ │          [ACTIVE TAB CONTENT]                  │ │
│ │                                                 │ │
│ └─────────────────────────────────────────────────┘ │
│ Status: Audio Running | FPS: 20 | Targets: 2       │
└─────────────────────────────────────────────────────┘
```

### Toolbar Buttons

| Button | Function | Shortcut |
|--------|----------|----------|
| **START/STOP** | Toggle detection | `Ctrl+S` |
| **⏺ REC** | Start/stop recording | `Ctrl+R` |
| **🔊** | Quick mute toggle | `Ctrl+M` |
| **EN/PL** | Switch language | - |
| **⬜ Detach Radar** | Open radar in separate window | - |
| **⬜ Detach LED** | Open LED overlay in separate window | - |
| **📊 Performance** | Show FPS/latency stats | - |

---

## Tab 1: Radar View

### Sub-tabs

#### 2D Military HUD Radar
- **Top-down view** - 360° circular radar
- **Range:** 0-100 meters
- **Target markers:** Color-coded by threat level
  - 🔴 Red = CRITICAL threat
  - 🟠 Orange = HIGH threat
  - 🟡 Yellow = MEDIUM threat
  - 🟢 Green = LOW threat
- **Sweep line:** Rotating radar sweep (cosmetic, not functional)
- **Target labels:** T1, T2, T3 with distance/angle

#### 3D Sphere Radar
- **3D spatial view** - Full sphere with elevation
- **Camera controls:** Mouse drag to rotate, scroll to zoom
- **Elevation visualization:** Targets above/below player plane
- **Distance rings:** 25m, 50m, 75m, 100m

### Radar Controls

| Control | Function |
|---------|----------|
| **Detach Window** | Open radar in separate window (multi-monitor) |
| **Frameless** | Remove window borders (overlay mode) |
| **Opacity Slider** | Adjust radar transparency (25-100%) |
| **Reset Camera** | Return 3D view to default position |

### Target Information

Each target shows:
- **ID:** T1, T2, T3
- **Angle:** 0-360° (0° = front, 90° = right, 180° = rear, 270° = left)
- **Distance:** 0-100 meters
- **Type:** Walk, Run, Shot, Rifle, Pistol, etc.
- **Threat Level:** Critical/High/Medium/Low

---

## Tab 2: Detection & Audio

### Audio Configuration

#### Device Selection
```
Device: [Dropdown menu]
├── Microphones (Default Device)
│   ├── Built-in Microphone
│   └── External Microphone
└── Loopback Devices
    ├── Stereo Mix (Realtek)
    ├── CABLE Output (VB-Audio)
    └── What U Hear (Sound Blaster)
```

**Loopback Mode:** ☑ Enable when capturing game audio

#### Sample Rate & Block Size
- **Sample Rate:** 48000 Hz (auto-configured for ARC Raiders)
- **Block Size:** 2048 samples (~42.7 ms latency)
- **Channels:** Stereo (auto-downmix from 5.1/7.1)

**Note:** These are auto-configured. Manual adjustment not recommended.

### Detection Thresholds

```
Walk Threshold:  [────●────] 35  (Range: 0-100)
Run Threshold:   [────●────] 35  (Range: 0-100)
Shot Threshold:  [────●────] 45  (Range: 0-100)
```

**Lower = more sensitive** (more false positives)
**Higher = less sensitive** (may miss quiet sounds)

**Recommended Settings:**
- **Quiet environment:** Walk: 25, Run: 25, Shot: 35
- **Normal environment:** Walk: 35, Run: 35, Shot: 45 (default)
- **Noisy environment:** Walk: 50, Run: 50, Shot: 60

### Audio Processing

#### Auto-Gain
☑ **Enable Auto-Gain** - Automatically amplify quiet audio to -20 dBFS

**Use when:**
- Game audio is too quiet
- Footsteps barely audible
- Consistent volume needed

**Disable when:**
- Audio already loud enough
- Dynamic range preservation important

#### Manual Gain
**Gain:** [────●────] 1.0x to 100.0x

**Use when:**
- Auto-gain not sufficient
- Precise control needed
- Boosting specific frequency ranges

#### Noise Gate
**Threshold:** [────●────] -80 dB to -20 dB

**Function:** Blocks audio below threshold (removes background noise)

**Recommended:**
- **PC fans/AC:** -60 dB
- **Keyboard typing:** -50 dB
- **Quiet room:** -70 dB

### Waveform Display

Real-time audio waveform visualization:
- **Green:** Audio within normal range
- **Yellow:** Audio approaching clipping
- **Red:** Audio clipping (reduce gain!)

### Detection Status

```
┌──────────────────────────┐
│ WALK:  ⚫ OFF            │
│ RUN:   ⚫ OFF            │
│ SHOT:  ⚫ OFF            │
├──────────────────────────┤
│ RMS: -42.5 dBFS          │
│ Audio: ✓ Initialized     │
└──────────────────────────┘
```

**Live indicators:**
- ⚫ OFF = No detection
- 🟢 ON = Currently detecting
- Hold time: 3 frames (~150 ms)

### Test Mode

☑ **Enable Test Mode**

**Function:** Generate synthetic test signals (no audio input needed)

**Test signals:**
- **Walk:** 80 Hz sine wave
- **Run:** 420 Hz sine wave
- **Shot:** 2200 Hz sine wave (burst every 2 seconds)

**Use for:**
- Testing radar visualization
- Verifying detection algorithms
- Demonstrating system without game

---

## Tab 3: Game Detection

### Game Scanner

**Auto-scan every 5 seconds** for running games.

**Detected info:**
```
┌────────────────────────────────────┐
│ 🎮 ARC Raiders via Steam           │
│ Process: PioneerGame.exe           │
│ Platform: Steam (AppID: 12345)     │
└────────────────────────────────────┘
```

### Platform Launcher Status

Shows status of gaming platforms:
```
Steam:       ✓ Running (High priority)
Epic Games:  ✓ Running (High priority)
GOG Galaxy:  ⚫ Not running
Battle.net:  ⚫ Not running
EA App:      ⚫ Not running
```

**Priority levels:**
- **High:** Steam, Epic (auto-detect games)
- **Medium:** GOG, Battle.net
- **Low:** EA App

### Audio Source Scanner

**Auto-scan every 2 seconds** for active audio sources.

**Detected sources:**
```
┌─────────────────────────────────────┐
│ ✓ ARC Raiders (Game)               │
│ ⚫ Discord (Filtered - VoIP)       │
│ ⚫ Spotify (Filtered - Music)      │
│ ✓ System Sounds (Allowed)         │
└─────────────────────────────────────┘
```

**Filtering logic:**
- **Allowed:** Games, system sounds
- **Filtered:** VoIP (Discord, TeamSpeak), music players, browsers

---

## Tab 4: Analysis

### Performance Metrics

```
FPS:       20.0 (target: 20 FPS)
Latency:   8.5 ms (audio → radar)
CPU:       12.3% (idle: ~5-10%)
Memory:    245 MB
```

**Interpretation:**
- **FPS < 15:** System overloaded, reduce detection sensitivity
- **Latency > 50 ms:** Audio processing too slow
- **CPU > 50%:** Enable GPU acceleration or reduce MAX_WORKERS
- **Memory increasing:** Memory leak, restart application

### Target History

Shows last 10 detected targets:
```
Timestamp | ID | Type  | Angle | Distance | Threat
──────────┼────┼───────┼───────┼──────────┼────────
14:32:15  | T1 | Rifle | 045°  | 32.5m    | HIGH
14:32:10  | T2 | Walk  | 180°  | 12.0m    | MEDIUM
14:32:05  | T3 | Shot  | 270°  | 65.0m    | LOW
```

### Frequency Spectrum

Real-time FFT visualization:
- **X-axis:** Frequency (Hz)
- **Y-axis:** Magnitude (dB)
- **Bands highlighted:**
  - Walk: 40-250 Hz (blue)
  - Run: 200-1200 Hz (green)
  - Shot: 1500-8000 Hz (red)

---

## Keyboard Shortcuts

### Global Shortcuts (Work in Any Tab)

| Shortcut | Function |
|----------|----------|
| `Ctrl+S` | Toggle START/STOP |
| `Ctrl+R` | Toggle recording |
| `Ctrl+M` | Quick mute |
| `Ctrl+F` | Toggle fullscreen |
| `Ctrl+1` | Switch to Tab 1 (Radar) |
| `Ctrl+2` | Switch to Tab 2 (Detection) |
| `Ctrl+3` | Switch to Tab 3 (Game Detection) |
| `Ctrl+4` | Switch to Tab 4 (Analysis) |
| `Ctrl+Q` | Quit application |
| `F11` | Toggle fullscreen (alternative) |

### Radar Controls

| Shortcut | Function |
|----------|----------|
| `R` | Reset radar camera (3D mode) |
| `+` | Increase opacity |
| `-` | Decrease opacity |

---

## Detection Modes

### Standard Mode (Default)

Normal sensitivity, suitable for most environments.

**Detection parameters:**
```
Walk:  40-250 Hz, threshold 0.03 RMS
Run:   200-1200 Hz, threshold 0.025 RMS
Shot:  1500-8000 Hz, threshold 0.05 RMS
```

### Night Mode (Enhanced Sensitivity)

Enables audio compression for better quiet sound detection.

**How to enable:**
```python
# Edit app/core/constants.py
NIGHT_MODE_ENABLED = True
COMPRESSION_RATIO = 4.0  # 4:1 compression
```

**Effect:**
- Quiet sounds (footsteps) boosted +12 dB
- Loud sounds (explosions) reduced -6 dB
- Better balance for competitive play

**Use when:**
- Difficult to hear footsteps
- Competing in tournaments
- Need every tactical advantage

---

## Recording Sessions

### Start Recording

**Method 1:** Toolbar → **⏺ REC** button
**Method 2:** Keyboard → `Ctrl+R`

**What's recorded:**
- **Audio:** 16-bit WAV format (48 kHz stereo)
- **Metadata:** JSON file with:
  - Timestamp of each detection
  - Target positions (angle, distance, elevation)
  - Classification results (type, confidence)
  - Performance metrics (FPS, latency)

### Recording UI

```
┌─────────────────────────┐
│ ⏺ RECORDING             │
│ Duration: 02:35         │
│ Size: 12.5 MB           │
└─────────────────────────┘
```

### Stop Recording

Press **⏺ REC** again or `Ctrl+R`.

**Output files:**
```
recordings/
├── session_20251201_143052.wav      (audio)
└── session_20251201_143052.json     (metadata)
```

### Replay & Analysis

**Audio playback:** Use any media player (VLC, Windows Media Player)

**Metadata analysis:**
```python
import json

with open('session_20251201_143052.json') as f:
    data = json.load(f)

for event in data['detections']:
    print(f"{event['timestamp']}: {event['type']} at {event['angle']}° / {event['distance']}m")
```

---

## Advanced Features

### Detachable Windows

**Radar Window:**
1. Click "Detach Radar" button
2. Drag window to second monitor
3. Check "Frameless" for overlay mode
4. Adjust opacity for transparency

**LED Overlay:**
1. Click "Detach LED" button
2. Position over game window
3. Shows directional indicators for detected targets

**Use case:** Multi-monitor gaming setup, radar on second screen

### Multi-Target Tracking

Supports up to **3 simultaneous targets**.

**Tracking logic:**
- New detection → Create target (T1, T2, T3)
- Subsequent detections → Match to closest existing target
- No detection for 3 seconds → Remove target
- Targets ranked by threat level (highest priority first)

### Threat Priority System

**Automatic ranking** based on:
```
ThreatScore = WeaponScore × DistanceFactor × DirectionFactor + Confidence

Weapon Scores:
- Sniper: 100, Explosive: 90, Rifle: 85, Pistol: 70, Footstep: 50

Distance Factor:
- <20m: 1.5x, 20-50m: 1.0x, >50m: 0.5x

Direction Factor:
- Rear (135-225°): 1.3x (higher threat from behind)
- Side (45-135°, 225-315°): 1.0x
- Front (315-45°): 0.8x (lower threat from front)
```

**Threat categories:**
- **CRITICAL** (>150): Red marker, top priority
- **HIGH** (100-150): Orange marker
- **MEDIUM** (50-100): Yellow marker
- **LOW** (<50): Green marker

---

## Tips & Best Practices

### For Competitive Gaming

1. **Use loopback mode** - More reliable than microphone
2. **Enable Night Mode** - Better footstep detection
3. **Detach radar** - Second monitor for situational awareness
4. **Lower thresholds** - Catch distant footsteps (25/25/35)
5. **Record sessions** - Post-game analysis of missed detections

### For Optimal Performance

1. **Close background apps** - Minimize CPU usage
2. **48 kHz sample rate** - Native FMOD/UE5 rate (no resampling)
3. **GPU acceleration** - Enable if NVIDIA GPU available
4. **Wired headphones** - Lower latency than Bluetooth

### For Accurate Detection

1. **Calibrate thresholds** - Adjust based on your audio environment
2. **Test mode first** - Verify radar working before game
3. **Quiet environment** - Minimize background noise
4. **Good audio drivers** - Update to latest version

### Troubleshooting Workflow

**No detections appearing:**
```
1. Check START button is active (green)
2. Verify audio device selected (Tab 2)
3. Check waveform shows activity (Tab 2)
4. Enable Test Mode to verify radar working
5. Lower detection thresholds (25/25/35)
```

**Too many false positives:**
```
1. Increase detection thresholds (50/50/60)
2. Enable noise gate (-50 dB)
3. Check for background noise sources
4. Disable auto-gain if environment already loud
```

**Poor performance (FPS < 15):**
```
1. Close other applications
2. Reduce MAX_WORKERS in constants.py
3. Disable 3D radar (use 2D only)
4. Lower sample rate to 44100 Hz (not recommended)
```

---

## Next Steps

- **[Configuration Guide](CONFIGURATION.md)** - Detailed parameter tuning
- **[Architecture Guide](ARCHITECTURE.md)** - Understanding system internals
- **[Module Reference](MODULES.md)** - API documentation for developers

---

**RadarSuite V4.2.0** - Master the audio battlefield!
