"""
RadarSuite v4.2.0 - Audio Module
Audio processing, recording, classification, voice detection

ENHANCED v4.2.0: Added AudioProcessor for 3D localization algorithms
"""

from .cache import AudioProcessingCache
from .engine import AudioEngine
from .classifier import SoundClassifier
from .recorder import AudioRecorder
from .voice_detector import HumanVoiceDetector
from .processor import AudioProcessor, get_audio_processor

__all__ = [
    'AudioProcessingCache',
    'AudioEngine',
    'SoundClassifier',
    'AudioRecorder',
    'HumanVoiceDetector',
    'AudioProcessor',
    'get_audio_processor',
]
