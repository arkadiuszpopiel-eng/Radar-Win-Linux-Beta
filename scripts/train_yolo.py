"""
Skrypt do trenowania modelu YOLOv8 na AMD GPU (RX 7900 GRE).

Zoptymalizowany dla:
- CPU: AMD Ryzen 7 5700X3D (8 rdzeni, 16 wątków)
- GPU: AMD Radeon RX 7900 GRE

Wymagania:
1. Przygotowany dataset w formacie YOLO
2. Struktura katalogów:
   data/labeled/images/train/
   data/labeled/images/val/
   data/labeled/labels/train/
   data/labeled/labels/val/
"""

import os
import sys
from pathlib import Path
import torch
from ultralytics import YOLO
import yaml

# Dodaj src do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class YOLOTrainer:
    """Trainer dla modelu YOLO z optymalizacją AMD."""

    def __init__(self, model_size: str = "n", dataset_config: str = "data/dataset.yaml"):
        """Inicjalizacja trainera.

        Args:
            model_size: Rozmiar modelu ('n', 's', 'm', 'l', 'x')
                       n = nano (najszybszy, dla CPU/słabsze GPU)
                       s = small (balans)
                       m = medium (więcej dokładności)
            dataset_config: Ścieżka do pliku konfiguracyjnego datasetu.
        """
        self.model_size = model_size
        self.dataset_config = Path(dataset_config)
        self.model = None

        # Sprawdź dostępność GPU
        self.device = self._detect_device()

        print("=" * 60)
        print("YOLO TRAINER - Trening modelu detekcji")
        print("=" * 60)
        print(f"Model: YOLOv8{model_size}")
        print(f"Dataset: {self.dataset_config}")
        print(f"Urządzenie: {self.device}")
        print("=" * 60)
        print()

    def _detect_device(self) -> str:
        """Wykryj dostępne urządzenie obliczeniowe.

        Returns:
            Nazwa urządzenia ('cuda', 'cpu').
        """
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✓ Wykryto GPU: {gpu_name}")
            return "cuda"
        else:
            print("⚠ GPU niedostępne, używam CPU")
            print("  Dla AMD GPU zainstaluj: pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm5.7")
            return "cpu"

    def train(self,
              epochs: int = 100,
              batch: int = 16,
              imgsz: int = 640,
              workers: int = 16,
              patience: int = 50,
              save_dir: str = "runs/train",
              resume: bool = False):
        """Rozpocznij trening modelu.

        Args:
            epochs: Liczba epok treningowych (50-100 zalecane).
            batch: Rozmiar batcha (8-32, dostosuj do pamięci GPU).
            imgsz: Rozmiar obrazu wejściowego (640 zalecane).
            workers: Liczba workerów (16 dla Ryzen 7 5700X3D).
            patience: Early stopping patience.
            save_dir: Katalog do zapisywania wyników.
            resume: Wznów trening z ostatniego checkpointa.
        """
        # Załaduj model
        model_name = f"yolov8{self.model_size}.pt"
        print(f"Ładowanie modelu: {model_name}")
        self.model = YOLO(model_name)

        # Parametry treningu
        train_args = {
            "data": str(self.dataset_config),
            "epochs": epochs,
            "batch": batch,
            "imgsz": imgsz,
            "device": self.device,
            "workers": workers,
            "patience": patience,
            "save": True,
            "save_period": 10,  # Zapisuj checkpoint co 10 epok
            "project": save_dir,
            "name": f"yolov8{self.model_size}_crate_detector",
            "exist_ok": True,
            "pretrained": True,
            "optimizer": "AdamW",
            "verbose": True,
            "seed": 42,
            "deterministic": False,
            "single_cls": True,  # Single class (crate)
            "rect": False,  # Rectangular training
            "cos_lr": True,  # Cosine LR scheduler
            "close_mosaic": 10,  # Wyłącz mosaic ostatnie 10 epok
            "resume": resume,
            # Augmentacja
            "hsv_h": 0.015,
            "hsv_s": 0.7,
            "hsv_v": 0.4,
            "degrees": 10.0,
            "translate": 0.1,
            "scale": 0.5,
            "shear": 0.0,
            "perspective": 0.0,
            "flipud": 0.0,
            "fliplr": 0.5,
            "mosaic": 1.0,
            "mixup": 0.0,
            "copy_paste": 0.0,
        }

        print("\nParametry treningu:")
        for key, value in train_args.items():
            if key not in ['data']:
                print(f"  {key}: {value}")
        print()

        # Rozpocznij trening
        print("Rozpoczynam trening...")
        print()

        results = self.model.train(**train_args)

        print()
        print("=" * 60)
        print("TRENING ZAKOŃCZONY")
        print("=" * 60)
        print(f"Wyniki zapisane w: {save_dir}")
        print()
        print("Najlepszy model: runs/train/yolov8{}_crate_detector/weights/best.pt".format(self.model_size))
        print("=" * 60)

        return results

    def export_to_onnx(self, model_path: str = None, output_dir: str = "data/models"):
        """Eksportuj model do formatu ONNX.

        Args:
            model_path: Ścieżka do modelu .pt (jeśli None, użyj ostatniego trenowanego).
            output_dir: Katalog wyjściowy dla modelu ONNX.
        """
        if model_path is None:
            # Użyj ostatnio wytrenowanego modelu
            model_path = f"runs/train/yolov8{self.model_size}_crate_detector/weights/best.pt"

        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model nie znaleziony: {model_path}")

        print("=" * 60)
        print("EKSPORT DO ONNX")
        print("=" * 60)
        print(f"Model wejściowy: {model_path}")
        print()

        # Załaduj model
        model = YOLO(str(model_path))

        # Eksportuj do ONNX
        print("Eksportowanie...")
        output_path = model.export(
            format="onnx",
            dynamic=False,
            simplify=True,
            opset=12
        )

        # Przenieś do docelowego katalogu
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        final_path = output_dir / "best.onnx"

        import shutil
        shutil.copy(output_path, final_path)

        print()
        print("=" * 60)
        print("EKSPORT ZAKOŃCZONY")
        print("=" * 60)
        print(f"Model ONNX zapisany: {final_path}")
        print("=" * 60)

        return final_path


def main():
    """Główna funkcja."""
    import argparse

    parser = argparse.ArgumentParser(description="YOLO Trainer - trening modelu detekcji skrzynek")
    parser.add_argument("--model", "-m", default="n", choices=["n", "s", "m", "l", "x"],
                       help="Rozmiar modelu (n=nano, s=small, m=medium, l=large, x=xlarge)")
    parser.add_argument("--epochs", "-e", type=int, default=100,
                       help="Liczba epok treningowych")
    parser.add_argument("--batch", "-b", type=int, default=16,
                       help="Rozmiar batcha")
    parser.add_argument("--imgsz", "-i", type=int, default=640,
                       help="Rozmiar obrazu")
    parser.add_argument("--workers", "-w", type=int, default=16,
                       help="Liczba workerów (16 dla Ryzen 7 5700X3D)")
    parser.add_argument("--export", action="store_true",
                       help="Eksportuj do ONNX po treningu")
    parser.add_argument("--export-only", action="store_true",
                       help="Tylko eksport (bez treningu)")
    parser.add_argument("--resume", action="store_true",
                       help="Wznów trening")

    args = parser.parse_args()

    trainer = YOLOTrainer(model_size=args.model)

    try:
        if args.export_only:
            # Tylko eksport
            trainer.export_to_onnx()
        else:
            # Trening
            trainer.train(
                epochs=args.epochs,
                batch=args.batch,
                imgsz=args.imgsz,
                workers=args.workers,
                resume=args.resume
            )

            # Eksport jeśli zaznaczono
            if args.export:
                trainer.export_to_onnx()

    except KeyboardInterrupt:
        print("\n\nTrening przerwany przez użytkownika.")
    except Exception as e:
        print(f"\n\nBłąd: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
