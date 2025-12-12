# RadarSuite V4.2.0 - ARC Raiders Edition

## Overview

RadarSuite V4.2.0 is specifically optimized for **ARC Raiders** audio detection, based on detailed analysis of the game's FMOD + Unreal Engine 5 audio system.

## Key Features

### 1. **48 kHz Audio Processing**
- Native sample rate for FMOD + UE5 (console/PC standard)
- Optimized for ARC Raiders' multi-distance recording system
- Full 5.1/7.1 surround downmix support

### 2. **Advanced Spectral Analysis**
- **MFCC (Mel-Frequency Cepstral Coefficients)**: 13-coefficient extraction for sound classification
- **Spectral Features**: Centroid, roll-off, flatness for texture analysis
- **Band Energy Ratios**: Bass/mid/high analysis for sound categorization

### 3. **Shot & Explosion Detection**
Enhanced classification system:
- **Close Shots** (< 30m): High crest factor, bright spectrum, sharp transient
- **Distant Shots** (> 30m): Softer transient, rolled-off highs, more reverb
- **Explosions**: Wide spectrum, strong bass (> 30% energy < 200 Hz), long tail
- **Weapon Type**: Rifle, pistol, shotgun, sniper classification

### 4. **Surface Type Detection**
Footstep surface classification using spectral analysis:
- **Metal**: High spectral centroid (~400 Hz peak), bright, ringing
- **Dirt/Earth**: Mid-low centroid (~200 Hz peak), dull, thuddy
- **Snow**: Low centroid (~150 Hz peak), muffled, soft
- **Concrete**: Balanced spectrum, sharp transient
- **Wood**: Mid-range emphasis, resonant

### 5. **ARC Machine State Detection**
Detects and classifies ARC machine states based on sound patterns:
- **Idle**: Low modulation (5-15%), steady hum
- **Patrol**: Medium modulation (15-30%), rhythmic movement
- **Search**: Higher modulation (30-50%), irregular scanning
- **Combat**: High modulation (50-100%), aggressive sounds

Uses bass envelope analysis (50-300 Hz) and temporal modulation detection.

### 6. **Walk/Run Classification**
Improved gait detection:
- **Walk**: 1.5-2.5 steps/sec (~0.6s interval)
- **Run**: 3.0-4.5 steps/sec (~0.3s interval)
- Interval tolerance: ±0.15s for natural variation

## Technical Details

### Audio Engine
- **Sample Rate**: 48,000 Hz
- **Block Size**: 2048 samples (~42.7 ms @ 48 kHz)
- **Channels**: Stereo (downmix from 5.1/7.1)

### Detection Parameters

#### Transient Detection
- Window: 10 ms
- Threshold Ratio: 3.0 (Peak/RMS)
- Attack Time: 20 ms

#### Spectral Features
- MFCC Coefficients: 13
- Mel Bands: 40
- Frequency Range: 20 Hz - 8000 Hz

#### Shot Detection
- Frequency Range: 200 Hz - 8000 Hz
- Bass Threshold (explosions): 30% energy < 200 Hz
- Close Shot Distance: < 30 meters

#### Footstep Detection
- Frequency Range: 100 Hz - 800 Hz
- Surface peak frequencies:
  - Metal: 400 Hz
  - Dirt: 200 Hz
  - Snow: 150 Hz

#### Machine Detection
- Bass Range: 50 Hz - 300 Hz
- Detection Window: 2.0 seconds
- Modulation Threshold: 10%

## New Modules

### `detection/spectral.py`
**SpectralFeatureExtractor** class for advanced audio analysis:
- `extract_mfcc()`: MFCC coefficient extraction
- `extract_spectral_centroid()`: Center of mass of spectrum
- `extract_spectral_rolloff()`: 85% energy threshold frequency
- `extract_spectral_flatness()`: Noisiness measure (0-1)
- `extract_band_energy_ratio()`: Energy in specific frequency bands
- `extract_all_features()`: Complete feature set extraction

### `detection/shot.py`
**ShotDetector** class for weapon fire detection:
- `detect_transient()`: Sharp onset detection
- `classify_shot_type()`: Close/distant/explosion classification
- Weapon type identification (rifle/pistol/shotgun/sniper/explosive)
- Distance estimation based on spectral characteristics

### `detection/machine.py`
**ARCMachineDetector** class for machine detection:
- `extract_bass_envelope()`: Low-frequency mechanical sound analysis
- `analyze_modulation()`: Temporal modulation pattern detection
- `classify_machine_state()`: Idle/patrol/search/combat classification
- `get_dominant_state()`: Most frequent state from history

### Enhanced `detection/footstep.py`
**HumanFootstepDetector** with new features:
- `classify_surface_type()`: Metal/dirt/snow/concrete/wood detection
- Integration with SpectralFeatureExtractor
- Improved walk/run distinction using interval analysis

## ARC Raiders Game Integration

Based on official documentation and analysis:

### Audio Middleware
- **FMOD Studio**: Event-based audio system
- **Unreal Engine 5**: Native spatial audio
- **Platform**: PC/PS5/Xbox Series X|S (48 kHz standard)

### Sound Design Philosophy
From official "Soundscapes of ARC Raiders" blog:
- Multi-distance recordings (close/distant layers)
- Procedural audio logic (hundreds of rules)
- Surface-aware footsteps (material detection)
- Machine state-dependent sounds
- Equipment/backpack weight affects sound

### Night Mode Support
Simulated compression for enhanced quiet sound detection:
- Compression Ratio: 4:1
- Quiet sounds (footsteps) boosted
- Loud sounds (explosions) reduced
- Better competitive gameplay balance

## Usage Example

```python
from detection import (
    SpectralFeatureExtractor,
    ShotDetector,
    HumanFootstepDetector,
    ARCMachineDetector
)

# Initialize detectors
spectral = SpectralFeatureExtractor(sample_rate=48000)
shot_detector = ShotDetector(sample_rate=48000)
footstep_detector = HumanFootstepDetector(sample_rate=48000)
machine_detector = ARCMachineDetector(sample_rate=48000)

# Process audio block
audio_block = capture_audio()  # Your audio capture

# Detect shots
shot_result = shot_detector.detect(audio_block)
if shot_result:
    print(f"Shot detected: {shot_result['type']} at ~{shot_result['distance_estimate']}m")
    print(f"Weapon: {shot_result['weapon_type']}, Confidence: {shot_result['confidence']}%")

# Detect footsteps with surface type
footstep_result = footstep_detector.analyze_footstep(audio_block, sample_rate=48000)
if footstep_result['is_human_step']:
    print(f"Footstep: {footstep_result['gait_type']} on {footstep_result['surface']}")
    print(f"Distance: {footstep_result['distance_m']:.1f}m, Confidence: {footstep_result['confidence']:.0f}%")

# Detect machines
machine_result = machine_detector.detect(audio_block)
if machine_result:
    print(f"Machine detected: {machine_result['state']} state")
    print(f"Confidence: {machine_result['confidence']}%, Modulation: {machine_result['modulation_depth']:.2f}")
```

## Performance Optimizations

### Computational Efficiency
- FFT caching for multiple feature extractions
- Mel filterbank pre-computed at initialization
- Efficient numpy operations for spectral analysis
- History-based temporal analysis (minimal overhead)

### Detection Accuracy
- Adaptive noise floor estimation (V4.1.2)
- Type-aware target matching (V4.1.2)
- Spectral feature-based classification (V4.2.0)
- Multi-window temporal analysis (V4.2.0)

## Known Limitations

### Vertical Positioning (Z-axis)
ARC Raiders currently has issues with vertical audio positioning - sounds from different floors may appear to be on the same level. This is a game bug, not a detection limitation.

### Bluetooth Audio Switching
When switching to Bluetooth headphones, re-run "Quick Setup" to reconfigure the audio input device.

### Classification Accuracy
- Surface type detection requires clear, isolated footstep sounds
- Machine state detection needs ~2 seconds of sustained audio
- Shot classification accuracy decreases with distance (> 100m)

## Future Enhancements

- [ ] Neural network-based classification (CNN on mel-spectrograms)
- [ ] LSTM/Transformer for temporal sequence modeling
- [ ] Real-time FMOD event hooking (requires game modding)
- [ ] Multi-target tracking with Kalman filtering
- [ ] Vertical audio position estimation (when game bug is fixed)

## Credits

### Based On
- V4.1 detection improvements
- ARC Raiders official soundscape documentation
- FMOD + UE5 audio analysis
- Community feedback and testing

### References
1. "The Soundscapes of ARC Raiders" - Official Blog
2. FMOD Studio Documentation
3. Unreal Engine 5 Audio System
4. Spectral Audio Signal Processing (SASP)

## Version History

### V4.2.0 (2025-11-28)
- Added MFCC and spectral feature extraction
- Implemented shot/explosion classification (close/distant)
- Added surface type detection for footsteps
- Created ARC machine state detector
- Updated to 48 kHz sample rate (FMOD/UE5 standard)
- Enhanced walk/run classification

### V4.1.2 (Previous)
- Adaptive noise floor estimation
- Auto-detection of channel count (5.1/7.1)
- Transient detection for weapon classification
- Type-aware target tracking
- Detached window cleanup

## License

Proprietary - For use with ARC Raiders audio radar system only.
