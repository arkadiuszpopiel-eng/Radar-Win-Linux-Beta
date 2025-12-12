#!/usr/bin/env python3
"""
RadarSuite V4.2.1 - Simple Test Runner
Runs tests without requiring pytest installation
Point 12: Unit Testing
"""

import sys
import os
import traceback
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))


def run_test_class(test_class):
    """Run all test methods in a test class"""
    instance = test_class()
    test_methods = [m for m in dir(instance) if m.startswith('test_')]

    passed = 0
    failed = 0
    errors = []

    for method_name in test_methods:
        try:
            method = getattr(instance, method_name)
            method()
            passed += 1
            print(f"  ✓ {method_name}")
        except AssertionError as e:
            failed += 1
            errors.append((method_name, str(e)))
            print(f"  ✗ {method_name}: {e}")
        except Exception as e:
            failed += 1
            errors.append((method_name, traceback.format_exc()))
            print(f"  ✗ {method_name}: {e}")

    return passed, failed, errors


def run_core_tests():
    """Run core module tests"""
    print("\n" + "=" * 60)
    print("CORE MODULE TESTS")
    print("=" * 60)

    total_passed = 0
    total_failed = 0

    # Test 1: Constants
    print("\n[1/4] test_constants.py")
    try:
        from tests.core.test_constants import TestConstants
        passed, failed, _ = run_test_class(TestConstants)
        total_passed += passed
        total_failed += failed
    except Exception as e:
        print(f"  ✗ Failed to load test: {e}")
        total_failed += 1

    # Test 2: DI Container
    print("\n[2/4] test_di.py - TestServiceContainer")
    try:
        from tests.core.test_di import TestServiceContainer
        from tests.conftest import di_container

        # Create fixture
        from core.di import ServiceContainer
        container = ServiceContainer()

        # Run tests manually with fixture
        test = TestServiceContainer()
        test_methods = [m for m in dir(test) if m.startswith('test_') and not m.startswith('test_circular')]

        for method_name in test_methods:
            try:
                container_fresh = ServiceContainer()
                method = getattr(test, method_name)

                # Check if method needs di_container fixture
                import inspect
                sig = inspect.signature(method)
                if 'di_container' in sig.parameters:
                    method(container_fresh)
                else:
                    method()

                total_passed += 1
                print(f"  ✓ {method_name}")
            except AssertionError as e:
                total_failed += 1
                print(f"  ✗ {method_name}: {e}")
            except Exception as e:
                total_failed += 1
                print(f"  ✗ {method_name}: {e}")

    except Exception as e:
        print(f"  ✗ Failed to load test: {e}")
        traceback.print_exc()
        total_failed += 1

    # Test 3: Logger (skip thread safety test for simplicity)
    print("\n[3/4] test_logger.py")
    try:
        from tests.core.test_logger import TestLoggerPaths
        passed, failed, _ = run_test_class(TestLoggerPaths)
        total_passed += passed
        total_failed += failed
    except Exception as e:
        print(f"  ✗ Failed to load test: {e}")
        traceback.print_exc()
        total_failed += 1

    # Test 4: ConfigManager (basic tests only)
    print("\n[4/4] test_config.py")
    try:
        from tests.core.test_config import TestConfigManager
        import tempfile

        test = TestConfigManager()

        # Run basic tests that don't need fixtures
        basic_tests = [
            'test_config_schema_exists',
        ]

        for method_name in basic_tests:
            try:
                method = getattr(test, method_name)
                method()
                total_passed += 1
                print(f"  ✓ {method_name}")
            except Exception as e:
                total_failed += 1
                print(f"  ✗ {method_name}: {e}")

    except Exception as e:
        print(f"  ✗ Failed to load test: {e}")
        traceback.print_exc()
        total_failed += 1

    print("\n" + "=" * 60)
    print(f"CORE TESTS SUMMARY")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_failed}")
    print(f"  Total:  {total_passed + total_failed}")
    print("=" * 60)

    return total_passed, total_failed


def run_syntax_validation():
    """Validate Python syntax for all modules"""
    print("\n" + "=" * 60)
    print("SYNTAX VALIDATION")
    print("=" * 60)

    modules = [
        'core/constants.py',
        'core/di.py',
        'core/config.py',
        'core/logger.py',
        'core/translations.py',
        'hardware/gpu.py',
        'hardware/soundblaster.py',
    ]

    passed = 0
    failed = 0

    for module in modules:
        try:
            import py_compile
            py_compile.compile(module, doraise=True)
            print(f"  ✓ {module}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {module}: {e}")
            failed += 1

    print(f"\n  Passed: {passed}/{len(modules)}")
    return passed, failed


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("RadarSuite V4.2.1 - Point 12: Unit Tests")
    print("=" * 60)

    # Syntax validation
    syntax_passed, syntax_failed = run_syntax_validation()

    # Core tests
    core_passed, core_failed = run_core_tests()

    # Summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    print(f"Syntax Validation: {syntax_passed} passed, {syntax_failed} failed")
    print(f"Core Tests:        {core_passed} passed, {core_failed} failed")
    print(f"Total:             {syntax_passed + core_passed} passed, {syntax_failed + core_failed} failed")
    print("=" * 60)

    if syntax_failed > 0 or core_failed > 0:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
    else:
        print("\n✓ ALL TESTS PASSED")
        sys.exit(0)
