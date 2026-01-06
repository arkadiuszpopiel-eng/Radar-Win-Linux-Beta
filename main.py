"""
YOLO Object Detection - Główna aplikacja

System wykrywania obiektów w grze oparty o Computer Vision i ML.

Zoptymalizowany dla:
- CPU: AMD Ryzen 7 5700X3D (8 rdzeni, 16 wątków)
- GPU: AMD Radeon RX 7900 GRE

Autor: Claude
Data: 2026
"""

import sys
import time
import threading
from pathlib import Path
from queue import Queue

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Dodaj src do path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.config import Config
from src.utils.hotkey_manager import HotkeyManager
from src.capture.screen_capture import ScreenCapture
from src.detection.yolo_detector import YOLODetector
from src.detection.stabilizer import DetectionStabilizer
from src.overlay.transparent_overlay import TransparentOverlay


class YOLODetectionApp:
    """Główna aplikacja detekcji YOLO."""

    def __init__(self, config_path: str = None):
        """Inicjalizacja aplikacji.

        Args:
            config_path: Ścieżka do pliku konfiguracyjnego.
        """
        print("=" * 70)
        print("YOLO OBJECT DETECTION - System wykrywania obiektów".center(70))
        print("=" * 70)
        print()

        # Załaduj konfigurację
        self.config = Config(config_path)
        print("✓ Załadowano konfigurację")

        # Flagi stanu
        self.running = False
        self.detection_enabled = True
        self.overlay_visible = True

        # Statystyki
        self.capture_fps = 0
        self.inference_fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()

        # Inicjalizuj komponenty
        self._init_components()

    def _init_components(self):
        """Inicjalizuj wszystkie komponenty."""
        print("\nInicjalizacja komponentów...")
        print("-" * 70)

        # 1. Screen Capture
        print("1. Screen Capture...")
        self.capture = ScreenCapture(
            monitor=self.config.get("capture.monitor", 0),
            target_fps=self.config.get("capture.fps", 60)
        )
        monitor_info = self.capture.get_monitor_info()
        self.screen_width = monitor_info["width"]
        self.screen_height = monitor_info["height"]
        print(f"   ✓ Rozdzielczość: {self.screen_width}x{self.screen_height}")

        # 2. YOLO Detector
        print("\n2. YOLO Detector...")
        model_path = self.config.get("model.path", "data/models/best.onnx")
        if not Path(model_path).exists():
            print(f"\n⚠ UWAGA: Model nie znaleziony: {model_path}")
            print("   Najpierw wytrenuj model używając: python scripts/train_yolo.py")
            print("   Lub pobierz gotowy model i umieść go w: data/models/best.onnx")
            print()
            self.detector = None
        else:
            self.detector = YOLODetector(
                model_path=model_path,
                class_names=self.config.get("model.classes", ["crate"]),
                conf_threshold=self.config.get("model.confidence_threshold", 0.5),
                nms_threshold=self.config.get("model.nms_threshold", 0.45),
                input_size=self.config.get("model.imgsz", 640),
                use_gpu=self.config.get("inference.use_gpu", True)
            )
            print("   ✓ Model YOLO gotowy")

        # 3. Detection Stabilizer
        print("\n3. Detection Stabilizer...")
        self.stabilizer = DetectionStabilizer(
            iou_threshold=self.config.get("stabilization.iou_threshold", 0.5),
            ema_alpha=self.config.get("stabilization.ema_alpha", 0.7),
            ttl_frames=self.config.get("stabilization.ttl_frames", 5),
            min_box_size=self.config.get("stabilization.min_box_size", 20)
        )
        print("   ✓ Stabilizator gotowy")

        # 4. Qt Application & Overlay
        print("\n4. Transparent Overlay...")
        self.qt_app = QApplication(sys.argv)
        self.overlay = TransparentOverlay(
            screen_width=self.screen_width,
            screen_height=self.screen_height,
            show_boxes=self.config.get("overlay.show_boxes", True),
            show_labels=self.config.get("overlay.show_labels", True),
            show_confidence=self.config.get("overlay.show_confidence", True),
            show_center_dot=self.config.get("overlay.show_center_dot", True),
            box_thickness=self.config.get("overlay.box_thickness", 2),
            font_scale=self.config.get("overlay.font_scale", 0.6)
        )
        self.overlay.show()
        print("   ✓ Overlay gotowy")

        # 5. Hotkey Manager
        print("\n5. Hotkey Manager...")
        self.hotkey_manager = HotkeyManager()
        self._register_hotkeys()

        print("\n" + "=" * 70)
        print("✓ Wszystkie komponenty gotowe")
        print("=" * 70)
        print()

    def _register_hotkeys(self):
        """Zarejestruj hotkeys."""
        # Toggle overlay
        self.hotkey_manager.register(
            self.config.get("hotkeys.toggle_overlay", "F9"),
            self.toggle_overlay,
            "Przełącz overlay"
        )

        # Toggle detection
        self.hotkey_manager.register(
            self.config.get("hotkeys.toggle_detection", "F10"),
            self.toggle_detection,
            "Przełącz detekcję"
        )

        # Increase confidence
        self.hotkey_manager.register(
            self.config.get("hotkeys.increase_confidence", "F11"),
            self.increase_confidence,
            "Zwiększ confidence (+0.05)"
        )

        # Decrease confidence
        self.hotkey_manager.register(
            self.config.get("hotkeys.decrease_confidence", "F12"),
            self.decrease_confidence,
            "Zmniejsz confidence (-0.05)"
        )

        # Quit
        self.hotkey_manager.register(
            self.config.get("hotkeys.quit", "ctrl+q"),
            self.quit,
            "Zakończ program"
        )

    def toggle_overlay(self):
        """Przełącz widoczność overlay."""
        self.overlay_visible = not self.overlay_visible
        self.overlay.set_visibility(self.overlay_visible)
        status = "WŁĄCZONY" if self.overlay_visible else "WYŁĄCZONY"
        print(f"\n[Overlay] {status}")

    def toggle_detection(self):
        """Przełącz detekcję."""
        self.detection_enabled = not self.detection_enabled
        status = "WŁĄCZONA" if self.detection_enabled else "WYŁĄCZONA"
        print(f"\n[Detekcja] {status}")

        if not self.detection_enabled:
            self.overlay.update_detections([])

    def increase_confidence(self):
        """Zwiększ próg confidence."""
        if self.detector:
            current = self.detector.conf_threshold
            new_value = min(1.0, current + 0.05)
            self.detector.update_confidence_threshold(new_value)
            print(f"\n[Confidence] {current:.2f} -> {new_value:.2f}")

    def decrease_confidence(self):
        """Zmniejsz próg confidence."""
        if self.detector:
            current = self.detector.conf_threshold
            new_value = max(0.0, current - 0.05)
            self.detector.update_confidence_threshold(new_value)
            print(f"\n[Confidence] {current:.2f} -> {new_value:.2f}")

    def quit(self):
        """Zakończ program."""
        print("\n\nZamykanie...")
        self.running = False

    def process_frame(self):
        """Przetwórz pojedynczą klatkę."""
        if not self.running:
            return

        # Capture
        frame = self.capture.capture_frame()

        # Detection
        if self.detection_enabled and self.detector:
            # YOLO inference
            detections = self.detector.detect(frame)

            # Stabilization
            if self.config.get("stabilization.enabled", True):
                detections = self.stabilizer.update(detections)

            # Update overlay
            self.overlay.update_detections(detections)

            # Update FPS info
            self.overlay.update_debug_info(
                fps=self.capture.get_fps(),
                show_fps=self.config.get("debug.show_fps", True),
                show_detection_count=self.config.get("debug.show_detection_count", True)
            )

    def run(self):
        """Uruchom aplikację."""
        if self.detector is None:
            print("\n❌ Nie można uruchomić - brak modelu YOLO!")
            print("   Wytrenuj model lub pobierz gotowy model.")
            return

        print("\n🚀 Uruchamianie...")
        print()
        print("Program działa! Sterowanie:")
        print()

        self.running = True
        self.hotkey_manager.start()

        # Timer dla Qt (przetwarzanie klatek)
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)

        # FPS inference z config
        inference_fps = self.config.get("inference.fps", 30)
        interval_ms = int(1000 / inference_fps)
        self.timer.start(interval_ms)

        print(f"✓ Inference FPS: {inference_fps}")
        print(f"✓ Capture FPS: {self.config.get('capture.fps', 60)}")
        print()
        print("=" * 70)
        print("APLIKACJA URUCHOMIONA".center(70))
        print("=" * 70)
        print()

        # Qt event loop
        try:
            sys.exit(self.qt_app.exec_())
        except KeyboardInterrupt:
            print("\n\nPrzerwano przez użytkownika")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup zasobów."""
        print("\nSprzątanie...")

        self.running = False

        if hasattr(self, 'timer'):
            self.timer.stop()

        self.hotkey_manager.stop()
        self.capture.close()

        print("✓ Zakończono")


def main():
    """Główna funkcja."""
    import argparse

    parser = argparse.ArgumentParser(
        description="YOLO Object Detection - System wykrywania obiektów w grze",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady użycia:
  python main.py                          # Domyślna konfiguracja
  python main.py --config my_config.json  # Własna konfiguracja

Sterowanie (domyślne):
  F9      - Przełącz overlay
  F10     - Przełącz detekcję
  F11     - Zwiększ confidence
  F12     - Zmniejsz confidence
  Ctrl+Q  - Zakończ program
        """
    )

    parser.add_argument(
        "--config", "-c",
        default=None,
        help="Ścieżka do pliku konfiguracyjnego JSON"
    )

    args = parser.parse_args()

    # Uruchom aplikację
    app = YOLODetectionApp(config_path=args.config)
    app.run()


if __name__ == "__main__":
    main()
