"""
RadarSuite v4.2.0 - YAMNet Audio Classifier Wrapper
Pre-trained model for audio event classification

YAMNet: Yet Another Mobile Network for audio classification
- Trained on AudioSet (632 classes)
- Lightweight (~3.7M params)
- Real-time capable on CPU

Relevant classes for RadarSuite:
- Gunshot, gunfire (IDs: 427-432)
- Footsteps (ID: 440)
- Walk, footsteps (ID: 441)
- Run (ID: 442)
- Explosion (IDs: 426, 433)
- Silence (ID: 0)
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import threading

try:
    from ..core.logger import log
except ImportError:
    from core.logger import log


# ============================================================================
# YAMNET CLASS MAPPING (AudioSet ontology)
# ============================================================================

# Map YAMNet class IDs to RadarSuite detection categories
YAMNET_CLASS_MAP = {
    # Gunshots / Weapons
    427: ("shot", "Gunshot, gunfire"),
    428: ("shot", "Machine gun"),
    429: ("shot", "Fusillade"),
    430: ("shot", "Artillery fire"),
    431: ("shot", "Cap gun"),
    432: ("shot", "Fireworks"),
    426: ("shot", "Explosion"),
    433: ("shot", "Boom"),

    # Footsteps / Movement
    440: ("walk", "Footsteps"),
    441: ("walk", "Walk, footsteps"),
    442: ("run", "Run"),
    443: ("walk", "Shuffle"),

    # Vehicle / Machine sounds (for machine detector)
    300: ("machine", "Vehicle"),
    307: ("machine", "Engine"),
    308: ("machine", "Motor"),
    340: ("machine", "Helicopter"),

    # Human sounds (potential false positives to filter)
    0: ("silence", "Speech"),
    1: ("voice", "Male speech"),
    2: ("voice", "Female speech"),
    16: ("silence", "Silence"),

    # Environmental (ignore)
    288: ("ambient", "Wind"),
    289: ("ambient", "Rain"),
}

# Reverse mapping for quick lookup
CATEGORY_CLASSES = {
    "shot": [427, 428, 429, 430, 431, 426, 433],
    "walk": [440, 441, 443],
    "run": [442],
    "machine": [300, 307, 308, 340],
    "voice": [0, 1, 2],
    "silence": [16],
}


class YAMNetDetector:
    """
    YAMNet-based audio event detector.

    Uses TensorFlow Lite for inference if available,
    otherwise falls back to simplified heuristic model.
    """

    # Detection thresholds
    SHOT_THRESHOLD = 0.3      # Minimum confidence for shot detection
    WALK_THRESHOLD = 0.25     # Minimum confidence for walk detection
    RUN_THRESHOLD = 0.3       # Minimum confidence for run detection
    MACHINE_THRESHOLD = 0.4   # Minimum confidence for machine detection

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize YAMNet detector.

        Args:
            model_path: Path to YAMNet TFLite model (optional)
        """
        self._interpreter = None
        self._input_details = None
        self._output_details = None
        self._lock = threading.Lock()
        self._use_tflite = False
        self._model_loaded = False

        # Try to load TFLite model
        if model_path:
            self._load_tflite_model(model_path)
        else:
            self._try_load_default_model()

        if self._use_tflite:
            log("YAMNetDetector initialized with TFLite model", "INFO")
        else:
            log("YAMNetDetector initialized with heuristic fallback (no TFLite)", "WARNING")

    def _try_load_default_model(self) -> None:
        """Try to load YAMNet model from default locations."""
        default_paths = [
            Path(__file__).parent / "models" / "yamnet.tflite",
            Path(__file__).parent / "yamnet.tflite",
            Path.home() / ".radarsuite" / "models" / "yamnet.tflite",
        ]

        for path in default_paths:
            if path.exists():
                self._load_tflite_model(str(path))
                if self._use_tflite:
                    return

    def _load_tflite_model(self, model_path: str) -> None:
        """
        Load TensorFlow Lite model.

        Args:
            model_path: Path to .tflite file
        """
        try:
            import tflite_runtime.interpreter as tflite
            self._interpreter = tflite.Interpreter(model_path=model_path)
            self._interpreter.allocate_tensors()
            self._input_details = self._interpreter.get_input_details()
            self._output_details = self._interpreter.get_output_details()
            self._use_tflite = True
            self._model_loaded = True
            log(f"TFLite model loaded: {model_path}", "INFO")

        except ImportError:
            try:
                # Try full TensorFlow
                import tensorflow as tf
                self._interpreter = tf.lite.Interpreter(model_path=model_path)
                self._interpreter.allocate_tensors()
                self._input_details = self._interpreter.get_input_details()
                self._output_details = self._interpreter.get_output_details()
                self._use_tflite = True
                self._model_loaded = True
                log(f"TensorFlow Lite model loaded: {model_path}", "INFO")

            except Exception as e:
                log(f"Could not load TFLite model: {e}", "WARNING")
                self._use_tflite = False

        except Exception as e:
            log(f"Error loading model {model_path}: {e}", "ERROR")
            self._use_tflite = False

    def predict(self, features: np.ndarray) -> Dict[str, float]:
        """
        Run inference on mel-spectrogram features.

        Args:
            features: Log-mel spectrogram (frames, n_mels)

        Returns:
            Dictionary of detection scores {category: confidence}
        """
        if self._use_tflite:
            return self._predict_tflite(features)
        else:
            return self._predict_heuristic(features)

    def _predict_tflite(self, features: np.ndarray) -> Dict[str, float]:
        """
        Run TFLite inference.

        Args:
            features: Input features

        Returns:
            Detection scores per category
        """
        try:
            with self._lock:
                # Prepare input (add batch dimension if needed)
                if features.ndim == 2:
                    features = np.expand_dims(features, axis=0)

                # Ensure float32
                features = features.astype(np.float32)

                # Set input tensor
                self._interpreter.set_tensor(
                    self._input_details[0]['index'],
                    features
                )

                # Run inference
                self._interpreter.invoke()

                # Get output (class probabilities)
                output = self._interpreter.get_tensor(
                    self._output_details[0]['index']
                )

                # Aggregate to categories
                return self._aggregate_to_categories(output[0])

        except Exception as e:
            log(f"TFLite inference error: {e}", "ERROR")
            return self._get_default_scores()

    def _predict_heuristic(self, features: np.ndarray) -> Dict[str, float]:
        """
        Heuristic-based prediction when TFLite is not available.

        Uses spectral characteristics to estimate detection categories.

        Args:
            features: Log-mel spectrogram (frames, n_mels)

        Returns:
            Detection scores per category
        """
        try:
            # Compute mean energy per mel band
            mean_energy = np.mean(features, axis=0)

            # Total energy
            total_energy = np.sum(mean_energy)

            if total_energy < 0.01:
                return {"silence": 0.9, "shot": 0.0, "walk": 0.0, "run": 0.0, "machine": 0.0}

            # Spectral characteristics
            # Low bands (0-16): bass, footsteps
            low_energy = np.mean(mean_energy[:16])

            # Mid bands (16-40): voice, some footsteps
            mid_energy = np.mean(mean_energy[16:40])

            # High bands (40-64): shots, transients
            high_energy = np.mean(mean_energy[40:])

            # Temporal variation (transient detection)
            temporal_std = np.std(features, axis=0).mean()

            # Compute scores based on spectral profile
            scores = {}

            # Shot detection: high energy in upper bands + high temporal variation
            shot_score = (high_energy * 0.6 + temporal_std * 0.4) * 2
            scores["shot"] = min(1.0, max(0.0, shot_score))

            # Walk detection: rhythmic low-mid energy
            walk_score = low_energy * 0.7 + mid_energy * 0.3
            scores["walk"] = min(1.0, max(0.0, walk_score * 1.5))

            # Run detection: faster rhythm, higher energy
            run_score = scores["walk"] * (1 + temporal_std)
            scores["run"] = min(1.0, max(0.0, run_score - 0.2))

            # Machine detection: sustained low frequency
            machine_score = low_energy * 0.8 - temporal_std * 0.5
            scores["machine"] = min(1.0, max(0.0, machine_score))

            # Silence detection
            scores["silence"] = max(0.0, 1.0 - total_energy * 5)

            return scores

        except Exception as e:
            log(f"Heuristic prediction error: {e}", "ERROR")
            return self._get_default_scores()

    def _aggregate_to_categories(self, class_probs: np.ndarray) -> Dict[str, float]:
        """
        Aggregate YAMNet class probabilities to RadarSuite categories.

        Args:
            class_probs: Array of 521 class probabilities

        Returns:
            Category scores
        """
        scores = {}

        for category, class_ids in CATEGORY_CLASSES.items():
            # Take max probability from all classes in category
            category_probs = [class_probs[i] for i in class_ids if i < len(class_probs)]
            if category_probs:
                scores[category] = float(max(category_probs))
            else:
                scores[category] = 0.0

        return scores

    def _get_default_scores(self) -> Dict[str, float]:
        """Return default (no detection) scores."""
        return {
            "shot": 0.0,
            "walk": 0.0,
            "run": 0.0,
            "machine": 0.0,
            "silence": 0.5,
        }

    def detect(self, features: np.ndarray) -> Dict[str, bool]:
        """
        Run detection with thresholds.

        Args:
            features: Log-mel spectrogram

        Returns:
            Dictionary of boolean detections
        """
        scores = self.predict(features)

        return {
            "shot": scores.get("shot", 0) >= self.SHOT_THRESHOLD,
            "walk": scores.get("walk", 0) >= self.WALK_THRESHOLD,
            "run": scores.get("run", 0) >= self.RUN_THRESHOLD,
            "machine": scores.get("machine", 0) >= self.MACHINE_THRESHOLD,
        }

    def detect_with_scores(self, features: np.ndarray) -> Tuple[Dict[str, bool], Dict[str, float]]:
        """
        Run detection and return both boolean results and confidence scores.

        Args:
            features: Log-mel spectrogram

        Returns:
            Tuple of (detections, scores)
        """
        scores = self.predict(features)

        detections = {
            "shot": scores.get("shot", 0) >= self.SHOT_THRESHOLD,
            "walk": scores.get("walk", 0) >= self.WALK_THRESHOLD,
            "run": scores.get("run", 0) >= self.RUN_THRESHOLD,
            "machine": scores.get("machine", 0) >= self.MACHINE_THRESHOLD,
        }

        return detections, scores

    @property
    def is_ml_enabled(self) -> bool:
        """Check if real ML model is loaded."""
        return self._use_tflite and self._model_loaded

    def get_model_info(self) -> Dict[str, any]:
        """Get information about loaded model."""
        return {
            "tflite_enabled": self._use_tflite,
            "model_loaded": self._model_loaded,
            "thresholds": {
                "shot": self.SHOT_THRESHOLD,
                "walk": self.WALK_THRESHOLD,
                "run": self.RUN_THRESHOLD,
                "machine": self.MACHINE_THRESHOLD,
            }
        }
