"""
RadarSuite v4.2.1 - Audio Engine
Audio capture via sounddevice/soundcard/pyaudiowpatch

FIXED v4.2.1: Added comprehensive type hints
"""

from __future__ import annotations

import time
import queue
import threading
import sys
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING

import numpy as np

from core.logger import log

if TYPE_CHECKING:
    from numpy.typing import NDArray

# FIXED v3.5.4: Proper numpy compatibility wrapper for soundcard library
# numpy.fromstring was removed in numpy 2.0, soundcard may use it internally
_original_frombuffer = np.frombuffer
def _fromstring_compat(string, dtype=float, count=-1, sep='', **kwargs):
    """Compatibility wrapper: numpy.fromstring -> numpy.frombuffer"""
    if sep == '' or sep is None:
        return _original_frombuffer(string, dtype=dtype, count=count)
    else:
        raise NotImplementedError("Text mode fromstring not supported in compat shim")

if not hasattr(np, 'fromstring'):
    np.fromstring = _fromstring_compat

sd = None
sd_import_error = None
sc = None
sc_import_error = None


def _load_sounddevice():
    """Lazy import sounddevice with detailed error logging."""
    global sd, sd_import_error
    if sd is not None:
        return sd
    try:
        import sounddevice as _sd

        sd = _sd
        sd_import_error = None
    except Exception as exc:
        sd = None
        sd_import_error = f"{type(exc).__name__}: {exc}"
        log(f"sounddevice unavailable: {sd_import_error}", "WARN")
    return sd


def _load_soundcard():
    """Lazy import soundcard with detailed error logging."""
    global sc, sc_import_error
    if sc is not None:
        return sc
    try:
        import soundcard as _sc

        sc = _sc
        sc_import_error = None
    except Exception as exc:
        sc = None
        sc_import_error = f"{type(exc).__name__}: {exc}"
        log(f"soundcard unavailable: {sc_import_error}", "WARN")
    return sc

# FIXED v4.1.1: Try pyaudiowpatch for WASAPI loopback with detailed error logging
PYAUDIO_AVAILABLE = False
PYAUDIO_IMPORT_ERROR = None
pyaudio = None

try:
    import pyaudiowpatch as pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError as e:
    PYAUDIO_IMPORT_ERROR = f"ImportError: {e}"
except OSError as e:
    # DLL loading errors on Windows
    PYAUDIO_IMPORT_ERROR = f"OSError (likely missing DLL): {e}"
except Exception as e:
    PYAUDIO_IMPORT_ERROR = f"{type(e).__name__}: {e}"

# Log pyaudiowpatch availability at module load
if PYAUDIO_AVAILABLE:
    log(f"pyaudiowpatch loaded successfully", "INFO")
else:
    log(f"pyaudiowpatch NOT available - {PYAUDIO_IMPORT_ERROR}", "WARN")


class AudioEngine:
    """
    Audio capture engine supporting:
    - sounddevice (standard input devices)
    - soundcard loopback (capture from speaker output)

    FIXED v4.1.2: Auto-detection of channel count for 5.1/7.1 support
    FIXED v4.2.1: Added comprehensive type hints
    """

    sample_rate: int
    blocksize: int
    channels: int
    device: Optional[Any]
    stream: Optional[Any]
    running: bool
    backend: str
    use_loopback: bool

    def __init__(self) -> None:
        log("AudioEngine.__init__", "INFO")
        self.sample_rate = 48000
        self.blocksize = 2048
        self.channels = 2  # Default, will be auto-detected
        self.requested_channels = 0  # 0 = auto-detect from device
        self.actual_channels = 2  # What we actually got from device
        self.device = None
        self.stream = None
        self.queue = queue.Queue(maxsize=8)
        self.last_block = None
        self._last_block_lock = threading.Lock()  # FIXED v4.2.1-k0004: Thread safety for last_block
        self.running = False
        self.backend = "sounddevice"
        self.use_loopback = False

        # FIXED v4.1.2: Channel layout info for spatial audio
        self.channel_layout = "stereo"  # "stereo", "5.1", "7.1"
        self.has_surround = False  # True if 5.1 or higher

    def list_devices(self) -> List[Dict[str, Any]]:
        """List available audio devices (v4.2.1: type hints)."""
        devices: List[Dict[str, Any]] = []

        sd_module = _load_sounddevice()
        if sd_module is not None:
            try:
                sd_devices = sd_module.query_devices()
                for idx, dev in enumerate(sd_devices):
                    devices.append({
                        'index': idx,
                        'name': dev['name'],
                        'channels': dev['max_input_channels'],
                        'samplerate': int(dev['default_samplerate']),
                        'hostapi': sd_module.query_hostapis(dev['hostapi'])['name'],
                        'type': 'input' if dev['max_input_channels'] > 0 else 'output',
                        'backend': 'sounddevice'
                    })
            except Exception as e:
                log(f"Error listing sounddevice devices: {e}", "ERROR")

        sc_module = _load_soundcard()
        if sc_module is not None:
            try:
                speakers = sc_module.all_speakers()
                for idx, spk in enumerate(speakers):
                    devices.append({
                        'index': f"loopback_{idx}",
                        'name': f"{spk.name} (Loopback)",
                        'channels': spk.channels,
                        'samplerate': 48000,
                        'hostapi': 'soundcard',
                        'type': 'loopback',
                        'backend': 'soundcard',
                        'speaker_obj': spk
                    })
            except Exception as e:
                log(f"Error listing soundcard devices: {e}", "ERROR")

        return devices

    def start(self) -> None:
        """Start audio capture (v4.2.1: type hints)."""
        if self.running:
            log("AudioEngine already running", "WARN")
            return

        # Validate backend availability before flipping the running flag to avoid
        # leaving the engine in a half-started state when optional dependencies
        # are missing (e.g., sounddevice not installed). This was previously
        # causing an AttributeError on environments without sounddevice because
        # `_start_sounddevice` unconditionally referenced the module-level `sd`.
        if self.use_loopback:
            if _load_soundcard() is None and not (PYAUDIO_AVAILABLE and sys.platform == 'win32'):
                log("Cannot start loopback: no soundcard or pyaudiowpatch backend available", "ERROR")
                return
        elif _load_sounddevice() is None:
            log("Cannot start sounddevice input: sounddevice module is not available", "ERROR")
            return

        self.running = True

        sc_module = _load_soundcard()

        if self.use_loopback and sc_module is not None:
            log(f"Starting soundcard loopback: {self.sample_rate}Hz, {self.blocksize} samples", "INFO")
            self._start_loopback()
        else:
            log(f"Starting sounddevice: device={self.device}, {self.sample_rate}Hz, {self.blocksize} samples", "INFO")
            self._start_sounddevice()

    def _start_sounddevice(self) -> None:
        """Start sounddevice input stream (v4.2.1: type hints)."""
        sd_module = _load_sounddevice()
        if sd_module is None:
            log("sounddevice backend unavailable; aborting audio capture", "ERROR")
            self.running = False
            return

        try:
            def callback(indata, frames, time_info, status):
                if status:
                    log(f"sounddevice status: {status}", "WARN")

                data = indata.copy()
                with self._last_block_lock:  # FIXED v4.2.1-k0004: Thread-safe access
                    self.last_block = data

                try:
                    self.queue.put_nowait(data)
                except queue.Full:
                    pass

            self.stream = sd_module.InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.blocksize,
                callback=callback
            )
            self.stream.start()
            log(f"sounddevice stream started successfully", "INFO")

        except Exception as e:
            log(f"Error starting sounddevice: {e}", "ERROR")
            self.running = False

    def _start_loopback(self):
        """Start loopback capture - tries pyaudiowpatch first, falls back to soundcard"""

        # FIXED v3.5.4: Use pyaudiowpatch for WASAPI loopback (most reliable)
        if PYAUDIO_AVAILABLE and sys.platform == 'win32':
            log("Attempting loopback via pyaudiowpatch (WASAPI)", "INFO")
            if self._start_loopback_pyaudio():
                return
            log("pyaudiowpatch failed, trying soundcard fallback", "WARN")

        # Fallback to soundcard
        sc_module = _load_soundcard()
        if sc_module is not None:
            log("Attempting loopback via soundcard", "INFO")
            self._start_loopback_soundcard(sc_module)
        else:
            log("No loopback backend available!", "ERROR")
            self.running = False

    def _start_loopback_pyaudio(self):
        """Start WASAPI loopback using pyaudiowpatch (preferred method)"""
        try:
            def loopback_thread():
                p = None
                stream = None
                try:
                    p = pyaudio.PyAudio()

                    # Find WASAPI host API
                    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
                    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

                    log(f"Default speakers: {default_speakers['name']}", "INFO")

                    # Find the loopback device for these speakers
                    # pyaudiowpatch exposes loopback devices with isLoopbackDevice=True
                    loopback_device = None
                    for i in range(p.get_device_count()):
                        dev_info = p.get_device_info_by_index(i)
                        # Check if this is a loopback device matching our speakers
                        if dev_info.get("isLoopbackDevice", False):
                            if default_speakers["name"] in dev_info["name"]:
                                loopback_device = dev_info
                                log(f"Found loopback device: {dev_info['name']}", "INFO")
                                break

                    if loopback_device is None:
                        log("No loopback device found for default speakers", "ERROR")
                        self.running = False
                        return

                    # FIXED v4.1.2: Auto-detect channel count from device
                    device_channels = int(loopback_device["maxInputChannels"])
                    sample_rate = int(loopback_device["defaultSampleRate"])

                    # Use device's native channel count if auto-detect (0) or requested > available
                    if self.requested_channels == 0 or self.requested_channels > device_channels:
                        channels = device_channels
                    else:
                        channels = self.requested_channels

                    # Update engine's actual channel count
                    self.actual_channels = channels

                    # Determine channel layout for spatial audio
                    if channels >= 8:
                        self.channel_layout = "7.1"
                        self.has_surround = True
                    elif channels >= 6:
                        self.channel_layout = "5.1"
                        self.has_surround = True
                    else:
                        self.channel_layout = "stereo"
                        self.has_surround = False

                    log(f"WASAPI loopback: {loopback_device['name']}", "INFO")
                    log(f"  Device channels: {device_channels}, Using: {channels} ({self.channel_layout})", "INFO")
                    log(f"  Sample rate: {sample_rate}Hz, Surround: {self.has_surround}", "INFO")

                    # Open loopback stream (no as_loopback needed - device IS loopback)
                    stream = p.open(
                        format=pyaudio.paFloat32,
                        channels=channels,
                        rate=sample_rate,
                        frames_per_buffer=self.blocksize,
                        input=True,
                        input_device_index=loopback_device["index"]
                    )

                    log(f"pyaudiowpatch loopback started: {sample_rate}Hz, {channels}ch", "INFO")

                    while self.running:
                        try:
                            raw_data = stream.read(self.blocksize, exception_on_overflow=False)
                            data = np.frombuffer(raw_data, dtype=np.float32)

                            # Reshape to (frames, channels)
                            if channels > 1:
                                data = data.reshape(-1, channels)
                            else:
                                data = data.reshape(-1, 1)

                            with self._last_block_lock:  # FIXED v4.2.1-k0004: Thread-safe access
                                self.last_block = data.copy()

                            try:
                                self.queue.put_nowait(data.copy())
                            except queue.Full:
                                pass

                        except Exception as e:
                            if self.running:
                                log(f"Loopback read error: {e}", "WARN")
                            break

                except Exception as e:
                    log(f"Error in pyaudiowpatch loopback thread: {e}", "ERROR")
                    self.running = False
                finally:
                    if stream is not None:
                        try:
                            stream.stop_stream()
                            stream.close()
                        except (OSError, RuntimeError, AttributeError):
                            pass  # Stream already closed or invalid
                    if p is not None:
                        try:
                            p.terminate()
                        except (OSError, RuntimeError, AttributeError):
                            pass  # PyAudio already terminated

            thread = threading.Thread(target=loopback_thread, daemon=True)
            thread.start()
            return True

        except Exception as e:
            log(f"Failed to start pyaudiowpatch loopback: {e}", "ERROR")
            return False

    def _start_loopback_soundcard(self, sc_module):
        """Start soundcard loopback capture (fallback method)"""

        def loopback_thread():
            # FIXED v3.5.3: Initialize COM on Windows for WASAPI loopback
            com_initialized = False
            if sys.platform == 'win32':
                # Try pythoncom first, then fallback to ctypes
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                    com_initialized = True
                    log("COM initialized via pythoncom", "INFO")
                except ImportError:
                    # Fallback: use ctypes to initialize COM
                    try:
                        import ctypes
                        ctypes.windll.ole32.CoInitialize(None)
                        com_initialized = True
                        log("COM initialized via ctypes", "INFO")
                    except Exception as e:
                        log(f"COM init failed (ctypes): {e}", "WARN")
                except Exception as e:
                    log(f"COM init error: {e}", "WARN")

            try:
                # FIXED v3.5.4: Apply numpy patch again inside thread with proper wrapper
                import numpy as _np
                if not hasattr(_np, 'fromstring'):
                    _np.fromstring = _fromstring_compat
                    log("Numpy fromstring patched in loopback thread", "INFO")

                spk = sc_module.default_speaker()
                log(f"Using speaker: {spk.name}, channels: {spk.channels}", "INFO")

                # FIXED v3.5.3: Use get_microphone with include_loopback for WASAPI loopback
                loopback_mic = sc_module.get_microphone(id=str(spk.id), include_loopback=True)
                log(f"Loopback microphone: {loopback_mic.name}", "INFO")

                with loopback_mic.recorder(samplerate=self.sample_rate, channels=self.channels, blocksize=self.blocksize) as rec:
                    while self.running:
                        data = rec.record(numframes=self.blocksize)
                        with self._last_block_lock:  # FIXED v4.2.1-k0004: Thread-safe access
                            self.last_block = data.copy()

                        try:
                            self.queue.put_nowait(data.copy())
                        except queue.Full:
                            pass

            except Exception as e:
                log(f"Error in soundcard loopback thread: {e}", "ERROR")
                self.running = False
            finally:
                # Cleanup COM
                if com_initialized and sys.platform == 'win32':
                    try:
                        import ctypes
                        ctypes.windll.ole32.CoUninitialize()
                    except (OSError, AttributeError, ImportError):
                        pass  # COM cleanup failed, non-critical

        thread = threading.Thread(target=loopback_thread, daemon=True)
        thread.start()

    def stop(self):
        """
        Stop audio capture with automatic retry

        ENHANCED v3.5.0: Retry logic prevents hangs on device errors
        """
        if not self.running:
            return

        log("Stopping AudioEngine", "INFO")
        self.running = False

        if self.stream is not None:
            retry_count = 0
            max_retries = 3

            while retry_count < max_retries:
                try:
                    self.stream.stop()
                    self.stream.close()
                    self.stream = None
                    log("Audio stream stopped successfully", "INFO")
                    break  # Success
                except Exception as e:
                    retry_count += 1
                    log(f"Error stopping stream (attempt {retry_count}/{max_retries}): {e}", "WARNING")

                    if retry_count < max_retries:
                        time.sleep(0.5)  # Wait before retry
                    else:
                        log("Failed to stop stream after retries, forcing cleanup", "ERROR")
                        self.stream = None  # Force cleanup to prevent memory leak

    def read_block(self, timeout=0.0):
        """Read audio block from queue"""
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_last_block(self):
        """Thread-safe access to last_block (FIXED v4.2.1-k0004)"""
        with self._last_block_lock:
            return self.last_block

