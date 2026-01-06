"""
Moduł stabilizacji detekcji.

Rozwiązuje problemy:
- Drgania bounding boxów
- Znikanie obiektów między klatkami
- Niestabilne detekcje

Metody:
- EMA (Exponential Moving Average) - wygładzanie pozycji
- IoU tracking - śledzenie obiektów między klatkami
- TTL (Time To Live) - podtrzymanie boxów
"""

import numpy as np
from typing import List, Dict, Optional
from collections import defaultdict

from .yolo_detector import Detection


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """Oblicz IoU (Intersection over Union) między dwoma boxami.

    Args:
        box1: [x1, y1, x2, y2]
        box2: [x1, y1, x2, y2]

    Returns:
        IoU score (0-1).
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    # Pole przecięcia
    inter_x_min = max(x1_min, x2_min)
    inter_y_min = max(y1_min, y2_min)
    inter_x_max = min(x1_max, x2_max)
    inter_y_max = min(y1_max, y2_max)

    inter_w = max(0, inter_x_max - inter_x_min)
    inter_h = max(0, inter_y_max - inter_y_min)
    inter_area = inter_w * inter_h

    # Pole sumy
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = box1_area + box2_area - inter_area

    if union_area == 0:
        return 0.0

    return inter_area / union_area


class TrackedDetection:
    """Śledzona detekcja z EMA i TTL."""

    def __init__(self, detection: Detection, track_id: int, ema_alpha: float = 0.7, ttl: int = 5):
        """Inicjalizacja śledzonej detekcji.

        Args:
            detection: Początkowa detekcja.
            track_id: ID trackingu.
            ema_alpha: Współczynnik EMA (0-1, większy = bardziej responsywny).
            ttl: Time to live w klatkach.
        """
        self.track_id = track_id
        self.ema_alpha = ema_alpha
        self.max_ttl = ttl
        self.ttl = ttl

        # Wygładzona pozycja (EMA)
        self.smoothed_bbox = detection.bbox.copy()
        self.smoothed_confidence = detection.confidence

        # Ostatnia surowa detekcja
        self.last_detection = detection

        # Statystyki
        self.frames_tracked = 1
        self.last_seen_frame = 0

    def update(self, detection: Detection, frame_idx: int):
        """Zaktualizuj track nową detekcją (EMA).

        Args:
            detection: Nowa detekcja.
            frame_idx: Indeks klatki.
        """
        # EMA dla bounding boxa
        for i in range(4):
            self.smoothed_bbox[i] = (
                self.ema_alpha * detection.bbox[i] +
                (1 - self.ema_alpha) * self.smoothed_bbox[i]
            )

        # EMA dla confidence
        self.smoothed_confidence = (
            self.ema_alpha * detection.confidence +
            (1 - self.ema_alpha) * self.smoothed_confidence
        )

        # Aktualizacja stanu
        self.last_detection = detection
        self.ttl = self.max_ttl  # Reset TTL
        self.frames_tracked += 1
        self.last_seen_frame = frame_idx

    def decay(self):
        """Zmniejsz TTL (brak detekcji w tej klatce)."""
        self.ttl = max(0, self.ttl - 1)

    def is_alive(self) -> bool:
        """Sprawdź czy track jest aktywny.

        Returns:
            True jeśli TTL > 0.
        """
        return self.ttl > 0

    def get_detection(self) -> Detection:
        """Pobierz wygładzoną detekcję.

        Returns:
            Detection z wygładzoną pozycją.
        """
        return Detection(
            bbox=self.smoothed_bbox.copy(),
            confidence=self.smoothed_confidence,
            class_id=self.last_detection.class_id,
            class_name=self.last_detection.class_name
        )


class DetectionStabilizer:
    """Stabilizator detekcji z EMA, IoU tracking i TTL."""

    def __init__(self,
                 iou_threshold: float = 0.5,
                 ema_alpha: float = 0.7,
                 ttl_frames: int = 5,
                 min_box_size: int = 20):
        """Inicjalizacja stabilizatora.

        Args:
            iou_threshold: Próg IoU dla matching (0-1).
            ema_alpha: Współczynnik EMA (0-1).
            ttl_frames: Liczba klatek TTL.
            min_box_size: Minimalny rozmiar boxa (piksele).
        """
        self.iou_threshold = iou_threshold
        self.ema_alpha = ema_alpha
        self.ttl_frames = ttl_frames
        self.min_box_size = min_box_size

        # Aktywne tracki
        self.tracks: Dict[int, TrackedDetection] = {}
        self.next_track_id = 0
        self.frame_idx = 0

    def update(self, detections: List[Detection]) -> List[Detection]:
        """Zaktualizuj stabilizator z nowymi detekcjami.

        Args:
            detections: Lista surowych detekcji z YOLO.

        Returns:
            Lista stabilizowanych detekcji.
        """
        self.frame_idx += 1

        # Filtruj za małe boxy
        detections = [
            det for det in detections
            if det.width >= self.min_box_size and det.height >= self.min_box_size
        ]

        # Matching: dopasuj detekcje do istniejących tracków
        matched_tracks = set()
        matched_detections = set()

        for det_idx, detection in enumerate(detections):
            best_iou = 0.0
            best_track_id = None

            # Znajdź najlepszy match
            for track_id, track in self.tracks.items():
                if track_id in matched_tracks:
                    continue

                iou = calculate_iou(detection.bbox, track.smoothed_bbox)

                if iou > best_iou and iou >= self.iou_threshold:
                    best_iou = iou
                    best_track_id = track_id

            # Aktualizuj track lub stwórz nowy
            if best_track_id is not None:
                self.tracks[best_track_id].update(detection, self.frame_idx)
                matched_tracks.add(best_track_id)
                matched_detections.add(det_idx)
            else:
                # Nowy track
                new_track = TrackedDetection(
                    detection,
                    self.next_track_id,
                    ema_alpha=self.ema_alpha,
                    ttl=self.ttl_frames
                )
                self.tracks[self.next_track_id] = new_track
                self.next_track_id += 1

        # Decay nie-zmatchowanych tracków
        for track_id, track in list(self.tracks.items()):
            if track_id not in matched_tracks:
                track.decay()

                # Usuń martwe tracki
                if not track.is_alive():
                    del self.tracks[track_id]

        # Zwróć stabilizowane detekcje
        stabilized_detections = [
            track.get_detection()
            for track in self.tracks.values()
            if track.is_alive()
        ]

        return stabilized_detections

    def reset(self):
        """Zresetuj stabilizator."""
        self.tracks.clear()
        self.next_track_id = 0
        self.frame_idx = 0

    def get_stats(self) -> Dict:
        """Pobierz statystyki stabilizatora.

        Returns:
            Słownik ze statystykami.
        """
        return {
            "active_tracks": len(self.tracks),
            "frame_idx": self.frame_idx,
            "total_tracks_created": self.next_track_id
        }
