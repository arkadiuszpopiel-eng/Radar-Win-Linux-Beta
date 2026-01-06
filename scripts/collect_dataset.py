"""
Narzędzie do zbierania datasetu - screenshot collector.

Skróty klawiszowe:
- SPACJA: Zapisz screenshot
- Q: Wyjdź z programu
- P: Pauza/Wznów podgląd
"""

import cv2
import os
import time
import keyboard
from datetime import datetime
from pathlib import Path
import sys

# Dodaj src do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from capture.screen_capture import ScreenCapture
from utils.config import Config


class DatasetCollector:
    """Collector do zbierania screensh otów dla datasetu YOLO."""

    def __init__(self, output_dir: str = "data/raw", monitor: int = 0):
        """Inicjalizacja collectora.

        Args:
            output_dir: Katalog wyjściowy dla screenshotów.
            monitor: Numer monitora do przechwytywania.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.capture = ScreenCapture(monitor=monitor, target_fps=30)
        self.screenshot_count = 0
        self.paused = False

        print("=" * 60)
        print("DATASET COLLECTOR - Zbieranie screenshotów dla YOLO")
        print("=" * 60)
        print(f"Katalog wyjściowy: {self.output_dir}")
        print(f"Monitor: {monitor}")
        print()
        print("INSTRUKCJE:")
        print("  SPACJA  - Zapisz screenshot")
        print("  P       - Pauza/Wznów podgląd")
        print("  Q       - Wyjdź")
        print("=" * 60)
        print()

    def save_screenshot(self, frame):
        """Zapisz screenshot do pliku.

        Args:
            frame: Ramka do zapisania.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"screenshot_{timestamp}.png"
        filepath = self.output_dir / filename

        cv2.imwrite(str(filepath), frame)
        self.screenshot_count += 1

        print(f"✓ Zapisano: {filename} (Łącznie: {self.screenshot_count})")

    def run(self):
        """Uruchom collector."""
        print("Uruchamianie...")
        print("Okno podglądu pojawi się za chwilę...")
        print()

        for frame in self.capture.capture_stream():
            # Dodaj informacje na ekranie
            display_frame = frame.copy()

            # HUD
            cv2.putText(display_frame, f"Screenshots: {self.screenshot_count}",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display_frame, f"FPS: {self.capture.get_fps():.1f}",
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            if self.paused:
                cv2.putText(display_frame, "PAUZA", (10, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Instrukcje
            cv2.putText(display_frame, "SPACJA=Zapisz | P=Pauza | Q=Wyjdz",
                       (10, display_frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Wyświetl
            cv2.imshow("Dataset Collector", display_frame)

            # Obsługa klawiszy
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:  # Q lub ESC
                print("\nZamykanie...")
                break
            elif key == ord(' '):  # SPACJA
                self.save_screenshot(frame)
            elif key == ord('p'):  # P
                self.paused = not self.paused
                status = "PAUZA" if self.paused else "WZNOWIONO"
                print(f"\n{status}\n")

        # Cleanup
        self.capture.close()
        cv2.destroyAllWindows()

        print()
        print("=" * 60)
        print(f"Zakończono. Zebrano {self.screenshot_count} screenshotów.")
        print(f"Lokalizacja: {self.output_dir}")
        print("=" * 60)


def main():
    """Główna funkcja."""
    import argparse

    parser = argparse.ArgumentParser(description="Dataset Collector - zbieranie screenshotów")
    parser.add_argument("--output", "-o", default="data/raw",
                       help="Katalog wyjściowy (domyślnie: data/raw)")
    parser.add_argument("--monitor", "-m", type=int, default=0,
                       help="Numer monitora (domyślnie: 0 = wszystkie)")

    args = parser.parse_args()

    collector = DatasetCollector(output_dir=args.output, monitor=args.monitor)

    try:
        collector.run()
    except KeyboardInterrupt:
        print("\n\nPrzerwano przez użytkownika.")
        collector.capture.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
