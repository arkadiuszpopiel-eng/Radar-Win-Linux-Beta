"""
RadarSuite v4.2.0 - Main ML Detector
Unified interface for ML-based audio event detection

Combines:
- FeatureExtractor: Audio → Mel-spectrogram
- YAMNetDetector: Mel-spectrogram → Event predictions

Provides:
- Fallback to rule-based detection if ML unavailable
- Confidence scores for each detection
- Thread-safe operation
"""

import numpy as np
import threading
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass

try:
    from ..core.logger import log
    from ..core.profiler import profile, measure
except ImportError:
    from core.logger import log
    # Fallback if profiler not available
    def profile(name=None):
        def decorator(func):
            return func
        return decorator
    def measure(name):
        class DummyContext:
            def __enter__(self): return self
            def __exit__(self, *args): pass
        return DummyContext()

from .feature_extractor import FeatureExtractor
from .yamnet import YAMNetDetector


@dataclass
class MLDetectionResult:
    """
    Result of ML detection.

    Attributes:
        events: Dictionary of detected events {type: detected}
        scores: Confidence scores for each event type
        ml_enabled: Whether ML model was used (vs fallback)
        latency_ms: Inference time in milliseconds
    """
    events: Dict[str, bool]
    scores: Dict[str, float]
    ml_enabled: bool
    latency_ms: float

    def __bool__(self) -> bool:
        """True if any event was detected."""
        return any(self.events.values())

    @property
    def has_shot(self) -> bool:
        return self.events.get("shot", False)

    @property
    def has_walk(self) -> bool:
        return self.events.get("walk", False)

    @property
    def has_run(self) -> bool:
        return self.events.get("run", False)

    @property
    def shot_confidence(self) -> float:
        return self.scores.get("shot", 0.0)

    @property
    def walk_confidence(self) -> float:
        return self.scores.get("walk", 0.0)

    @property
    def run_confidence(self) -> float:
        return self.scores.get("run", 0.0)


class MLDetector:
    """
    Main ML-based audio event detector.

    Provides a unified interface for ML detection with:
    - Automatic feature extraction
    - YAMNet inference (TFLite) or heuristic fallback
    - Thread-safe operation
    - Performance profiling

    Usage:
        detector = MLDetector()
        result = detector.detect(audio_block, sample_rate=48000)

        if result.has_shot:
            print(f"Shot detected with {result.shot_confidence:.0%} confidence")
    """

    def __init__(
        self,
        sample_rate: int = 48000,
        model_path: Optional[str] = None,
        enable_profiling: bool = True
    ):
        """
        Initialize ML Detector.

        Args:
            sample_rate: Audio sample rate (default 48000 Hz)
            model_path: Optional path to YAMNet TFLite model
            enable_profiling: Enable performance profiling
        """
        self.sample_rate = sample_rate
        self._enable_profiling = enable_profiling

        # Initialize components
        self._feature_extractor = FeatureExtractor(sample_rate)
        self._yamnet = YAMNetDetector(model_path)

        # FIXED v4.2.1: Cache FeatureExtractors per sample_rate to prevent memory leak
        self._extractor_cache: Dict[int, FeatureExtractor] = {sample_rate: self._feature_extractor}

        # Thread safety
        self._lock = threading.Lock()

        # Statistics
        self._inference_count = 0
        self._total_latency_ms = 0.0

        log(
            f"MLDetector initialized (sample_rate={sample_rate}, "
            f"ml_enabled={self._yamnet.is_ml_enabled})",
            "INFO"
        )

    @profile("ml_detection")
    def detect(self, audio: np.ndarray, sample_rate: Optional[int] = None) -> MLDetectionResult:
        """
        Detect audio events in audio block.

        Args:
            audio: Raw audio data (samples,) or (samples, channels)
            sample_rate: Optional override for sample rate

        Returns:
            MLDetectionResult with events, scores, and metadata
        """
        import time
        start_time = time.perf_counter()

        try:
            # FIXED v4.2.1: Use cached FeatureExtractor to prevent memory leak
            if sample_rate and sample_rate != self._feature_extractor.source_sr:
                if sample_rate not in self._extractor_cache:
                    self._extractor_cache[sample_rate] = FeatureExtractor(sample_rate)
                self._feature_extractor = self._extractor_cache[sample_rate]

            # Extract features
            with measure("ml_feature_extraction"):
                features = self._feature_extractor.extract_with_context(audio)

            # Run inference
            with measure("ml_inference"):
                events, scores = self._yamnet.detect_with_scores(features)

            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Update statistics
            self._inference_count += 1
            self._total_latency_ms += latency_ms

            return MLDetectionResult(
                events=events,
                scores=scores,
                ml_enabled=self._yamnet.is_ml_enabled,
                latency_ms=latency_ms
            )

        except Exception as e:
            log(f"ML detection error: {e}", "ERROR")
            return self._get_error_result()

    def detect_batch(self, audio_blocks: list, sample_rate: int = 48000) -> list:
        """
        Detect events in multiple audio blocks.

        Args:
            audio_blocks: List of audio arrays
            sample_rate: Sample rate for all blocks

        Returns:
            List of MLDetectionResult
        """
        results = []
        for block in audio_blocks:
            results.append(self.detect(block, sample_rate))
        return results

    def get_scores(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Get raw confidence scores without thresholding.

        Args:
            audio: Raw audio data

        Returns:
            Dictionary of confidence scores per event type
        """
        features = self._feature_extractor.extract_with_context(audio)
        return self._yamnet.predict(features)

    def _get_error_result(self) -> MLDetectionResult:
        """Return error/default result."""
        return MLDetectionResult(
            events={"shot": False, "walk": False, "run": False, "machine": False},
            scores={"shot": 0.0, "walk": 0.0, "run": 0.0, "machine": 0.0},
            ml_enabled=False,
            latency_ms=0.0
        )

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    def set_thresholds(
        self,
        shot: Optional[float] = None,
        walk: Optional[float] = None,
        run: Optional[float] = None,
        machine: Optional[float] = None
    ) -> None:
        """
        Adjust detection thresholds.

        Args:
            shot: Shot detection threshold (0.0-1.0)
            walk: Walk detection threshold (0.0-1.0)
            run: Run detection threshold (0.0-1.0)
            machine: Machine detection threshold (0.0-1.0)
        """
        if shot is not None:
            self._yamnet.SHOT_THRESHOLD = max(0.0, min(1.0, shot))
        if walk is not None:
            self._yamnet.WALK_THRESHOLD = max(0.0, min(1.0, walk))
        if run is not None:
            self._yamnet.RUN_THRESHOLD = max(0.0, min(1.0, run))
        if machine is not None:
            self._yamnet.MACHINE_THRESHOLD = max(0.0, min(1.0, machine))

        log(f"ML thresholds updated: shot={self._yamnet.SHOT_THRESHOLD}, "
            f"walk={self._yamnet.WALK_THRESHOLD}, run={self._yamnet.RUN_THRESHOLD}", "INFO")

    def get_thresholds(self) -> Dict[str, float]:
        """Get current detection thresholds."""
        return {
            "shot": self._yamnet.SHOT_THRESHOLD,
            "walk": self._yamnet.WALK_THRESHOLD,
            "run": self._yamnet.RUN_THRESHOLD,
            "machine": self._yamnet.MACHINE_THRESHOLD,
        }

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get detector statistics.

        Returns:
            Dictionary with performance stats
        """
        avg_latency = (
            self._total_latency_ms / self._inference_count
            if self._inference_count > 0 else 0.0
        )

        return {
            "ml_enabled": self._yamnet.is_ml_enabled,
            "inference_count": self._inference_count,
            "avg_latency_ms": avg_latency,
            "total_latency_ms": self._total_latency_ms,
            "sample_rate": self.sample_rate,
            "thresholds": self.get_thresholds(),
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._inference_count = 0
        self._total_latency_ms = 0.0

    @property
    def is_ml_enabled(self) -> bool:
        """Check if real ML model is active."""
        return self._yamnet.is_ml_enabled

    # ========================================================================
    # MODEL MANAGEMENT
    # ========================================================================

    def load_model(self, model_path: str) -> bool:
        """
        Load a TFLite model.

        Args:
            model_path: Path to .tflite file

        Returns:
            True if model loaded successfully
        """
        try:
            self._yamnet = YAMNetDetector(model_path)
            return self._yamnet.is_ml_enabled
        except Exception as e:
            log(f"Failed to load model: {e}", "ERROR")
            return False


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_ml_detector: Optional[MLDetector] = None
_detector_lock = threading.Lock()


def get_ml_detector(
    sample_rate: int = 48000,
    model_path: Optional[str] = None
) -> MLDetector:
    """
    Get or create global MLDetector instance.

    Thread-safe singleton access.

    Args:
        sample_rate: Audio sample rate
        model_path: Optional model path (only used on first call)

    Returns:
        MLDetector instance
    """
    global _ml_detector

    with _detector_lock:
        if _ml_detector is None:
            _ml_detector = MLDetector(sample_rate, model_path)
        return _ml_detector


def detect_audio_events(
    audio: np.ndarray,
    sample_rate: int = 48000
) -> MLDetectionResult:
    """
    Convenience function for one-shot detection.

    Args:
        audio: Raw audio data
        sample_rate: Sample rate

    Returns:
        MLDetectionResult
    """
    detector = get_ml_detector(sample_rate)
    return detector.detect(audio, sample_rate)
