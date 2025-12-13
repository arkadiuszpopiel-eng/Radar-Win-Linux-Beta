"""Internal self-test runner for RadarSuite."""

from __future__ import annotations

import threading
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import numpy as np

try:  # pragma: no cover - optional in headless tests
    from PyQt5.QtWidgets import QApplication
    QT_AVAILABLE = True
except Exception:  # pragma: no cover - no Qt in environment
    QT_AVAILABLE = False

from app.core.logger import log
from app.core.config import ConfigManager
from app.core import get_selftest_log_path, get_selftest_report_path


@dataclass
class SelfTestResult:
    name: str
    success: bool
    message: str = ""
    error: Optional[str] = None


class SelfTestRunner:
    """Executes quick or full self-tests inside the app."""

    def __init__(self, config_manager: Optional[ConfigManager] = None, include_gui_checks: bool = True):
        self.config_manager = config_manager or ConfigManager()
        self.include_gui_checks = include_gui_checks and QT_AVAILABLE
        self._log_lines: List[str] = []
        self._report_path: Optional[Path] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run_quick(self) -> Tuple[List[SelfTestResult], Path]:
        steps: List[Tuple[str, Callable[[], None]]] = [
            ("Config load", self._step_config_load),
            ("ML imports", self._step_ml_imports),
            ("Recording FSM", self._step_recording_flow),
        ]

        if self.include_gui_checks:
            steps.append(("Overlay logic", self._step_overlay_logic))

        results = self._execute_steps(steps)
        return results, self._report_path or Path("logs/selftest_latest.log")

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------
    def _step_config_load(self) -> None:
        cfg = self.config_manager.load()
        _ = cfg.get("ml_overlay", {})
        if "audio" not in cfg:
            raise AssertionError("Audio section missing")

    def _step_ml_imports(self) -> None:
        from app.widgets.ml_training_panel import MLTrainingPanel  # noqa: F401
        from app.widgets.ml_quick_overlay import MLQuickRecordOverlay  # noqa: F401
        from app.ml.training import RecordingController  # noqa: F401

    def _step_recording_flow(self) -> None:
        from app.ml.training import RecordingController
        from app.ml.training.session_manager import SessionManager

        manager = SessionManager(base_path=Path("./Data/TestSessions"))
        controller = RecordingController(session_manager=manager, test_mode=True)
        session = controller.simulate_quick_capture()
        assert session is not None

    def _step_overlay_logic(self) -> None:
        if not QT_AVAILABLE:
            return
        from app.ml.training import RecordingController
        from app.widgets.ml_quick_overlay import MLQuickRecordOverlay
        from app.ml.training.session_manager import SessionManager

        owned_app = None
        app = QApplication.instance()
        if app is None:
            owned_app = QApplication([])
        controller = RecordingController(
            session_manager=SessionManager(base_path=Path("./Data/TestSessions")),
            test_mode=True,
        )
        overlay = MLQuickRecordOverlay(controller=controller, config_manager=self.config_manager)
        overlay.hide()
        overlay._apply_size_preset()  # noqa: SLF001
        overlay._toggle_frameless(1)
        overlay.close()
        if owned_app:
            owned_app.quit()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _execute_steps(self, steps: List[Tuple[str, Callable[[], None]]]) -> List[SelfTestResult]:
        results: List[SelfTestResult] = []
        for name, func in steps:
            result = self._run_step_with_timeout(name, func)
            results.append(result)

        self._report_path = self._write_report(results)
        return results

    def _run_step_with_timeout(self, name: str, func: Callable[[], None], timeout: float = 5.0) -> SelfTestResult:
        result_holder: dict = {}

        def target():
            try:
                func()
                result_holder["result"] = SelfTestResult(name=name, success=True, message="OK")
            except Exception as exc:  # pragma: no cover - defensive
                tb = traceback.format_exc()
                result_holder["result"] = SelfTestResult(name=name, success=False, message=str(exc), error=tb)

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            self._log_lines.append(f"✗ {name}: timeout after {timeout}s")
            return SelfTestResult(name=name, success=False, message=f"timeout after {timeout}s")

        result = result_holder.get("result")
        if result and result.success:
            self._log_lines.append(f"✓ {name}")
        elif result:
            self._log_lines.append(f"✗ {name}: {result.message}")
        else:  # pragma: no cover - defensive
            self._log_lines.append(f"✗ {name}: unknown error")
            result = SelfTestResult(name=name, success=False, message="unknown error")

        return result

    def _write_report(self, results: List[SelfTestResult]) -> Path:
        # FIXED v4.2.1-k0008: Use centralized log directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = get_selftest_log_path(timestamp)
        report_path = get_selftest_report_path(timestamp)

        # Write detailed log
        with log_path.open("w", encoding="utf-8") as fh:
            fh.write("RadarSuite Self-Test Log\n")
            fh.write("=" * 60 + "\n")
            for line in self._log_lines:
                fh.write(line + "\n")
            for result in results:
                if not result.success and result.error:
                    fh.write("\n" + result.error + "\n")

        # Write summary report
        with report_path.open("w", encoding="utf-8") as fh:
            fh.write("RadarSuite Self-Test Summary Report\n")
            fh.write("=" * 60 + "\n")
            fh.write(f"Timestamp: {timestamp}\n")
            fh.write(f"Total Tests: {len(results)}\n")

            passed = sum(1 for r in results if r.success)
            failed = len(results) - passed
            fh.write(f"Passed: {passed}\n")
            fh.write(f"Failed: {failed}\n")
            fh.write("\n")

            # List all results
            for result in results:
                status = "✓ PASS" if result.success else "✗ FAIL"
                fh.write(f"{status} - {result.name}: {result.message}\n")

        return log_path  # Return log path for backward compatibility
