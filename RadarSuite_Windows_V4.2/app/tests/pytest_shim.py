"""
Simple pytest compatibility shim for environments without pytest
Provides basic pytest functionality for our tests
"""

import functools


class FixtureRegistry:
    """Registry for fixtures"""
    def __init__(self):
        self.fixtures = {}

    def register(self, name, func, autouse=False):
        self.fixtures[name] = {'func': func, 'autouse': autouse}

    def get(self, name):
        if name in self.fixtures:
            return self.fixtures[name]['func']()
        raise KeyError(f"Fixture {name} not found")


_fixture_registry = FixtureRegistry()


def fixture(func=None, *, autouse=False):
    """Decorator to mark a function as a fixture"""
    def decorator(f):
        _fixture_registry.register(f.__name__, f, autouse)
        return f

    if func is None:
        return decorator
    else:
        return decorator(func)


class RaisesContext:
    """Context manager for pytest.raises"""
    def __init__(self, exc_type):
        self.exc_type = exc_type
        self.value = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            raise AssertionError(f"Expected {self.exc_type.__name__} but no exception was raised")
        if not issubclass(exc_type, self.exc_type):
            return False  # Re-raise the exception
        self.value = exc_val
        return True  # Suppress the exception


def raises(exc_type):
    """Assert that a block raises an exception"""
    return RaisesContext(exc_type)


class MarkDecorator:
    """Decorator for test markers"""
    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        if not hasattr(func, '_marks'):
            func._marks = []
        func._marks.append(self.name)
        return func


class Mark:
    """Marker for tests"""
    def __getattr__(self, name):
        return MarkDecorator(name)


mark = Mark()


def fail(msg):
    """Explicitly fail a test"""
    raise AssertionError(msg)


# Make everything available
__all__ = ['fixture', 'raises', 'mark', 'fail', '_fixture_registry']
