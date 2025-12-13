"""
RadarSuite v4.2.0 - Machine Learning Detection Module
Real-time ML Detection Enhancement (Roadmap Item 1)

Replaces rule-based detection with lightweight ML models (TFLite/ONNX)
Target: 30-50% better accuracy for footstep/gunshot recognition

Components:
- FeatureExtractor: Audio → Mel-spectrogram conversion
- YAMNetDetector: Pre-trained audio classifier (TFLite)
- MLDetector: Main interface combining features + inference
"""

from .feature_extractor import FeatureExtractor, extract_mel_spectrogram
from .yamnet import YAMNetDetector, YAMNET_CLASS_MAP
from .detector import MLDetector, get_ml_detector

__all__ = [
    'FeatureExtractor',
    'extract_mel_spectrogram',
    'YAMNetDetector',
    'YAMNET_CLASS_MAP',
    'MLDetector',
    'get_ml_detector',
]
