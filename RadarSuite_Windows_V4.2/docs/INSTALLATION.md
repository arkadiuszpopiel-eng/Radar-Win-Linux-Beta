# Installation Guide - RadarSuite V4.2.0

Complete installation instructions for Windows 10/11 x64 systems.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Python Installation](#python-installation)
3. [Dependency Installation](#dependency-installation)
4. [Audio Drivers](#audio-drivers)
5. [GPU Acceleration (Optional)](#gpu-acceleration-optional)
6. [Running from Source](#running-from-source)
7. [Running from Binary](#running-from-binary)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS:** Windows 10 (64-bit, build 1809+) or Windows 11
- **CPU:** Dual-core processor @ 2.0 GHz
- **RAM:** 4 GB
- **Disk:** 100 MB free space (+ 500 MB for Python and dependencies)
- **Audio:** Stereo audio input (microphone or loopback device)
- **Display:** 1280x720 resolution

### Recommended Requirements
- **OS:** Windows 11 (64-bit)
- **CPU:** Quad-core processor @ 3.0 GHz or higher
- **RAM:** 8 GB or more
- **Disk:** 1 GB free space
- **Audio:** 5.1 or 7.1 surround sound system (automatic downmix to stereo)
- **GPU:** NVIDIA GPU with CUDA support (for GPU acceleration)
- **Display:** 1920x1080 or higher, dual monitors recommended

---

## Python Installation

### Step 1: Download Python 3.11

Download Python 3.11 from the official website:
- **URL:** https://www.python.org/downloads/
- **Version:** Python 3.11.x (64-bit)

**Important:** RadarSuite requires Python 3.11. Newer versions (3.12+) may have compatibility issues with some dependencies.

### Step 2: Install Python

Run the installer with these settings:
1. ✅ Check **"Add Python 3.11 to PATH"** (CRITICAL!)
2. ✅ Check **"Install for all users"** (recommended)
3. Click **"Install Now"**

### Step 3: Verify Installation

Open Command Prompt (Win+R → `cmd`) and run:
```cmd
py -3.11 --version
```

**Expected output:**
```
Python 3.11.x
```

If this fails, Python is not in PATH. Reinstall with "Add to PATH" checked.

---

## Dependency Installation

### Method 1: Automated Installation (Recommended)

```cmd
cd AudioRadar\RadarSuite_Windows_V4.2
pip install -r requirements-windows.txt
```

### Method 2: Manual Installation

Install each package individually:
```cmd
pip install PyQt5>=5.15.0
pip install pyqtgraph>=0.13.0
pip install PyOpenGL>=3.1.0
pip install PyOpenGL_accelerate>=3.1.0
pip install numpy>=1.21.0
pip install scipy>=1.7.0
pip install sounddevice>=0.4.0
pip install soundcard>=0.4.0
pip install pyaudiowpatch>=0.2.12
pip install psutil>=5.9.0
pip install pyinstaller>=6.0.0
```

### Dependency Breakdown

| Package | Purpose | Size |
|---------|---------|------|
| **PyQt5** | GUI framework | ~50 MB |
| **pyqtgraph** | Real-time plotting | ~5 MB |
| **PyOpenGL** | 3D radar rendering | ~2 MB |
| **numpy** | Array processing | ~20 MB |
| **scipy** | Signal processing | ~30 MB |
| **sounddevice** | Audio I/O | ~1 MB |
| **soundcard** | Loopback audio | ~0.5 MB |
| **pyaudiowpatch** | WASAPI loopback (Windows) | ~1 MB |
| **psutil** | System monitoring | ~0.5 MB |

**Total size:** ~110 MB

### Verification

Verify all packages installed:
```cmd
pip list | findstr "PyQt5 numpy scipy sounddevice pyaudiowpatch"
```

---

## Audio Drivers

### Required: Virtual Audio Cable (for Game Audio Loopback)

To capture game audio, you need a loopback audio device.

#### Option 1: Windows Built-in (Windows 11+)
Windows 11 includes built-in loopback support via WASAPI. No additional drivers needed.

#### Option 2: VB-Audio Virtual Cable (All Windows)
1. Download VB-CABLE from: https://vb-audio.com/Cable/
2. Extract ZIP → Right-click `VBCABLE_Setup_x64.exe` → "Run as Administrator"
3. Restart computer
4. Verify: Control Panel → Sound → Recording → Should see "CABLE Output"

#### Option 3: Sound Blaster Z SE (Optimal)
If you have Sound Blaster Z SE audio card:
1. Install latest drivers from Creative website
2. Enable "What U Hear" or "Stereo Mix" in Recording Devices
3. RadarSuite will auto-detect and optimize settings

### Audio Device Setup

**For Microphone Input:**
1. Control Panel → Sound → Recording
2. Right-click microphone → "Set as Default Device"
3. Properties → Advanced → Set sample rate to **48000 Hz**

**For Game Audio (Loopback):**
1. Control Panel → Sound → Recording
2. Right-click loopback device (e.g., "Stereo Mix", "CABLE Output") → "Enable" → "Set as Default Device"
3. Properties → Advanced → Set sample rate to **48000 Hz**

---

## GPU Acceleration (Optional)

For improved performance with GPU-accelerated FFT:

### NVIDIA CUDA Setup

1. **Check GPU compatibility:**
   - NVIDIA GPU with Compute Capability 3.5+ required
   - Check: https://developer.nvidia.com/cuda-gpus

2. **Install CUDA Toolkit 11.8:**
   - Download: https://developer.nvidia.com/cuda-11-8-0-download-archive
   - Select: Windows → x86_64 → 11 → exe (local)
   - Install with default settings

3. **Install CuPy:**
   ```cmd
   pip install cupy-cuda11x
   ```

4. **Verify:**
   ```cmd
   python -c "import cupy; print(cupy.cuda.runtime.getDeviceCount())"
   ```
   Should print: `1` (or number of NVIDIA GPUs)

**Note:** GPU acceleration is optional. RadarSuite runs fine on CPU-only systems.

---

## Running from Source

### Method 1: Direct Execution

```cmd
cd AudioRadar\RadarSuite_Windows_V4.2
python app\main.py
```

### Method 2: Python Launcher

```cmd
cd AudioRadar\RadarSuite_Windows_V4.2
py -3.11 app\main.py
```

### First Launch

On first launch, RadarSuite will:
1. Scan for audio devices
2. Scan for running games
3. Load default configuration
4. Display main window (4 tabs)

**Default state:** Detection STOPPED (press START to begin)

---

## Running from Binary

### Download Binary Release

1. Go to: https://github.com/yourusername/AudioRadar/releases
2. Download: `RadarSuite_V4.2.0_Windows-x64.zip`
3. Extract to: `C:\RadarSuite\`

### Run Binary

```cmd
cd C:\RadarSuite
RadarSuite_V4.2.0_win.exe
```

**No Python installation required** - all dependencies bundled.

---

## Configuration

### First-Time Setup

1. **Select Language:**
   - Toolbar → Flag icon → English/Polski

2. **Audio Configuration:**
   - Tab 2: Detection & Audio
   - Device: Select microphone or loopback
   - Loopback Mode: Enable for game audio
   - Sample Rate: 48000 Hz (auto-configured)
   - Block Size: 2048 samples (auto-configured)

3. **Detection Thresholds:**
   - Tab 2 → Thresholds section
   - Walk: 35 (default)
   - Run: 35 (default)
   - Shot: 45 (default)
   - Adjust based on audio environment

4. **Game Detection:**
   - Tab 3: Game Detection
   - Auto-scans for running games every 5 seconds
   - Shows detected game + platform (Steam, Epic, etc.)

### Quick Setup (Recommended)

For game audio capture:
1. Launch game (e.g., ARC Raiders)
2. Click **"Quick Setup"** button (Tab 1 or Tab 2)
3. RadarSuite auto-configures loopback mode
4. Press **START** to begin detection

### Configuration Files

Configuration stored in:
```
%APPDATA%\RadarSuite\config.json
```

**Example config:**
```json
{
  "audio": {
    "sample_rate": 48000,
    "block_size": 2048,
    "loopback": true
  },
  "detection": {
    "thresholds": {
      "walk": 35,
      "run": 35,
      "shot": 45
    }
  },
  "performance": {
    "use_gpu": true
  }
}
```

---

## Troubleshooting

### Issue: "Python not found"

**Solution:**
```cmd
# Check if Python in PATH
where python
where py

# If not found, reinstall Python with "Add to PATH" checked
```

### Issue: "PyQt5 DLL load failed"

**Cause:** Missing Visual C++ Redistributable

**Solution:**
1. Download VC++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Install
3. Restart computer

### Issue: "sounddevice: no audio devices found"

**Cause:** No audio drivers installed

**Solution:**
1. Install audio drivers for your hardware
2. Verify: Control Panel → Sound → At least one Recording device should be present
3. Restart RadarSuite

### Issue: "No loopback device found"

**Solution:**
1. Install VB-Audio Virtual Cable (see [Audio Drivers](#audio-drivers))
2. Enable "Stereo Mix" or "What U Hear" in Recording Devices:
   - Control Panel → Sound → Recording
   - Right-click empty area → "Show Disabled Devices"
   - Right-click "Stereo Mix" → "Enable"

### Issue: "ModuleNotFoundError: No module named 'PyQt5'"

**Solution:**
```cmd
pip install PyQt5
```

If still fails:
```cmd
pip uninstall PyQt5
pip install PyQt5==5.15.9
```

### Issue: Application freezes on detection

**Cause:** Old version (pre-V4.2.0) without worker integration

**Solution:** Update to V4.2.0+ which uses parallel detection processing

### Issue: High CPU usage (>50%)

**Possible causes:**
1. GPU acceleration disabled → Enable in config
2. Too many targets tracked → Reduce detection sensitivity
3. High sample rate → Use 48000 Hz (not 96000 Hz)

**Check:**
```python
# In app/core/constants.py
SAMPLE_RATE = 48000  # Should be 48000, not 96000
MAX_WORKERS = 3       # Increase if CPU has 8+ cores
```

### Issue: No game detected (Tab 3 shows "No games running")

**Solution:**
1. Launch game first, then RadarSuite
2. Wait 5 seconds for auto-scan
3. If still not detected, game may not be in database
4. Check: `app/utils/game_detector.py` for supported games list

### Issue: Bluetooth audio not working after switching

**Solution:**
1. Stop detection (press STOP)
2. Tab 2 → Click "Rescan Devices"
3. Select Bluetooth device
4. Press "Apply"
5. Press START

---

## Uninstallation

### Remove RadarSuite

```cmd
# Remove source code
rmdir /s AudioRadar

# Remove configuration
rmdir /s "%APPDATA%\RadarSuite"

# Uninstall Python packages (if not needed for other projects)
pip uninstall PyQt5 numpy scipy sounddevice pyaudiowpatch -y
```

### Remove Python 3.11

1. Control Panel → Programs → Uninstall a program
2. Find "Python 3.11.x" → Uninstall

---

## Next Steps

After installation:
1. **Read [Usage Guide](USAGE.md)** for feature walkthrough
2. **Configure audio** for your setup (mic vs loopback)
3. **Test detection** with test mode (Tab 2 → Enable Test Mode)
4. **Optimize settings** based on your audio environment

---

**RadarSuite V4.2.0** - Installation complete! Ready for tactical audio intelligence.
