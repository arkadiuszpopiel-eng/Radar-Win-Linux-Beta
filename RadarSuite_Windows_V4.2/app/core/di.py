"""
RadarSuite V4.2.1 - Dependency Injection Container
Point 11: Inversion of Control for better testability and modularity

Simple but powerful DI container with:
- Singleton registration
- Factory registration
- Lazy initialization
- Dependency resolution
"""

from typing import Any, Callable, Dict, Optional, Type
from .logger import log  # FIXED v4.2.1: Use relative import


class ServiceContainer:
    """
    Dependency Injection Container

    Point 11 - v3.5.0: IoC container for decoupling dependencies
    Enables easy testing, configuration, and extension
    """

    def __init__(self):
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._instances: Dict[str, Any] = {}

    def register_singleton(self, name: str, factory: Callable) -> None:
        """
        Register a singleton service (lazy instantiated)

        Args:
            name: Service identifier
            factory: Factory function that creates the service
        """
        self._factories[name] = factory
        log(f"DI: Registered singleton '{name}'", "DEBUG")

    def register_instance(self, name: str, instance: Any) -> None:
        """
        Register an already-created instance

        Args:
            name: Service identifier
            instance: Pre-created instance
        """
        self._instances[name] = instance
        log(f"DI: Registered instance '{name}'", "DEBUG")

    def get(self, name: str) -> Any:
        """
        Resolve and return a service

        Args:
            name: Service identifier

        Returns:
            Service instance

        Raises:
            KeyError: If service not registered
        """
        # Check if already instantiated
        if name in self._instances:
            return self._instances[name]

        # Check if factory registered
        if name not in self._factories:
            raise KeyError(f"Service '{name}' not registered in DI container")

        # Lazy instantiation
        log(f"DI: Instantiating '{name}'", "DEBUG")
        factory = self._factories[name]
        instance = factory(self)  # Pass container for dependency resolution
        self._instances[name] = instance

        return instance

    def has(self, name: str) -> bool:
        """Check if service is registered"""
        return name in self._factories or name in self._instances

    def reset(self) -> None:
        """Clear all instances (useful for testing)"""
        self._instances.clear()
        log("DI: All instances cleared", "DEBUG")

    def get_registered_services(self) -> list:
        """Get list of all registered service names"""
        return list(self._factories.keys()) + list(self._instances.keys())


# Global container instance
_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global DI container"""
    return _container


def configure_services(config: dict) -> ServiceContainer:
    """
    Configure all application services in the DI container

    Point 11 - v3.5.0: Centralized dependency configuration
    All dependencies defined in one place for easy management

    Args:
        config: Application configuration dict

    Returns:
        Configured ServiceContainer
    """
    container = get_container()

    # Reset previous configuration
    container.reset()

    log("DI: Configuring services...", "INFO")

    # ========================================================================
    # CORE SERVICES
    # ========================================================================

    # ConfigManager (already created, register as instance)
    from core import ConfigManager
    config_manager = ConfigManager()
    container.register_instance('config_manager', config_manager)

    # ========================================================================
    # HARDWARE SERVICES
    # ========================================================================

    from hardware import GPUAccelerator, SoundBlasterOptimizer

    container.register_singleton('gpu', lambda c: GPUAccelerator(
        enable_gpu=config.get('performance', {}).get('use_gpu', True)
    ))

    container.register_singleton('soundblaster', lambda c: SoundBlasterOptimizer())

    # ========================================================================
    # AUDIO SERVICES
    # ========================================================================

    from audio import (
        AudioProcessingCache,
        AudioEngine,
        SoundClassifier,
        AudioRecorder,
        HumanVoiceDetector
    )

    container.register_singleton('audio_cache', lambda c: AudioProcessingCache(
        max_size=5,
        gpu_accelerator=c.get('gpu')
    ))

    container.register_singleton('audio_engine', lambda c: AudioEngine())

    container.register_singleton('sound_classifier', lambda c: SoundClassifier())

    container.register_singleton('audio_recorder', lambda c: AudioRecorder(
        sample_rate=config.get('audio', {}).get('sample_rate', 48000)
    ))

    container.register_singleton('voice_detector', lambda c: HumanVoiceDetector())

    # ========================================================================
    # DETECTION SERVICES
    # ========================================================================

    from detection import DetectionWorker, HumanFootstepDetector

    container.register_singleton('detection_worker', lambda c: DetectionWorker(
        max_workers=config.get('performance', {}).get('max_workers', 3)
    ))

    container.register_singleton('footstep_detector', lambda c: HumanFootstepDetector())

    # ========================================================================
    # TRACKING SERVICES
    # ========================================================================

    from tracking import TargetTracker, ThreatPrioritySystem

    container.register_singleton('target_tracker', lambda c: TargetTracker(
        max_targets=3
    ))

    container.register_singleton('threat_system', lambda c: ThreatPrioritySystem())

    # ========================================================================
    # UTILITY SERVICES
    # ========================================================================

    from utils import (
        PerformanceMonitor,
        GameProcessDetector,
        PlatformLauncherDetector,
        AudioSourceScanner
    )

    container.register_singleton('performance_monitor', lambda c: PerformanceMonitor())

    container.register_singleton('game_detector', lambda c: GameProcessDetector())

    container.register_singleton('launcher_detector', lambda c: PlatformLauncherDetector())

    container.register_singleton('audio_scanner', lambda c: AudioSourceScanner(
        platform_detector=c.get('launcher_detector')
    ))

    log(f"DI: {len(container.get_registered_services())} services configured", "INFO")

    return container
