from app.audio.engine import AudioEngine


def test_deduplicate_devices_merges_backends():
    devices = [
        {
            'backend': 'sounddevice',
            'hostapi': 'MME',
            'index': 0,
            'name': 'Microphone',
        },
        {
            'backend': 'sounddevice',
            'hostapi': 'MME',
            'index': 0,
            'name': 'Microphone',
        },
        {
            'backend': 'soundcard',
            'hostapi': 'soundcard',
            'index': 'loopback_0',
            'name': 'Speakers (Loopback)',
        },
    ]

    unique = AudioEngine._deduplicate_devices(devices)

    assert len(unique) == 2
    backends = {dev['backend'] for dev in unique}
    assert backends == {'sounddevice', 'soundcard'}


def test_deduplicate_devices_respects_backend_and_index():
    devices = [
        {
            'backend': 'sounddevice',
            'hostapi': 'WASAPI',
            'index': 1,
            'name': 'Input A',
        },
        {
            'backend': 'sounddevice',
            'hostapi': 'WASAPI',
            'index': 2,
            'name': 'Input A',
        },
    ]

    unique = AudioEngine._deduplicate_devices(devices)

    # Different index → keep both entries
    assert len(unique) == 2
