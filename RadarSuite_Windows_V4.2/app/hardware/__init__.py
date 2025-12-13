"""
RadarSuite V4.2.1 - Hardware Optimization Module
GPU acceleration and Sound Blaster optimization
"""

from .gpu import GPUAccelerator
from .soundblaster import SoundBlasterOptimizer

__all__ = [
    'GPUAccelerator',
    'SoundBlasterOptimizer',
]
