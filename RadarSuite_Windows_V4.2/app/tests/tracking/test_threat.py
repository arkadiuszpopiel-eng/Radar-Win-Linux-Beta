"""
RadarSuite v3.5.0 - Point 12: Threat Priority System Tests
Tests for tracking/threat.py
"""

from tests.compat import pytest
from tracking.threat import ThreatPrioritySystem


class TestThreatPrioritySystem:
    """Test suite for ThreatPrioritySystem class"""

    def test_initialization(self):
        """Test ThreatPrioritySystem initialization"""
        threat_system = ThreatPrioritySystem()

        assert hasattr(threat_system, 'threat_scores')
        assert hasattr(threat_system, 'direction_zones')
        assert isinstance(threat_system.threat_scores, dict)
        assert isinstance(threat_system.direction_zones, dict)

    def test_threat_scores_defined(self):
        """Test that threat scores are defined for common types"""
        threat_system = ThreatPrioritySystem()

        # Weapons should have scores
        assert 'sniper' in threat_system.threat_scores
        assert 'rifle' in threat_system.threat_scores
        assert 'pistol' in threat_system.threat_scores
        assert 'shot' in threat_system.threat_scores

        # Humans should have scores
        assert 'footstep' in threat_system.threat_scores
        assert 'voice' in threat_system.threat_scores

        # Unknown should have score
        assert 'unknown' in threat_system.threat_scores

    def test_threat_scores_ranking(self):
        """Test that weapons have higher threat than footsteps"""
        threat_system = ThreatPrioritySystem()

        # Weapons should be more threatening than footsteps
        assert threat_system.threat_scores['sniper'] > threat_system.threat_scores['footstep']
        assert threat_system.threat_scores['rifle'] > threat_system.threat_scores['voice']
        assert threat_system.threat_scores['shot'] > threat_system.threat_scores['unknown']

    def test_calculate_threat_level_basic(self):
        """Test basic threat level calculation"""
        threat_system = ThreatPrioritySystem()

        target = {
            'type': 'rifle',
            'angle': 90,
            'distance': 30,
            'confidence': 100
        }

        result = threat_system.calculate_threat_level(target)

        assert 'threat_level' in result
        assert 'category' in result
        assert 'color' in result
        assert 0 <= result['threat_level'] <= 100

    def test_distance_affects_threat(self):
        """Test that closer targets are more threatening"""
        threat_system = ThreatPrioritySystem()

        # Close target
        close_target = {
            'type': 'rifle',
            'angle': 90,
            'distance': 10,
            'confidence': 100
        }

        # Far target
        far_target = {
            'type': 'rifle',
            'angle': 90,
            'distance': 80,
            'confidence': 100
        }

        close_threat = threat_system.calculate_threat_level(close_target)
        far_threat = threat_system.calculate_threat_level(far_target)

        assert close_threat['threat_level'] > far_threat['threat_level']

    def test_type_affects_threat(self):
        """Test that weapon type affects threat level"""
        threat_system = ThreatPrioritySystem()

        # Sniper (high threat)
        sniper_target = {
            'type': 'sniper',
            'angle': 90,
            'distance': 30,
            'confidence': 100
        }

        # Footstep (lower threat)
        footstep_target = {
            'type': 'footstep',
            'angle': 90,
            'distance': 30,
            'confidence': 100
        }

        sniper_threat = threat_system.calculate_threat_level(sniper_target)
        footstep_threat = threat_system.calculate_threat_level(footstep_target)

        assert sniper_threat['threat_level'] > footstep_threat['threat_level']

    def test_direction_affects_threat(self):
        """Test that rear threats are more dangerous than front"""
        threat_system = ThreatPrioritySystem()

        # Front target
        front_target = {
            'type': 'rifle',
            'angle': 0,  # Front
            'distance': 30,
            'confidence': 100
        }

        # Rear target
        rear_target = {
            'type': 'rifle',
            'angle': 180,  # Rear
            'distance': 30,
            'confidence': 100
        }

        front_threat = threat_system.calculate_threat_level(front_target)
        rear_threat = threat_system.calculate_threat_level(rear_target)

        assert rear_threat['threat_level'] > front_threat['threat_level']

    def test_confidence_affects_threat(self):
        """Test that confidence affects threat level"""
        threat_system = ThreatPrioritySystem()

        # High confidence
        high_conf_target = {
            'type': 'rifle',
            'angle': 90,
            'distance': 30,
            'confidence': 100
        }

        # Low confidence
        low_conf_target = {
            'type': 'rifle',
            'angle': 90,
            'distance': 30,
            'confidence': 20
        }

        high_conf_threat = threat_system.calculate_threat_level(high_conf_target)
        low_conf_threat = threat_system.calculate_threat_level(low_conf_target)

        assert high_conf_threat['threat_level'] > low_conf_threat['threat_level']

    def test_threat_categories(self):
        """Test threat categorization"""
        threat_system = ThreatPrioritySystem()

        # Very high threat
        critical_target = {
            'type': 'sniper',
            'angle': 180,  # Rear
            'distance': 10,
            'confidence': 100
        }

        # Very low threat
        minimal_target = {
            'type': 'unknown',
            'angle': 0,
            'distance': 90,
            'confidence': 30
        }

        critical_threat = threat_system.calculate_threat_level(critical_target)
        minimal_threat = threat_system.calculate_threat_level(minimal_target)

        # Critical should be high threat
        assert critical_threat['category'] in ['CRITICAL', 'HIGH']

        # Minimal should be low threat
        assert minimal_threat['category'] in ['LOW', 'MINIMAL']

    def test_threat_colors(self):
        """Test that threat colors are RGB tuples"""
        threat_system = ThreatPrioritySystem()

        target = {
            'type': 'rifle',
            'angle': 90,
            'distance': 30,
            'confidence': 100
        }

        result = threat_system.calculate_threat_level(target)

        assert isinstance(result['color'], tuple)
        assert len(result['color']) == 3
        # All RGB values should be 0-255
        assert all(0 <= c <= 255 for c in result['color'])

    def test_threat_level_clamped(self):
        """Test that threat level is clamped to 0-100"""
        threat_system = ThreatPrioritySystem()

        # Extreme high threat scenario
        extreme_target = {
            'type': 'sniper',
            'angle': 180,
            'distance': 1,
            'confidence': 100
        }

        result = threat_system.calculate_threat_level(extreme_target)

        assert 0 <= result['threat_level'] <= 100

    def test_unknown_type_defaults(self):
        """Test handling of unknown sound types"""
        threat_system = ThreatPrioritySystem()

        target = {
            'type': 'completely_unknown_type',
            'angle': 90,
            'distance': 30,
            'confidence': 100
        }

        result = threat_system.calculate_threat_level(target)

        # Should not crash and should return valid result
        assert 'threat_level' in result
        assert result['threat_level'] >= 0

    def test_missing_fields_defaults(self):
        """Test handling of missing fields in target dict"""
        threat_system = ThreatPrioritySystem()

        # Minimal target with missing fields
        target = {'type': 'rifle'}

        result = threat_system.calculate_threat_level(target)

        # Should use defaults and not crash
        assert 'threat_level' in result
        assert result['threat_level'] >= 0

    def test_get_direction_factor_front(self):
        """Test direction factor for front zone"""
        threat_system = ThreatPrioritySystem()

        front_angles = [0, 30, 330, 350]

        for angle in front_angles:
            factor = threat_system._get_direction_factor(angle)
            assert factor == threat_system.direction_zones['front']

    def test_get_direction_factor_rear(self):
        """Test direction factor for rear zone"""
        threat_system = ThreatPrioritySystem()

        rear_angles = [180, 200, 160, 220]

        for angle in rear_angles:
            factor = threat_system._get_direction_factor(angle)
            assert factor == threat_system.direction_zones['rear']

    def test_get_direction_factor_side(self):
        """Test direction factor for side zones"""
        threat_system = ThreatPrioritySystem()

        side_angles = [90, 270]

        for angle in side_angles:
            factor = threat_system._get_direction_factor(angle)
            assert factor == threat_system.direction_zones['side']

    def test_direction_zones_multipliers(self):
        """Test that rear is more dangerous than front"""
        threat_system = ThreatPrioritySystem()

        assert threat_system.direction_zones['rear'] > threat_system.direction_zones['front']
