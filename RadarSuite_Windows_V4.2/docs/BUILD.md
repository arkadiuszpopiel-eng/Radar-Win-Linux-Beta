# Build Guide - RadarSuite V4.2.0

Instructions for building standalone executables with PyInstaller.

---

## Table of Contents

1. [Build Overview](#build-overview)
2. [Prerequisites](#prerequisites)
3. [Windows Build](#windows-build)
4. [Build Configuration](#build-configuration)
5. [Manual Build](#manual-build)
6. [Build Output](#build-output)
7. [Distribution](#distribution)
8. [Troubleshooting](#troubleshooting)

---

## Build Overview

RadarSuite uses **PyInstaller 6.0+** to create standalone executables for Windows.

**Build scripts:**
- `RUN_BUILD_ALL_Win.cmd` - Automated Windows build (recommended)
- Manual PyInstaller invocation (advanced)

**Platform support:**
- ✅ **Windows 10/11** (x64) - Full support
- ❌ **Linux** - Not supported in V4.2 (was in V3.5.0, deprecated)

---

## Prerequisites

### Required Software

1. **Python 3.11** (64-bit)
   - Download: https://www.python.org/downloads/
   - **CRITICAL:** Add to PATH during installation

2. **PowerShell** (for ZIP packaging)
   - Built into Windows 10/11
   - Verify: `where powershell`

3. **Git** (optional, for version control)
   - Download: https://git-scm.com/

### Required Python Packages

Install all dependencies:
```cmd
pip install -r requirements-windows.txt
```

**Key packages:**
- `pyinstaller>=6.0.0` (build tool)
- All runtime dependencies (PyQt5, numpy, etc.)

---

## Windows Build

### Automated Build (Recommended)

**Script:** `RUN_BUILD_ALL_Win.cmd`

**Usage:**
```cmd
cd AudioRadar\RadarSuite_Windows_V4.2
RUN_BUILD_ALL_Win.cmd
```

**What it does:**
1. ✅ Verify Python 3.11 installed
2. ✅ Create virtual environment (.venv)
3. ✅ Install dependencies from requirements-windows.txt
4. ✅ Run tests (optional, if pytest installed)
5. ✅ Clean previous build artifacts
6. ✅ Build with PyInstaller
7. ✅ Package to timestamped ZIP

**Build time:** ~5-10 minutes (first build), ~2-3 minutes (subsequent)

### Build Output

**Console output:**
```
==========================================
RadarSuite V4.2.0 - Windows Build Script
==========================================
Step 1/7: Checking Python 3.11...
✓ Python 3.11.7 found

Step 2/7: Creating virtual environment...
✓ Virtual environment created

Step 3/7: Installing dependencies...
✓ Dependencies installed

Step 4/7: Running tests...
✓ 250 tests passed

Step 5/7: Cleaning build directory...
✓ Build directory cleaned

Step 6/7: Building with PyInstaller...
Building RadarSuite_V4.2.0_win.exe...
✓ Build complete

Step 7/7: Packaging to ZIP...
✓ Package created: RadarSuite_V4.2.0_Windows-x64_20251201_143052.zip

==========================================
BUILD SUCCESS!
==========================================
Output: dist/RadarSuite_V4.2.0_Windows-x64_20251201_143052.zip
Size: 125.3 MB
```

### File Locations

**After build:**
```
RadarSuite_Windows_V4.2/
├── build/                          (temporary build files - safe to delete)
├── dist/
│   ├── RadarSuite_V4.2.0_win/      (extracted executable directory)
│   │   ├── RadarSuite_V4.2.0_win.exe
│   │   ├── *.dll (Qt, Python runtime)
│   │   └── ... (all dependencies)
│   └── RadarSuite_V4.2.0_Windows-x64_20251201_143052.zip
└── RadarSuite_V4.2.0_win.spec      (PyInstaller spec file)
```

---

## Build Configuration

### PyInstaller Spec File

**Location:** `build_tools/RadarSuite_V4.2.0_win.spec`

**Key configuration:**
```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['../app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../app/core/*.py', 'core'),
        ('../app/audio/*.py', 'audio'),
        ('../app/detection/*.py', 'detection'),
        ('../app/tracking/*.py', 'tracking'),
        ('../app/utils/*.py', 'utils'),
        ('../app/hardware/*.py', 'hardware'),
        ('../app/widgets/*.py', 'widgets'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'pyqtgraph.opengl',
        'numpy',
        'scipy',
        'sounddevice',
        'pyaudiowpatch',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RadarSuite_V4.2.0_win',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,              # Compress with UPX
    console=False,         # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'        # Application icon (if exists)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RadarSuite_V4.2.0_win',
)
```

### Customization

#### Change Version Number

**Edit:** `build_tools/RadarSuite_V4.2.0_win.spec`

```python
# Change all occurrences
name='RadarSuite_V4.3.0_win',  # Update version
```

**Also update:**
- `app/version.py` - `__version_full__ = "v4.3.0"`
- `app/core/constants.py` - Import from version.py
- `RUN_BUILD_ALL_Win.cmd` - ZIP filename

#### Add Application Icon

1. Place `icon.ico` in `build_tools/` directory
2. Edit spec file: `icon='build_tools/icon.ico'`

#### Include Additional Files

```python
datas=[
    ('../app/core/*.py', 'core'),
    ('../README.md', '.'),           # Include README in root
    ('../docs/*', 'docs'),           # Include docs folder
],
```

#### Reduce Executable Size

**Enable more compression:**
```python
exe = EXE(
    ...
    upx=True,          # Enable UPX compression
    upx_exclude=[],    # Don't exclude any DLLs
)
```

**Exclude unused modules:**
```python
a = Analysis(
    ...
    excludes=[
        'matplotlib',  # If not used
        'pandas',      # If not used
    ],
)
```

---

## Manual Build

For advanced users who want full control.

### Step 1: Activate Virtual Environment

```cmd
cd AudioRadar\RadarSuite_Windows_V4.2
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
```

### Step 2: Install Dependencies

```cmd
pip install -r requirements-windows.txt
```

### Step 3: Clean Previous Builds

```cmd
rmdir /s /q build
rmdir /s /q dist
del *.spec
```

### Step 4: Run PyInstaller

**Using spec file (recommended):**
```cmd
pyinstaller build_tools/RadarSuite_V4.2.0_win.spec
```

**Direct invocation (creates new spec):**
```cmd
pyinstaller ^
    --name RadarSuite_V4.2.0_win ^
    --windowed ^
    --onedir ^
    --icon=build_tools/icon.ico ^
    --add-data "app/core;core" ^
    --add-data "app/audio;audio" ^
    --add-data "app/detection;detection" ^
    --add-data "app/tracking;tracking" ^
    --add-data "app/utils;utils" ^
    --add-data "app/hardware;hardware" ^
    --add-data "app/widgets;widgets" ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import PyQt5.QtWidgets ^
    --hidden-import pyqtgraph.opengl ^
    app/main.py
```

### Step 5: Package to ZIP (Optional)

**Using PowerShell:**
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipName = "RadarSuite_V4.2.0_Windows-x64_$timestamp.zip"
Compress-Archive -Path dist\RadarSuite_V4.2.0_win -DestinationPath dist\$zipName
```

---

## Build Output

### Executable Structure

```
RadarSuite_V4.2.0_win/
├── RadarSuite_V4.2.0_win.exe       (main executable)
├── python311.dll                   (Python runtime)
├── Qt5Core.dll                     (Qt framework)
├── Qt5Gui.dll
├── Qt5Widgets.dll
├── Qt5OpenGL.dll
├── numpy.libs/                     (NumPy binaries)
├── scipy.libs/                     (SciPy binaries)
├── _sounddevice.pyd                (Audio I/O)
├── _pyaudiowpatch.pyd              (WASAPI loopback)
└── ... (other dependencies)
```

### Size Breakdown

```
Total:                ~125 MB

Python Runtime:       ~15 MB
Qt5 Libraries:        ~50 MB
NumPy/SciPy:          ~40 MB
Audio Libraries:      ~5 MB
Application Code:     ~5 MB
Other Dependencies:   ~10 MB
```

---

## Distribution

### For End Users

**Distribute:**
- `RadarSuite_V4.2.0_Windows-x64_YYYYMMDD_HHMMSS.zip`

**Instructions for users:**
```
1. Extract ZIP to C:\RadarSuite\
2. Run RadarSuite_V4.2.0_win.exe
3. No Python installation needed
```

### For Developers

**Include:**
- Source code (full repository)
- `requirements-windows.txt`
- Build scripts (`RUN_BUILD_ALL_Win.cmd`)
- Documentation (`docs/` folder)

---

## Troubleshooting

### Issue: "Python 3.11 not found"

**Solution:**
```cmd
# Check Python installation
py -3.11 --version

# If missing, download from python.org
# Reinstall with "Add Python to PATH" checked
```

### Issue: "PyInstaller failed: No module named 'PyQt5'"

**Cause:** Dependencies not installed

**Solution:**
```cmd
pip install -r requirements-windows.txt
```

### Issue: "Executable fails to start - missing DLL"

**Cause:** Missing Visual C++ Redistributable

**Solution:**
1. Download VC++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Install on target system
3. Retry executable

### Issue: "Build succeeds but executable is huge (>500 MB)"

**Cause:** Including unnecessary packages

**Solution:**
```python
# Edit spec file - add to excludes:
excludes=[
    'matplotlib',
    'pandas',
    'PIL',
    'tkinter',
],
```

### Issue: "UPX compression failed"

**Cause:** UPX not installed or incompatible version

**Solution:**
```python
# Disable UPX in spec file:
exe = EXE(
    ...
    upx=False,  # Disable compression
)
```

### Issue: "Hidden imports not found at runtime"

**Cause:** PyInstaller didn't detect dynamic imports

**Solution:**
```python
# Add to spec file:
hiddenimports=[
    'your_module_name',
    'another.module',
],
```

### Issue: "Console window appears (GUI app)"

**Cause:** `console=True` in spec file

**Solution:**
```python
exe = EXE(
    ...
    console=False,  # No console for GUI app
)
```

---

## Build Verification

After build, test executable:

### Functional Test

```cmd
cd dist\RadarSuite_V4.2.0_win
RadarSuite_V4.2.0_win.exe
```

**Verify:**
- ✅ Application launches without errors
- ✅ All 4 tabs load correctly
- ✅ Audio devices detected
- ✅ Detection works (test mode)
- ✅ Radar displays correctly

### Dependency Check

```cmd
dumpbin /dependents RadarSuite_V4.2.0_win.exe
```

**Should NOT depend on:**
- ❌ Python installation (python311.dll bundled)
- ❌ System Qt libraries (all DLLs included)

---

## Next Steps

- **[Installation Guide](INSTALLATION.md)** - For end users installing the binary
- **[Usage Guide](USAGE.md)** - Using the application
- **[Known Issues](KNOWN_ISSUES.md)** - Build-related limitations

---

**RadarSuite V4.2.0** - Build standalone executables with ease.
