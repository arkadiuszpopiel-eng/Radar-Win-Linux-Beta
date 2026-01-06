"""
Transparentne okno overlay do rysowania detekcji.

Właściwości:
- Przezroczyste tło
- Always-on-top
- Click-through (można klikać przez nie)
- DPI aware
- Multi-monitor safe
"""

import sys
from typing import List, Tuple
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont

import platform

# Windows-specific dla click-through
if platform.system() == "Windows":
    try:
        import win32gui
        import win32con
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
        print("⚠ win32gui niedostępne - click-through może nie działać")
else:
    HAS_WIN32 = False


class TransparentOverlay(QWidget):
    """Transparentne okno overlay."""

    def __init__(self,
                 screen_width: int,
                 screen_height: int,
                 show_boxes: bool = True,
                 show_labels: bool = True,
                 show_confidence: bool = True,
                 show_center_dot: bool = True,
                 box_thickness: int = 2,
                 font_scale: float = 0.6):
        """Inicjalizacja overlay.

        Args:
            screen_width: Szerokość ekranu.
            screen_height: Wysokość ekranu.
            show_boxes: Czy rysować boxy.
            show_labels: Czy rysować etykiety.
            show_confidence: Czy pokazywać confidence.
            show_center_dot: Czy rysować kropkę w środku.
            box_thickness: Grubość linii boxów.
            font_scale: Rozmiar czcionki.
        """
        super().__init__()

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.show_boxes = show_boxes
        self.show_labels = show_labels
        self.show_confidence = show_confidence
        self.show_center_dot = show_center_dot
        self.box_thickness = box_thickness
        self.font_scale = font_scale

        # Detekcje do narysowania
        self.detections = []

        # Debug info
        self.debug_info = {
            "fps": 0,
            "detection_count": 0,
            "show_fps": True,
            "show_detection_count": True
        }

        # Kolory (BGR -> RGB conversion)
        self.color_high = QColor(0, 255, 0)  # Zielony
        self.color_medium = QColor(255, 255, 0)  # Żółty
        self.color_low = QColor(255, 165, 0)  # Pomarańczowy

        self._setup_window()

    def _setup_window(self):
        """Konfiguracja okna."""
        # Ustawienia okna
        self.setWindowTitle("YOLO Overlay")

        # Flagi: transparent, frameless, always on top
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )

        # Przezroczystość
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Click-through w Qt

        # Rozmiar i pozycja
        self.setGeometry(0, 0, self.screen_width, self.screen_height)

        # Windows click-through (WS_EX_TRANSPARENT)
        if HAS_WIN32 and platform.system() == "Windows":
            hwnd = int(self.winId())
            extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(
                hwnd,
                win32con.GWL_EXSTYLE,
                extended_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            )

    def update_detections(self, detections: List):
        """Zaktualizuj detekcje do narysowania.

        Args:
            detections: Lista obiektów Detection.
        """
        self.detections = detections
        self.debug_info["detection_count"] = len(detections)
        self.update()  # Trigger repaint

    def update_debug_info(self, fps: float = None, **kwargs):
        """Zaktualizuj informacje debug.

        Args:
            fps: FPS do wyświetlenia.
            **kwargs: Dodatkowe parametry debug.
        """
        if fps is not None:
            self.debug_info["fps"] = fps

        for key, value in kwargs.items():
            self.debug_info[key] = value

    def _get_color_by_confidence(self, confidence: float) -> QColor:
        """Pobierz kolor na podstawie confidence.

        Args:
            confidence: Wartość confidence (0-1).

        Returns:
            Kolor Qt.
        """
        if confidence >= 0.8:
            return self.color_high
        elif confidence >= 0.6:
            return self.color_medium
        else:
            return self.color_low

    def paintEvent(self, event):
        """Rysowanie overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Rysuj detekcje
        for detection in self.detections:
            color = self._get_color_by_confidence(detection.confidence)

            # Bounding box
            if self.show_boxes:
                pen = QPen(color, self.box_thickness)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)

                x1, y1 = detection.x1, detection.y1
                w, h = detection.width, detection.height

                painter.drawRect(x1, y1, w, h)

            # Center dot
            if self.show_center_dot:
                cx, cy = detection.center
                dot_size = 6

                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(
                    cx - dot_size // 2,
                    cy - dot_size // 2,
                    dot_size,
                    dot_size
                )

            # Label
            if self.show_labels:
                label_parts = [detection.class_name.upper()]

                if self.show_confidence:
                    label_parts.append(f"{detection.confidence:.2f}")

                label = " ".join(label_parts)

                # Font
                font = QFont("Arial", int(12 * self.font_scale), QFont.Bold)
                painter.setFont(font)

                # Tło etykiety
                metrics = painter.fontMetrics()
                text_width = metrics.width(label)
                text_height = metrics.height()

                label_x = detection.x1
                label_y = detection.y1 - text_height - 5

                # Clip do ekranu
                if label_y < 0:
                    label_y = detection.y1 + text_height + 5

                # Tło
                bg_color = QColor(color)
                bg_color.setAlpha(180)
                painter.setBrush(QBrush(bg_color))
                painter.setPen(Qt.NoPen)
                painter.drawRect(
                    label_x,
                    label_y,
                    text_width + 10,
                    text_height + 5
                )

                # Tekst
                painter.setPen(QPen(Qt.black))
                painter.drawText(
                    label_x + 5,
                    label_y + text_height,
                    label
                )

        # Debug HUD (lewy górny róg)
        if self.debug_info.get("show_fps") or self.debug_info.get("show_detection_count"):
            painter.setFont(QFont("Arial", 12, QFont.Bold))

            debug_lines = []

            if self.debug_info.get("show_fps"):
                debug_lines.append(f"FPS: {self.debug_info['fps']:.1f}")

            if self.debug_info.get("show_detection_count"):
                debug_lines.append(f"Detekcje: {self.debug_info['detection_count']}")

            y_offset = 30
            for line in debug_lines:
                # Tło
                metrics = painter.fontMetrics()
                text_width = metrics.width(line)
                text_height = metrics.height()

                bg_color = QColor(0, 0, 0)
                bg_color.setAlpha(150)
                painter.setBrush(QBrush(bg_color))
                painter.setPen(Qt.NoPen)
                painter.drawRect(10, y_offset - text_height, text_width + 20, text_height + 10)

                # Tekst
                painter.setPen(QPen(Qt.green))
                painter.drawText(20, y_offset, line)

                y_offset += text_height + 15

        painter.end()

    def set_visibility(self, visible: bool):
        """Ustaw widoczność overlay.

        Args:
            visible: True = pokaż, False = ukryj.
        """
        if visible:
            self.show()
        else:
            self.hide()

    def toggle_visibility(self):
        """Przełącz widoczność."""
        self.setVisible(not self.isVisible())
