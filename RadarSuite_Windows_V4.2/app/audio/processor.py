"""
RadarSuite v4.2.0 - Audio Processor
Audio signal processing and 3D localization algorithms

Extracted from MainWindow as part of god object refactoring (Punkt 1)
"""

import numpy as np
from scipy import signal as sp_signal
from typing import Tuple, Dict, Optional

try:
    from .core.logger import log
except ImportError:
    from core.logger import log


class AudioProcessor:
    """
    Handles audio signal processing and 3D spatial analysis.

    Extracted from MainWindow to improve code organization and testability.

    Features:
    - Audio gain control (manual and auto)
    - Noise gate filtering
    - 3D localization using ITD/ILD
    - Energy and balance computation
    - Elevation estimation

    FIXED v4.2.0: Extracted from main.py god object
    """

    # Physical constants for 3D localization
    SPEED_OF_SOUND = 343.0  # m/s at 20°C
    HEAD_WIDTH = 0.17       # meters (average human head width)

    # ITD/ILD thresholds for localization
    ITD_THRESHOLD = 0.001   # seconds (minimum detectable ITD)
    ILD_THRESHOLD = 0.5     # dB (minimum detectable ILD)

    def __init__(self, sample_rate: int = 48000):
        """
        Initialize AudioProcessor.

        Args:
            sample_rate: Audio sample rate in Hz (default 48000 for FMOD/UE5)
        """
        self.sample_rate = sample_rate
        log(f"AudioProcessor initialized (sample_rate={sample_rate}Hz)", "INFO")

    def apply_processing(
        self,
        block: np.ndarray,
        auto_gain: bool = False,
        manual_gain: float = 1.0,
        noise_gate_db: float = -60.0
    ) -> np.ndarray:
        """
        Apply audio enhancements: auto-gain, manual gain, noise gate.

        Args:
            block: Audio data (numpy array, shape [samples] or [samples, channels])
            auto_gain: Enable automatic gain control
            manual_gain: Manual gain multiplier (1.0 = unity)
            noise_gate_db: Noise gate threshold in dB (-80 to -20)

        Returns:
            Processed audio block (same shape as input)
        """
        try:
            if block is None or len(block) == 0:
                return block

            processed = block.copy()

            # Apply noise gate (remove audio below threshold)
            noise_gate_linear = 10 ** (noise_gate_db / 20.0)
            rms = np.sqrt(np.mean(processed ** 2))

            if rms < noise_gate_linear:
                # Below noise gate - mute
                return np.zeros_like(processed)

            # Apply gain (auto or manual)
            if auto_gain:
                # Auto-gain: target -20 dBFS RMS
                target_rms = 0.1  # -20 dBFS
                current_rms = np.sqrt(np.mean(processed ** 2)) + 1e-10
                auto_gain_value = target_rms / current_rms

                # Limit auto-gain to reasonable range (1x to 100x)
                auto_gain_value = np.clip(auto_gain_value, 1.0, 100.0)
                processed *= auto_gain_value
            else:
                # Manual gain
                processed *= manual_gain

            # Prevent clipping - normalize if over ±1.0
            max_val = np.max(np.abs(processed))
            if max_val > 1.0:
                processed /= max_val

            return processed

        except Exception as e:
            log(f"Error in apply_processing: {e}", "ERROR")
            return block  # Return original on error

    def compute_orientation(self, block: np.ndarray) -> Tuple[float, float]:
        """
        Compute energy and L/R balance from stereo audio.

        Args:
            block: Audio data (numpy array, shape [samples, channels])

        Returns:
            Tuple of (energy, balance) where:
            - energy: RMS energy (0.0 to 1.0)
            - balance: L/R balance (-1.0 = full left, +1.0 = full right)
        """
        try:
            if block.ndim == 2 and block.shape[1] >= 2:
                left = block[:, 0]
                right = block[:, 1]

                energy_left = np.sqrt(np.mean(left ** 2))
                energy_right = np.sqrt(np.mean(right ** 2))
                total_energy = (energy_left + energy_right) / 2.0

                # Calculate balance (-1 = full left, +1 = full right)
                if total_energy > 1e-10:
                    balance = (energy_right - energy_left) / (energy_right + energy_left + 1e-10)
                else:
                    balance = 0.0

                return total_energy, balance
            else:
                # Mono audio
                energy = np.sqrt(np.mean(block ** 2))
                return energy, 0.0

        except Exception as e:
            log(f"Error in compute_orientation: {e}", "ERROR")
            return 0.0, 0.0

    def compute_location_3d(self, block: np.ndarray) -> Dict[str, float]:
        """
        Compute 3D spatial location using ITD/ILD analysis.

        Uses binaural cues:
        - ITD (Interaural Time Difference): For horizontal angle
        - ILD (Interaural Level Difference): For distance estimation
        - Frequency content: For elevation estimation

        Args:
            block: Stereo audio data (numpy array, shape [samples, 2+])

        Returns:
            Dictionary with:
            - 'angle': Horizontal angle in degrees (-180 to +180, 0 = front)
            - 'distance': Estimated distance in meters (0.5 to 15.0)
            - 'elevation': Elevation angle in degrees (-45 to +45)
            - 'confidence': Localization confidence (0.0 to 1.0)
        """
        result = {
            'angle': 0.0,
            'distance': 5.0,
            'elevation': 0.0,
            'confidence': 0.0
        }

        try:
            if block.ndim != 2 or block.shape[1] < 2:
                return result

            left = block[:, 0]
            right = block[:, 1]

            # Check for sufficient signal
            energy_left = np.sqrt(np.mean(left ** 2))
            energy_right = np.sqrt(np.mean(right ** 2))

            if energy_left < 1e-6 and energy_right < 1e-6:
                return result  # No signal

            # ================================================================
            # ITD Analysis (Interaural Time Difference)
            # ================================================================
            # Cross-correlation to find time delay between channels
            correlation = np.correlate(left, right, mode='full')
            correlation_center = len(correlation) // 2

            # Search window: ±3ms (max physical ITD for human head)
            max_delay_samples = int(0.003 * self.sample_rate)
            search_start = correlation_center - max_delay_samples
            search_end = correlation_center + max_delay_samples + 1

            # Find peak in correlation
            search_region = correlation[search_start:search_end]
            peak_index = np.argmax(np.abs(search_region))
            peak_delay = peak_index - max_delay_samples

            # Convert to time delay
            itd_seconds = peak_delay / self.sample_rate

            # Convert ITD to angle using head model
            # ITD = (d/c) * sin(theta), where d = head width, c = speed of sound
            max_itd = self.HEAD_WIDTH / self.SPEED_OF_SOUND

            if abs(itd_seconds) < max_itd:
                sin_theta = itd_seconds / max_itd
                sin_theta = np.clip(sin_theta, -1.0, 1.0)
                angle_rad = np.arcsin(sin_theta)
                angle_deg = np.degrees(angle_rad)
            else:
                # Clamp to ±90 degrees
                angle_deg = 90.0 if itd_seconds > 0 else -90.0

            result['angle'] = angle_deg

            # ================================================================
            # ILD Analysis (Interaural Level Difference)
            # ================================================================
            # ILD indicates distance - closer sounds have larger ILD
            ild_db = 20 * np.log10((energy_right + 1e-10) / (energy_left + 1e-10))

            # Map ILD to distance (inverse relationship)
            # Large ILD = close, small ILD = far
            ild_magnitude = abs(ild_db)

            if ild_magnitude > 10:
                distance = 1.0  # Very close
            elif ild_magnitude > 5:
                distance = 3.0  # Close
            elif ild_magnitude > 2:
                distance = 6.0  # Medium
            else:
                distance = 10.0  # Far

            result['distance'] = distance

            # ================================================================
            # Elevation Estimation (Frequency Content)
            # ================================================================
            elevation = self.compute_elevation(block)
            result['elevation'] = elevation

            # ================================================================
            # Confidence Calculation
            # ================================================================
            # Based on correlation strength and signal level
            correlation_max = np.max(np.abs(search_region))
            correlation_norm = correlation_max / (len(left) * np.sqrt(energy_left * energy_right + 1e-10))

            # Confidence: correlation strength × signal level
            signal_level = (energy_left + energy_right) / 2.0
            confidence = min(1.0, correlation_norm * 10) * min(1.0, signal_level * 100)

            result['confidence'] = confidence

            return result

        except Exception as e:
            log(f"Error in compute_location_3d: {e}", "ERROR")
            return result

    def compute_elevation(self, block: np.ndarray) -> float:
        """
        Estimate elevation angle from frequency content.

        Higher frequencies tend to come from above (HRTF characteristic).

        Args:
            block: Audio data (numpy array)

        Returns:
            Elevation angle in degrees (-45 to +45)
        """
        try:
            # Get mono signal
            if block.ndim == 2:
                mono = np.mean(block, axis=1)
            else:
                mono = block

            # Compute FFT
            n_fft = min(len(mono), 2048)
            spectrum = np.abs(np.fft.rfft(mono[:n_fft]))
            freqs = np.fft.rfftfreq(n_fft, 1.0 / self.sample_rate)

            # Calculate spectral centroid
            if np.sum(spectrum) > 1e-10:
                centroid = np.sum(freqs * spectrum) / np.sum(spectrum)
            else:
                centroid = 1000  # Default

            # Map centroid to elevation
            # Low centroid (<500 Hz) = below horizon
            # High centroid (>2000 Hz) = above horizon
            if centroid < 500:
                elevation = -30.0
            elif centroid < 1000:
                elevation = -15.0
            elif centroid < 2000:
                elevation = 0.0
            elif centroid < 4000:
                elevation = 15.0
            else:
                elevation = 30.0

            return elevation

        except Exception as e:
            log(f"Error in compute_elevation: {e}", "ERROR")
            return 0.0

    def generate_test_signal(
        self,
        duration_samples: int,
        channels: int = 2,
        frequency: float = 440.0,
        angle: float = 0.0
    ) -> np.ndarray:
        """
        Generate a test audio signal for debugging.

        Args:
            duration_samples: Number of samples to generate
            channels: Number of audio channels
            frequency: Test tone frequency in Hz
            angle: Simulated source angle in degrees

        Returns:
            Test audio block (numpy array)
        """
        t = np.arange(duration_samples) / self.sample_rate

        # Generate sine wave
        mono = 0.3 * np.sin(2 * np.pi * frequency * t)

        if channels == 1:
            return mono

        # Stereo: simulate spatial position
        angle_rad = np.radians(angle)

        # Simple panning based on angle
        pan = np.sin(angle_rad)  # -1 to +1

        left_gain = np.sqrt((1 - pan) / 2)
        right_gain = np.sqrt((1 + pan) / 2)

        stereo = np.column_stack([mono * left_gain, mono * right_gain])

        return stereo


# Singleton instance for backward compatibility
_processor_instance: Optional[AudioProcessor] = None


def get_audio_processor(sample_rate: int = 48000) -> AudioProcessor:
    """
    Get or create AudioProcessor singleton.

    Args:
        sample_rate: Audio sample rate in Hz

    Returns:
        AudioProcessor instance
    """
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = AudioProcessor(sample_rate)
    return _processor_instance
