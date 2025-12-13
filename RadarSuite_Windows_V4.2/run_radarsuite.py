"""Launcher stub for PyInstaller and local execution.

This wrapper ensures imports run in package context so relative imports inside
``app`` resolve correctly when bundled.
"""
from app.main import main

if __name__ == "__main__":
    raise SystemExit(main())
