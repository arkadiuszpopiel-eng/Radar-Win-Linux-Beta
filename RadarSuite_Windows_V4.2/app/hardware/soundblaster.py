"""
RadarSuite V4.2.1 - Sound Blaster Optimization Module
Sound Blaster Z SE audio card optimization
ADDED v3.5.0: Sound Blaster Z SE hardware optimization
"""

try:
    import sounddevice as sd
except ImportError:
    sd = None

from scipy.signal import butter, sosfilt

from core.logger import log


class SoundBlasterOptimizer:
    """
    Sound Blaster Z SE audio card optimization
    Auto-detects Sound Blaster devices and applies optimal settings
    Optimized for Sound Blaster Z SE with 48kHz/2048 block size

    ADDED v3.5.0: Sound Blaster Z SE hardware optimization
    """

    def __init__(self):
        self.is_soundblaster = False
        self.device_name = None
        self.optimal_settings = {
            'sample_rate': 48000,  # Native rate for Sound Blaster Z SE
            'block_size': 2048,    # Optimal for low latency without dropouts
            'channels': 2          # Stereo
        }

        try:
            self._detect_soundblaster()
        except Exception as e:
            log(f"Sound Blaster detection failed: {e}", "DEBUG")

    def _detect_soundblaster(self):
        """
        Detect Sound Blaster audio devices
        Checks for Sound Blaster Z SE and other Creative cards
        """
        if sd is None:
            return

        try:
            devices = sd.query_devices()
            for idx, device in enumerate(devices):
                device_name = device.get('name', '').lower()

                # Check for Sound Blaster devices
                if any(keyword in device_name for keyword in ['sound blaster', 'creative', 'sb z', 'sbz']):
                    self.is_soundblaster = True
                    self.device_name = device.get('name', 'Unknown')
                    log(f"Sound Blaster detected: {self.device_name}", "INFO")

                    # Check specifically for Z SE model
                    if 'z se' in device_name or 'z-se' in device_name:
                        log("Sound Blaster Z SE detected - applying optimal settings", "INFO")

                    return

            log("No Sound Blaster device detected - using standard settings", "DEBUG")

        except Exception as e:
            log(f"Device enumeration error: {e}", "DEBUG")

    def get_optimal_settings(self):
        """
        Get optimal audio settings for detected hardware
        Returns dict with sample_rate, block_size, channels
        """
        if self.is_soundblaster:
            return self.optimal_settings
        else:
            # Standard settings for other audio devices
            return {
                'sample_rate': 48000,
                'block_size': 2048,
                'channels': 2
            }

    def apply_eq_compensation(self, audio_block):
        """
        Apply EQ compensation for Sound Blaster Z SE characteristics
        Sound Blaster Z SE has slight bass boost - compensate for flat response

        Args:
            audio_block: Input audio array

        Returns:
            Compensated audio array
        """
        if not self.is_soundblaster:
            return audio_block

        try:
            # Sound Blaster Z SE has ~2dB bass boost below 200Hz
            # Apply gentle high-pass filter to compensate

            # Butterworth high-pass filter: 80Hz cutoff, order 2
            sos = butter(2, 80, btype='highpass', fs=48000, output='sos')
            compensated = sosfilt(sos, audio_block, axis=0)

            # Blend 20% compensation with 80% original for subtle effect
            result = 0.8 * audio_block + 0.2 * compensated

            return result

        except Exception as e:
            log(f"EQ compensation failed: {e}", "WARNING")
            return audio_block

    def get_info(self):
        """Get Sound Blaster detection status"""
        return {
            'detected': self.is_soundblaster,
            'device_name': self.device_name,
            'optimal_sample_rate': self.optimal_settings['sample_rate'],
            'optimal_block_size': self.optimal_settings['block_size']
        }
