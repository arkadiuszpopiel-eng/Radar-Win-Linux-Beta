"""
RadarSuite v4.2.1 - Model Trainer Tests
Unit tests for ml/training/trainer.py
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json


class TestTrainingStatus:
    """Tests for TrainingStatus enum."""

    def test_status_values(self):
        """Test all training status values exist."""
        from ml.training.trainer import TrainingStatus

        assert TrainingStatus.IDLE.value == "idle"
        assert TrainingStatus.PREPARING.value == "preparing"
        assert TrainingStatus.EXTRACTING_FEATURES.value == "extracting_features"
        assert TrainingStatus.TRAINING.value == "training"
        assert TrainingStatus.SAVING.value == "saving"
        assert TrainingStatus.COMPLETED.value == "completed"
        assert TrainingStatus.FAILED.value == "failed"
        assert TrainingStatus.CANCELLED.value == "cancelled"


class TestTrainingConfig:
    """Tests for TrainingConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        from ml.training.trainer import TrainingConfig

        config = TrainingConfig()

        assert config.segment_duration_sec == 1.0
        assert config.segment_before_sec == 0.2
        assert config.min_samples_per_class == 5
        assert config.n_mels == 64
        assert config.n_fft == 512
        assert config.test_split == 0.2
        assert config.epochs == 50
        assert config.batch_size == 32
        assert config.model_name == "radarsuite_custom"

    def test_custom_config(self):
        """Test custom configuration."""
        from ml.training.trainer import TrainingConfig

        config = TrainingConfig(
            segment_duration_sec=2.0,
            min_samples_per_class=10,
            epochs=100
        )

        assert config.segment_duration_sec == 2.0
        assert config.min_samples_per_class == 10
        assert config.epochs == 100


class TestTrainingProgress:
    """Tests for TrainingProgress dataclass."""

    def test_default_progress(self):
        """Test default progress values."""
        from ml.training.trainer import TrainingProgress, TrainingStatus

        progress = TrainingProgress()

        assert progress.status == TrainingStatus.IDLE
        assert progress.progress_percent == 0.0
        assert progress.current_step == ""
        assert progress.total_samples == 0
        assert progress.error_message == ""


class TestTrainingResult:
    """Tests for TrainingResult dataclass."""

    def test_default_result(self):
        """Test default result values."""
        from ml.training.trainer import TrainingResult

        result = TrainingResult()

        assert result.success is False
        assert result.model_path == ""
        assert result.accuracy == 0.0
        assert result.samples_used == 0

    def test_result_to_dict(self):
        """Test result serialization."""
        from ml.training.trainer import TrainingResult

        result = TrainingResult(
            success=True,
            model_path="/path/to/model",
            accuracy=0.85,
            samples_used=100
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["accuracy"] == 0.85
        assert data["samples_used"] == 100


class TestModelTrainer:
    """Tests for ModelTrainer class."""

    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager."""
        manager = Mock()
        manager.list_sessions.return_value = []
        manager.load_session.return_value = None
        manager.load_audio.return_value = None
        return manager

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_trainer_initialization(self, mock_session_manager, temp_output_dir):
        """Test trainer initialization."""
        from ml.training.trainer import ModelTrainer

        trainer = ModelTrainer(
            session_manager=mock_session_manager,
            output_dir=temp_output_dir
        )

        assert trainer.session_manager is mock_session_manager
        assert trainer.output_dir == temp_output_dir
        assert trainer.is_training is False

    def test_is_training_property(self, mock_session_manager, temp_output_dir):
        """Test is_training reflects current state."""
        from ml.training.trainer import ModelTrainer, TrainingStatus

        trainer = ModelTrainer(
            session_manager=mock_session_manager,
            output_dir=temp_output_dir
        )

        # Initially idle
        assert trainer.is_training is False

        # Simulate training state
        trainer._progress.status = TrainingStatus.TRAINING
        assert trainer.is_training is True

        # Completed
        trainer._progress.status = TrainingStatus.COMPLETED
        assert trainer.is_training is False

    def test_set_callbacks(self, mock_session_manager, temp_output_dir):
        """Test callback registration."""
        from ml.training.trainer import ModelTrainer

        trainer = ModelTrainer(
            session_manager=mock_session_manager,
            output_dir=temp_output_dir
        )

        on_progress = Mock()
        on_complete = Mock()
        on_log = Mock()

        trainer.set_callbacks(
            on_progress=on_progress,
            on_complete=on_complete,
            on_log=on_log
        )

        assert trainer._on_progress is on_progress
        assert trainer._on_complete is on_complete
        assert trainer._on_log is on_log

    def test_cancel_training(self, mock_session_manager, temp_output_dir):
        """Test training cancellation."""
        from ml.training.trainer import ModelTrainer

        trainer = ModelTrainer(
            session_manager=mock_session_manager,
            output_dir=temp_output_dir
        )

        trainer.cancel_training()

        assert trainer._cancel_requested is True

    def test_start_training_when_already_running(self, mock_session_manager, temp_output_dir):
        """Test start_training returns False when already running."""
        from ml.training.trainer import ModelTrainer, TrainingStatus

        trainer = ModelTrainer(
            session_manager=mock_session_manager,
            output_dir=temp_output_dir
        )

        # Simulate running state
        trainer._progress.status = TrainingStatus.TRAINING

        result = trainer.start_training()

        assert result is False

    def test_extract_segment(self, mock_session_manager, temp_output_dir):
        """Test audio segment extraction."""
        from ml.training.trainer import ModelTrainer

        trainer = ModelTrainer(
            session_manager=mock_session_manager,
            output_dir=temp_output_dir
        )

        # Create test audio (10 seconds at 48kHz)
        audio = np.random.rand(480000).astype(np.float32)

        # Extract segment at 5 seconds
        segment = trainer._extract_segment(audio, 5.0, 48000)

        assert segment is not None
        # Should be ~1 second (default segment_duration_sec)
        expected_length = int(trainer.config.segment_duration_sec * 48000)
        assert len(segment) == expected_length

    def test_extract_segment_out_of_bounds(self, mock_session_manager, temp_output_dir):
        """Test segment extraction handles out-of-bounds."""
        from ml.training.trainer import ModelTrainer

        trainer = ModelTrainer(
            session_manager=mock_session_manager,
            output_dir=temp_output_dir
        )

        # Short audio
        audio = np.random.rand(1000).astype(np.float32)

        # Try to extract beyond audio length
        segment = trainer._extract_segment(audio, 100.0, 48000)

        assert segment is None

    def test_list_trained_models_empty(self, mock_session_manager, temp_output_dir):
        """Test listing models when none exist."""
        from ml.training.trainer import ModelTrainer

        trainer = ModelTrainer(
            session_manager=mock_session_manager,
            output_dir=temp_output_dir
        )

        models = trainer.list_trained_models()

        assert isinstance(models, list)
        assert len(models) == 0

    def test_list_trained_models_with_models(self, mock_session_manager, temp_output_dir):
        """Test listing existing models."""
        from ml.training.trainer import ModelTrainer

        # Create fake model directory with metadata
        model_dir = temp_output_dir / "test_model_20251205"
        model_dir.mkdir()

        metadata = {
            "created_at": "2025-12-05T12:00:00",
            "accuracy": 0.85,
            "class_names": ["walk", "run"],
            "samples_used": 100
        }

        with open(model_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f)

        trainer = ModelTrainer(
            session_manager=mock_session_manager,
            output_dir=temp_output_dir
        )

        models = trainer.list_trained_models()

        assert len(models) == 1
        assert models[0]["accuracy"] == 0.85
        assert models[0]["class_count"] == 2


class TestTrainModel:
    """Tests for _train_model method (requires sklearn)."""

    @pytest.fixture
    def trainer_with_data(self, tmp_path):
        """Create trainer with mock data."""
        from ml.training.trainer import ModelTrainer

        mock_manager = Mock()
        trainer = ModelTrainer(
            session_manager=mock_manager,
            output_dir=tmp_path
        )
        return trainer

    def test_train_model_with_minimal_data(self, trainer_with_data):
        """Test training with minimal dataset."""
        # Create minimal training data
        X = np.random.rand(20, 96, 64).astype(np.float32)  # 20 samples
        y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
                      0, 0, 0, 0, 0, 1, 1, 1, 1, 1])  # 2 classes
        class_names = ["walk", "run"]

        model, accuracy, class_acc = trainer_with_data._train_model(X, y, class_names)

        assert model is not None
        assert 0.0 <= accuracy <= 1.0
        assert isinstance(class_acc, dict)
