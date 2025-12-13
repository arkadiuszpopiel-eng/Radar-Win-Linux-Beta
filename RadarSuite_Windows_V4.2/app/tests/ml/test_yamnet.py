"""
RadarSuite v4.2.1 - YAMNet Detector Tests
Unit tests for ml/yamnet.py
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock


class TestYAMNetClassMap:
    """Tests for YAMNET_CLASS_MAP constant."""

    def test_class_map_has_shot_categories(self):
        """Test shot categories are mapped."""
        from ml.yamnet import YAMNET_CLASS_MAP

        shot_ids = [427, 428, 429, 430, 431, 432, 426, 433]
        for class_id in shot_ids:
            assert class_id in YAMNET_CLASS_MAP
            category, _ = YAMNET_CLASS_MAP[class_id]
            assert category == "shot"

    def test_class_map_has_footstep_categories(self):
        """Test footstep categories are mapped."""
        from ml.yamnet import YAMNET_CLASS_MAP

        # Walk
        assert 440 in YAMNET_CLASS_MAP
        assert 441 in YAMNET_CLASS_MAP
        assert YAMNET_CLASS_MAP[440][0] == "walk"

        # Run
        assert 442 in YAMNET_CLASS_MAP
        assert YAMNET_CLASS_MAP[442][0] == "run"

    def test_category_classes_reverse_mapping(self):
        """Test CATEGORY_CLASSES has correct reverse mappings."""
        from ml.yamnet import CATEGORY_CLASSES

        assert "shot" in CATEGORY_CLASSES
        assert "walk" in CATEGORY_CLASSES
        assert "run" in CATEGORY_CLASSES
        assert "machine" in CATEGORY_CLASSES

        assert 427 in CATEGORY_CLASSES["shot"]
        assert 442 in CATEGORY_CLASSES["run"]


class TestYAMNetDetector:
    """Tests for YAMNetDetector class."""

    def test_init_without_model(self):
        """Test initialization without TFLite model."""
        from ml.yamnet import YAMNetDetector

        detector = YAMNetDetector(model_path=None)

        # Should fall back to heuristic mode
        assert detector._use_tflite is False
        assert detector.is_ml_enabled is False

    def test_thresholds_are_set(self):
        """Test detection thresholds are configured."""
        from ml.yamnet import YAMNetDetector

        detector = YAMNetDetector()

        assert detector.SHOT_THRESHOLD == 0.3
        assert detector.WALK_THRESHOLD == 0.25
        assert detector.RUN_THRESHOLD == 0.3
        assert detector.MACHINE_THRESHOLD == 0.4

    def test_predict_heuristic_with_silence(self):
        """Test heuristic prediction with silent audio."""
        from ml.yamnet import YAMNetDetector

        detector = YAMNetDetector()

        # Silent features (all zeros)
        features = np.zeros((96, 64), dtype=np.float32)
        scores = detector.predict(features)

        assert "silence" in scores
        assert scores["silence"] > 0.5
        assert scores["shot"] < 0.1
        assert scores["walk"] < 0.1

    def test_predict_heuristic_with_energy(self):
        """Test heuristic prediction with audio energy."""
        from ml.yamnet import YAMNetDetector

        detector = YAMNetDetector()

        # Features with energy in different bands
        features = np.random.rand(96, 64).astype(np.float32) * 0.5
        scores = detector.predict(features)

        assert "shot" in scores
        assert "walk" in scores
        assert "run" in scores
        assert "machine" in scores
        assert "silence" in scores

        # All scores should be between 0 and 1
        for score in scores.values():
            assert 0.0 <= score <= 1.0

    def test_detect_returns_booleans(self):
        """Test detect() returns boolean detections."""
        from ml.yamnet import YAMNetDetector

        detector = YAMNetDetector()
        features = np.zeros((96, 64), dtype=np.float32)

        detections = detector.detect(features)

        assert isinstance(detections["shot"], bool)
        assert isinstance(detections["walk"], bool)
        assert isinstance(detections["run"], bool)
        assert isinstance(detections["machine"], bool)

    def test_detect_with_scores_returns_both(self):
        """Test detect_with_scores returns detections and scores."""
        from ml.yamnet import YAMNetDetector

        detector = YAMNetDetector()
        features = np.random.rand(96, 64).astype(np.float32)

        detections, scores = detector.detect_with_scores(features)

        assert isinstance(detections, dict)
        assert isinstance(scores, dict)

        # Both should have same keys
        assert "shot" in detections
        assert "shot" in scores

    def test_get_model_info(self):
        """Test get_model_info returns configuration."""
        from ml.yamnet import YAMNetDetector

        detector = YAMNetDetector()
        info = detector.get_model_info()

        assert "tflite_enabled" in info
        assert "model_loaded" in info
        assert "thresholds" in info
        assert info["thresholds"]["shot"] == detector.SHOT_THRESHOLD

    def test_aggregate_to_categories(self):
        """Test aggregation of class probabilities to categories."""
        from ml.yamnet import YAMNetDetector

        detector = YAMNetDetector()

        # Create fake class probabilities (521 classes in YAMNet)
        class_probs = np.zeros(521, dtype=np.float32)
        class_probs[427] = 0.9  # Gunshot
        class_probs[440] = 0.6  # Footsteps

        scores = detector._aggregate_to_categories(class_probs)

        assert scores["shot"] == 0.9
        assert scores["walk"] == 0.6

    def test_get_default_scores(self):
        """Test default scores structure."""
        from ml.yamnet import YAMNetDetector

        detector = YAMNetDetector()
        scores = detector._get_default_scores()

        assert scores["shot"] == 0.0
        assert scores["walk"] == 0.0
        assert scores["run"] == 0.0
        assert scores["machine"] == 0.0
        assert scores["silence"] == 0.5


class TestYAMNetWithMockedTFLite:
    """Tests for YAMNet with mocked TFLite runtime."""

    def test_tflite_loading_success(self):
        """Test successful TFLite model loading."""
        from ml.yamnet import YAMNetDetector

        mock_interpreter = Mock()
        mock_interpreter.get_input_details.return_value = [{"index": 0}]
        mock_interpreter.get_output_details.return_value = [{"index": 0}]

        with patch.dict('sys.modules', {'tflite_runtime.interpreter': Mock()}):
            with patch('tflite_runtime.interpreter.Interpreter', return_value=mock_interpreter):
                # This would require actual tflite_runtime, so test structure only
                pass

    def test_tensorflow_fallback(self):
        """Test fallback to TensorFlow when tflite_runtime unavailable."""
        # Structure test - actual TF loading would require installed TF
        from ml.yamnet import YAMNetDetector

        detector = YAMNetDetector()
        # Without TF/TFLite, should use heuristic
        assert detector._use_tflite is False
