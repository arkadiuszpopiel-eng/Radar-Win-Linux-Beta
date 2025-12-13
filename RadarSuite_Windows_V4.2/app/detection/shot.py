"""
RadarSuite v4.2.0 - Shot Detection Module
Advanced shot and explosion detection for ARC Raiders

FIXED v4.2.0: Implements:
- Close vs distant shot classification
- Explosion detection (grenades, orbital drops)
- Transient-based detection
- FMOD/UE5 multi-distance recording characteristics
"""

import numpy as np
from collections import deque
from core import (
    SAMPLE_RATE, SHOT_FREQ_MIN_HZ, SHOT_FREQ_MAX_HZ,
    SHOT_BASS_THRESHOLD, SHOT_CLOSE_DISTANCE_M,
    TRANSIENT_THRESHOLD_RATIO, log
)
from detection.spectral import SpectralFeatureExtractor


class ShotDetector:
    """
    Detect and classify shots and explosions

    FIXED v4.2.0: ARC Raiders-specific:
    - FMOD multi-distance recordings (close/distant layers)
    - Transient detection (crack + tail)
    - Spectral analysis for weapon type
    """

    def __init__(self, sample_rate=SAMPLE_RATE):
        """
        Initialize shot detector

        Args:
            sample_rate: Audio sample rate (48 kHz for ARC Raiders)
        """
        self.sample_rate = sample_rate
        self.spectral_extractor = SpectralFeatureExtractor(sample_rate)

        # Detection history
        self.shot_history = deque(maxlen=10)  # Last 10 detections
        self.last_shot_time = 0

        # Thresholds
        self.transient_ratio = TRANSIENT_THRESHOLD_RATIO
        self.bass_threshold = SHOT_BASS_THRESHOLD

        log(f"ShotDetector initialized: {sample_rate} Hz", "INFO")

    def detect_transient(self, audio_block, window_ms=10):
        """
        Detect sharp transient (shot/explosion onset)

        Args:
            audio_block: Audio data (mono or stereo)
            window_ms: Window size for peak/RMS comparison

        Returns:
            Tuple (is_transient, crest_factor, peak_rms_ratio)
        """
        if audio_block is None or len(audio_block) == 0:
            return False, 0, 0

        try:
            # Ensure mono
            if len(audio_block.shape) > 1:
                mono = np.mean(audio_block, axis=1)
            else:
                mono = audio_block

            # Short window size
            window_samples = int(self.sample_rate * window_ms / 1000)
            if len(mono) < window_samples:
                window_samples = len(mono)

            # Split into short windows
            num_windows = len(mono) // window_samples
            if num_windows == 0:
                return False, 0, 0

            max_crest = 0
            max_ratio = 0

            for i in range(num_windows):
                start = i * window_samples
                end = start + window_samples
                window = mono[start:end]

                # Peak and RMS
                peak = np.max(np.abs(window))
                rms = np.sqrt(np.mean(window ** 2))

                if rms > 1e-10:
                    crest_factor = peak / rms
                    if crest_factor > max_crest:
                        max_crest = crest_factor
                        max_ratio = peak / (rms + 1e-10)

            # Transient if crest factor > threshold
            is_transient = max_crest >= self.transient_ratio

            return is_transient, max_crest, max_ratio

        except Exception as e:
            log(f"Error detecting transient: {e}", "ERROR")
            return False, 0, 0

    def classify_shot_type(self, audio_block, features=None):
        """
        Classify shot type: close/distant/explosion

        ARC Raiders uses FMOD multi-distance recordings:
        - Close shot: aggressive transient, high-freq content, tight reverb
        - Distant shot: softer transient, rolled-off highs, more reverb
        - Explosion: wide spectrum, strong bass, long tail

        Args:
            audio_block: Audio data (mono or stereo)
            features: Pre-computed spectral features (optional)

        Returns:
            Dictionary with:
            - type: 'shot_close', 'shot_distant', 'explosion', 'unknown'
            - confidence: 0-100
            - distance_estimate: meters (approximate)
            - weapon_type: 'rifle', 'pistol', 'shotgun', 'sniper', 'explosive'
        """
        if audio_block is None or len(audio_block) == 0:
            return {'type': 'unknown', 'confidence': 0, 'distance_estimate': 0, 'weapon_type': 'unknown'}

        try:
            # Ensure mono
            if len(audio_block.shape) > 1:
                mono = np.mean(audio_block, axis=1)
            else:
                mono = audio_block

            # Extract features if not provided
            if features is None:
                features = self.spectral_extractor.extract_all_features(mono)

            if features is None:
                return {'type': 'unknown', 'confidence': 0, 'distance_estimate': 0, 'weapon_type': 'unknown'}

            # Detect transient
            is_transient, crest_factor, _ = self.detect_transient(audio_block, window_ms=10)

            if not is_transient:
                return {'type': 'unknown', 'confidence': 0, 'distance_estimate': 0, 'weapon_type': 'unknown'}

            # Spectral features
            bass_ratio = features.get('bass_ratio', 0)
            low_mid_ratio = features.get('low_mid_ratio', 0)
            mid_ratio = features.get('mid_ratio', 0)
            high_mid_ratio = features.get('high_mid_ratio', 0)
            high_ratio = features.get('high_ratio', 0)
            spectral_centroid = features.get('spectral_centroid', 0)
            spectral_rolloff = features.get('spectral_rolloff', 0)

            # Classification logic
            shot_type = 'unknown'
            confidence = 0
            distance_estimate = 0
            weapon_type = 'unknown'

            # EXPLOSION: High bass, wide spectrum, long tail
            if bass_ratio > self.bass_threshold and (bass_ratio + low_mid_ratio) > 0.5:
                shot_type = 'explosion'
                weapon_type = 'explosive'
                confidence = min(100, int(bass_ratio * 150))
                distance_estimate = 50  # Explosions heard from far

            # CLOSE SHOT: High crest factor, bright spectrum, high-freq content
            elif crest_factor > 5.0 and spectral_centroid > 2000:
                shot_type = 'shot_close'
                confidence = min(100, int(crest_factor * 15))
                distance_estimate = min(SHOT_CLOSE_DISTANCE_M, 20)

                # Weapon type by spectral characteristics
                if high_ratio > 0.3:
                    weapon_type = 'sniper'  # Very bright, sharp crack
                elif mid_ratio > 0.4:
                    weapon_type = 'rifle'   # Balanced mid/high
                elif bass_ratio > 0.2:
                    weapon_type = 'shotgun' # More bass
                else:
                    weapon_type = 'pistol'  # Default

            # DISTANT SHOT: Lower crest, rolled-off highs, more reverb
            elif crest_factor > 3.0 and spectral_rolloff < 4000:
                shot_type = 'shot_distant'
                confidence = min(100, int(crest_factor * 20))
                distance_estimate = max(SHOT_CLOSE_DISTANCE_M, 50)

                # Weapon type harder to distinguish at distance
                if low_mid_ratio > 0.4:
                    weapon_type = 'rifle'
                else:
                    weapon_type = 'unknown'

            else:
                # Transient but doesn't match shot/explosion
                shot_type = 'unknown'
                confidence = 0

            return {
                'type': shot_type,
                'confidence': confidence,
                'distance_estimate': distance_estimate,
                'weapon_type': weapon_type,
                'crest_factor': crest_factor,
                'bass_ratio': bass_ratio,
                'spectral_centroid': spectral_centroid,
            }

        except Exception as e:
            log(f"Error classifying shot type: {e}", "ERROR")
            return {'type': 'unknown', 'confidence': 0, 'distance_estimate': 0, 'weapon_type': 'unknown'}

    def detect(self, audio_block):
        """
        Detect and classify shot/explosion in audio block

        Args:
            audio_block: Audio data (mono or stereo)

        Returns:
            Dictionary with detection result or None
        """
        if audio_block is None or len(audio_block) == 0:
            return None

        # Extract features
        features = self.spectral_extractor.extract_all_features(audio_block)

        # Classify
        result = self.classify_shot_type(audio_block, features)

        # Only return if confident
        if result['confidence'] >= 50:
            self.shot_history.append(result)
            return result
        else:
            return None
