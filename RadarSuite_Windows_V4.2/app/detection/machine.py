"""
RadarSuite v4.2.0 - ARC Machine State Detection Module
Detect and classify ARC machine states

FIXED v4.2.0: ARC Raiders-specific machine detection:
- Each machine has unique sound pattern
- States: idle, patrol, search, combat
- Bass modulation analysis (50-300 Hz)
- Spectral pattern recognition
"""

import numpy as np
from collections import deque
from core import (
    SAMPLE_RATE, MACHINE_DETECTION_WINDOW_S,
    MACHINE_MODULATION_THRESHOLD, MACHINE_BASS_MIN_HZ,
    MACHINE_BASS_MAX_HZ, log
)
from detection.spectral import SpectralFeatureExtractor


class ARCMachineDetector:
    """
    Detect and classify ARC machine states

    FIXED v4.2.0: Based on ARC Raiders official description:
    - Each machine has unique sound signature
    - Sound pattern changes with state (idle/patrol/search/combat)
    - Low-frequency modulation (mechanical sounds)
    - Temporal patterns (repetitive cycles)
    """

    def __init__(self, sample_rate=SAMPLE_RATE):
        """
        Initialize ARC machine detector

        Args:
            sample_rate: Audio sample rate (48 kHz for ARC Raiders)
        """
        self.sample_rate = sample_rate
        self.spectral_extractor = SpectralFeatureExtractor(sample_rate)

        # Detection history for temporal analysis
        self.detection_history = deque(maxlen=100)  # ~2 seconds @ 50ms blocks
        self.machine_states = deque(maxlen=20)

        # State characteristics (bass modulation depth)
        self.state_modulation = {
            'idle': (0.05, 0.15),      # Low, steady modulation
            'patrol': (0.15, 0.30),    # Medium, rhythmic modulation
            'search': (0.30, 0.50),    # Higher, irregular modulation
            'combat': (0.50, 1.00),    # High, aggressive modulation
        }

        log(f"ARCMachineDetector initialized: {sample_rate} Hz", "INFO")

    def extract_bass_envelope(self, audio_block):
        """
        Extract bass envelope for machine modulation analysis

        Machines produce low-frequency mechanical sounds (50-300 Hz)
        that modulate with their activity state

        Args:
            audio_block: Audio data (mono or stereo)

        Returns:
            Bass envelope amplitude, or 0 if invalid
        """
        if audio_block is None or len(audio_block) == 0:
            return 0

        try:
            # Ensure mono
            if len(audio_block.shape) > 1:
                mono = np.mean(audio_block, axis=1)
            else:
                mono = audio_block

            # FFT
            n_fft = min(len(mono), 2048)
            spectrum = np.fft.rfft(mono[:n_fft], n=n_fft)
            freqs = np.fft.rfftfreq(n_fft, 1.0 / self.sample_rate)

            # Bass band (machine frequencies)
            bass_mask = (freqs >= MACHINE_BASS_MIN_HZ) & (freqs <= MACHINE_BASS_MAX_HZ)
            bass_power = np.abs(spectrum[bass_mask])

            if len(bass_power) > 0:
                return np.mean(bass_power)
            else:
                return 0

        except Exception as e:
            log(f"Error extracting bass envelope: {e}", "ERROR")
            return 0

    def analyze_modulation(self, window_s=MACHINE_DETECTION_WINDOW_S):
        """
        Analyze bass modulation depth over time window

        Args:
            window_s: Time window in seconds for modulation analysis

        Returns:
            Tuple (modulation_depth, modulation_rate, is_rhythmic)
        """
        if len(self.detection_history) < 10:
            return 0, 0, False

        try:
            # Get bass envelope history
            bass_values = [h['bass_envelope'] for h in self.detection_history]

            # Calculate modulation depth (normalized variance)
            mean_bass = np.mean(bass_values)
            std_bass = np.std(bass_values)

            if mean_bass > 1e-10:
                modulation_depth = std_bass / mean_bass
            else:
                modulation_depth = 0

            # Detect modulation rate (frequency of oscillation)
            # Using autocorrelation to find periodicity
            if len(bass_values) >= 20:
                autocorr = np.correlate(bass_values, bass_values, mode='full')
                autocorr = autocorr[len(autocorr)//2:]  # Keep only positive lags

                # Find peaks
                peaks = []
                for i in range(1, len(autocorr)-1):
                    if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                        peaks.append(i)

                # First peak after lag 0 indicates period
                if len(peaks) > 1:
                    period_samples = peaks[1]  # Skip first peak (lag 0)
                    # Convert to Hz (samples @ ~50ms blocks = 20 Hz update rate)
                    modulation_rate = 20.0 / period_samples if period_samples > 0 else 0
                    is_rhythmic = True
                else:
                    modulation_rate = 0
                    is_rhythmic = False
            else:
                modulation_rate = 0
                is_rhythmic = False

            return modulation_depth, modulation_rate, is_rhythmic

        except Exception as e:
            log(f"Error analyzing modulation: {e}", "ERROR")
            return 0, 0, False

    def classify_machine_state(self, audio_block):
        """
        Classify ARC machine state based on sound pattern

        States (from ARC Raiders documentation):
        - idle: Low activity, steady hum
        - patrol: Medium activity, rhythmic movement
        - search: Increased activity, scanning sounds
        - combat: High activity, aggressive sounds

        Args:
            audio_block: Audio data (mono or stereo)

        Returns:
            Dictionary with:
            - state: 'idle', 'patrol', 'search', 'combat', 'none'
            - confidence: 0-100
            - modulation_depth: 0-1
            - is_machine: bool
        """
        if audio_block is None or len(audio_block) == 0:
            return {'state': 'none', 'confidence': 0, 'modulation_depth': 0, 'is_machine': False}

        try:
            # Extract bass envelope
            bass_envelope = self.extract_bass_envelope(audio_block)

            # Add to history
            self.detection_history.append({
                'bass_envelope': bass_envelope,
                'timestamp': np.mean(audio_block)  # Simplified timestamp
            })

            # Extract spectral features
            features = self.spectral_extractor.extract_all_features(audio_block)

            if features is None:
                return {'state': 'none', 'confidence': 0, 'modulation_depth': 0, 'is_machine': False}

            # Check if this sounds like a machine (bass-heavy, sustained)
            bass_ratio = features.get('bass_ratio', 0)
            low_mid_ratio = features.get('low_mid_ratio', 0)
            spectral_flatness = features.get('spectral_flatness', 0)

            # Machines: high bass ratio, low-mid content, relatively flat spectrum
            is_machine = (bass_ratio + low_mid_ratio) > 0.4 and spectral_flatness > 0.3

            if not is_machine:
                return {'state': 'none', 'confidence': 0, 'modulation_depth': 0, 'is_machine': False}

            # Analyze modulation if we have enough history
            modulation_depth, modulation_rate, is_rhythmic = self.analyze_modulation()

            # Classify state based on modulation depth
            state = 'none'
            confidence = 0

            for state_name, (mod_min, mod_max) in self.state_modulation.items():
                if mod_min <= modulation_depth <= mod_max:
                    state = state_name
                    # Confidence based on how centered we are in the range
                    range_center = (mod_min + mod_max) / 2
                    distance_from_center = abs(modulation_depth - range_center)
                    range_width = (mod_max - mod_min) / 2
                    confidence = max(0, 100 - int((distance_from_center / range_width) * 50))
                    break

            # Boost confidence if rhythmic (patrol/combat are rhythmic)
            if is_rhythmic and state in ['patrol', 'combat']:
                confidence = min(100, confidence + 15)

            return {
                'state': state,
                'confidence': confidence,
                'modulation_depth': modulation_depth,
                'modulation_rate': modulation_rate,
                'is_machine': is_machine,
                'is_rhythmic': is_rhythmic,
                'bass_ratio': bass_ratio
            }

        except Exception as e:
            log(f"Error classifying machine state: {e}", "ERROR")
            return {'state': 'none', 'confidence': 0, 'modulation_depth': 0, 'is_machine': False}

    def detect(self, audio_block):
        """
        Detect ARC machine and classify state

        Args:
            audio_block: Audio data (mono or stereo)

        Returns:
            Dictionary with detection result or None
        """
        result = self.classify_machine_state(audio_block)

        # Only return if confident this is a machine
        if result['is_machine'] and result['confidence'] >= 50:
            self.machine_states.append(result)
            return result
        else:
            return None

    def get_dominant_state(self):
        """
        Get most frequent machine state from recent history

        Returns:
            Tuple (state, confidence) or ('none', 0) if no clear state
        """
        if len(self.machine_states) < 3:
            return 'none', 0

        # Count state occurrences
        state_counts = {}
        for detection in self.machine_states:
            state = detection['state']
            if state != 'none':
                state_counts[state] = state_counts.get(state, 0) + 1

        if not state_counts:
            return 'none', 0

        # Most common state
        dominant_state = max(state_counts, key=state_counts.get)
        occurrence_ratio = state_counts[dominant_state] / len(self.machine_states)
        confidence = int(occurrence_ratio * 100)

        return dominant_state, confidence
