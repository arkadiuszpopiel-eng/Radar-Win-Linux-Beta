"""
RadarSuite v4.2.1 - ML Detector Tests
Unit tests for ml/detector.py
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock


class TestMLDetectionResult:
    """Tests for MLDetectionResult dataclass."""

    def test_result_creation_defaults(self):
        """Test creating result with default values."""
        from ml.detector import MLDetectionResult
        result = MLDetectionResult()

        assert result.has_shot is False
        assert result.has_walk is False
        assert result.has_run is False
        assert result.shot_confidence == 0.0
        assert result.walk_confidence == 0.0
        assert result.run_confidence == 0.0
        assert result.latency_ms == 0.0
        assert isinstance(result.scores, dict)

    def test_result_with_detections(self):
        """Test result with actual detections."""
        from ml.detector import MLDetectionResult
        result = MLDetectionResult(
            has_shot=True,
            shot_confidence=85.5,
            has_walk=True,
            walk_confidence=72.3,
            latency_ms=15.2,
            scores={"shot": 0.855, "walk": 0.723}
        )

        assert result.has_shot is True
        assert result.shot_confidence == 85.5
        assert result.has_walk is True
        assert result.walk_confidence == 72.3
        assert result.latency_ms == 15.2


class TestMLDetector:
    """Tests for MLDetector class."""

    @pytest.fixture
    def mock_yamnet(self):
        """Create mock YAMNet detector."""
        with patch('ml.detector.YAMNetDetector') as mock:
            instance = mock.return_value
            instance.is_ml_enabled = False
            instance.detect_with_scores.return_value = (
                {"shot": False, "walk": False, "run": False},
                {"shot": 0.1, "walk": 0.2, "run": 0.1}
            )
            yield instance

    @pytest.fixture
    def mock_feature_extractor(self):
        """Create mock feature extractor."""
        with patch('ml.detector.FeatureExtractor') as mock:
            instance = mock.return_value
            instance.source_sr = 48000
            instance.extract_with_context.return_value = np.zeros((96, 64))
            yield instance

    def test_detector_initialization(self, mock_yamnet, mock_feature_extractor):
        """Test detector initializes correctly."""
        from ml.detector import MLDetector

        with patch('ml.detector.YAMNetDetector', return_value=mock_yamnet), \
             patch('ml.detector.FeatureExtractor', return_value=mock_feature_extractor):
            detector = MLDetector(sample_rate=48000)

            assert detector.sample_rate == 48000
            assert detector._inference_count == 0
            assert detector._total_latency_ms == 0.0

    def test_detect_returns_result(self, mock_yamnet, mock_feature_extractor):
        """Test detect() returns MLDetectionResult."""
        from ml.detector import MLDetector, MLDetectionResult

        with patch('ml.detector.YAMNetDetector', return_value=mock_yamnet), \
             patch('ml.detector.FeatureExtractor', return_value=mock_feature_extractor):
            detector = MLDetector(sample_rate=48000)

            # Create test audio (1 second of silence)
            audio = np.zeros((48000, 2), dtype=np.float32)
            result = detector.detect(audio)

            assert isinstance(result, MLDetectionResult)

    def test_extractor_cache_prevents_leak(self, mock_yamnet):
        """Test that FeatureExtractor cache prevents memory leaks (FIXED v4.2.1)."""
        from ml.detector import MLDetector

        with patch('ml.detector.YAMNetDetector', return_value=mock_yamnet):
            detector = MLDetector(sample_rate=48000)

            # Cache should start with one entry
            assert 48000 in detector._extractor_cache

            # Detect with different sample rate
            audio = np.zeros((44100, 2), dtype=np.float32)

            with patch.object(detector._extractor_cache.get(48000, Mock()),
                            'source_sr', 48000):
                # Simulate sample rate change
                detector._extractor_cache[44100] = Mock()
                detector._extractor_cache[44100].source_sr = 44100

                # Cache should now have both
                assert 48000 in detector._extractor_cache
                assert 44100 in detector._extractor_cache

    def test_is_ml_enabled_property(self, mock_yamnet, mock_feature_extractor):
        """Test is_ml_enabled reflects YAMNet state."""
        from ml.detector import MLDetector

        mock_yamnet.is_ml_enabled = True

        with patch('ml.detector.YAMNetDetector', return_value=mock_yamnet), \
             patch('ml.detector.FeatureExtractor', return_value=mock_feature_extractor):
            detector = MLDetector()
            assert detector.is_ml_enabled is True

            mock_yamnet.is_ml_enabled = False
            assert detector.is_ml_enabled is False


class TestGetMLDetector:
    """Tests for get_ml_detector singleton function."""

    def test_returns_same_instance(self):
        """Test singleton returns same instance."""
        from ml.detector import get_ml_detector, _detector_instance

        # Reset singleton for test
        import ml.detector as module
        module._detector_instance = None

        with patch('ml.detector.MLDetector') as MockDetector:
            MockDetector.return_value = Mock()

            detector1 = get_ml_detector(48000)
            detector2 = get_ml_detector(48000)

            # Should be same instance
            assert detector1 is detector2


class TestDetectAudio:
    """Tests for detect_audio convenience function."""

    def test_detect_audio_calls_detector(self):
        """Test detect_audio uses singleton detector."""
        from ml.detector import detect_audio

        with patch('ml.detector.get_ml_detector') as mock_get:
            mock_detector = Mock()
            mock_detector.detect.return_value = Mock()
            mock_get.return_value = mock_detector

            audio = np.zeros((2048, 2))
            detect_audio(audio, 48000)

            mock_get.assert_called_once_with(48000)
            mock_detector.detect.assert_called_once()
