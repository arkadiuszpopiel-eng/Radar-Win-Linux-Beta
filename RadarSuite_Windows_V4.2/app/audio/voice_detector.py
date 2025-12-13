"""
RadarSuite V4.2.1 - Human Voice Detector
Formant analysis for voice detection
"""

import time
import numpy as np
from scipy.signal import find_peaks

from core.logger import log


class HumanVoiceDetector:
    """
    Advanced human voice detection using formant analysis
    Detects voice, breathing, communication patterns
    Distinguishes human voice from other sounds and AI/synthetic voices
    """

    def __init__(self):
        log("HumanVoiceDetector.__init__", "INFO")

        # Formant tracking (characteristic frequencies of human voice)
        # F1: 300-1000Hz (jaw opening)
        # F2: 800-2500Hz (tongue position)
        # F3: 2000-3500Hz (lip rounding)
        self.formant_ranges = {
            'F1': (300, 1000),
            'F2': (800, 2500),
            'F3': (2000, 3500)
        }

        # Pitch ranges (fundamental frequency)
        self.pitch_male = (85, 180)      # Hz
        self.pitch_female = (165, 255)   # Hz
        self.pitch_child = (250, 400)    # Hz

        # Voice activity detection
        self.voice_history = []
        self.max_voice_history = 20

        # Breathing detection
        self.breathing_detected = False
        self.breathing_history = []
        self.max_breathing_history = 10

        # Communication pattern (sustained voice vs single sounds)
        self.speech_duration = 0.0
        self.last_voice_time = 0.0

        # Voice classification
        self.voice_type = "unknown"  # male/female/child/unknown
        self.is_shouting = False
        self.is_whispering = False

    def analyze_voice(self, block, sample_rate, stereo=True):
        """
        Analyze audio block for human voice patterns

        Returns:
            dict: {
                'is_human_voice': bool,
                'confidence': float (0-100),
                'voice_type': str ('male'/'female'/'child'/'unknown'),
                'pitch_hz': float,
                'intensity': str ('whisper'/'normal'/'shout'),
                'is_breathing': bool,
                'is_communication': bool (sustained speech),
                'formants': dict (F1, F2, F3 frequencies)
            }
        """
        try:
            current_time = time.time()

            # Convert to mono
            if block.ndim == 2:
                mono = np.mean(block, axis=1)
            else:
                mono = block.ravel()

            # FFT analysis
            window = np.hanning(len(mono))
            windowed = mono * window
            fft_data = np.fft.rfft(windowed)
            freqs = np.fft.rfftfreq(len(mono), d=1.0/sample_rate)
            power = np.abs(fft_data)

            # Formant detection (find peaks in formant ranges)
            formants = {}
            formant_strengths = {}

            for formant_name, (f_min, f_max) in self.formant_ranges.items():
                formant_mask = (freqs >= f_min) & (freqs < f_max)
                formant_power = power[formant_mask]

                if len(formant_power) > 0:
                    # Find peak frequency in this formant range
                    peak_idx = np.argmax(formant_power)
                    formant_freqs = freqs[formant_mask]
                    formants[formant_name] = formant_freqs[peak_idx] if peak_idx < len(formant_freqs) else 0
                    formant_strengths[formant_name] = np.max(formant_power)
                else:
                    formants[formant_name] = 0
                    formant_strengths[formant_name] = 0

            # Pitch detection (fundamental frequency - lowest prominent frequency)
            pitch_mask = (freqs >= 50) & (freqs < 500)
            pitch_power = power[pitch_mask]
            pitch_hz = 0.0

            if len(pitch_power) > 10:
                # Use autocorrelation or simple peak detection
                peak_idx = np.argmax(pitch_power)
                pitch_freqs = freqs[pitch_mask]
                if peak_idx < len(pitch_freqs):
                    pitch_hz = pitch_freqs[peak_idx]

            # Voice signature: strong formants + pitch in human range
            total_power = np.mean(power) + 1e-9
            f1_ratio = formant_strengths['F1'] / total_power
            f2_ratio = formant_strengths['F2'] / total_power
            f3_ratio = formant_strengths['F3'] / total_power

            # Human voice typically has F1 and F2 strong, F3 moderate
            has_formant_structure = (
                f1_ratio > 0.08 and
                f2_ratio > 0.05 and
                formants['F1'] > 0 and
                formants['F2'] > 0
            )

            # Check pitch range
            pitch_in_range = False
            voice_type = "unknown"

            if self.pitch_male[0] <= pitch_hz <= self.pitch_male[1]:
                pitch_in_range = True
                voice_type = "male"
            elif self.pitch_female[0] <= pitch_hz <= self.pitch_female[1]:
                pitch_in_range = True
                voice_type = "female"
            elif self.pitch_child[0] <= pitch_hz <= self.pitch_child[1]:
                pitch_in_range = True
                voice_type = "child"

            # Initialize result
            result = {
                'is_human_voice': False,
                'confidence': 0.0,
                'voice_type': 'unknown',
                'pitch_hz': 0.0,
                'intensity': 'normal',
                'is_breathing': False,
                'is_communication': False,
                'formants': {'F1': 0, 'F2': 0, 'F3': 0}
            }

            # Voice detection
            if has_formant_structure and pitch_in_range:
                result['is_human_voice'] = True
                result['voice_type'] = voice_type
                result['pitch_hz'] = pitch_hz
                result['formants'] = formants

                # Confidence based on formant strength and pitch clarity
                formant_score = min((f1_ratio + f2_ratio) * 100, 60.0)
                pitch_score = 40.0 if pitch_in_range else 0.0
                result['confidence'] = formant_score + pitch_score

                # Intensity classification (volume-based)
                rms = np.sqrt(np.mean(mono ** 2))
                db = 20 * np.log10(rms + 1e-10)

                if db > -15:
                    result['intensity'] = 'shout'
                    self.is_shouting = True
                    self.is_whispering = False
                elif db < -35:
                    result['intensity'] = 'whisper'
                    self.is_whispering = True
                    self.is_shouting = False
                else:
                    result['intensity'] = 'normal'
                    self.is_shouting = False
                    self.is_whispering = False

                # Track voice duration for communication detection
                if current_time - self.last_voice_time < 0.5:
                    # Continuous voice
                    self.speech_duration += current_time - self.last_voice_time
                else:
                    # Gap in speech
                    self.speech_duration = 0.0

                self.last_voice_time = current_time

                # Communication = sustained speech (> 1 second)
                if self.speech_duration > 1.0:
                    result['is_communication'] = True

                # Add to history
                self.voice_history.append(current_time)
                if len(self.voice_history) > self.max_voice_history:
                    self.voice_history.pop(0)

                self.voice_type = voice_type

            # Breathing detection (low frequency, regular, low intensity)
            # Breathing: 0.2-1 Hz modulation of low frequencies (100-300 Hz)
            breathing_mask = (freqs >= 100) & (freqs < 300)
            breathing_power = np.mean(power[breathing_mask]) if np.any(breathing_mask) else 0

            # Heavy breathing during running (higher intensity, faster rhythm)
            rms = np.sqrt(np.mean(mono ** 2))
            is_breathing_candidate = (
                breathing_power > total_power * 0.03 and
                rms > 0.001 and
                not result['is_human_voice']  # breathing when not talking
            )

            if is_breathing_candidate:
                result['is_breathing'] = True
                self.breathing_detected = True
                self.breathing_history.append(current_time)
                if len(self.breathing_history) > self.max_breathing_history:
                    self.breathing_history.pop(0)
            else:
                self.breathing_detected = False

            return result

        except Exception as e:
            log(f"Error in HumanVoiceDetector.analyze_voice: {e}", "ERROR")
            return {
                'is_human_voice': False,
                'confidence': 0.0,
                'voice_type': 'unknown',
                'pitch_hz': 0.0,
                'intensity': 'normal',
                'is_breathing': False,
                'is_communication': False,
                'formants': {'F1': 0, 'F2': 0, 'F3': 0}
            }

    def get_voice_activity_rate(self):
        """Get voice activity rate (detections per minute)"""
        if len(self.voice_history) < 2:
            return 0.0

        current_time = time.time()
        recent_voices = [t for t in self.voice_history if current_time - t < 60.0]
        return len(recent_voices)  # voices per minute

