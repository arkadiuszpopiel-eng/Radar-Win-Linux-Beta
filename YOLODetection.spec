# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file dla YOLO Object Detection
Użycie: pyinstaller YOLODetection.spec
"""

from PyInstaller.utils.hooks import collect_all, collect_data_files
import os

block_cipher = None

# Zbierz dane dla pakietów
onnxruntime_datas, onnxruntime_binaries, onnxruntime_hiddenimports = collect_all('onnxruntime')
pyqt5_datas, pyqt5_binaries, pyqt5_hiddenimports = collect_all('PyQt5')
ultralytics_datas, ultralytics_binaries, ultralytics_hiddenimports = collect_all('ultralytics')

# Dodatkowe dane aplikacji
added_files = [
    ('config', 'config'),
    ('data/classes.txt', 'data'),
    ('data/dataset.yaml', 'data'),
]

# Wszystkie dane
all_datas = added_files + onnxruntime_datas + pyqt5_datas + ultralytics_datas

# Wszystkie binaria
all_binaries = onnxruntime_binaries + pyqt5_binaries + ultralytics_binaries

# Hidden imports
hiddenimports = [
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'cv2',
    'numpy',
    'onnxruntime',
    'mss',
    'keyboard',
    'ultralytics',
    'yaml',
    'PIL',
    'psutil',
]
hiddenimports.extend(onnxruntime_hiddenimports)
hiddenimports.extend(pyqt5_hiddenimports)
hiddenimports.extend(ultralytics_hiddenimports)

# Analysis
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'pandas',
        'scipy',
        'jupyter',
        'notebook',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE (jeden plik)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YOLODetection',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # True = pokaż konsolę (dla logów), False = ukryj
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
