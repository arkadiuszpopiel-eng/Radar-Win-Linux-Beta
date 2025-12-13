# Known Issues & Limitations - RadarSuite V4.2.0

Documented limitations, workarounds, and future improvements.

---

## Table of Contents

1. [Game-Specific Issues](#game-specific-issues)
2. [Audio System Limitations](#audio-system-limitations)
3. [Detection Accuracy](#detection-accuracy)
4. [Performance Limitations](#performance-limitations)
5. [Platform Limitations](#platform-limitations)
6. [UI/UX Issues](#uiux-issues)
7. [Planned Improvements](#planned-improvements)

---

## Game-Specific Issues

### ARC Raiders: Vertical Audio Positioning Bug

**Issue:** Sounds from different floors appear at same level

**Cause:** Game bug in ARC Raiders audio system (not RadarSuite)

**Impact:**
- Footsteps from floor above/below shown at player's level
- Cannot distinguish vertical position reliably
- Elevation detection unreliable in multi-story buildings

**Workaround:**
- Use distance estimation (close sounds likely same floor)
- Rely on game's visual cues for vertical position
- Monitor for ARC Raiders audio patches

**Status:** Waiting for game developer fix

---

### ARC Raiders: Loopback Device Detection

**Issue:** Some audio devices not detected in loopback mode

**Cause:** Windows WASAPI restrictions

**Symptoms:**
- "No loopback device found" error
- Stereo Mix disabled by default on some systems
- Virtual audio cables not installed

**Workaround:**
1. **Enable Stereo Mix:**
   - Control Panel → Sound → Recording
   - Right-click → "Show Disabled Devices"
   - Right-click "Stereo Mix" → Enable
   - Set as default device

2. **Install VB-Audio Virtual Cable:**
   - Download: https://vb-audio.com/Cable/
   - Install and restart
   - Use "CABLE Output" as loopback device

3. **Use Sound Blaster Z SE:**
   - Built-in "What U Hear" support
   - Auto-detected by RadarSuite

**Status:** Not fixable in RadarSuite (Windows limitation)

---

## Audio System Limitations

### Bluetooth Audio Switching

**Issue:** Detection fails after switching to Bluetooth headphones

**Cause:** Device ID changes, audio stream not reinitialized

**Symptoms:**
- "No audio device" after Bluetooth connection
- Audio waveform flatlines
- Detection stops working

**Workaround:**
1. Stop detection (press STOP)
2. Tab 2 → Click "Rescan Devices"
3. Select Bluetooth device from dropdown
4. Click "Apply"
5. Press START

**Alternatively:**
- Restart RadarSuite after Bluetooth connection
- Use wired headphones for lowest latency

**Status:** **Planned fix in V4.3.0** - Auto-detect device changes

---

### Multi-Channel Downmix Quality

**Issue:** 5.1/7.1 surround downmix may lose spatial information

**Cause:** Simple stereo downmix (front channels only)

**Impact:**
- Rear surround channels less prominent
- LFE (subwoofer) channel not included
- Slight reduction in localization accuracy for rear sounds

**Workaround:**
- Configure game for stereo output (if possible)
- Use stereo headphones instead of surround

**Status:** **Improvement planned** - Better downmix matrix

---

### Sample Rate Mismatch

**Issue:** Slight audio degradation if device sample rate ≠ 48000 Hz

**Cause:** Resampling overhead

**Impact:**
- Minimal (barely perceptible)
- Slightly higher CPU usage for resampling
- ~1-2% accuracy reduction

**Workaround:**
- Set device to 48000 Hz in Windows Sound settings:
  - Control Panel → Sound → Recording → Properties
  - Advanced → Default Format → 48000 Hz

**Status:** Working as designed (resampling is automatic)

---

## Detection Accuracy

### Close-Range Detection Limitations

**Issue:** Accuracy degrades for sounds <5 meters

**Cause:** ITD/ILD unreliable at very close range

**Impact:**
- Distance estimation less accurate (<5m shown as 5-10m)
- Angle estimation still reliable
- Elevation estimation unreliable

**Workaround:**
- Trust angle, be skeptical of distance for close sounds
- Use game visual cues for close targets

**Status:** **Inherent limitation** of stereo audio analysis

---

### Distant Shot Classification (<100m)

**Issue:** Shot classification accuracy decreases with distance

**Cause:** High-frequency attenuation over distance

**Impact:**
- Distant shots (>100m) may misclassify weapon type
- Distance estimation less reliable
- Close/distant classification still works

**Accuracy:**
```
<30m:  ~90% weapon classification accuracy
30-70m: ~70% accuracy
>100m:  ~50% accuracy (unreliable)
```

**Workaround:**
- Trust detection, be skeptical of weapon type at distance
- Use threat level (CRITICAL/HIGH/MEDIUM/LOW) for prioritization

**Status:** **Fundamental limitation** of spectral analysis

---

### Surface Type Detection Requirements

**Issue:** Surface classification requires clear, isolated footsteps

**Cause:** Overlapping sounds confuse spectral centroid analysis

**Impact:**
- Unreliable during combat (gunfire + footsteps)
- Less accurate with music/ambient sounds
- May misclassify with echoes/reverb

**Workaround:**
- Trust surface type only when single, clear footstep
- Disable surface detection if not needed (future config option)

**Status:** **Improvement planned** - Temporal filtering

---

### False Positives from Environmental Sounds

**Issue:** Some non-combat sounds trigger detection

**Examples:**
- Door creaking → detected as footstep
- Vehicle engine → detected as machine
- Ambient wind → detected as movement

**Cause:** Similar frequency profiles

**Mitigation:**
- Increase detection thresholds (reduce sensitivity)
- Enable noise gate to block ambient sounds
- Use energy threshold to ignore quiet sounds

**Status:** **Ongoing improvement** - Better classification models

---

## Performance Limitations

### UI Freezing on Slow Systems

**Issue:** Main window briefly freezes during heavy detection load

**Cause:** Worker pool saturation (pre-V4.2.0 issue)

**Impact:**
- ~100-500ms freeze when 3+ targets detected simultaneously
- Radar updates lag
- User input delayed

**Status:** **FIXED in V4.2.0** via parallel detection processing

**If still occurs:**
- Reduce MAX_WORKERS in constants.py:
  ```python
  MAX_WORKERS = 2  # Instead of 3
  ```
- Lower tick rate:
  ```python
  TICK_INTERVAL_MS = 100  # 10 FPS instead of 20
  ```

---

### High CPU Usage on Dual-Core Systems

**Issue:** CPU usage >40% on dual-core processors

**Cause:** 3 worker threads + main thread + audio thread = 5 threads

**Impact:**
- Laptop battery drain
- Fan noise
- Possible game performance impact

**Workaround:**
```python
# app/core/constants.py
MAX_WORKERS = 1  # Single worker thread for dual-core
TICK_INTERVAL_MS = 100  # Lower FPS
```

**Status:** **Acceptable trade-off** for real-time processing

---

### Memory Usage Growth Over Time

**Issue:** Memory increases slowly during long sessions (>2 hours)

**Cause:** Target history accumulation (minor leak)

**Impact:**
- ~50-100 MB increase over 2-3 hours
- Not critical for normal gaming sessions
- May become noticeable in 8+ hour marathon sessions

**Workaround:**
- Restart RadarSuite every 2-3 hours
- Clear target history periodically (future feature)

**Status:** **Low priority** - Minor issue, workaround available

---

## Platform Limitations

### Windows Only

**Issue:** No Linux/macOS support in V4.2.0

**Cause:** Focus on Windows gaming market

**Impact:**
- Linux gamers cannot use RadarSuite
- macOS not supported

**Workaround:**
- Run Windows in VM (high latency, not recommended)
- Use Wine (unstable, not tested)

**Status:** **No plans for Linux/macOS** in near future

---

### Windows 11 Exclusive Features

**Issue:** Some features require Windows 11

**Examples:**
- Native WASAPI loopback (no VB-Cable needed)
- Better audio device detection

**Workaround:**
- Windows 10 users: Install VB-Audio Virtual Cable
- All features work with workaround

**Status:** Working as designed

---

## UI/UX Issues

### MainWindow God Object (1,670 lines)

**Issue:** main.py is too large, hard to maintain

**Cause:** All UI/logic in single class

**Impact:**
- Difficult to add new features
- Hard to test individual components
- Code navigation challenging

**Status:** **Refactoring planned** - See REFACTORING_PLAN.md

**Phases:**
1. Extract UIBuilder (~363 lines)
2. Extract AudioProcessor (~300 lines)
3. Extract ApplicationController (~400 lines)
4. Extract EventHandlers (~200 lines)

**Target:** Reduce MainWindow to ~400-500 lines

---

### Language Switching Requires Restart

**Issue:** Switching EN/PL doesn't update all UI elements

**Cause:** Static text set during initialization

**Impact:**
- Some labels remain in old language
- Restart required for full language change

**Workaround:**
- Restart application after language change

**Status:** **Improvement planned** - Dynamic i18n

---

### Detached Windows Not Saved

**Issue:** Detached window positions not persisted

**Cause:** No position saving in config

**Impact:**
- Detached windows reset to center on restart
- Multi-monitor setup requires manual repositioning

**Workaround:**
- Position windows manually each session

**Status:** **Feature request** - Save window positions

---

### No Dark Mode

**Issue:** Only light theme available

**Impact:**
- Eye strain in dark environments
- Not modern UI standard

**Status:** **Feature request** - Qt dark theme

---

## Planned Improvements

### V4.3.0 (Next Release)

**Priority: HIGH**
- [ ] Auto-detect audio device changes (Bluetooth fix)
- [ ] Save detached window positions
- [ ] Extract UIBuilder (Phase 1 refactoring)
- [ ] Improved memory management (target history cleanup)

**Priority: MEDIUM**
- [ ] Dark mode theme
- [ ] Dynamic language switching (no restart)
- [ ] Better 5.1/7.1 downmix matrix
- [ ] Configurable surface type detection

**Priority: LOW**
- [ ] Linux support (community request)
- [ ] GPU acceleration for non-NVIDIA (AMD/Intel)
- [ ] Neural network classification (optional)

### V5.0.0 (Major Release)

**Architecture:**
- [ ] Complete MainWindow refactoring (all 4 phases)
- [ ] Microservice architecture (separate detection service)
- [ ] Plugin system for custom detectors

**Features:**
- [ ] Multi-game profiles (save settings per game)
- [ ] Cloud sync (config + recordings)
- [ ] Live streaming integration (OBS plugin)
- [ ] Machine learning classification (CNN on mel-spectrograms)

**Platform:**
- [ ] Linux native support
- [ ] macOS experimental support (if demand exists)

---

## Reporting Issues

### How to Report

1. **Check this document first** - Issue may be known
2. **GitHub Issues:** https://github.com/yourusername/AudioRadar/issues
3. **Provide:**
   - RadarSuite version (`app/version.py`)
   - Windows version (Win+R → `winver`)
   - Audio device (microphone/loopback)
   - Game being played
   - Steps to reproduce
   - Log output (if error occurs)

### Issue Template

```markdown
**RadarSuite Version:** V4.2.0
**Windows Version:** Windows 11 22H2
**Audio Device:** Sound Blaster Z SE (loopback)
**Game:** ARC Raiders

**Issue:**
Detection stops working after 30 minutes of gameplay.

**Steps to Reproduce:**
1. Launch ARC Raiders
2. Start RadarSuite
3. Play for 30+ minutes
4. Detection stops responding

**Expected Behavior:**
Detection should continue working indefinitely.

**Actual Behavior:**
Detection stops, radar shows no targets.

**Log Output:**
[Paste relevant log lines here]
```

---

## Workaround Summary

**Quick reference for common issues:**

| Issue | Quick Fix |
|-------|-----------|
| Bluetooth audio not working | Stop → Rescan → Apply → Start |
| No loopback device | Install VB-Audio Virtual Cable |
| High CPU usage | Reduce MAX_WORKERS to 2 |
| UI freezing | Update to V4.2.0 |
| Distant shot misclassification | Trust detection, ignore weapon type |
| False positives | Increase detection thresholds |
| Memory leak | Restart every 2-3 hours |
| Vertical positioning wrong | Game bug, not fixable |
| Language doesn't fully switch | Restart application |

---

**RadarSuite V4.2.0** - Honest documentation of limitations and solutions.
