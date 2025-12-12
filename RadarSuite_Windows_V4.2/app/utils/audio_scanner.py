"""
RadarSuite V4.2.1 - Audio Source Scanner
Scans and monitors audio sources - shows selected device and available devices
"""

import time
import psutil

from core.logger import log

sd = None
sd_import_error = None
sc = None
sc_import_error = None


def _load_sounddevice():
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
        log(f"sounddevice unavailable for AudioSourceScanner: {sd_import_error}", "WARN")
    return sd


def _load_soundcard():
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
        log(f"soundcard unavailable for AudioSourceScanner: {sc_import_error}", "WARN")
    return sc


class AudioSourceScanner:
    """
    Scans system for audio sources and monitors usage
    Shows: Currently selected device (green) vs available devices (gray)

    v3.5.1: Fixed - now properly tracks selected device instead of showing
            all devices as "active" incorrectly
    """

    def __init__(self, platform_detector=None):
        log("AudioSourceScanner.__init__", "INFO")

        self.selected_device = None  # Currently selected device name
        self.selected_device_index = -1
        self.is_receiving_audio = False  # True if audio data is being received

        self.active_sources = []   # Selected/in-use devices
        self.inactive_sources = [] # Available but not selected devices
        self.last_scan_time = 0.0
        self.scan_interval = 2.0  # Scan every 2 seconds
        self.platform_detector = platform_detector

        # Audio activity tracking
        self.last_audio_time = 0.0
        self.audio_activity_timeout = 3.0  # Consider inactive after 3 seconds

    def set_selected_device(self, device_name, device_index=-1):
        """Set the currently selected/active device"""
        self.selected_device = device_name
        self.selected_device_index = device_index
        log(f"AudioSourceScanner: Selected device set to '{device_name}'", "INFO")

    def report_audio_activity(self, has_audio=True):
        """Report that audio is being received (call from main audio loop)"""
        if has_audio:
            self.last_audio_time = time.time()
            self.is_receiving_audio = True
        else:
            # Check if we've timed out
            if time.time() - self.last_audio_time > self.audio_activity_timeout:
                self.is_receiving_audio = False

    def scan_audio_sources(self):
        """
        Scan for audio sources - properly shows selected vs available

        Returns: dict with 'active' (selected device) and 'inactive' (available devices)
        """
        try:
            current_time = time.time()

            # Don't scan too frequently
            if current_time - self.last_scan_time < self.scan_interval:
                return {
                    'active': self.active_sources,
                    'inactive': self.inactive_sources,
                    'total': len(self.active_sources) + len(self.inactive_sources),
                    'is_receiving': self.is_receiving_audio
                }

            self.last_scan_time = current_time

            active = []
            inactive = []

            # Check audio activity timeout
            if current_time - self.last_audio_time > self.audio_activity_timeout:
                self.is_receiving_audio = False

            # Scan sounddevice sources
            sd_module = _load_sounddevice()
            if sd_module:
                try:
                    devices = sd_module.query_devices()
                    default_input = None
                    try:
                        default_input = sd_module.query_devices(kind='input')
                    except Exception:
                        pass

                    for i, dev in enumerate(devices):
                        # Only show input devices
                        if dev['max_input_channels'] <= 0:
                            continue

                        dev_info = {
                            'name': dev['name'],
                            'index': i,
                            'channels': dev['max_input_channels'],
                            'samplerate': int(dev['default_samplerate']),
                            'backend': 'sounddevice',
                            'type': 'input',
                            'is_default': default_input and dev['name'] == default_input['name']
                        }

                        # Check if this is the selected device
                        is_selected = False
                        if self.selected_device:
                            is_selected = (
                                self.selected_device in dev['name'] or
                                dev['name'] in self.selected_device or
                                i == self.selected_device_index
                            )
                        elif dev_info['is_default']:
                            # If no device explicitly selected, use default
                            is_selected = True

                        if is_selected:
                            dev_info['status'] = 'receiving' if self.is_receiving_audio else 'selected'
                            active.append(dev_info)
                        else:
                            dev_info['status'] = 'available'
                            inactive.append(dev_info)

                except Exception as e:
                    log(f"Error scanning sounddevice: {e}", "ERROR")

            # Scan soundcard loopback sources
            sc_module = _load_soundcard()
            if sc_module:
                try:
                    speakers = sc_module.all_speakers()
                    for speaker in speakers:
                        dev_info = {
                            'name': f"[Loopback] {speaker.name}",
                            'index': speaker.id if hasattr(speaker, 'id') else 0,
                            'channels': speaker.channels if hasattr(speaker, 'channels') else 2,
                            'samplerate': 48000,
                            'backend': 'soundcard',
                            'type': 'loopback',
                            'is_default': False
                        }

                        # Check if loopback is selected
                        is_selected = False
                        if self.selected_device and 'loopback' in self.selected_device.lower():
                            is_selected = speaker.name in self.selected_device

                        if is_selected:
                            dev_info['status'] = 'receiving' if self.is_receiving_audio else 'selected'
                            active.append(dev_info)
                        else:
                            dev_info['status'] = 'available'
                            inactive.append(dev_info)

                except Exception as e:
                    log(f"Error scanning soundcard: {e}", "ERROR")

            self.active_sources = active
            self.inactive_sources = inactive

            return {
                'active': self.active_sources,
                'inactive': self.inactive_sources,
                'total': len(active) + len(inactive),
                'is_receiving': self.is_receiving_audio
            }

        except Exception as e:
            log(f"Error in AudioSourceScanner.scan_audio_sources: {e}", "ERROR")
            return {
                'active': [],
                'inactive': [],
                'total': 0,
                'is_receiving': False
            }


# ============================================================================
# HUMAN VOICE DETECTOR (v3.0)
# ============================================================================
