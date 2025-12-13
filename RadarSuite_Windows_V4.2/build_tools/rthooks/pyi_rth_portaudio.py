"""Runtime hook to ensure PortAudio DLLs are discoverable in PyInstaller builds.

This hook is intentionally defensive: it must never abort application startup even
if PortAudio binaries are missing. Only stdlib modules are used to avoid import
errors during the early bootstrap stage.
"""

import os
import sys


def _safe_add_dir(path: str) -> None:
    """Add *path* to the DLL search path if it exists."""

    try:
        if not path or not os.path.isdir(path):
            return

        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(path)
        else:
            os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        # Runtime hooks must never raise; swallow errors silently.
        pass


base_dir = getattr(sys, "_MEIPASS", None)
if base_dir and os.path.isdir(base_dir):
    _safe_add_dir(base_dir)

    candidates = [
        os.path.join(base_dir, "_sounddevice_data", "portaudio-binaries"),
        os.path.join(base_dir, "bin"),
        os.path.join(base_dir, "lib"),
        os.path.join(base_dir, "libs"),
    ]

    for candidate in candidates:
        _safe_add_dir(candidate)
