"""
RadarSuite v4.2.1 - Utilities Module
Performance monitoring, memory optimization, game detection, launcher detection, audio scanning

ENHANCED v4.2.1: Added MemoryOptimizer for ZADANIE 6
"""

from .performance import PerformanceMonitor, MemoryOptimizer, MemorySnapshot, MemoryStats
from .game_detector import GameProcessDetector
from .launcher import PlatformLauncherDetector
from .audio_scanner import AudioSourceScanner

__all__ = [
    'PerformanceMonitor',
    'MemoryOptimizer',
    'MemorySnapshot',
    'MemoryStats',
    'GameProcessDetector',
    'PlatformLauncherDetector',
    'AudioSourceScanner',
]
