"""
Unit tests for AudioEngine
Tests audio capture and device management
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from app.audio.engine import AudioEngine


class TestAudioEngine:
    """Test suite for AudioEngine class"""

    @pytest.fixture
    def engine(self):
        """Create a fresh engine instance"""
        return AudioEngine()

    def test_initialization(self, engine):
        """Test engine initialization"""
        assert engine.sample_rate == 48000
        assert engine.blocksize == 2048
        assert engine.channels == 2
        assert engine.device is None
        assert engine.stream is None
        assert engine.queue is not None
        assert engine.last_block is None
        assert engine.running == False
        assert engine.backend == "sounddevice"
        assert engine.use_loopback == False

    @patch('app.audio.engine.sd')
    def test_list_devices_sounddevice(self, mock_sd, engine):
        """Test listing sounddevice devices"""
        # Mock sounddevice devices
        mock_devices = [
            {
                'name': 'Microphone (USB)',
                'max_input_channels': 2,
                'max_output_channels': 0,
                'default_samplerate': 48000.0,
                'hostapi': 0
            },
            {
                'name': 'Speakers (Realtek)',
                'max_input_channels': 0,
                'max_output_channels': 2,
                'default_samplerate': 48000.0,
                'hostapi': 0
            }
        ]

        mock_sd.query_devices.return_value = mock_devices
        mock_sd.query_hostapis.return_value = {'name': 'MME'}

        devices = engine.list_devices()

        assert len(devices) >= 2
        assert devices[0]['name'] == 'Microphone (USB)'
        assert devices[0]['type'] == 'input'
        assert devices[0]['backend'] == 'sounddevice'

    @patch('app.audio.engine.sd', None)
    @patch('app.audio.engine.sc')
    def test_list_devices_soundcard(self, mock_sc, engine):
        """Test listing soundcard loopback devices"""
        # Mock soundcard speaker
        mock_speaker = Mock()
        mock_speaker.name = 'CABLE Output'
        mock_speaker.channels = 2

        mock_sc.all_speakers.return_value = [mock_speaker]

        devices = engine.list_devices()

        assert len(devices) >= 1
        assert 'Loopback' in devices[0]['name']
        assert devices[0]['type'] == 'loopback'
        assert devices[0]['backend'] == 'soundcard'

    @patch('app.audio.engine.sd', None)
    @patch('app.audio.engine.sc', None)
    def test_list_devices_no_backends(self, engine):
        """Test listing devices when no backends available"""
        devices = engine.list_devices()

        # Should return empty list
        assert devices == []

    @patch('app.audio.engine.sd')
    def test_list_devices_error_handling(self, mock_sd, engine):
        """Test error handling when listing devices fails"""
        mock_sd.query_devices.side_effect = Exception("Device query failed")

        # Should handle error gracefully
        devices = engine.list_devices()

        # May return empty or partial list
        assert isinstance(devices, list)

    def test_queue_initialization(self, engine):
        """Test audio queue initialization"""
        assert engine.queue is not None
        assert engine.queue.maxsize == 8
        assert engine.queue.empty()

    def test_start_when_already_running(self, engine):
        """Test starting engine when already running"""
        engine.running = True

        # Should return without error
        engine.start()

        # Still running
        assert engine.running == True

    def test_default_settings(self, engine):
        """Test default audio settings"""
        assert engine.sample_rate == 48000
        assert engine.blocksize == 2048
        assert engine.channels == 2

    def test_backend_selection(self, engine):
        """Test backend selection"""
        # Default backend
        assert engine.backend == "sounddevice"

        # Can switch to loopback
        engine.use_loopback = True
        assert engine.use_loopback == True

    def test_device_configuration(self, engine):
        """Test device configuration"""
        # Initially None
        assert engine.device is None

        # Can be set
        engine.device = 1
        assert engine.device == 1

    def test_queue_size(self, engine):
        """Test queue size limit"""
        assert engine.queue.maxsize == 8

    @patch('app.audio.engine.sd')
    def test_sounddevice_availability_check(self, mock_sd, engine):
        """Test checking sounddevice availability"""
        devices = engine.list_devices()

        # Should query sounddevice
        mock_sd.query_devices.assert_called()

    def test_last_block_initially_none(self, engine):
        """Test that last_block is initially None"""
        assert engine.last_block is None

    def test_sample_rate_configuration(self, engine):
        """Test sample rate configuration"""
        engine.sample_rate = 44100
        assert engine.sample_rate == 44100

        engine.sample_rate = 96000
        assert engine.sample_rate == 96000

    def test_blocksize_configuration(self, engine):
        """Test blocksize configuration"""
        engine.blocksize = 1024
        assert engine.blocksize == 1024

        engine.blocksize = 4096
        assert engine.blocksize == 4096

    def test_channels_configuration(self, engine):
        """Test channels configuration"""
        engine.channels = 1  # Mono
        assert engine.channels == 1

        engine.channels = 2  # Stereo
        assert engine.channels == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
