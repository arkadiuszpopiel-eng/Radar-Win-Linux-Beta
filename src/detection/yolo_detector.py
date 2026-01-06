"""
Moduł detekcji YOLO z użyciem ONNX Runtime.
Zoptymalizowany dla AMD RX 7900 GRE (DirectML/ROCm).
"""

import cv2
import numpy as np
import onnxruntime as ort
from typing import List, Tuple, Optional
import platform


class Detection:
    """Klasa reprezentująca pojedynczą detekcję."""

    def __init__(self, bbox: List[float], confidence: float, class_id: int, class_name: str):
        """Inicjalizacja detekcji.

        Args:
            bbox: Bounding box [x1, y1, x2, y2].
            confidence: Pewność detekcji (0-1).
            class_id: ID klasy.
            class_name: Nazwa klasy.
        """
        self.bbox = bbox
        self.confidence = confidence
        self.class_id = class_id
        self.class_name = class_name

    @property
    def x1(self) -> int:
        return int(self.bbox[0])

    @property
    def y1(self) -> int:
        return int(self.bbox[1])

    @property
    def x2(self) -> int:
        return int(self.bbox[2])

    @property
    def y2(self) -> int:
        return int(self.bbox[3])

    @property
    def center(self) -> Tuple[int, int]:
        """Środek bounding boxa."""
        cx = int((self.x1 + self.x2) / 2)
        cy = int((self.y1 + self.y2) / 2)
        return (cx, cy)

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def area(self) -> int:
        return self.width * self.height


class YOLODetector:
    """Detektor YOLO z ONNX Runtime i wsparciem AMD GPU."""

    def __init__(self,
                 model_path: str,
                 class_names: List[str],
                 conf_threshold: float = 0.5,
                 nms_threshold: float = 0.45,
                 input_size: int = 640,
                 use_gpu: bool = True):
        """Inicjalizacja detektora.

        Args:
            model_path: Ścieżka do modelu ONNX.
            class_names: Lista nazw klas.
            conf_threshold: Próg pewności (0-1).
            nms_threshold: Próg NMS.
            input_size: Rozmiar wejściowy modelu.
            use_gpu: Czy używać GPU (DirectML/ROCm).
        """
        self.model_path = model_path
        self.class_names = class_names
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.input_size = input_size
        self.use_gpu = use_gpu

        # Inicjalizuj ONNX session
        self.session = self._create_session()

        # Pobierz informacje o I/O
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [output.name for output in self.session.get_outputs()]

        print(f"✓ Załadowano model YOLO: {model_path}")
        print(f"  Input: {self.input_name}")
        print(f"  Outputs: {self.output_names}")

    def _create_session(self) -> ort.InferenceSession:
        """Utwórz ONNX Runtime session z odpowiednim providerem.

        Returns:
            ONNX InferenceSession.
        """
        providers = []
        system = platform.system()

        if self.use_gpu:
            if system == "Windows":
                # DirectML dla AMD GPU na Windows
                if "DmlExecutionProvider" in ort.get_available_providers():
                    providers.append("DmlExecutionProvider")
                    print("✓ Używam DirectML (AMD GPU)")
                else:
                    print("⚠ DirectML niedostępny")
            elif system == "Linux":
                # ROCm dla AMD GPU na Linux
                if "ROCMExecutionProvider" in ort.get_available_providers():
                    providers.append("ROCMExecutionProvider")
                    print("✓ Używam ROCm (AMD GPU)")
                else:
                    print("⚠ ROCm niedostępny")

        # CPU jako fallback
        providers.append("CPUExecutionProvider")

        # Opcje sesji dla wydajności
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 8  # Dla Ryzen 7 5700X3D
        sess_options.inter_op_num_threads = 8

        print(f"Providers: {providers}")

        return ort.InferenceSession(
            self.model_path,
            sess_options=sess_options,
            providers=providers
        )

    def preprocess(self, image: np.ndarray) -> Tuple[np.ndarray, float, Tuple[int, int]]:
        """Przygotuj obraz do inferencji.

        Args:
            image: Obraz wejściowy (BGR).

        Returns:
            Tuple: (preprocessed_image, scale, padding)
        """
        # Oryginalny rozmiar
        h, w = image.shape[:2]

        # Oblicz skalę (letterbox)
        scale = min(self.input_size / h, self.input_size / w)
        new_h, new_w = int(h * scale), int(w * scale)

        # Resize
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Padding do kwadratu
        pad_h = self.input_size - new_h
        pad_w = self.input_size - new_w
        top, left = pad_h // 2, pad_w // 2
        bottom, right = pad_h - top, pad_w - left

        padded = cv2.copyMakeBorder(
            resized, top, bottom, left, right,
            cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )

        # Normalizacja i konwersja
        # BGR -> RGB -> float32 -> normalize -> transpose
        blob = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
        blob = blob.astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))  # HWC -> CHW
        blob = np.expand_dims(blob, axis=0)  # Add batch dimension

        return blob, scale, (left, top)

    def postprocess(self,
                    outputs: np.ndarray,
                    scale: float,
                    padding: Tuple[int, int],
                    original_shape: Tuple[int, int]) -> List[Detection]:
        """Przetwórz wyjście modelu.

        Args:
            outputs: Wyjście z modelu.
            scale: Skala użyta w preprocessing.
            padding: Padding (left, top).
            original_shape: Oryginalny rozmiar obrazu (h, w).

        Returns:
            Lista detekcji.
        """
        # YOLOv8 output shape: (1, 84, 8400) -> transpose -> (8400, 84)
        # 84 = 4 (bbox) + 80 (classes COCO), ale dla 1 klasy: 5 = 4 + 1
        output = outputs[0]

        # Transpose jeśli potrzeba
        if len(output.shape) == 3:
            output = np.squeeze(output, axis=0)

        if output.shape[0] < output.shape[1]:
            output = output.T  # (84, 8400) -> (8400, 84)

        # Parse detections
        boxes = []
        confidences = []
        class_ids = []

        for detection in output:
            # Detection format: [cx, cy, w, h, conf, ...]
            cx, cy, w, h = detection[:4]
            class_scores = detection[4:]

            # Znajdź najlepszą klasę
            class_id = np.argmax(class_scores)
            confidence = class_scores[class_id]

            # Filtruj po confidence
            if confidence < self.conf_threshold:
                continue

            # Konwertuj cx, cy, w, h -> x1, y1, x2, y2
            x1 = cx - w / 2
            y1 = cy - h / 2
            x2 = cx + w / 2
            y2 = cy + h / 2

            # Odwróć padding
            pad_left, pad_top = padding
            x1 = (x1 - pad_left) / scale
            y1 = (y1 - pad_top) / scale
            x2 = (x2 - pad_left) / scale
            y2 = (y2 - pad_top) / scale

            # Clip do oryginalnego rozmiaru
            h, w = original_shape
            x1 = max(0, min(x1, w))
            y1 = max(0, min(y1, h))
            x2 = max(0, min(x2, w))
            y2 = max(0, min(y2, h))

            boxes.append([x1, y1, x2, y2])
            confidences.append(float(confidence))
            class_ids.append(int(class_id))

        # NMS (Non-Maximum Suppression)
        if len(boxes) > 0:
            indices = cv2.dnn.NMSBoxes(
                boxes, confidences,
                self.conf_threshold,
                self.nms_threshold
            )

            detections = []
            if len(indices) > 0:
                for i in indices.flatten():
                    detection = Detection(
                        bbox=boxes[i],
                        confidence=confidences[i],
                        class_id=class_ids[i],
                        class_name=self.class_names[class_ids[i]] if class_ids[i] < len(self.class_names) else "unknown"
                    )
                    detections.append(detection)

            return detections

        return []

    def detect(self, image: np.ndarray) -> List[Detection]:
        """Wykryj obiekty na obrazie.

        Args:
            image: Obraz wejściowy (BGR).

        Returns:
            Lista detekcji.
        """
        original_shape = image.shape[:2]

        # Preprocessing
        blob, scale, padding = self.preprocess(image)

        # Inference
        outputs = self.session.run(self.output_names, {self.input_name: blob})

        # Postprocessing
        detections = self.postprocess(outputs[0], scale, padding, original_shape)

        return detections

    def update_confidence_threshold(self, threshold: float):
        """Zaktualizuj próg pewności.

        Args:
            threshold: Nowy próg (0-1).
        """
        self.conf_threshold = max(0.0, min(1.0, threshold))
