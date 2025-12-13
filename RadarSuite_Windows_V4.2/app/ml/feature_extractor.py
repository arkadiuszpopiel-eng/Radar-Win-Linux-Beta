"""
RadarSuite v4.2.0 - Audio Feature Extractor for ML
Converts raw audio to mel-spectrograms for neural network input

YAMNet expects:
- 16kHz sample rate (we resample from 48kHz)
- Log-mel spectrogram with 64 mel bands
- Window: 25ms, Hop: 10ms
- 0.96s context (96 frames)
"""

import numpy as np
from typing import Optional, Tuple
from scipy import signal as sp_signal

try:
    from ..core.logger import log
except ImportError:
    from core.logger import log


class FeatureExtractor:
    """
    Extracts mel-spectrogram features from audio for ML inference.

    Optimized for YAMNet-compatible feature extraction.
    Thread-safe, can be used from detection workers.
    """

    # YAMNet parameters
    TARGET_SAMPLE_RATE = 16000  # YAMNet expects 16kHz
    N_MELS = 64                 # Number of mel bands
    N_FFT = 512                 # FFT window size (32ms at 16kHz)
    HOP_LENGTH = 160            # Hop length (10ms at 16kHz)
    WIN_LENGTH = 400            # Window length (25ms at 16kHz)
    FMIN = 125.0                # Minimum frequency for mel filterbank
    FMAX = 7500.0               # Maximum frequency for mel filterbank

    # Context for YAMNet (0.96s = 96 frames)
    CONTEXT_FRAMES = 96

    def __init__(self, source_sample_rate: int = 48000):
        """
        Initialize feature extractor.

        Args:
            source_sample_rate: Input audio sample rate (default 48kHz)
        """
        self.source_sr = source_sample_rate
        self._mel_filterbank: Optional[np.ndarray] = None
        self._init_mel_filterbank()

        log(f"FeatureExtractor initialized (source={source_sample_rate}Hz → target={self.TARGET_SAMPLE_RATE}Hz)", "INFO")

    def _init_mel_filterbank(self) -> None:
        """Pre-compute mel filterbank matrix for efficiency."""
        # Mel frequency points
        mel_min = self._hz_to_mel(self.FMIN)
        mel_max = self._hz_to_mel(self.FMAX)
        mel_points = np.linspace(mel_min, mel_max, self.N_MELS + 2)
        hz_points = self._mel_to_hz(mel_points)

        # FFT bin frequencies
        n_fft_bins = self.N_FFT // 2 + 1
        fft_freqs = np.linspace(0, self.TARGET_SAMPLE_RATE / 2, n_fft_bins)

        # Create filterbank
        self._mel_filterbank = np.zeros((self.N_MELS, n_fft_bins))

        for i in range(self.N_MELS):
            left = hz_points[i]
            center = hz_points[i + 1]
            right = hz_points[i + 2]

            # Rising slope
            left_slope = (fft_freqs - left) / (center - left + 1e-10)
            # Falling slope
            right_slope = (right - fft_freqs) / (right - center + 1e-10)

            self._mel_filterbank[i] = np.maximum(0, np.minimum(left_slope, right_slope))

    @staticmethod
    def _hz_to_mel(hz: float) -> float:
        """Convert Hz to mel scale."""
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    @staticmethod
    def _mel_to_hz(mel: float) -> float:
        """Convert mel scale to Hz."""
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    def _resample(self, audio: np.ndarray) -> np.ndarray:
        """
        Resample audio from source rate to 16kHz.

        Args:
            audio: Input audio array

        Returns:
            Resampled audio at 16kHz
        """
        if self.source_sr == self.TARGET_SAMPLE_RATE:
            return audio

        # Calculate resampling ratio
        ratio = self.TARGET_SAMPLE_RATE / self.source_sr
        new_length = int(len(audio) * ratio)

        # Use scipy resample for quality
        resampled = sp_signal.resample(audio, new_length)

        return resampled.astype(np.float32)

    def _to_mono(self, audio: np.ndarray) -> np.ndarray:
        """Convert stereo to mono by averaging channels."""
        if audio.ndim == 2:
            return np.mean(audio, axis=1).astype(np.float32)
        return audio.astype(np.float32)

    def extract(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract log-mel spectrogram features from audio.

        Args:
            audio: Raw audio data (samples,) or (samples, channels)

        Returns:
            Log-mel spectrogram (frames, n_mels) ready for ML model
        """
        try:
            # Convert to mono
            mono = self._to_mono(audio)

            # Normalize to [-1, 1]
            max_val = np.max(np.abs(mono))
            if max_val > 0:
                mono = mono / max_val

            # Resample to 16kHz
            resampled = self._resample(mono)

            # Compute STFT
            stft = self._compute_stft(resampled)

            # Convert to mel spectrogram
            mel_spec = self._stft_to_mel(stft)

            # Convert to log scale (dB)
            log_mel = self._to_log_mel(mel_spec)

            return log_mel

        except Exception as e:
            log(f"Feature extraction error: {e}", "ERROR")
            # Return empty features on error
            return np.zeros((1, self.N_MELS), dtype=np.float32)

    def _compute_stft(self, audio: np.ndarray) -> np.ndarray:
        """
        Compute Short-Time Fourier Transform.

        Args:
            audio: Mono audio at 16kHz

        Returns:
            STFT magnitude spectrogram (frames, n_fft_bins)
        """
        # Pad audio to ensure we get at least one frame
        pad_length = max(0, self.N_FFT - len(audio))
        if pad_length > 0:
            audio = np.pad(audio, (0, pad_length), mode='constant')

        # Number of frames
        n_frames = 1 + (len(audio) - self.N_FFT) // self.HOP_LENGTH

        if n_frames <= 0:
            n_frames = 1

        # Allocate output
        n_fft_bins = self.N_FFT // 2 + 1
        stft_mag = np.zeros((n_frames, n_fft_bins), dtype=np.float32)

        # Hann window
        window = np.hanning(self.WIN_LENGTH)

        # Pad window to N_FFT
        window_padded = np.zeros(self.N_FFT)
        window_padded[:self.WIN_LENGTH] = window

        for i in range(n_frames):
            start = i * self.HOP_LENGTH
            end = start + self.N_FFT

            if end > len(audio):
                # Pad last frame
                frame = np.zeros(self.N_FFT)
                frame[:len(audio) - start] = audio[start:]
            else:
                frame = audio[start:end]

            # Apply window and FFT
            windowed = frame * window_padded
            fft_result = np.fft.rfft(windowed)
            stft_mag[i] = np.abs(fft_result)

        return stft_mag

    def _stft_to_mel(self, stft: np.ndarray) -> np.ndarray:
        """
        Apply mel filterbank to STFT magnitude.

        Args:
            stft: STFT magnitude (frames, n_fft_bins)

        Returns:
            Mel spectrogram (frames, n_mels)
        """
        # Apply filterbank: (frames, n_fft_bins) @ (n_fft_bins, n_mels).T
        mel_spec = np.dot(stft, self._mel_filterbank.T)
        return mel_spec

    def _to_log_mel(self, mel_spec: np.ndarray) -> np.ndarray:
        """
        Convert mel spectrogram to log scale.

        Args:
            mel_spec: Mel spectrogram (frames, n_mels)

        Returns:
            Log-mel spectrogram in dB scale
        """
        # Add small epsilon to avoid log(0)
        log_mel = np.log(mel_spec + 1e-6)

        # Normalize to [0, 1] range (approximate)
        log_mel = (log_mel + 6) / 12  # Assuming range [-6, 6]
        log_mel = np.clip(log_mel, 0, 1)

        return log_mel.astype(np.float32)

    def extract_with_context(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract features with context padding for YAMNet.

        Ensures output has CONTEXT_FRAMES frames.

        Args:
            audio: Raw audio data

        Returns:
            Log-mel spectrogram (CONTEXT_FRAMES, n_mels)
        """
        features = self.extract(audio)

        n_frames = features.shape[0]

        if n_frames >= self.CONTEXT_FRAMES:
            # Take last CONTEXT_FRAMES
            return features[-self.CONTEXT_FRAMES:]
        else:
            # Pad with zeros at the beginning
            padded = np.zeros((self.CONTEXT_FRAMES, self.N_MELS), dtype=np.float32)
            padded[-n_frames:] = features
            return padded


# Singleton instance
_extractor: Optional[FeatureExtractor] = None


def extract_mel_spectrogram(
    audio: np.ndarray,
    sample_rate: int = 48000
) -> np.ndarray:
    """
    Convenience function to extract mel-spectrogram features.

    Args:
        audio: Raw audio data
        sample_rate: Source sample rate

    Returns:
        Log-mel spectrogram features
    """
    global _extractor

    if _extractor is None or _extractor.source_sr != sample_rate:
        _extractor = FeatureExtractor(sample_rate)

    return _extractor.extract_with_context(audio)
