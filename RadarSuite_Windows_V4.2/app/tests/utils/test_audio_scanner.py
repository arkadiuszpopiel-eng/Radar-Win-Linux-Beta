"""
Unit tests for AudioSourceScanner
Tests audio source scanning and device enumeration
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from app.utils.audio_scanner import AudioSourceScanner


class TestAudioSourceScanner:
    """Test suite for AudioSourceScanner class"""

    @pytest.fixture
    def scanner(self):
        """Create a fresh scanner instance for each test"""
        return AudioSourceScanner()

    @pytest.fixture
    def scanner_with_platform(self):
        """Create scanner with mock platform detector"""
        platform_detector = Mock()
        return AudioSourceScanner(platform_detector=platform_detector)

    def test_initialization(self, scanner):
        """Test that scanner initializes correctly"""
        assert scanner.active_sources == []
        assert scanner.inactive_sources == []
        assert scanner.last_scan_time == 0.0
        assert scanner.scan_interval == 2.0
        assert scanner.platform_detector is None

    def test_initialization_with_platform_detector(self, scanner_with_platform):
        """Test initialization with platform detector"""
        assert scanner_with_platform.platform_detector is not None

    @patch('app.utils.audio_scanner.sd')
    def test_scan_audio_sources_no_devices(self, mock_sd, scanner):
        """Test scanning when no audio devices available"""
        mock_sd.query_devices.return_value = []

        result = scanner.scan_audio_sources()

        assert 'active' in result
        assert 'inactive' in result
        assert 'total' in result
        assert result['total'] == 0

    @patch('app.utils.audio_scanner.sd')
    def test_scan_audio_sources_with_devices(self, mock_sd, scanner):
        """Test scanning with available devices"""
        # Mock sounddevice devices
        mock_devices = [
            {
                'name': 'Microphone (USB)',
                'max_input_channels': 2,
                'max_output_channels': 0,
                'default_samplerate': 48000.0
            },
            {
                'name': 'Speakers (Realtek)',
                'max_input_channels': 0,
                'max_output_channels': 2,
                'default_samplerate': 48000.0
            }
        ]

        mock_sd.query_devices.return_value = mock_devices

        result = scanner.scan_audio_sources()

        assert result['total'] > 0
        assert len(result['active']) + len(result['inactive']) > 0

    @patch('app.utils.audio_scanner.sd')
    def test_scan_interval(self, mock_sd, scanner):
        """Test that scans respect the scan interval"""
        mock_sd.query_devices.return_value = []

        # First scan
        result1 = scanner.scan_audio_sources()
        scan_time1 = scanner.last_scan_time

        # Immediate second scan (should use cached result)
        result2 = scanner.scan_audio_sources()
        scan_time2 = scanner.last_scan_time

        # Scan time should not have changed
        assert scan_time1 == scan_time2

        # Wait for interval to pass
        scanner.last_scan_time = 0.0  # Force rescan

        # Third scan (should actually scan)
        result3 = scanner.scan_audio_sources()
        scan_time3 = scanner.last_scan_time

        # Scan time should have updated
        assert scan_time3 > scan_time1

    @patch('app.utils.audio_scanner.sd')
    def test_input_device_classification(self, mock_sd, scanner):
        """Test classification of input devices"""
        mock_devices = [
            {
                'name': 'Microphone',
                'max_input_channels': 2,
                'max_output_channels': 0,
                'default_samplerate': 48000.0
            }
        ]

        mock_sd.query_devices.side_effect = [
            mock_devices,  # First call returns device list
            mock_devices[0]  # Second call returns default device
        ]

        result = scanner.scan_audio_sources()

        # Input device should be classified
        assert result['total'] > 0

    @patch('app.utils.audio_scanner.sd')
    def test_output_device_classification(self, mock_sd, scanner):
        """Test classification of output devices"""
        mock_devices = [
            {
                'name': 'Speakers',
                'max_input_channels': 0,
                'max_output_channels': 2,
                'default_samplerate': 48000.0
            }
        ]

        mock_sd.query_devices.return_value = mock_devices

        result = scanner.scan_audio_sources()

        # Should handle output devices
        assert 'active' in result
        assert 'inactive' in result

    @patch('app.utils.audio_scanner.sd')
    @patch('app.utils.audio_scanner.sc')
    def test_soundcard_loopback_detection(self, mock_sc, mock_sd, scanner):
        """Test detection of soundcard loopback devices"""
        # Mock sounddevice (no devices)
        mock_sd.query_devices.return_value = []

        # Mock soundcard speakers
        mock_speaker = Mock()
        mock_speaker.name = 'CABLE Output (VB-Audio)'
        mock_speaker.id = 'loopback_0'
        mock_speaker.channels = 2

        mock_sc.all_speakers.return_value = [mock_speaker]

        result = scanner.scan_audio_sources()

        # Should detect loopback device
        assert result['total'] > 0
        assert any(dev['backend'] == 'soundcard' for dev in result['active'])

    @patch('app.utils.audio_scanner.sd')
    def test_default_device_detection(self, mock_sd, scanner):
        """Test detection of default audio device"""
        mock_device = {
            'name': 'Default Microphone',
            'max_input_channels': 2,
            'max_output_channels': 0,
            'default_samplerate': 48000.0
        }

        # First call returns device list, second returns default
        mock_sd.query_devices.side_effect = [
            [mock_device],
            mock_device
        ]

        result = scanner.scan_audio_sources()

        # Default device should be in active list
        assert len(result['active']) > 0

    @patch('app.utils.audio_scanner.sd')
    def test_error_handling_sounddevice(self, mock_sd, scanner):
        """Test error handling when sounddevice fails"""
        # Make query_devices raise an error
        mock_sd.query_devices.side_effect = Exception("Device query failed")

        # Should handle error gracefully
        result = scanner.scan_audio_sources()

        assert result['active'] == []
        assert result['inactive'] == []
        assert result['total'] == 0

    @patch('app.utils.audio_scanner.sd')
    def test_scan_audio_sources_overall_error(self, mock_sd, scanner):
        """Test handling of overall scan errors"""
        # Make the entire scan fail
        mock_sd.query_devices.side_effect = RuntimeError("Critical error")

        # Should return empty result
        result = scanner.scan_audio_sources()

        assert 'active' in result
        assert 'inactive' in result
        assert 'total' in result
        assert result['total'] == 0

    @patch('app.utils.audio_scanner.sd')
    def test_device_info_structure(self, mock_sd, scanner):
        """Test structure of device info dictionaries"""
        mock_devices = [
            {
                'name': 'Test Device',
                'max_input_channels': 2,
                'max_output_channels': 0,
                'default_samplerate': 44100.0
            }
        ]

        mock_sd.query_devices.return_value = mock_devices

        result = scanner.scan_audio_sources()

        # Check device info structure
        if len(result['active']) > 0:
            dev = result['active'][0]
            assert 'name' in dev
            assert 'index' in dev
            assert 'channels' in dev
            assert 'samplerate' in dev
            assert 'backend' in dev
            assert 'type' in dev

    @patch('app.utils.audio_scanner.sd', None)
    @patch('app.utils.audio_scanner.sc', None)
    def test_no_audio_libraries_available(self, scanner):
        """Test behavior when no audio libraries are available"""
        # Should handle gracefully
        result = scanner.scan_audio_sources()

        # Should return empty result
        assert result['total'] == 0

    @patch('app.utils.audio_scanner.sd')
    def test_cached_results(self, mock_sd, scanner):
        """Test that results are cached during scan interval"""
        mock_devices = [
            {
                'name': 'Test Device',
                'max_input_channels': 2,
                'max_output_channels': 0,
                'default_samplerate': 48000.0
            }
        ]

        mock_sd.query_devices.return_value = mock_devices

        # First scan
        result1 = scanner.scan_audio_sources()

        # Store active sources
        active_count1 = len(result1['active'])

        # Second scan (within interval, should use cache)
        result2 = scanner.scan_audio_sources()
        active_count2 = len(result2['active'])

        # Should return same cached result
        assert active_count1 == active_count2

    @patch('app.utils.audio_scanner.sc')
    def test_soundcard_error_handling(self, mock_sc, scanner):
        """Test error handling when soundcard library fails"""
        # Make soundcard fail
        mock_sc.all_speakers.side_effect = Exception("Soundcard error")

        # Should handle error gracefully
        result = scanner.scan_audio_sources()

        # Should still return valid result
        assert 'active' in result
        assert 'inactive' in result

    @patch('app.utils.audio_scanner.sd')
    def test_multiple_scans(self, mock_sd, scanner):
        """Test multiple consecutive scans"""
        mock_devices = [
            {
                'name': 'Device 1',
                'max_input_channels': 2,
                'max_output_channels': 0,
                'default_samplerate': 48000.0
            }
        ]

        mock_sd.query_devices.return_value = mock_devices

        # Multiple scans
        for _ in range(5):
            scanner.last_scan_time = 0.0  # Force rescan
            result = scanner.scan_audio_sources()

            assert 'total' in result

    @patch('app.utils.audio_scanner.sd')
    def test_device_type_classification(self, mock_sd, scanner):
        """Test correct classification of device types"""
        mock_devices = [
            {
                'name': 'Input Device',
                'max_input_channels': 2,
                'max_output_channels': 0,
                'default_samplerate': 48000.0
            },
            {
                'name': 'Output Device',
                'max_input_channels': 0,
                'max_output_channels': 2,
                'default_samplerate': 48000.0
            }
        ]

        mock_sd.query_devices.return_value = mock_devices

        result = scanner.scan_audio_sources()

        # Check that devices have correct type field
        all_devices = result['active'] + result['inactive']
        for dev in all_devices:
            assert dev['type'] in ['input', 'output', 'loopback']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
