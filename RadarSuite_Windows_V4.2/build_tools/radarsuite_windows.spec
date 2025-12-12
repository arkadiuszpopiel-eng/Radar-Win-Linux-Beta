# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for RadarSuite Windows V4
Builds standalone Windows executable with all dependencies
Platform: Windows x64 ONLY
Optimized: Excludes Linux-only modules and reduces warnings
Includes: PyQt5, pyqtgraph, PyOpenGL (3D radar), psutil (game detection)
"""

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Get base path - use __file__ for more reliable path resolution
# SPEC variable may not work correctly in all environments
try:
    spec_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback to SPEC if __file__ not available (older PyInstaller)
    spec_dir = os.path.dirname(os.path.abspath(SPEC))

BASE = os.path.dirname(spec_dir)
APP_DIR = os.path.join(BASE, 'app')

# Entry point
entry_script = os.path.join(BASE, 'app', 'main.py')

# Verify entry script exists
if not os.path.exists(entry_script):
    raise FileNotFoundError(f"Entry script not found: {entry_script}\nBASE={BASE}\nCWD={os.getcwd()}")

# Add app directory to Python path for module imports
sys.path.insert(0, APP_DIR)

# Collect essential PyQt5 and pyqtgraph modules
# Note: Using selective imports to avoid Qt initialization issues during build
hiddenimports = []

# Custom application modules (CRITICAL for PyInstaller)
# FIXED v4.2.1: Corrected module names to match actual structure
hiddenimports += [
    # Version module
    'version',
    # Core modules
    'core', 'core.constants', 'core.config', 'core.logger', 'core.translations',
    'core.di', 'core.confidence', 'core.error_handler', 'core.profiler', 'core.export_import',
    # Hardware modules
    'hardware', 'hardware.gpu', 'hardware.soundblaster',
    # Utilities
    'utils', 'utils.performance', 'utils.game_detector', 'utils.audio_scanner', 'utils.launcher',
    # Tracking modules
    'tracking', 'tracking.target', 'tracking.threat',
    # Detection modules
    'detection', 'detection.worker', 'detection.footstep', 'detection.shot',
    'detection.machine', 'detection.spectral',
    # Audio modules
    'audio', 'audio.cache', 'audio.engine', 'audio.classifier',
    'audio.processor', 'audio.recorder', 'audio.voice_detector',
    # Widgets (all in separate files)
    'widgets', 'widgets.toast', 'widgets.radar', 'widgets.led', 'widgets.spectrum',
    'widgets.detection_panel', 'widgets.device_panel', 'widgets.ml_training_panel',
    'widgets.ml_waveform', 'widgets.military_spectrum', 'widgets.waveform_timeline',
    # ML modules
    'ml', 'ml.detector', 'ml.feature_extractor', 'ml.yamnet',
    'ml.training', 'ml.training.recorder', 'ml.training.session_manager', 'ml.training.trainer',
    # UI modules
    'ui', 'ui.builder'
]

# PyQt5 modules
hiddenimports += [
    'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
    'PyQt5.QtOpenGL', 'PyQt5.sip'
]

# pyqtgraph modules
hiddenimports += [
    'pyqtgraph', 'pyqtgraph.graphicsItems', 'pyqtgraph.opengl',
    'pyqtgraph.widgets', 'pyqtgraph.exporters'
]

# OpenGL modules
hiddenimports += [
    'OpenGL', 'OpenGL.GL', 'OpenGL.GLU', 'OpenGL.GLUT',
    'OpenGL.arrays', 'OpenGL.platform'
]

# Scientific computing
hiddenimports += ['numpy', 'scipy', 'scipy.signal', 'scipy.fft']

# Audio libraries
hiddenimports += ['sounddevice', 'soundcard']

# System utilities
hiddenimports += ['psutil']  # Required for game detection (Module 3)

# Standard library
hiddenimports += ['queue', 'math', 'pathlib', 'datetime', 'collections', 'threading']

# Collect data files for PyQt5 and pyqtgraph
datas = []
datas += collect_data_files('PyQt5')
datas += collect_data_files('pyqtgraph')

# CRITICAL: Include sounddevice data files (contains PortAudio DLLs)
try:
    datas += collect_data_files('sounddevice')
except Exception:
    print("Warning: Could not collect sounddevice data files")

# Also try to collect _sounddevice_data which contains PortAudio binaries
try:
    datas += collect_data_files('_sounddevice_data')
except Exception:
    pass

# WINDOWS OPTIMIZATIONS: Exclude modules that cause warnings
excludes = [
    # GUI frameworks we don't use
    'matplotlib', 'pandas', 'PIL', 'tkinter',
    # Optional pyqtgraph features
    'pyqtgraph.jupyter', 'jupyter_rfb',
    # Optional scipy modules
    'scipy.special._cdflib',
    # Qt5 3D modules (not used in RadarSuite)
    'PyQt5.Qt3DCore', 'PyQt5.Qt3DRender', 'PyQt5.Qt3DAnimation',
    'PyQt5.Qt3DInput', 'PyQt5.Qt3DLogic', 'PyQt5.Qt3DExtras',
    # Qt5 WebEngine (not used)
    'PyQt5.QtWebEngine', 'PyQt5.QtWebEngineCore', 'PyQt5.QtWebEngineWidgets',
    # Qt5 Multimedia (not used - we use sounddevice instead)
    'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets',
    # Qt5 SQL (not used)
    'PyQt5.QtSql',
]

# Analysis
a = Analysis(
    [entry_script],
    pathex=[BASE, APP_DIR],  # Include app directory for module imports
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RadarSuite_Windows',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# COLLECT
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RadarSuite_Windows',
)
