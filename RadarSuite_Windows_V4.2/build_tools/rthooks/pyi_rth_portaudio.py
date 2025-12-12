"""Ensure PortAudio DLL directory is discoverable before importing sounddevice."""

import os
import sys
from pathlib import Path


def _resolve_base_dir() -> Path:
    """Return base directory depending on PyInstaller mode."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(sys.executable).parent


def _add_portaudio_dir():
    base_dir = _resolve_base_dir()
    candidates = [
        base_dir / "_internal" / "_sounddevice_data" / "portaudio-binaries",
        base_dir / "_sounddevice_data" / "portaudio-binaries",
        base_dir / "portaudio-binaries",
    ]

    for cand in candidates:
        if cand.exists():
            os.add_dll_directory(str(cand))
            os.environ["PATH"] = str(cand) + os.pathsep + os.environ.get("PATH", "")
            print(f"[pyi_rth_portaudio] Added PortAudio directory: {cand}")
            return

    print("[pyi_rth_portaudio] PortAudio directory not found; sounddevice may fail to load")


try:
    _add_portaudio_dir()
except Exception as exc:  # pragma: no cover - defensive logging only
    print(f"[pyi_rth_portaudio] Failed to configure PortAudio DLL path: {exc}")
