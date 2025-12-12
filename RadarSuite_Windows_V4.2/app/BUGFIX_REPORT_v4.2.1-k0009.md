# BUGFIX REPORT v4.2.1-k0009

## Scope
Focused review of `app/audio/engine.py` startup flow for audio capture backends.

## Findings
- **Missing dependency guard for sounddevice**: `AudioEngine.start` unconditionally invoked `_start_sounddevice`, which dereferenced the module-level `sd`. On hosts without `sounddevice` installed, this resulted in `AttributeError: 'NoneType' object has no attribute 'InputStream'`, leaving the engine stuck with `running=True` and no recovery path.

## Fixes Applied
- Added backend availability checks before toggling `running` to `True`, ensuring startup aborts cleanly with an error log when required backends are absent.
- Added a defensive guard inside `_start_sounddevice` to bail out early and reset `running` if `sounddevice` is unavailable at runtime.

## Next Steps
- Extend unit tests to mock missing optional dependencies (`sounddevice`, `soundcard`, `pyaudiowpatch`) and assert graceful degradation paths.
- Consider exposing a public method to report backend readiness so UI can inform users before attempting capture.
