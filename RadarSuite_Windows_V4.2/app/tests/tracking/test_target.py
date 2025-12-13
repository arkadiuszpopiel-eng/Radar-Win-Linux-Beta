"""
RadarSuite v3.5.0 - Point 12: Target Tracking Tests
Tests for tracking/target.py
"""

import time
from tests.compat import pytest
from tracking.target import Target, TargetTracker


class TestTarget:
    """Test suite for Target class"""

    def test_target_initialization(self):
        """Test Target creation with default values"""
        target = Target(
            target_id=1,
            angle=45.0,
            distance=10.0,
            elevation=5.0,
            target_type='footstep'
        )

        assert target.id == 1
        assert target.angle == 45.0
        assert target.distance == 10.0
        assert target.elevation == 5.0
        assert target.type == 'footstep'
        assert target.confidence == 1.0
        assert target.is_active is True
        assert target.update_count == 1
        assert len(target.history) == 1

    def test_target_update(self):
        """Test target position update"""
        target = Target(1, 0, 0, 0, 'unknown')

        initial_update_count = target.update_count
        initial_confidence = target.confidence

        target.update(angle=90.0, distance=15.0, elevation=10.0)

        assert target.angle == 90.0
        assert target.distance == 15.0
        assert target.elevation == 10.0
        assert target.update_count == initial_update_count + 1
        assert target.confidence >= initial_confidence  # Confidence increases
        assert len(target.history) == 2

    def test_target_history_limit(self):
        """Test that history is limited to max_history"""
        target = Target(1, 0, 0)
        target.max_history = 5

        # Add more updates than max_history
        for i in range(10):
            target.update(i, i, i)

        assert len(target.history) <= target.max_history

    def test_target_decay(self):
        """Test target confidence decay"""
        target = Target(1, 0, 0)
        initial_confidence = target.confidence
        initial_lifetime = target.lifetime

        # Decay for 0.5 seconds
        target.decay(0.5)

        assert target.confidence < initial_confidence
        assert target.lifetime > initial_lifetime

    def test_target_decay_deactivates(self):
        """Test that target becomes inactive when confidence reaches zero"""
        target = Target(1, 0, 0)

        # Decay for a long time to force confidence to zero
        target.decay(10.0)

        assert target.confidence <= 0
        assert target.is_active is False

    def test_target_get_color_by_type(self):
        """Test that get_color returns correct colors for different types"""
        footstep = Target(1, 0, 0, target_type='footstep')
        voice = Target(2, 0, 0, target_type='voice')
        shot = Target(3, 0, 0, target_type='shot')
        unknown = Target(4, 0, 0, target_type='unknown')

        footstep_color = footstep.get_color()
        voice_color = voice.get_color()
        shot_color = shot.get_color()
        unknown_color = unknown.get_color()

        # Check that colors are different
        assert footstep_color[:3] == (0, 1, 0)  # Green
        assert voice_color[:3] == (0, 0.7, 1)   # Cyan
        assert shot_color[:3] == (1, 0, 0)      # Red
        assert unknown_color[:3] == (1, 1, 0)   # Yellow

        # All should have alpha channel
        assert len(footstep_color) == 4
        assert 0 <= footstep_color[3] <= 1

    def test_target_color_alpha_fades(self):
        """Test that alpha decreases with confidence"""
        target = Target(1, 0, 0)

        initial_color = target.get_color()
        initial_alpha = initial_color[3]

        # Decay to reduce confidence
        target.decay(1.0)

        faded_color = target.get_color()
        faded_alpha = faded_color[3]

        assert faded_alpha < initial_alpha or faded_alpha == 0.3  # Min alpha is 0.3


class TestTargetTracker:
    """Test suite for TargetTracker class"""

    def test_tracker_initialization(self):
        """Test TargetTracker initialization"""
        tracker = TargetTracker(max_targets=5)

        assert tracker.max_targets == 5
        assert len(tracker.targets) == 0
        assert tracker.next_id == 1

    def test_tracker_default_max_targets(self):
        """Test default max_targets value"""
        tracker = TargetTracker()
        assert tracker.max_targets == 3

    def test_tracker_add_single_detection(self):
        """Test adding a single detection"""
        tracker = TargetTracker()

        detections = [
            {'angle': 45.0, 'distance': 10.0, 'elevation': 0.0, 'type': 'footstep'}
        ]

        tracker.update(detections)

        assert len(tracker.targets) == 1
        target = list(tracker.targets.values())[0]
        assert target.angle == 45.0
        assert target.distance == 10.0
        assert target.type == 'footstep'

    def test_tracker_update_existing_target(self):
        """Test updating an existing target"""
        tracker = TargetTracker()

        # First detection
        detections1 = [
            {'angle': 45.0, 'distance': 10.0, 'elevation': 0.0, 'type': 'footstep'}
        ]
        tracker.update(detections1)

        initial_id = list(tracker.targets.keys())[0]

        # Similar detection (should update, not create new)
        detections2 = [
            {'angle': 50.0, 'distance': 12.0, 'elevation': 0.0, 'type': 'footstep'}
        ]
        tracker.update(detections2)

        # Should still be 1 target (updated)
        assert len(tracker.targets) == 1
        assert initial_id in tracker.targets

    def test_tracker_multiple_targets(self):
        """Test tracking multiple simultaneous targets"""
        tracker = TargetTracker(max_targets=3)

        # Add 3 separate targets (far apart)
        detections = [
            {'angle': 0.0, 'distance': 10.0, 'elevation': 0.0, 'type': 'footstep'},
            {'angle': 120.0, 'distance': 10.0, 'elevation': 0.0, 'type': 'voice'},
            {'angle': 240.0, 'distance': 10.0, 'elevation': 0.0, 'type': 'shot'},
        ]

        tracker.update(detections)

        assert len(tracker.targets) <= 3

    def test_tracker_removes_old_targets(self):
        """Test that old targets are removed after timeout"""
        tracker = TargetTracker()
        tracker.timeout = 0.1  # 100ms timeout for testing

        # Add a target
        detections = [
            {'angle': 45.0, 'distance': 10.0, 'elevation': 0.0, 'type': 'footstep'}
        ]
        tracker.update(detections)

        assert len(tracker.targets) == 1

        # Wait longer than timeout
        time.sleep(0.2)

        # Update with no detections
        tracker.update([])

        # Old target should be removed
        assert len(tracker.targets) == 0

    def test_tracker_respects_max_targets(self):
        """Test that tracker doesn't exceed max_targets"""
        tracker = TargetTracker(max_targets=2)

        # Try to add 5 targets
        detections = [
            {'angle': i * 60.0, 'distance': 10.0, 'elevation': 0.0, 'type': 'unknown'}
            for i in range(5)
        ]

        tracker.update(detections)

        # Should not exceed max_targets
        assert len(tracker.targets) <= 2

    def test_tracker_get_active_targets(self):
        """Test get_active_targets method"""
        tracker = TargetTracker()

        detections = [
            {'angle': 45.0, 'distance': 10.0, 'elevation': 0.0, 'type': 'footstep'}
        ]
        tracker.update(detections)

        active_targets = tracker.get_active_targets()
        assert len(active_targets) == 1
        assert active_targets[0].angle == 45.0

    def test_tracker_clear_all_targets(self):
        """Test clear method"""
        tracker = TargetTracker()

        # Add some targets
        detections = [
            {'angle': 45.0, 'distance': 10.0, 'elevation': 0.0, 'type': 'footstep'},
            {'angle': 135.0, 'distance': 10.0, 'elevation': 0.0, 'type': 'voice'}
        ]
        tracker.update(detections)

        assert len(tracker.targets) > 0

        tracker.clear()

        assert len(tracker.targets) == 0
        assert tracker.next_id == 1  # Reset ID counter
