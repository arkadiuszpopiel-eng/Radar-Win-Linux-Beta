"""
RadarSuite v4.2.0 - Target Tracking
Target and TargetTracker for multi-target tracking
FIXED v4.1.0: Thread-safe operations with locks
FIXED v4.2.0: Normalized confidence logging (0-100%)
"""

import time
import math
import threading
from collections import deque

from core.logger import log
from core.confidence import ConfidenceNormalizer
from core.constants import TARGET_CONFIDENCE_ALGORITHM_MIN, TARGET_CONFIDENCE_UI_MIN


class Target:
    """Represents a single tracked target"""

    def __init__(self, target_id, angle, distance, elevation=0, target_type='unknown'):
        self.id = target_id
        self.angle = angle  # Azimuth in degrees
        self.distance = distance  # Distance in meters
        self.elevation = elevation  # Elevation in degrees
        self.type = target_type  # 'footstep', 'voice', 'shot', 'unknown'

        # Tracking data
        self.last_update_time = time.time()
        self.lifetime = 0.0
        self.update_count = 1

        # Movement history (for trails)
        self.history = [(angle, distance, elevation)]
        self.max_history = 10

        # Confidence and persistence
        self.confidence = 1.0
        self.is_active = True

        # FIXED v4.2.0: Type stability - track recent type detections
        self.type_history = deque(maxlen=5)
        self.type_history.append(target_type)

    def update(self, angle, distance, elevation, target_type=None):
        """
        Update target position and type

        FIXED v4.1.2: Now accepts target_type to allow type changes
        FIXED v4.2.0: Type stabilization with voting to prevent spam
        """
        self.angle = angle
        self.distance = distance
        self.elevation = elevation
        self.last_update_time = time.time()
        self.update_count += 1
        self.confidence = min(1.0, self.confidence + 0.1)

        # FIXED v4.2.0: Type stabilization - use majority voting
        if target_type is not None and target_type != 'unknown':
            self.type_history.append(target_type)

            # Vote on type based on recent history
            if len(self.type_history) >= 3:
                # Count occurrences
                type_counts = {}
                for t in self.type_history:
                    type_counts[t] = type_counts.get(t, 0) + 1

                # Get most common type
                most_common = max(type_counts, key=type_counts.get)
                self.type = most_common
            else:
                # Not enough history, use current
                self.type = target_type
        elif target_type is not None:
            # Unknown type - keep current
            pass

        # Add to history
        self.history.append((angle, distance, elevation))
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def decay(self, dt):
        """
        Decay confidence over time (for targets not updated)

        FIXED v4.2.0: Added TTL check - targets expire after timeout
        """
        self.confidence -= dt * 0.5  # Lose 50% confidence per second
        self.lifetime += dt

        # FIXED v4.2.0: Check time since last update (TTL)
        time_since_update = time.time() - self.last_update_time

        if self.confidence <= 0 or time_since_update > 2.0:
            self.is_active = False

    def get_color(self):
        """Get target color based on type and confidence"""
        # Base colors by type
        type_colors = {
            'footstep': (0, 1, 0),      # Green
            'voice': (0, 0.7, 1),        # Cyan
            'shot': (1, 0, 0),           # Red
            'unknown': (1, 1, 0)         # Yellow
        }

        base_color = type_colors.get(self.type, (1, 1, 0))
        alpha = max(0.3, self.confidence)  # Fade out as confidence decreases

        return (*base_color, alpha)



class TargetTracker:
    """
    Multi-target tracking system
    Tracks up to 3 simultaneous targets
    Assigns IDs, manages persistence, and handles target updates

    FIXED v4.1.0: Thread-safe with lock protection
    """

    def __init__(self, max_targets=3):
        log("TargetTracker.__init__", "INFO")

        self.max_targets = max_targets
        self.targets = {}  # {target_id: Target}
        self.next_id = 1

        # Tracking parameters
        self.merge_distance = 15.0  # Merge targets closer than 15m
        self.merge_angle = 20.0     # Merge targets within 20° angle
        self.timeout = 2.0          # Remove targets after 2s of no updates

        self.last_update_time = time.time()

        # FIXED v4.1.0: Thread safety
        self._lock = threading.Lock()

    def update(self, detections):
        """
        Update tracker with new detections (THREAD-SAFE v4.1.0)

        Args:
            detections: List of detection dicts with keys:
                       'angle', 'distance', 'elevation', 'type'
        """
        with self._lock:
            current_time = time.time()
            dt = current_time - self.last_update_time
            self.last_update_time = current_time

            # Decay existing targets
            for target in self.targets.values():
                target.decay(dt)

            # FIXED v4.2.0: Remove inactive targets with logging (normalized confidence)
            inactive_targets = [(tid, t) for tid, t in self.targets.items() if not t.is_active]
            for tid, target in inactive_targets:
                # Normalize confidence to 0-100% for readable logging
                conf_normalized = ConfidenceNormalizer.normalize(target.confidence, 'probability')
                log(f"Removing target #{tid} ({target.type}) - "
                    f"timeout={time.time() - target.last_update_time:.1f}s, "
                    f"conf={conf_normalized:.1f}%", "DEBUG")
            self.targets = {tid: t for tid, t in self.targets.items() if t.is_active}

            # Process new detections
            for detection in detections:
                angle = detection.get('angle', 0)
                distance = detection.get('distance', 50)
                elevation = detection.get('elevation', 0)
                target_type = detection.get('type', 'unknown')

                # FIXED v4.1.2: Try to match with existing target (type-aware)
                matched_target = self._find_matching_target_unlocked(angle, distance, elevation, target_type)

                if matched_target:
                    # FIXED v4.1.2: Update existing target WITH type
                    matched_target.update(angle, distance, elevation, target_type)
                elif len(self.targets) < self.max_targets:
                    # Create new target
                    new_target = Target(self.next_id, angle, distance, elevation, target_type)
                    self.targets[self.next_id] = new_target
                    self.next_id += 1
                    log(f"New target #{new_target.id} created: {target_type} at {distance:.1f}m", "INFO")
                else:
                    # FIXED v4.1.2: Max targets reached - replace lowest confidence target if this is more important
                    self._try_replace_target_unlocked(angle, distance, elevation, target_type)

            return self._get_active_targets_unlocked()

    def _find_matching_target_unlocked(self, angle, distance, elevation, target_type='unknown'):
        """
        Find existing target that matches the detection (must hold lock)

        FIXED v4.1.2: Now type-aware - only matches compatible types
        """
        best_match = None
        min_score = float('inf')

        for target in self.targets.values():
            # FIXED v4.1.2: Check type compatibility first
            if not self._types_compatible(target.type, target_type):
                continue  # Skip incompatible types

            # Calculate angular difference (handle wrap-around at 0°/360°)
            angle_diff = abs(angle - target.angle)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff

            # Calculate distance difference
            dist_diff = abs(distance - target.distance)

            # Calculate elevation difference
            elev_diff = abs(elevation - target.elevation)

            # Combined score (lower is better)
            score = angle_diff + dist_diff + elev_diff * 0.5

            # Check if within merge thresholds
            if (angle_diff < self.merge_angle and
                dist_diff < self.merge_distance and
                score < min_score):
                best_match = target
                min_score = score

        return best_match

    def _types_compatible(self, type1, type2):
        """
        FIXED v4.1.2: Check if two target types are compatible for merging

        Returns:
            True if types can be merged, False otherwise
        """
        # Same type is always compatible
        if type1 == type2:
            return True

        # 'unknown' can match anything
        if type1 == 'unknown' or type2 == 'unknown':
            return True

        # Footsteps are compatible with each other
        footstep_types = {'footstep', 'run', 'walk'}
        if type1 in footstep_types and type2 in footstep_types:
            return True

        # Different incompatible types (e.g., 'shot' vs 'footstep')
        return False

    def _try_replace_target_unlocked(self, angle, distance, elevation, target_type):
        """
        FIXED v4.1.2: Try to replace lowest confidence target with new detection

        Only replaces if new detection is more important (shots > footsteps)
        """
        # Find lowest confidence target
        min_confidence = 1.0
        weakest_target = None

        for target in self.targets.values():
            if target.confidence < min_confidence:
                min_confidence = target.confidence
                weakest_target = target

        # Replace if new detection is shot (high priority) or weakest is very low confidence
        type_priority = {'shot': 3, 'rifle': 3, 'pistol': 3, 'shotgun': 3, 'sniper': 3,
                        'footstep': 2, 'run': 2, 'walk': 2, 'unknown': 1}

        new_priority = type_priority.get(target_type, 1)
        old_priority = type_priority.get(weakest_target.type, 1) if weakest_target else 0

        if weakest_target and (new_priority > old_priority or min_confidence < 0.3):
            # FIXED v4.2.0: Normalize confidence for readable logging
            conf_normalized = ConfidenceNormalizer.normalize(min_confidence, 'probability')
            log(f"Replacing target #{weakest_target.id} ({weakest_target.type}, conf={conf_normalized:.1f}%) "
                f"with {target_type}", "INFO")
            weakest_target.update(angle, distance, elevation, target_type)
            weakest_target.confidence = 0.8  # Reset confidence

    def _get_active_targets_unlocked(self):
        """Get list of active targets (must hold lock)"""
        return [
            {
                'id': target.id,
                'angle': target.angle,
                'distance': target.distance,
                'elevation': target.elevation,
                'type': target.type,
                'confidence': target.confidence,
                'color': target.get_color(),
                'history': list(target.history)  # Copy to prevent concurrent modification
            }
            for target in self.targets.values()
            if target.is_active
        ]

    def get_active_targets(self):
        """Get list of active targets for display (THREAD-SAFE v4.1.0)"""
        with self._lock:
            return self._get_active_targets_unlocked()

    def clear(self):
        """Clear all targets (THREAD-SAFE v4.1.0)"""
        with self._lock:
            self.targets = {}
            self.next_id = 1

