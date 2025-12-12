# 🧪 RADARSUITE V4.2.1-K0003 - MASTER TEST PLAN
## Professional Comprehensive Testing, Diagnostics & Repair Plan

**Document Version**: 1.0
**Software Version**: RadarSuite v4.2.1-k0003
**Date**: 2025-12-09
**Test Engineer**: Senior QA Engineer + Senior Software Engineer
**Methodology**: ISTQB Foundation + Advanced Automation
**Target**: 100% Automated Testing, Diagnostics & Repair

---

## 📊 EXECUTIVE SUMMARY

### Application Overview
**RadarSuite Windows V4.2.1** - Professional real-time audio detection and spatial tracking system for gaming (ARC Raiders). PyQt5-based desktop application with advanced ML training capabilities, multi-threaded audio processing, 3D radar visualization, and custom model training.

### Testing Objectives
1. **Validate all critical functionality** post k0003 bugfixes
2. **Detect all remaining bugs** through automated analysis
3. **Ensure thread safety** in PyQt5 multi-threaded architecture
4. **Verify ML training pipeline** integrity
5. **Achieve >90% code coverage** with automated tests
6. **Zero critical/major bugs** before production release
7. **Automatic repair** of all detected issues

### Test Environment
- **Platform**: Windows 10/11 (Linux compatible)
- **Python**: 3.8+
- **Framework**: PyQt5 + NumPy + SciPy
- **Audio**: sounddevice/soundcard
- **ML**: TensorFlow/scikit-learn
- **Testing Stack**: pytest + pytest-qt + pytest-cov + pylint + mypy + bandit

### Success Metrics
- ✅ Code Coverage: >90% (target: 95%)
- ✅ Static Analysis Score: >9.0/10
- ✅ Security Vulnerabilities: 0 critical, <3 medium
- ✅ Performance: UI response <100ms, audio latency <50ms
- ✅ Memory Leaks: 0 detected
- ✅ Threading Issues: 0 race conditions, 0 deadlocks
- ✅ All Critical Bugs: Fixed automatically
- ✅ All Major Bugs: Fixed or documented

---

## 🎯 SECTION 1: TEST LEVELS (Pyramid Strategy)

### Test Effort Distribution
- **Unit Tests**: 40% (fast, isolated, high coverage)
- **Integration Tests**: 30% (module interactions)
- **System Tests**: 20% (end-to-end flows)
- **Acceptance Tests**: 10% (user-centric)

---

## 🔬 1.1 UNIT TESTS (40% Effort)

### Objective
Test smallest units of code in isolation - individual functions, methods, classes.

### Scope
- All pure functions in `app/core/`, `app/audio/`, `app/detection/`, `app/ml/`
- Mathematical calculations (FFT, MFCC, spatial algorithms)
- Data structures and utilities
- Configuration management

### Tools
- **pytest** (test runner)
- **pytest-cov** (coverage)
- **unittest.mock** (mocking dependencies)
- **hypothesis** (property-based testing)

### Automated Test Suite

#### 1.1.1 Core Module Tests

**File**: `app/tests/core/test_config.py` ✅ (Exists)
**Status**: Review and extend

**File**: `app/tests/core/test_logger.py` ✅ (Exists)
**Status**: Review and extend

**File**: `app/tests/core/test_constants.py` ✅ (Exists)
**Status**: Review and extend

**NEW**: `app/tests/core/test_translations.py`
```python
# TEST: Translation system
def test_tr_function_returns_string():
    from app.core.translations import tr
    assert isinstance(tr("test_key"), str)

def test_tr_fallback_to_key_if_missing():
    from app.core.translations import tr
    result = tr("nonexistent_key_12345")
    assert result == "nonexistent_key_12345"
```

#### 1.1.2 Audio Processing Tests

**File**: `app/tests/audio/test_processor.py` ✅ (Exists)
**Status**: Review and extend

**NEW**: `app/tests/audio/test_fft_accuracy.py`
```python
# TEST: FFT computation accuracy
import numpy as np
from app.audio.processor import AudioProcessor

def test_fft_sine_wave_peak_detection():
    """Test FFT correctly identifies sine wave frequency"""
    sample_rate = 48000
    freq = 440  # A4 note
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    signal = np.sin(2 * np.pi * freq * t)

    processor = AudioProcessor(sample_rate=sample_rate)
    fft_result = processor.compute_fft(signal)

    # Find peak frequency
    peak_idx = np.argmax(np.abs(fft_result))
    detected_freq = peak_idx * sample_rate / len(signal)

    assert abs(detected_freq - freq) < 5  # Within 5Hz tolerance
```

#### 1.1.3 Detection Algorithm Tests

**File**: `app/tests/detection/test_footstep.py` ✅ (Exists)
**Status**: Review and extend

**NEW**: `app/tests/detection/test_threshold_adaptation.py`
```python
# TEST: Adaptive threshold algorithm
from app.detection.footstep import HumanFootstepDetector

def test_threshold_increases_with_noise():
    detector = HumanFootstepDetector()
    initial_threshold = detector.get_threshold()

    # Simulate high noise environment
    noise_samples = [np.random.randn(1024) * 10 for _ in range(100)]
    for sample in noise_samples:
        detector.process(sample)

    final_threshold = detector.get_threshold()
    assert final_threshold > initial_threshold
```

#### 1.1.4 ML Module Tests

**File**: `app/tests/ml/test_trainer.py` ✅ (Exists)
**Status**: Review and extend

**NEW**: `app/tests/ml/test_feature_extraction.py`
```python
# TEST: Feature extraction consistency
from app.ml.feature_extractor import FeatureExtractor
import numpy as np

def test_mfcc_features_shape():
    extractor = FeatureExtractor(n_mfcc=13)
    audio = np.random.randn(48000)  # 1 second at 48kHz

    features = extractor.extract_mfcc(audio)

    assert features.shape[0] == 13  # n_mfcc coefficients
    assert features.shape[1] > 0    # time frames

def test_feature_extraction_deterministic():
    """Same input should produce same output"""
    extractor = FeatureExtractor(n_mfcc=13)
    audio = np.random.randn(48000)

    features1 = extractor.extract_mfcc(audio)
    features2 = extractor.extract_mfcc(audio)

    np.testing.assert_array_almost_equal(features1, features2)
```

#### 1.1.5 Tracking Module Tests

**NEW**: `app/tests/tracking/test_spatial_math.py`
```python
# TEST: Spatial localization mathematics
from app.tracking.target import SpatialLocalizer

def test_itd_to_angle_conversion():
    """Test ITD (Interaural Time Difference) to angle"""
    localizer = SpatialLocalizer()

    # 0° should have ~0 ITD
    angle_0 = localizer.itd_to_angle(0.0)
    assert abs(angle_0) < 5

    # 90° should have maximum positive ITD
    max_itd = 0.0006  # ~0.6ms for human head
    angle_90 = localizer.itd_to_angle(max_itd)
    assert 85 < angle_90 < 95
```

### Coverage Target: >95% for pure functions

---

## 🔗 1.2 INTEGRATION TESTS (30% Effort)

### Objective
Test interactions between modules, components, and external systems.

### Scope
- Audio pipeline: Capture → Processing → Detection
- ML pipeline: Recording → Feature Extraction → Training → Inference
- UI ↔ Backend communication (Qt Signals/Slots)
- Database operations (session storage)
- File I/O (config, models, sessions)

### Tools
- **pytest** with fixtures
- **pytest-qt** (Qt application testing)
- **pytest-mock** (mocking external dependencies)

### Automated Test Suite

#### 1.2.1 Audio Pipeline Integration

**NEW**: `app/tests/integration/test_audio_pipeline.py`
```python
# TEST: End-to-end audio processing pipeline
import pytest
from app.audio.engine import AudioEngine
from app.detection.worker import DetectionWorker

@pytest.fixture
def audio_engine():
    engine = AudioEngine()
    yield engine
    engine.cleanup()

def test_audio_capture_to_detection_flow(audio_engine):
    """Test audio flows from capture to detection"""
    detector = DetectionWorker()

    # Simulate audio block
    audio_block = np.random.randn(1024, 2)  # Stereo

    # Process through pipeline
    audio_engine.process_block(audio_block)
    result = detector.process(audio_block)

    assert result is not None
    assert 'confidence' in result
```

#### 1.2.2 ML Training Pipeline Integration

**NEW**: `app/tests/integration/test_ml_pipeline.py`
```python
# TEST: ML training end-to-end
from app.ml.training import SessionManager, ModelTrainer
import tempfile
import os

def test_record_label_train_workflow():
    """Test complete ML workflow"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        session_mgr = SessionManager(base_path=tmpdir)
        session_mgr.start_session("test_session")

        # Record fake audio
        fake_audio = np.random.randn(48000)
        session_mgr.add_audio_chunk(fake_audio, sample_rate=48000)

        # Add labels
        session_mgr.add_label(0.5, "footstep", "Test label")
        session_mgr.add_label(0.8, "shot", "Test label 2")

        session_mgr.stop_session()

        # Train model
        trainer = ModelTrainer(session_mgr)
        # Add more sessions for minimum training data
        for i in range(5):
            session_mgr.start_session(f"session_{i}")
            session_mgr.add_audio_chunk(np.random.randn(48000), 48000)
            session_mgr.add_label(0.5, "footstep", f"Label {i}")
            session_mgr.stop_session()

        result = trainer.train()

        assert result.success
        assert os.path.exists(result.model_path)
```

#### 1.2.3 PyQt5 UI Integration

**NEW**: `app/tests/integration/test_ui_backend_signals.py`
```python
# TEST: Qt Signals/Slots communication
import pytest
from pytestqt.qtbot import QtBot
from app.widgets.ml_training_panel import MLTrainingPanel

def test_recording_state_propagates_to_ui(qtbot):
    """Test recording state changes update UI correctly"""
    panel = MLTrainingPanel()
    qtbot.addWidget(panel)

    # Simulate start recording
    with qtbot.waitSignal(panel.recording_controller.state_changed, timeout=1000):
        panel._on_start_recording()

    assert panel.status_label.text().contains("Recording")
    assert panel.start_btn.isEnabled() == False
    assert panel.stop_btn.isEnabled() == True
```

### Coverage Target: >85% for integration paths

---

## 🖥️ 1.3 SYSTEM TESTS (20% Effort)

### Objective
Test complete system behavior against requirements - end-to-end user flows.

### Scope
- Complete user workflows (launch → configure → detect → visualize)
- ML training workflow (record → label → train → use)
- Multi-tab navigation and state management
- Window management (detach/attach widgets)
- Configuration persistence
- Error handling and recovery

### Tools
- **pytest-qt** (UI automation)
- **Selenium** (if web components exist)
- **pyautogui** (system-level UI automation)

### Automated Test Suite

#### 1.3.1 Application Launch & Initialization

**NEW**: `app/tests/system/test_app_lifecycle.py`
```python
# TEST: Application startup and shutdown
from PyQt5.QtWidgets import QApplication
from app.main import MainWindow
import sys

def test_application_launches_without_crash():
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()

    assert window.isVisible()

    window.close()
    assert not window.isVisible()
```

#### 1.3.2 ML Training Complete Workflow

**NEW**: `app/tests/system/test_ml_training_e2e.py`
```python
# TEST: Complete ML training user journey
def test_user_records_labels_and_trains_model(qtbot):
    """Simulate complete user workflow"""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    qtbot.addWidget(window)

    # Navigate to ML tab
    ml_tab_index = window.main_tabs.indexOf(window.ml_training_panel)
    window.main_tabs.setCurrentIndex(ml_tab_index)

    # Start recording
    qtbot.mouseClick(window.ml_training_panel.start_btn, Qt.LeftButton)
    qtbot.wait(2000)  # Record for 2 seconds

    # Add label (simulate hotkey)
    qtbot.keyPress(window.ml_training_panel, Qt.Key_1)

    # Stop recording
    qtbot.mouseClick(window.ml_training_panel.stop_btn, Qt.LeftButton)

    # Verify session saved
    sessions = window.ml_training_panel.session_manager.list_sessions()
    assert len(sessions) > 0
```

### Coverage Target: >80% for critical user paths

---

## ✅ 1.4 ACCEPTANCE TESTS (10% Effort)

### Objective
Validate system meets business requirements and user needs.

### Scope
- User stories from requirements
- Performance benchmarks
- Usability criteria
- Deployment verification

### Tools
- **TestRail** (manual test management)
- **User feedback forms**
- **Performance monitoring**

### Acceptance Criteria Checklist

| ID | Requirement | Test Method | Status |
|---|---|---|---|
| AC-001 | ML tab loads with all widgets visible | Automated UI test | ⏳ |
| AC-002 | Recording starts/stops without freeze | Automated + Manual | ⏳ |
| AC-003 | Model training completes in <5min for 100 samples | Performance test | ⏳ |
| AC-004 | Audio detection latency <50ms | Benchmark test | ⏳ |
| AC-005 | Application uses <500MB RAM during normal operation | Memory profiling | ⏳ |
| AC-006 | No crashes during 8-hour stress test | Soak test | ⏳ |

---

## 🧪 SECTION 2: TEST TYPES BY APPROACH

### 2.1 White-Box Testing
**Focus**: Internal code structure, logic paths, branches
**Tools**: pytest + coverage.py + JaCoCo equivalent
**Target**: 100% branch coverage for critical modules

**Test Cases**:
- All if/else branches
- Loop boundaries (0, 1, N iterations)
- Exception handling paths
- State machine transitions

### 2.2 Black-Box Testing
**Focus**: Functionality without code knowledge - inputs/outputs
**Techniques**:
- Equivalence Partitioning
- Boundary Value Analysis
- Decision Tables

**Example**: Audio input validation
```python
# Boundary Value Analysis for sample rate
def test_sample_rate_boundaries():
    valid_rates = [44100, 48000, 96000]
    invalid_rates = [0, -1, 1000, 999999]

    for rate in valid_rates:
        assert AudioEngine(sample_rate=rate)  # Should not raise

    for rate in invalid_rates:
        with pytest.raises(ValueError):
            AudioEngine(sample_rate=rate)
```

### 2.3 Gray-Box Testing
**Focus**: Partial code knowledge - API/database integration
**Use Case**: Test ML model file I/O with knowledge of file format

---

## 🎯 SECTION 3: FUNCTIONAL TESTING AREAS

### 3.1 Core Functionality Tests

| Feature | Test Cases | Priority | Automation |
|---|---|---|---|
| Audio Capture | Device selection, format validation, error handling | CRITICAL | 100% |
| FFT Processing | Accuracy, performance, edge cases | CRITICAL | 100% |
| Footstep Detection | True positives, false positives, threshold adaptation | HIGH | 100% |
| Spatial Localization | ITD/ILD calculation, angle accuracy | HIGH | 100% |
| ML Training | Recording, labeling, training, inference | CRITICAL | 90% |
| Configuration | Save/load, validation, migration | MEDIUM | 80% |
| UI Navigation | Tab switching, widget detachment, state persistence | HIGH | 70% |

### Test Coverage Strategy
- **CRITICAL features**: 100% automated, run on every commit
- **HIGH features**: 90% automated, run daily
- **MEDIUM features**: 80% automated, run weekly

---

## ⚡ SECTION 4: NON-FUNCTIONAL TESTING

### 4.1 Performance Testing

**Tools**: pytest-benchmark, memory_profiler, py-spy

#### 4.1.1 Speed Tests
```python
# TEST: Audio processing speed
def test_audio_processing_meets_realtime_requirement(benchmark):
    processor = AudioProcessor()
    audio_block = np.random.randn(1024, 2)

    result = benchmark(processor.process, audio_block)

    # Must process 1024 samples faster than they're captured
    max_time_ms = (1024 / 48000) * 1000  # Time to capture
    assert result.stats.mean * 1000 < max_time_ms
```

#### 4.1.2 Load Tests
```python
# TEST: Sustained load
def test_application_handles_8_hour_continuous_operation():
    """Soak test - run for 8 hours"""
    app = MainWindow()
    start_memory = get_memory_usage()

    # Simulate 8 hours of audio processing
    for _ in range(8 * 60 * 60):  # 8 hours in seconds
        audio_block = np.random.randn(1024, 2)
        app.process_audio(audio_block)
        time.sleep(1)

    end_memory = get_memory_usage()
    memory_increase = end_memory - start_memory

    assert memory_increase < 100 * 1024 * 1024  # <100MB leak acceptable
```

**Benchmarks**:
- Audio processing: <1ms per 1024-sample block
- UI response: <100ms for button clicks
- Model training: <5min for 1000 samples
- Application startup: <3 seconds

### 4.2 Security Testing

**Tools**: bandit (SAST), safety (dependency vulnerabilities)

#### Automated Scans
```bash
# Run security scan
bandit -r app/ -f json -o security_report.json

# Check dependencies
safety check --json > dependency_vulnerabilities.json
```

**Focus Areas**:
- Input validation (prevent code injection)
- File path sanitization
- Dependency vulnerabilities
- Sensitive data handling (if any)

### 4.3 Usability Testing

**Method**: Heuristic evaluation + user testing

**Nielsen's Heuristics Checklist**:
- ✅ Visibility of system status (progress bars, status labels)
- ✅ Match between system and real world (clear labels)
- ✅ User control (start/stop, undo)
- ✅ Error prevention (validation, confirmations)
- ✅ Recognition over recall (tooltips, hints)

### 4.4 Compatibility Testing

**Platforms**:
- Windows 10/11 ✅
- Linux (Ubuntu 22.04) ⏳
- macOS (if supported) ⏳

**Python Versions**:
- 3.8 ✅
- 3.9 ✅
- 3.10 ✅
- 3.11 ⏳

### 4.5 Reliability Testing

**Test Scenarios**:
- Crash recovery (unexpected shutdown)
- Network loss (if applicable)
- Disk full during session save
- Audio device disconnect
- Out of memory conditions

---

## 🔄 SECTION 5: SPECIALIZED TEST TYPES

### 5.1 Regression Testing

**Trigger**: Every code change (CI/CD)
**Scope**: All previously passing tests
**Automation**: 100%

**Suite**: `pytest tests/ -m regression`

**Test Selection Strategy**:
- All tests for changed files
- All integration tests touching changed modules
- Smoke tests for entire application

### 5.2 Re-testing (Confirmation Testing)

**Trigger**: Bug fix verification
**Scope**: Specific test cases that exposed the bug

**Example** (k0003 bugs):
```python
# TEST: Verify k0003 import fixes
def test_ml_panel_imports_correctly():
    """Regression test for k0003 import bug"""
    from app.ui.builder import ML_TRAINING_AVAILABLE
    assert ML_TRAINING_AVAILABLE == True

def test_waveform_timeline_widget_initializes():
    """Regression test for waveform_timeline import"""
    from app.widgets.waveform_timeline import WaveformTimelineWidget
    widget = WaveformTimelineWidget()
    assert widget is not None
```

### 5.3 API Testing

**Scope**: If RadarSuite exposes APIs (internal or external)

**Tools**: pytest-requests, hypothesis

### 5.4 Smoke Testing (Post-Deployment)

**Trigger**: After deployment to production
**Duration**: <5 minutes
**Scope**: Critical path validation

```python
# Smoke test suite
@pytest.mark.smoke
def test_application_launches():
    pass

@pytest.mark.smoke
def test_audio_device_detected():
    pass

@pytest.mark.smoke
def test_ml_tab_visible():
    pass
```

---

## 🤖 SECTION 6: AUTOMATION ARCHITECTURE

### 6.1 Technology Stack

```yaml
Testing Framework: pytest 7.4+
UI Testing: pytest-qt 4.2+
Coverage: pytest-cov + coverage.py
Static Analysis: pylint, mypy, flake8
Security: bandit, safety
Performance: pytest-benchmark, memory_profiler
CI/CD: GitHub Actions (or GitLab CI)
Reporting: Allure, pytest-html
```

### 6.2 Project Structure

```
RadarSuite_Windows_V4.2/
├── app/                          # Source code
│   ├── core/
│   ├── audio/
│   ├── ml/
│   └── widgets/
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests (fast)
│   │   ├── test_audio.py
│   │   ├── test_detection.py
│   │   └── test_ml.py
│   ├── integration/              # Integration tests
│   │   ├── test_audio_pipeline.py
│   │   └── test_ml_pipeline.py
│   ├── system/                   # System/E2E tests
│   │   └── test_ml_workflow.py
│   ├── performance/              # Performance tests
│   │   └── test_benchmarks.py
│   ├── security/                 # Security tests
│   │   └── test_vulnerabilities.py
│   ├── conftest.py               # Shared fixtures
│   └── pytest.ini                # Pytest configuration
├── .github/workflows/
│   └── ci.yml                    # CI/CD pipeline
├── requirements-test.txt         # Test dependencies
└── TEST_PLAN_MASTER_v4.2.1.md   # This document
```

### 6.3 Example Test Code

#### Unit Test Example
```python
# tests/unit/test_audio_processor.py
import pytest
import numpy as np
from app.audio.processor import AudioProcessor

@pytest.fixture
def processor():
    return AudioProcessor(sample_rate=48000, block_size=1024)

def test_processor_initialization(processor):
    assert processor.sample_rate == 48000
    assert processor.block_size == 1024

def test_process_audio_block_shape(processor):
    audio = np.random.randn(1024, 2)
    result = processor.process(audio)
    assert result.shape == audio.shape

def test_compute_spectrum_returns_correct_length(processor):
    audio = np.random.randn(1024)
    spectrum = processor.compute_spectrum(audio)
    assert len(spectrum) == 1024 // 2 + 1  # FFT length
```

#### Integration Test Example
```python
# tests/integration/test_ml_pipeline.py
import pytest
import tempfile
from app.ml.training import SessionManager, LabeledRecorder, ModelTrainer

@pytest.fixture
def temp_session_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_end_to_end_ml_training(temp_session_dir):
    # Setup components
    session_mgr = SessionManager(base_path=temp_session_dir)
    recorder = LabeledRecorder(session_mgr)
    trainer = ModelTrainer(session_mgr)

    # Record session
    recorder.start_session("test_session")
    fake_audio = np.random.randn(48000)
    recorder.add_audio(fake_audio, sample_rate=48000)
    recorder.add_label(timestamp=0.5, label_class="footstep")
    recorder.stop_session()

    # Train model (need multiple sessions)
    for i in range(10):
        recorder.start_session(f"session_{i}")
        recorder.add_audio(np.random.randn(48000), 48000)
        recorder.add_label(0.5, "footstep")
        recorder.stop_session()

    result = trainer.train()
    assert result.success
    assert result.accuracy > 0.5  # Basic sanity check
```

#### System Test Example
```python
# tests/system/test_ui_workflows.py
import pytest
from pytestqt.qtbot import QtBot
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from app.main import MainWindow

@pytest.fixture
def app(qtbot):
    test_app = QApplication.instance() or QApplication([])
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    yield window
    window.close()

def test_navigate_to_ml_tab_and_start_recording(app, qtbot):
    # Find ML tab
    ml_tab_idx = -1
    for i in range(app.main_tabs.count()):
        if "ML" in app.main_tabs.tabText(i):
            ml_tab_idx = i
            break

    assert ml_tab_idx >= 0, "ML tab not found"

    # Navigate to ML tab
    app.main_tabs.setCurrentIndex(ml_tab_idx)
    ml_panel = app.ml_training_panel

    # Verify panel loaded
    assert ml_panel is not None
    assert ml_panel.isVisible()

    # Click start button
    qtbot.mouseClick(ml_panel.start_btn, Qt.LeftButton)

    # Wait for state change
    qtbot.wait(500)

    # Verify recording started
    assert not ml_panel.start_btn.isEnabled()
    assert ml_panel.stop_btn.isEnabled()
```

### 6.4 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: RadarSuite CI/CD

on:
  push:
    branches: [ main, claude/* ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run static analysis
      run: |
        pylint app/ --exit-zero
        flake8 app/ --exit-zero
        mypy app/ --ignore-missing-imports

    - name: Run security scan
      run: |
        bandit -r app/ -f json -o bandit-report.json
        safety check

    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=app --cov-report=xml

    - name: Run integration tests
      run: |
        pytest tests/integration/ -v

    - name: Run system tests
      run: |
        pytest tests/system/ -v --maxfail=3

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

    - name: Generate test report
      if: always()
      run: |
        pytest --html=report.html --self-contained-html

    - name: Upload test report
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-report-${{ matrix.os }}-py${{ matrix.python-version }}
        path: report.html

  deploy:
    needs: test
    runs-on: windows-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Build executable
      run: |
        pip install pyinstaller
        pyinstaller RadarSuite_Windows_V4.2.spec

    - name: Run smoke tests
      run: |
        pytest tests/ -m smoke

    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: RadarSuite-Windows-v4.2.1-k0003
        path: dist/
```

---

## 📈 SECTION 7: DIAGNOSTICS & DEEP ANALYSIS

### 7.1 Static Code Analysis

#### 7.1.1 Code Quality Metrics

**Tools**: pylint, radon, mccabe

```bash
# Complexity analysis
radon cc app/ -a -nb

# Maintainability index
radon mi app/ -nb

# Code quality
pylint app/ --output-format=json > pylint_report.json
```

**Target Metrics**:
- **Pylint Score**: >9.0/10
- **Cyclomatic Complexity**: <10 per function
- **Maintainability Index**: >65 (good), >85 (excellent)
- **Code Duplication**: <5%

#### 7.1.2 Type Checking

**Tool**: mypy

```bash
mypy app/ --strict --ignore-missing-imports --html-report mypy-report/
```

**Focus Areas**:
- Function signatures
- Return types
- Optional types handling
- Type annotations coverage >80%

### 7.2 Security Vulnerability Scan

#### 7.2.1 SAST (Static Application Security Testing)

**Tool**: bandit

```bash
bandit -r app/ -f json -o bandit-report.json -ll
```

**Common Issues to Detect**:
- Hardcoded secrets
- SQL injection risks
- Command injection (subprocess)
- Insecure deserialization
- Weak cryptography

#### 7.2.2 Dependency Vulnerabilities

**Tool**: safety, pip-audit

```bash
safety check --json > safety-report.json
pip-audit --format json > pip-audit-report.json
```

### 7.3 Memory Leak Detection

**Tools**: memory_profiler, objgraph, tracemalloc

```python
# tests/diagnostics/test_memory_leaks.py
import tracemalloc
from app.main import MainWindow

def test_no_memory_leak_in_audio_processing():
    tracemalloc.start()

    app = MainWindow()

    # Baseline
    snapshot1 = tracemalloc.take_snapshot()

    # Process audio for 1000 iterations
    for _ in range(1000):
        audio = np.random.randn(1024, 2)
        app.process_audio(audio)

    snapshot2 = tracemalloc.take_snapshot()

    # Compare memory usage
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    total_increase = sum(stat.size_diff for stat in top_stats)

    # Allow small increase (<10MB for 1000 iterations)
    assert total_increase < 10 * 1024 * 1024
```

### 7.4 Threading & Concurrency Analysis

#### 7.4.1 Race Condition Detection

**Tool**: Thread sanitizer (if available), manual code review

**Focus Areas**:
- Shared state between threads
- Qt signal/slot thread safety
- Audio buffer access
- ML training thread synchronization

```python
# Test for data races
def test_concurrent_audio_processing_no_race():
    processor = AudioProcessor()

    def worker():
        for _ in range(100):
            audio = np.random.randn(1024, 2)
            processor.process(audio)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # If no exception, no obvious race condition
    assert True
```

#### 7.4.2 Deadlock Detection

**Method**: Timeout-based tests, manual review

```python
def test_no_deadlock_in_ml_training():
    trainer = ModelTrainer()

    # Start training with timeout
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Training deadlocked!")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(60)  # 60 second timeout

    try:
        trainer.train()
        signal.alarm(0)  # Cancel alarm
    except TimeoutError:
        pytest.fail("Deadlock detected in training")
```

### 7.5 Performance Profiling

**Tools**: cProfile, py-spy, line_profiler

```bash
# Profile application
python -m cProfile -o profile.stats app/main.py

# Analyze results
python -c "import pstats; p=pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

# Live profiling
py-spy record -o profile.svg -- python app/main.py
```

### 7.6 Import Dependency Analysis

**Tool**: Custom script + graphviz

```python
# tests/diagnostics/test_import_structure.py
def test_no_circular_imports():
    """Detect circular import dependencies"""
    import importlib
    import sys

    modules = [
        'app.core',
        'app.audio',
        'app.widgets',
        'app.ml',
        'app.detection'
    ]

    for module in modules:
        # Clear cache
        if module in sys.modules:
            del sys.modules[module]

        # Try import
        try:
            importlib.import_module(module)
        except ImportError as e:
            if "circular import" in str(e).lower():
                pytest.fail(f"Circular import detected in {module}: {e}")
```

---

## 🔧 SECTION 8: AUTOMATED REPAIR STRATEGY

### 8.1 Repair Priority Levels

**CRITICAL** → Auto-fix immediately
**MAJOR** → Auto-fix with validation
**MINOR** → Document + suggest fix
**TRIVIAL** → Log only

### 8.2 Auto-Fix Categories

#### 8.2.1 Code Quality Fixes

**Detectable Issues**:
- Missing docstrings → Generate from function signature
- Unused imports → Remove automatically
- Inconsistent formatting → Apply black/autopep8
- Type annotation missing → Add based on usage

**Tool**: autopep8, black, isort, autoflake

```bash
# Auto-format code
black app/ --line-length 100
isort app/ --profile black
autoflake --in-place --remove-unused-variables app/**/*.py
```

#### 8.2.2 Security Fixes

**Auto-fixable**:
- Update vulnerable dependencies → `pip install --upgrade package`
- Remove hardcoded credentials → Replace with env vars
- Fix insecure random → Replace `random` with `secrets`

#### 8.2.3 Performance Fixes

**Auto-optimizable**:
- Cache repeated computations → Add `@lru_cache`
- Replace loops with numpy operations
- Use generators instead of lists

### 8.3 Repair Validation

After each auto-fix:
1. Run affected tests
2. Verify no regressions
3. Commit with descriptive message
4. Update documentation

---

## 📊 SECTION 9: REPORTING & METRICS

### 9.1 Test Execution Report

**Template**:

```markdown
# RadarSuite v4.2.1-k0003 Test Execution Report

**Date**: 2025-12-09
**Build**: v4.2.1-k0003
**Environment**: Windows 11, Python 3.10

## Summary
- **Total Tests**: 247
- **Passed**: 235 ✅
- **Failed**: 8 ❌
- **Skipped**: 4 ⏭️
- **Duration**: 5m 32s

## Coverage
- **Line Coverage**: 92.3%
- **Branch Coverage**: 87.1%
- **Function Coverage**: 94.5%

## Failures

| Test | Module | Reason | Severity |
|---|---|---|---|
| test_audio_device_init | audio.engine | Device not found | MAJOR |
| test_ml_training_accuracy | ml.trainer | Accuracy below threshold | MINOR |

## Performance Benchmarks

| Metric | Target | Actual | Status |
|---|---|---|---|
| Audio Processing | <1ms | 0.7ms | ✅ |
| Model Training (100 samples) | <5min | 3m 42s | ✅ |
| UI Response Time | <100ms | 45ms | ✅ |

## Security Scan Results
- **Critical**: 0
- **High**: 0
- **Medium**: 2 (documented)
- **Low**: 5

## Recommendations
1. Fix audio device initialization test
2. Increase ML training data for better accuracy
3. Address medium-severity security issues
```

### 9.2 Code Quality Dashboard

**Metrics Tracked**:
- Test coverage trend
- Bug density (bugs per KLOC)
- Code complexity trend
- Technical debt ratio

### 9.3 Continuous Monitoring

**Setup**: Integrate with monitoring tools
- **SonarQube** (code quality)
- **CodeClimate** (maintainability)
- **Codecov** (coverage visualization)

---

## 🎯 SECTION 10: EXECUTION PLAN

### Phase 1: Setup (Day 1)
- [ ] Install test dependencies
- [ ] Configure pytest
- [ ] Setup CI/CD pipeline
- [ ] Create test data fixtures

### Phase 2: Unit Testing (Day 1-2)
- [ ] Write unit tests for all modules
- [ ] Achieve >90% coverage
- [ ] Fix detected bugs

### Phase 3: Integration Testing (Day 2-3)
- [ ] Write integration tests
- [ ] Test audio pipeline
- [ ] Test ML pipeline
- [ ] Achieve >85% integration coverage

### Phase 4: System Testing (Day 3-4)
- [ ] Write E2E tests
- [ ] Test complete workflows
- [ ] UI automation tests

### Phase 5: Diagnostics (Day 4-5)
- [ ] Run static analysis
- [ ] Security scan
- [ ] Performance profiling
- [ ] Memory leak detection

### Phase 6: Repair (Day 5-6)
- [ ] Auto-fix critical issues
- [ ] Manual fix major issues
- [ ] Document minor issues
- [ ] Validate all fixes

### Phase 7: Reporting (Day 6-7)
- [ ] Generate comprehensive report
- [ ] Document all changes
- [ ] Update version
- [ ] Create release notes

---

## 📚 REFERENCES

### Standards & Methodologies
- **ISTQB Foundation Level Syllabus**
- **IEEE 829 Test Documentation Standard**
- **Agile Testing Quadrants** (Brian Marick)

### Resources
- **testerzy.pl**: Rodzaje testów wg poziomów (modułowe, integracyjne)
- **craftware.pl**: Testy manualne (funkcjonalne, czarnej skrzynki)
- **pytest Documentation**: https://docs.pytest.org/
- **PyQt5 Testing**: https://pytest-qt.readthedocs.io/

### Tools Documentation
- **pylint**: https://pylint.pycqa.org/
- **bandit**: https://bandit.readthedocs.io/
- **coverage.py**: https://coverage.readthedocs.io/

---

## ✅ SIGN-OFF

**Test Plan Approved By**: Senior QA Engineer
**Date**: 2025-12-09
**Status**: READY FOR EXECUTION

**Next Steps**: Execute automated test suite and diagnostics

---

**END OF MASTER TEST PLAN**
