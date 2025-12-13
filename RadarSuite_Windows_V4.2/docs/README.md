# RadarSuite V4.2.0

**Real-time audio detection and spatial tracking system for tactical gaming**

---

## Overview

RadarSuite is a professional-grade audio radar system designed for competitive gaming environments. It provides real-time detection, classification, and 3D spatial tracking of in-game audio events through advanced signal processing and spectral analysis.

**Primary Target:** ARC Raiders (FMOD + Unreal Engine 5 audio)
**Platform:** Windows 10/11 (x64)
**Version:** 4.2.0
**Release Date:** 2025-12-01

---

## Key Capabilities

### Detection & Classification
- **Footstep Detection** - Walk/run classification with surface type identification (metal, dirt, snow, concrete, wood)
- **Weapon Detection** - Shot classification with weapon type identification (rifle, pistol, shotgun, sniper, explosive)
- **Distance Estimation** - Close (<30m) vs distant (>30m) shot classification
- **Machine Detection** - ARC machine state detection (idle, patrol, search, combat)
- **Multi-Target Tracking** - Simultaneous tracking of up to 3 targets with threat prioritization

### Spatial Processing
- **3D Localization** - ITD (Interaural Time Difference) and ILD (Interaural Level Difference) analysis
- **Azimuth Detection** - 360° horizontal position tracking
- **Elevation Estimation** - Vertical position approximation via frequency analysis
- **Distance Estimation** - Based on spectral characteristics and energy decay

### Audio Processing
- **48 kHz Sample Rate** - Native FMOD/UE5 standard for optimal quality
- **Spectral Analysis** - MFCC (13 coefficients), spectral centroid, rolloff, flatness
- **Real-time FFT** - Cached computation for performance (4x reduction in redundant calculations)
- **Multi-threaded Processing** - Parallel detection via worker pool (prevents UI freezing)

### Visualization
- **2D Military HUD Radar** - Tactical top-down view with target markers
- **3D Sphere Radar** - Full spatial awareness with elevation display
- **Detachable Windows** - Multi-monitor support for radar and LED overlays
- **Real-time Performance Metrics** - FPS, latency, CPU, memory monitoring

---

## For Whom?

### Competitive Gamers
- Enhance situational awareness in ARC Raiders
- Detect enemy positions before visual contact
- Tactical advantage through audio intelligence

### Audio Researchers
- Advanced signal processing testbed
- Spectral feature extraction framework
- Real-time classification algorithms

### Game Developers
- Audio system analysis and debugging
- Spatial audio testing and validation
- Performance profiling for audio pipelines

---

## System Requirements

**Minimum:**
- Windows 10 (64-bit) or Windows 11
- Python 3.11
- 4 GB RAM
- Stereo audio input (microphone or loopback)
- 100 MB disk space

**Recommended:**
- Windows 11 (64-bit)
- Python 3.11
- 8 GB RAM
- 5.1/7.1 surround audio (automatic downmix to stereo)
- NVIDIA GPU with CUDA support (optional, for GPU acceleration)
- Sound Blaster Z SE or equivalent (optimized drivers)

---

## Quick Start

### 1. Installation
```bash
# Clone repository
git clone https://github.com/yourusername/AudioRadar.git
cd AudioRadar/RadarSuite_Windows_V4.2

# Install dependencies
pip install -r requirements-windows.txt

# Run application
python app/main.py
```

### 2. First Use
1. **Select Audio Source** - Tab 2: Detection & Audio → Choose microphone or loopback device
2. **Enable Loopback** (for game audio) - Check "Loopback Mode" to capture game output
3. **Quick Setup** - Click "Quick Setup" button for automatic game audio configuration
4. **Start Detection** - Press **START** button or **Ctrl+S**

### 3. Game Audio Capture (ARC Raiders)
1. Launch ARC Raiders
2. In RadarSuite: Tab 2 → Enable "Loopback Mode"
3. Select speaker/headphone loopback device (e.g., "Loopback (Speakers)")
4. Click "Apply" → Press "START"
5. Radar will show detected footsteps, shots, and machines in real-time

---

## Core Features

### Detection Modes

**Standard Mode** - Normal audio sensitivity
```
Walk:   40-250 Hz   (threshold: 0.03 RMS)
Run:    200-1200 Hz (threshold: 0.025 RMS)
Shot:   1500-8000 Hz (threshold: 0.05 RMS)
```

**Night Mode** - Enhanced sensitivity (4:1 compression)
```
Quiet sounds boosted (footsteps more audible)
Loud sounds reduced (prevents audio masking)
Recommended for competitive play
```

### Threat Priority System

Targets automatically ranked by danger level:
- **CRITICAL** (Red) - Close-range sniper/explosive (<20m)
- **HIGH** (Orange) - Close-range rifle/rear attacks
- **MEDIUM** (Yellow) - Mid-range threats (20-50m)
- **LOW** (Green) - Distant or low-threat sounds (>50m)

**Scoring Formula:**
```
Threat = (WeaponScore × DistanceFactor × DirectionFactor) + ConfidenceBonus

Weapon Scores:
- Sniper: 100, Explosive: 90, Rifle: 85, Pistol: 70, Footstep: 50

Distance Factor:
- <20m: 1.5x, 20-50m: 1.0x, >50m: 0.5x

Direction Factor:
- Rear (135-225°): 1.3x, Side: 1.0x, Front: 0.8x
```

---

## Technology Stack

**GUI Framework:** PyQt5
**Visualization:** pyqtgraph, PyOpenGL
**Audio I/O:** sounddevice, soundcard, pyaudiowpatch (WASAPI loopback)
**Signal Processing:** NumPy, SciPy
**System Info:** psutil

**Architecture Pattern:** Dependency Injection (IoC container)
**Concurrency:** ThreadPoolExecutor for parallel detection
**Testing:** pytest with 250+ unit tests

---

## Documentation

- **[Installation Guide](INSTALLATION.md)** - Detailed setup, dependencies, troubleshooting
- **[Usage Guide](USAGE.md)** - Complete feature walkthrough, tips, workflows
- **[Architecture](ARCHITECTURE.md)** - System design, data flow, component interaction
- **[Module Reference](MODULES.md)** - Detailed API documentation for all modules
- **[Configuration](CONFIGURATION.md)** - All parameters, constants, tuning guide
- **[Build Guide](BUILD.md)** - Building executables with PyInstaller
- **[Changelog](CHANGELOG.md)** - Version history and release notes
- **[Known Issues](KNOWN_ISSUES.md)** - Limitations, workarounds, troubleshooting

---

## Project Status

**Current Version:** 4.2.0
**Status:** Production-ready
**Last Updated:** 2025-12-01

**Recent Improvements (V4.2.0):**
- ✅ Refactored DetectionWorker with explicit error handling
- ✅ Integrated parallel detection processing (no more UI freezing)
- ✅ Professional code documentation (removed marketing bloat)
- ✅ Comprehensive refactoring plan for MainWindow god object

---

## Contributing

This project follows professional software engineering practices:
- **Code Reviews** - All changes reviewed before merge
- **Testing** - Minimum 80% code coverage required
- **Documentation** - All public APIs documented
- **Semantic Versioning** - MAJOR.MINOR.PATCH versioning scheme

---

## License

Proprietary - For authorized use only.

---

## Support

**Issues:** Report bugs and request features via GitHub Issues
**Documentation:** See `docs/` directory for complete technical documentation
**Version:** Check `app/version.py` for current build information

---

**RadarSuite V4.2.0** - Advanced Audio Intelligence for Tactical Gaming
