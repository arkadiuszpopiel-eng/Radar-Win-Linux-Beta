#!/usr/bin/env python3
"""
Quick DI Container Test - Point 11 Validation
Verifies all services can be instantiated and resolved
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import configure_services, ConfigManager

def test_di_container():
    """Test DI container service resolution"""

    print("=" * 60)
    print("Point 11 - DI Container Test")
    print("=" * 60)

    # Load configuration
    config_mgr = ConfigManager()
    config = config_mgr.load()

    # Configure DI container
    print("\n[1/3] Configuring DI container...")
    container = configure_services(config)

    registered_services = container.get_registered_services()
    print(f"✓ {len(registered_services)} services registered")

    # Test service resolution
    print("\n[2/3] Testing service resolution...")

    services_to_test = [
        'config_manager',
        'gpu',
        'soundblaster',
        'audio_cache',
        'audio_engine',
        'sound_classifier',
        'audio_recorder',
        'voice_detector',
        'detection_worker',
        'footstep_detector',
        'target_tracker',
        'threat_system',
        'performance_monitor',
        'game_detector',
        'launcher_detector',
        'audio_scanner',
    ]

    resolved = 0
    failed = []

    for service_name in services_to_test:
        try:
            service = container.get(service_name)
            print(f"  ✓ {service_name}: {type(service).__name__}")
            resolved += 1
        except Exception as e:
            print(f"  ✗ {service_name}: {e}")
            failed.append(service_name)

    # Summary
    print("\n[3/3] Results:")
    print(f"  Resolved: {resolved}/{len(services_to_test)}")
    print(f"  Failed:   {len(failed)}/{len(services_to_test)}")

    if failed:
        print(f"\n✗ Failed services: {', '.join(failed)}")
        return False
    else:
        print("\n✓ All services resolved successfully!")
        print("✓ Point 11 - DI Container: VALIDATED")
        return True

if __name__ == '__main__':
    try:
        success = test_di_container()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
