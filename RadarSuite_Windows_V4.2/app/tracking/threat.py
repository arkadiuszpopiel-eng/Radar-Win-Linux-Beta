"""
RadarSuite v3.5.0 - Threat Priority System
Intelligent threat ranking by danger level
"""

from core.logger import log


class ThreatPrioritySystem:
    """
    Advanced threat assessment and priority ranking
    Scores targets based on type, distance, direction, confidence
    """

    def __init__(self):
        log("ThreatPrioritySystem.__init__", "INFO")

        # Threat scores by sound type (0-100)
        self.threat_scores = {
            # Weapons (highest threat)
            'sniper': 100,
            'rifle': 85,
            'shotgun': 80,
            'pistol': 70,
            'explosion': 90,
            'grenade': 95,

            # Vehicles (medium threat)
            'helicopter': 60,
            'car_engine': 50,

            # Humans (lower threat but still important)
            'footstep': 40,
            'voice': 30,
            'breathing': 20,

            # Generic
            'shot': 75,
            'unknown': 10,
            'silence': 0
        }

        # Direction multipliers (rear is more dangerous)
        self.direction_zones = {
            'front': 0.8,      # 45-135° (less threatening)
            'side': 1.0,       # 135-225° or 315-45° (medium)
            'rear': 1.3        # 225-315° (most threatening - can't see)
        }

    def calculate_threat_level(self, target):
        """
        Calculate threat level for a target (0-100 scale)

        Args:
            target: dict with type, angle, distance, elevation, confidence

        Returns:
            dict with threat_level, threat_category, color, priority_rank
        """
        try:
            # Base threat from sound type
            sound_type = target.get('type', 'unknown')
            base_threat = self.threat_scores.get(sound_type, 10)

            # Distance factor (closer = more threatening)
            # 0-20m = 1.5x, 20-50m = 1.0x, 50-100m = 0.5x
            distance = target.get('distance', 50)
            if distance < 20:
                distance_factor = 1.5
            elif distance < 50:
                distance_factor = 1.0 + (50 - distance) / 60.0  # Linear interpolation
            else:
                distance_factor = max(0.5, 1.0 - (distance - 50) / 100.0)

            # Direction factor (rear attacks are dangerous)
            angle = target.get('angle', 90)
            direction_factor = self._get_direction_factor(angle)

            # Confidence factor (low confidence = reduce threat)
            confidence = target.get('confidence', 100) / 100.0

            # Calculate final threat level
            threat_level = base_threat * distance_factor * direction_factor * confidence
            threat_level = min(100, max(0, threat_level))  # Clamp to 0-100

            # Categorize threat
            if threat_level >= 80:
                category = 'CRITICAL'
                color = (255, 0, 0)  # Red
            elif threat_level >= 60:
                category = 'HIGH'
                color = (255, 100, 0)  # Orange
            elif threat_level >= 40:
                category = 'MEDIUM'
                color = (255, 200, 0)  # Yellow
            elif threat_level >= 20:
                category = 'LOW'
                color = (100, 200, 100)  # Green
            else:
                category = 'MINIMAL'
                color = (100, 100, 255)  # Blue

            return {
                'threat_level': threat_level,
                'category': category,
                'color': color,
                'base_threat': base_threat,
                'distance_factor': distance_factor,
                'direction_factor': direction_factor,
                'confidence_factor': confidence
            }

        except Exception as e:
            log(f"Error in calculate_threat_level: {e}", "ERROR")
            return {
                'threat_level': 0,
                'category': 'UNKNOWN',
                'color': (128, 128, 128),
                'base_threat': 0,
                'distance_factor': 1.0,
                'direction_factor': 1.0,
                'confidence_factor': 1.0
            }

    def _get_direction_factor(self, angle):
        """
        Get direction threat multiplier based on angle

        Radar coordinates: 0° = top, 90° = right, 180° = bottom, 270° = left
        Player faces forward (top), so rear is bottom (180°)
        """
        # Normalize angle to 0-360
        angle = angle % 360

        # Front zone: 315-45° (top of radar)
        if (angle >= 315 or angle < 45):
            return self.direction_zones['front']

        # Rear zone: 135-225° (bottom of radar - behind player)
        elif 135 <= angle < 225:
            return self.direction_zones['rear']

        # Side zones: 45-135° (right) or 225-315° (left)
        else:
            return self.direction_zones['side']

    def rank_targets(self, targets):
        """
        Rank list of targets by threat priority

        Returns: list of targets sorted by threat level (highest first)
        """
        try:
            if not targets:
                return []

            # Calculate threat for each target
            for target in targets:
                threat_info = self.calculate_threat_level(target)
                target.update(threat_info)

            # Sort by threat level (descending)
            ranked = sorted(targets, key=lambda t: t.get('threat_level', 0), reverse=True)

            return ranked

        except Exception as e:
            log(f"Error in rank_targets: {e}", "ERROR")
            return targets

