"""
RadarSuite v4.2.0 - Spectral Features Module
Advanced spectral analysis for ARC Raiders detection

FIXED v4.2.0: Implements MFCC and spectral features for:
- Surface type classification (metal/dirt/snow)
- Shot type classification (close/distant)
- Machine state detection
- Equipment/backpack detection
"""

import numpy as np
from scipy.signal import get_window
from scipy.fftpack import dct
from core import (
    SAMPLE_RATE, MFCC_NUM_COEFFS, MEL_NUM_BANDS,
    MEL_FREQ_MIN_HZ, MEL_FREQ_MAX_HZ, log
)


class SpectralFeatureExtractor:
    """
    Extract spectral features for audio classification

    FIXED v4.2.0: Designed for ARC Raiders audio characteristics:
    - MFCC (Mel-Frequency Cepstral Coefficients)
    - Spectral centroid, roll-off, flatness
    - Energy ratios in different bands
    """

    def __init__(self, sample_rate=SAMPLE_RATE, n_fft=2048):
        """
        Initialize spectral feature extractor

        Args:
            sample_rate: Audio sample rate (default: 48 kHz for ARC Raiders)
            n_fft: FFT size for spectral analysis
        """
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = n_fft // 2

        # Build mel filterbank
        self.mel_filterbank = self._build_mel_filterbank(
            n_fft, sample_rate, MEL_NUM_BANDS,
            MEL_FREQ_MIN_HZ, MEL_FREQ_MAX_HZ
        )

        log(f"SpectralFeatureExtractor initialized: {sample_rate} Hz, {n_fft} FFT", "INFO")

    def _hz_to_mel(self, freq_hz):
        """Convert frequency in Hz to mel scale"""
        return 2595.0 * np.log10(1.0 + freq_hz / 700.0)

    def _mel_to_hz(self, mel):
        """Convert mel scale to frequency in Hz"""
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    def _build_mel_filterbank(self, n_fft, sample_rate, n_mels, f_min, f_max):
        """
        Build mel filterbank for MFCC extraction

        Args:
            n_fft: FFT size
            sample_rate: Sample rate in Hz
            n_mels: Number of mel bands
            f_min: Minimum frequency in Hz
            f_max: Maximum frequency in Hz

        Returns:
            Mel filterbank matrix (n_mels, n_fft//2 + 1)
        """
        # Convert to mel scale
        mel_min = self._hz_to_mel(f_min)
        mel_max = self._hz_to_mel(f_max)

        # Create evenly spaced mel points
        mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
        hz_points = self._mel_to_hz(mel_points)

        # Convert to FFT bin numbers
        bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

        # Create filterbank
        n_bins = n_fft // 2 + 1
        filterbank = np.zeros((n_mels, n_bins))

        for m in range(1, n_mels + 1):
            f_left = bin_points[m - 1]
            f_center = bin_points[m]
            f_right = bin_points[m + 1]

            # Rising slope
            for k in range(f_left, f_center):
                if f_center != f_left:
                    filterbank[m - 1, k] = (k - f_left) / (f_center - f_left)

            # Falling slope
            for k in range(f_center, f_right):
                if f_right != f_center:
                    filterbank[m - 1, k] = (f_right - k) / (f_right - f_center)

        return filterbank

    def extract_mfcc(self, audio_block, num_coeffs=MFCC_NUM_COEFFS):
        """
        Extract MFCC features from audio block

        Args:
            audio_block: Audio data (mono, numpy array)
            num_coeffs: Number of MFCC coefficients to extract

        Returns:
            MFCC coefficients (num_coeffs,) or None if invalid
        """
        if audio_block is None or len(audio_block) < self.n_fft:
            return None

        try:
            # Ensure mono
            if len(audio_block.shape) > 1:
                audio_block = np.mean(audio_block, axis=1)

            # Apply window
            windowed = audio_block[:self.n_fft] * get_window('hamming', self.n_fft)

            # FFT
            spectrum = np.fft.rfft(windowed, n=self.n_fft)
            power_spectrum = np.abs(spectrum) ** 2

            # Apply mel filterbank
            mel_energies = np.dot(self.mel_filterbank, power_spectrum)

            # Log mel energies (avoid log(0))
            mel_energies = np.where(mel_energies == 0, np.finfo(float).eps, mel_energies)
            log_mel_energies = np.log(mel_energies)

            # DCT to get MFCC
            mfcc = dct(log_mel_energies, type=2, axis=0, norm='ortho')

            return mfcc[:num_coeffs]

        except Exception as e:
            log(f"Error extracting MFCC: {e}", "ERROR")
            return None

    def extract_spectral_centroid(self, audio_block):
        """
        Extract spectral centroid (center of mass of spectrum)

        Higher for bright sounds (metal), lower for dull sounds (dirt)

        Args:
            audio_block: Audio data (mono, numpy array)

        Returns:
            Spectral centroid in Hz, or 0 if invalid
        """
        if audio_block is None or len(audio_block) < self.n_fft:
            return 0

        try:
            # Ensure mono
            if len(audio_block.shape) > 1:
                audio_block = np.mean(audio_block, axis=1)

            # FFT
            spectrum = np.fft.rfft(audio_block[:self.n_fft], n=self.n_fft)
            magnitude = np.abs(spectrum)

            # Frequency bins
            freqs = np.fft.rfftfreq(self.n_fft, 1.0 / self.sample_rate)

            # Weighted mean
            if np.sum(magnitude) > 0:
                centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
                return centroid
            else:
                return 0

        except Exception as e:
            log(f"Error extracting spectral centroid: {e}", "ERROR")
            return 0

    def extract_spectral_rolloff(self, audio_block, rolloff_percent=0.85):
        """
        Extract spectral roll-off (frequency below which X% of energy lies)

        Args:
            audio_block: Audio data (mono, numpy array)
            rolloff_percent: Percentage threshold (default 0.85 = 85%)

        Returns:
            Spectral roll-off frequency in Hz, or 0 if invalid
        """
        if audio_block is None or len(audio_block) < self.n_fft:
            return 0

        try:
            # Ensure mono
            if len(audio_block.shape) > 1:
                audio_block = np.mean(audio_block, axis=1)

            # FFT
            spectrum = np.fft.rfft(audio_block[:self.n_fft], n=self.n_fft)
            magnitude = np.abs(spectrum)

            # Frequency bins
            freqs = np.fft.rfftfreq(self.n_fft, 1.0 / self.sample_rate)

            # Cumulative sum
            cumsum = np.cumsum(magnitude)
            threshold = rolloff_percent * cumsum[-1]

            # Find rolloff frequency
            rolloff_idx = np.where(cumsum >= threshold)[0]
            if len(rolloff_idx) > 0:
                return freqs[rolloff_idx[0]]
            else:
                return freqs[-1]

        except Exception as e:
            log(f"Error extracting spectral rolloff: {e}", "ERROR")
            return 0

    def extract_spectral_flatness(self, audio_block):
        """
        Extract spectral flatness (measure of noisiness)

        High flatness = noise-like (equipment rustle)
        Low flatness = tonal (footsteps, shots)

        Args:
            audio_block: Audio data (mono, numpy array)

        Returns:
            Spectral flatness (0-1), or 0 if invalid
        """
        if audio_block is None or len(audio_block) < self.n_fft:
            return 0

        try:
            # Ensure mono
            if len(audio_block.shape) > 1:
                audio_block = np.mean(audio_block, axis=1)

            # FFT
            spectrum = np.fft.rfft(audio_block[:self.n_fft], n=self.n_fft)
            magnitude = np.abs(spectrum)

            # Avoid log(0)
            magnitude = np.where(magnitude == 0, np.finfo(float).eps, magnitude)

            # Geometric mean / arithmetic mean
            geometric_mean = np.exp(np.mean(np.log(magnitude)))
            arithmetic_mean = np.mean(magnitude)

            if arithmetic_mean > 0:
                flatness = geometric_mean / arithmetic_mean
                return flatness
            else:
                return 0

        except Exception as e:
            log(f"Error extracting spectral flatness: {e}", "ERROR")
            return 0

    def extract_band_energy_ratio(self, audio_block, freq_min, freq_max):
        """
        Extract energy ratio in a specific frequency band

        Useful for:
        - Bass ratio for explosions vs shots
        - Mid-range for footsteps
        - High-range for metal vs dirt

        Args:
            audio_block: Audio data (mono, numpy array)
            freq_min: Minimum frequency in Hz
            freq_max: Maximum frequency in Hz

        Returns:
            Energy ratio (0-1) for the band, or 0 if invalid
        """
        if audio_block is None or len(audio_block) < self.n_fft:
            return 0

        try:
            # Ensure mono
            if len(audio_block.shape) > 1:
                audio_block = np.mean(audio_block, axis=1)

            # FFT
            spectrum = np.fft.rfft(audio_block[:self.n_fft], n=self.n_fft)
            power_spectrum = np.abs(spectrum) ** 2

            # Frequency bins
            freqs = np.fft.rfftfreq(self.n_fft, 1.0 / self.sample_rate)

            # Find bins in range
            band_mask = (freqs >= freq_min) & (freqs <= freq_max)

            # Energy ratio
            band_energy = np.sum(power_spectrum[band_mask])
            total_energy = np.sum(power_spectrum)

            if total_energy > 0:
                return band_energy / total_energy
            else:
                return 0

        except Exception as e:
            log(f"Error extracting band energy ratio: {e}", "ERROR")
            return 0

    def extract_all_features(self, audio_block):
        """
        Extract all spectral features at once

        Args:
            audio_block: Audio data (mono, numpy array)

        Returns:
            Dictionary with all features, or None if invalid
        """
        if audio_block is None or len(audio_block) < self.n_fft:
            return None

        try:
            features = {
                'mfcc': self.extract_mfcc(audio_block),
                'spectral_centroid': self.extract_spectral_centroid(audio_block),
                'spectral_rolloff': self.extract_spectral_rolloff(audio_block),
                'spectral_flatness': self.extract_spectral_flatness(audio_block),
                # Band energy ratios
                'bass_ratio': self.extract_band_energy_ratio(audio_block, 20, 200),
                'low_mid_ratio': self.extract_band_energy_ratio(audio_block, 200, 800),
                'mid_ratio': self.extract_band_energy_ratio(audio_block, 800, 2000),
                'high_mid_ratio': self.extract_band_energy_ratio(audio_block, 2000, 5000),
                'high_ratio': self.extract_band_energy_ratio(audio_block, 5000, 12000),
            }

            return features

        except Exception as e:
            log(f"Error extracting all features: {e}", "ERROR")
            return None
