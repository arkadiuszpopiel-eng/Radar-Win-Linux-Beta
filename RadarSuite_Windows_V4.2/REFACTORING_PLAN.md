# RadarSuite V4.2 - God Object Refactoring Plan

## Current State Analysis

**File:** `app/main.py`
**Lines:** 2,001 (after header reduction from 2,136)
**Main Class:** `MainWindow` (~1,670 lines)

### Identified Responsibilities in MainWindow

1. **UI Construction** (~363 lines in `create_ui()`)
   - Tab creation (4 tabs: Radar, Detection, Game Detection, Analysis)
   - Widget initialization (radars, panels, controls)
   - Layout management
   - Stylesheet definitions
   - Toolbar setup
   - Status bar setup

2. **UI Event Handlers** (~200 lines)
   - toggle_start_stop, toggle_recording, toggle_fullscreen
   - toggle_detach_radar, toggle_detach_led
   - toggle_language, update_ui_translations
   - update_radar_alpha, update_led_alpha
   - reset_radar, quick_mute_toggle
   - setup_shortcuts

3. **Audio Processing** (~300 lines)
   - apply_audio_processing (gain, noise gate)
   - compute_orientation (energy, balance)
   - compute_precise_location_3d (ITD/ILD)
   - compute_elevation (frequency analysis)
   - generate_test_block

4. **Main Update Loop** (~400 lines)
   - tick() - main coordinator
   - _update_radar_sweep
   - _acquire_audio_block
   - _update_recording
   - _process_audio_visualizations
   - _process_audio_level_monitoring
   - _process_detection_and_tracking (FIXED v4.2.0)
   - _update_ui_elements

5. **Lifecycle Management** (~150 lines)
   - __init__ with DI support
   - _inject_dependencies
   - _create_dependencies
   - start, stop
   - closeEvent (cleanup)

6. **Background Tasks** (~150 lines)
   - scan_games (game detection)
   - scan_audio_sources (audio device scanning)
   - quick_setup_game_audio

## Proposed Refactoring Strategy

### Phase 1: Extract UI Builder (HIGH PRIORITY)
**Goal:** Move UI construction out of MainWindow

```python
class RadarSuiteUIBuilder:
    """Responsible for building all UI components"""

    def __init__(self, main_window):
        self.main = main_window

    def build_ui(self):
        """Build complete UI"""
        self._build_tabs()
        self._build_toolbar()
        self._build_statusbar()
        self._setup_styling()

    def _build_tabs(self):
        """Build tab widget and all tabs"""
        self._build_radar_tab()
        self._build_detection_tab()
        self._build_game_detection_tab()
        self._build_analysis_tab()

    # ... additional helper methods
```

**Benefits:**
- Reduces MainWindow by ~363 lines
- Separates presentation from logic
- Easier to modify UI layout
- Better testability

**Risk:** LOW - UI construction is mostly isolated

### Phase 2: Extract Audio Processor (MEDIUM PRIORITY)
**Goal:** Move audio processing algorithms out of MainWindow

```python
class AudioProcessor:
    """Handles audio signal processing and analysis"""

    def __init__(self, sample_rate=48000):
        self.sample_rate = sample_rate

    def apply_processing(self, block, auto_gain, manual_gain, noise_gate_db):
        """Apply gain and noise gate"""
        # Move apply_audio_processing logic here

    def compute_orientation(self, block):
        """Compute energy and L/R balance"""
        # Move compute_orientation logic here

    def compute_location_3d(self, block):
        """3D localization using ITD/ILD"""
        # Move compute_precise_location_3d logic here

    def compute_elevation(self, block):
        """Estimate elevation from frequency content"""
        # Move compute_elevation logic here
```

**Benefits:**
- Reduces MainWindow by ~300 lines
- Reusable audio processing logic
- Easier to test algorithms
- Can be optimized independently

**Risk:** MEDIUM - Requires careful testing of audio algorithms

### Phase 3: Extract Update Coordinator (MEDIUM PRIORITY)
**Goal:** Move tick loop coordination to separate controller

```python
class ApplicationController:
    """Coordinates main update loop and subsystems"""

    def __init__(self, main_window, audio_processor, detection_manager):
        self.main = main_window
        self.audio_processor = audio_processor
        self.detection_manager = detection_manager

    def tick(self):
        """Main update loop - coordinates all subsystems"""
        self._update_radar_sweep()
        self._process_audio()
        self._update_recording()
        self._update_visualizations()
        self._update_ui()

    # ... coordinate helper methods
```

**Benefits:**
- Reduces MainWindow by ~400 lines
- Clear separation of coordination logic
- Easier to understand application flow
- Better for testing update sequences

**Risk:** MEDIUM - Central coordination, needs careful testing

### Phase 4: Extract Event Handlers (LOW PRIORITY)
**Goal:** Group related event handlers into handler classes

```python
class UIEventHandlers:
    """Handles UI events and user interactions"""

    def __init__(self, main_window):
        self.main = main_window

    def handle_start_stop(self):
        """Toggle audio capture"""

    def handle_recording_toggle(self):
        """Toggle recording"""

    def handle_detach_radar(self, checked):
        """Detach/attach radar window"""

    # ... additional handlers
```

**Benefits:**
- Groups related functionality
- Easier to find event handlers
- Can create specialized handler classes

**Risk:** LOW - Event handlers are mostly independent

## Implementation Guidelines

### 1. Test Before Refactoring
- Run existing tests (if any)
- Manually test all features
- Document current behavior

### 2. Incremental Approach
- Complete Phase 1 fully before starting Phase 2
- Commit after each major extraction
- Test after each commit

### 3. Maintain Backward Compatibility
- Keep existing public APIs
- Use delegation pattern initially
- MainWindow becomes a facade

### 4. Preserve Dependency Injection
- Pass dependencies to new classes
- Don't break existing DI container
- Keep constructor signatures compatible

### 5. Update Documentation
- Update docstrings for extracted classes
- Add architecture diagram
- Document new class relationships

## Expected Results

### Before Refactoring
- **MainWindow:** ~1,670 lines
- **Responsibilities:** 6+ major concerns
- **Testability:** Difficult (tight coupling)

### After Refactoring (All Phases)
- **MainWindow:** ~400-500 lines (facade/coordinator)
- **UIBuilder:** ~400 lines
- **AudioProcessor:** ~300 lines
- **ApplicationController:** ~400 lines
- **EventHandlers:** ~200 lines
- **Total:** Similar line count, better organized
- **Testability:** Much improved (loose coupling)

## Priority Order

1. **Phase 1** (UIBuilder) - Extract UI construction
2. **Phase 2** (AudioProcessor) - Extract audio algorithms
3. **Phase 3** (ApplicationController) - Extract tick coordination
4. **Phase 4** (EventHandlers) - Extract event handlers

## Success Criteria

- [ ] All existing features work unchanged
- [ ] All tests pass (unit + integration)
- [ ] MainWindow reduced to <500 lines
- [ ] Each extracted class has single responsibility
- [ ] Code coverage maintained or improved
- [ ] Performance not degraded
- [ ] Memory usage unchanged
- [ ] Startup time unchanged

## Notes

- This refactoring is marked **IMPORTANT** (not CRITICAL)
- Take time to do it properly
- Don't break existing functionality
- Test thoroughly at each step
- Can be done incrementally over multiple PRs

## Related Work

- ✅ **COMPLETED:** DetectionWorker refactoring (v4.2.0)
- ✅ **COMPLETED:** DetectionWorker integration (v4.2.0)
- ✅ **COMPLETED:** Marketing header removal (v4.2.0)
- ⏳ **PENDING:** God object refactoring (this plan)
