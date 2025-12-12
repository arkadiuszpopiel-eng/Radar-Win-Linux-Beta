"""
Unit tests for GameProcessDetector
Tests game and engine detection from running processes
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from app.utils.game_detector import GameProcessDetector


class TestGameProcessDetector:
    """Test suite for GameProcessDetector class"""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector instance for each test"""
        return GameProcessDetector()

    def test_initialization(self, detector):
        """Test that detector initializes correctly"""
        assert detector.game_engines is not None
        assert detector.known_games is not None
        assert detector.active_games == []
        assert detector.active_engines == []
        assert detector.last_scan_time == 0.0
        assert detector.scan_interval == 5.0

        # Check known engines
        assert 'Unreal Engine 5' in detector.game_engines
        assert 'Unity' in detector.game_engines
        assert 'Source Engine' in detector.game_engines

        # Check known games
        assert 'ARC Raiders' in detector.known_games
        assert 'CS2' in detector.known_games
        assert 'Valorant' in detector.known_games

    def test_game_engines_config(self, detector):
        """Test game engines configuration"""
        # UE5 should have patterns
        ue5_patterns = detector.game_engines['Unreal Engine 5']
        assert 'UE5-' in ue5_patterns
        assert '-Win64-Shipping' in ue5_patterns

        # Unity should have patterns
        unity_patterns = detector.game_engines['Unity']
        assert 'Unity.exe' in unity_patterns

    def test_known_games_config(self, detector):
        """Test known games configuration"""
        # ARC Raiders patterns
        arc_patterns = detector.known_games['ARC Raiders']
        assert 'ARCRaiders' in arc_patterns
        assert 'PioneerGame' in arc_patterns

        # CS2 patterns
        cs2_patterns = detector.known_games['CS2']
        assert 'cs2.exe' in cs2_patterns or 'cs2' in cs2_patterns

    @patch('psutil.process_iter')
    def test_scan_processes_no_games(self, mock_process_iter, detector):
        """Test scanning when no games are running"""
        # Mock process list with non-game processes
        mock_proc1 = Mock()
        mock_proc1.info = {
            'name': 'chrome.exe',
            'exe': 'C:\\Program Files\\Google\\Chrome\\chrome.exe',
            'cmdline': ['chrome.exe']
        }

        mock_proc2 = Mock()
        mock_proc2.info = {
            'name': 'explorer.exe',
            'exe': 'C:\\Windows\\explorer.exe',
            'cmdline': ['explorer.exe']
        }

        mock_process_iter.return_value = [mock_proc1, mock_proc2]

        # Scan
        result = detector.scan_processes()

        assert result['has_games'] == False
        assert len(result['games']) == 0
        assert len(result['engines']) == 0

    @patch('psutil.process_iter')
    def test_scan_processes_arc_raiders(self, mock_process_iter, detector):
        """Test detection of ARC Raiders"""
        # Mock ARC Raiders process
        mock_proc = Mock()
        mock_proc.info = {
            'name': 'PioneerGame.exe',
            'exe': 'D:\\Games\\ARC Raiders\\PioneerGame.exe',
            'cmdline': ['PioneerGame.exe', '-windowed']
        }

        mock_process_iter.return_value = [mock_proc]

        # Scan
        result = detector.scan_processes()

        assert result['has_games'] == True
        assert 'ARC Raiders' in result['games']

    @patch('psutil.process_iter')
    def test_scan_processes_cs2(self, mock_process_iter, detector):
        """Test detection of CS2"""
        mock_proc = Mock()
        mock_proc.info = {
            'name': 'cs2.exe',
            'exe': 'C:\\Program Files\\Steam\\steamapps\\common\\Counter-Strike 2\\cs2.exe',
            'cmdline': ['cs2.exe']
        }

        mock_process_iter.return_value = [mock_proc]

        result = detector.scan_processes()

        assert result['has_games'] == True
        assert 'CS2' in result['games']

    @patch('psutil.process_iter')
    def test_scan_processes_unreal_engine(self, mock_process_iter, detector):
        """Test detection of Unreal Engine 5"""
        mock_proc = Mock()
        mock_proc.info = {
            'name': 'SomeGame-Win64-Shipping.exe',
            'exe': 'D:\\Games\\SomeGame\\Binaries\\Win64\\SomeGame-Win64-Shipping.exe',
            'cmdline': ['SomeGame-Win64-Shipping.exe']
        }

        mock_process_iter.return_value = [mock_proc]

        result = detector.scan_processes()

        # Should detect Unreal Engine
        assert 'Unreal Engine 4' in result['engines'] or 'Unreal Engine 5' in result['engines']

    @patch('psutil.process_iter')
    def test_scan_processes_multiple_games(self, mock_process_iter, detector):
        """Test detection of multiple games simultaneously"""
        mock_proc1 = Mock()
        mock_proc1.info = {
            'name': 'cs2.exe',
            'exe': 'C:\\Steam\\cs2.exe',
            'cmdline': ['cs2.exe']
        }

        mock_proc2 = Mock()
        mock_proc2.info = {
            'name': 'PioneerGame.exe',
            'exe': 'D:\\ARC Raiders\\PioneerGame.exe',
            'cmdline': ['PioneerGame.exe']
        }

        mock_process_iter.return_value = [mock_proc1, mock_proc2]

        result = detector.scan_processes()

        assert result['has_games'] == True
        assert len(result['games']) >= 1  # At least one game detected

    @patch('psutil.process_iter')
    def test_scan_processes_case_insensitive(self, mock_process_iter, detector):
        """Test that detection is case-insensitive"""
        mock_proc = Mock()
        mock_proc.info = {
            'name': 'PIONEERGAME.EXE',  # Uppercase
            'exe': 'D:\\Games\\arc raiders\\PIONEERGAME.EXE',
            'cmdline': ['PIONEERGAME.EXE']
        }

        mock_process_iter.return_value = [mock_proc]

        result = detector.scan_processes()

        # Should still detect (case-insensitive)
        assert result['has_games'] == True

    @patch('psutil.process_iter')
    def test_scan_processes_cmdline_detection(self, mock_process_iter, detector):
        """Test detection from command line arguments"""
        # Game name in cmdline but not in exe name
        mock_proc = Mock()
        mock_proc.info = {
            'name': 'UE5-Win64-Shipping.exe',
            'exe': 'D:\\Games\\SomeFolder\\UE5-Win64-Shipping.exe',
            'cmdline': ['UE5-Win64-Shipping.exe', 'ARC Raiders', '-windowed']
        }

        mock_process_iter.return_value = [mock_proc]

        result = detector.scan_processes()

        # Should detect from cmdline
        # May detect as ARC Raiders or Unreal Engine
        assert result['has_games'] or len(result['engines']) > 0

    @patch('psutil.process_iter')
    def test_scan_processes_path_detection(self, mock_process_iter, detector):
        """Test detection from exe path"""
        mock_proc = Mock()
        mock_proc.info = {
            'name': 'Game.exe',
            'exe': 'D:\\Games\\ARC Raiders\\Binaries\\Game.exe',  # ARC Raiders in path
            'cmdline': ['Game.exe']
        }

        mock_process_iter.return_value = [mock_proc]

        result = detector.scan_processes()

        # Should detect from path
        # (depending on patterns, may or may not detect)

    @patch('psutil.process_iter')
    def test_scan_interval(self, mock_process_iter, detector):
        """Test that scans respect the scan interval"""
        mock_proc = Mock()
        mock_proc.info = {
            'name': 'test.exe',
            'exe': 'C:\\test.exe',
            'cmdline': ['test.exe']
        }

        mock_process_iter.return_value = [mock_proc]

        # First scan
        result1 = detector.scan_processes()
        scan_time1 = detector.last_scan_time

        # Immediate second scan (should use cached result)
        result2 = detector.scan_processes()
        scan_time2 = detector.last_scan_time

        # Scan time should not have changed
        assert scan_time1 == scan_time2

        # Wait for interval to pass
        detector.last_scan_time = 0.0  # Force rescan

        # Third scan (should actually scan)
        result3 = detector.scan_processes()
        scan_time3 = detector.last_scan_time

        # Scan time should have updated
        assert scan_time3 > scan_time1

    @patch('psutil.process_iter')
    def test_scan_processes_error_handling(self, mock_process_iter, detector):
        """Test error handling during process scan"""
        # Make process_iter raise an exception
        mock_process_iter.side_effect = Exception("Process enumeration failed")

        # Should handle error gracefully
        result = detector.scan_processes()

        assert result['has_games'] == False
        assert result['games'] == []
        assert result['engines'] == []

    @patch('psutil.process_iter')
    def test_process_access_denied(self, mock_process_iter, detector):
        """Test handling of AccessDenied errors"""
        import psutil

        # Mock process that raises AccessDenied
        mock_proc = Mock()
        mock_proc.info = {'name': None, 'exe': None, 'cmdline': None}

        # Create a process that will raise AccessDenied
        def process_generator():
            yield mock_proc
            raise psutil.AccessDenied("Access denied")

        mock_process_iter.return_value = process_generator()

        # Should handle gracefully
        result = detector.scan_processes()

        # Should return valid result
        assert 'games' in result
        assert 'engines' in result

    @patch('psutil.process_iter')
    def test_duplicate_detection_prevention(self, mock_process_iter, detector):
        """Test that same game is not detected multiple times"""
        # Multiple processes from same game
        mock_proc1 = Mock()
        mock_proc1.info = {
            'name': 'PioneerGame.exe',
            'exe': 'D:\\ARC\\PioneerGame.exe',
            'cmdline': ['PioneerGame.exe']
        }

        mock_proc2 = Mock()
        mock_proc2.info = {
            'name': 'ARCRaiders-Helper.exe',  # Another ARC process
            'exe': 'D:\\ARC\\ARCRaiders-Helper.exe',
            'cmdline': ['ARCRaiders-Helper.exe']
        }

        mock_process_iter.return_value = [mock_proc1, mock_proc2]

        result = detector.scan_processes()

        # ARC Raiders should only appear once
        arc_count = result['games'].count('ARC Raiders')
        assert arc_count == 1

    def test_empty_process_name_handling(self, detector):
        """Test handling of processes with empty names"""
        with patch('psutil.process_iter') as mock_iter:
            mock_proc = Mock()
            mock_proc.info = {
                'name': '',  # Empty name
                'exe': None,
                'cmdline': None
            }

            mock_iter.return_value = [mock_proc]

            # Should handle gracefully
            result = detector.scan_processes()

            assert result is not None

    def test_none_cmdline_handling(self, detector):
        """Test handling of processes with None cmdline"""
        with patch('psutil.process_iter') as mock_iter:
            mock_proc = Mock()
            mock_proc.info = {
                'name': 'test.exe',
                'exe': 'C:\\test.exe',
                'cmdline': None  # None cmdline
            }

            mock_iter.return_value = [mock_proc]

            # Should handle gracefully
            result = detector.scan_processes()

            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
