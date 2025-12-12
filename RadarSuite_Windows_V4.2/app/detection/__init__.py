"""
RadarSuite v4.2.0 - Detection Module
Detection worker and pattern recognition

FIXED v4.2.0: ARC Raiders-specific detection modules:
- SpectralFeatureExtractor: MFCC and spectral features
- ShotDetector: Close/distant shots and explosions
- HumanFootstepDetector: Enhanced with surface type classification
- ARCMachineDetector: Machine state detection (idle/patrol/search/combat)
"""

from .worker import DetectionWorker
from .footstep import HumanFootstepDetector
from .spectral import SpectralFeatureExtractor
from .shot import ShotDetector
from .machine import ARCMachineDetector

__all__ = [
    'DetectionWorker',
    'HumanFootstepDetector',
    'SpectralFeatureExtractor',
    'ShotDetector',
    'ARCMachineDetector',
]
