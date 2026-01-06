# YOLO Object Detection - System Wykrywania Obiektów

System wykrywania skrzynek/loot/obiektów w grze oparty **WYŁĄCZNIE** o analizę obrazu (Computer Vision + Machine Learning) i rysowanie overlay.

**✅ Bezpieczny - bez ingerencji w grę:**
- ❌ Nie czyta pamięci gry
- ❌ Nie robi DLL injection
- ❌ Nie hookuje DirectX
- ❌ Nie omija anti-cheat
- ✅ Tylko analiza obrazu i overlay

## 🖥️ Specyfikacja Sprzętowa

System zoptymalizowany dla:
- **CPU:** AMD Ryzen 7 5700X3D (8 rdzeni, 16 wątków)
- **GPU:** AMD Radeon RX 7900 GRE
- **OS:** Windows (DirectML) / Linux (ROCm)

## ⚡ Cechy Systemu

### Computer Vision
- **Model:** YOLOv8n (ONNX)
- **Akceleracja:** DirectML (Windows) / ROCm (Linux) dla AMD GPU
- **Inference FPS:** 30 FPS (konfigurowalne)
- **Capture FPS:** 60 FPS (konfigurowalne)

### Stabilizacja Detekcji
- **EMA** (Exponential Moving Average) - wygładzanie pozycji
- **IoU Tracking** - śledzenie obiektów między klatkami
- **TTL** (Time To Live) - podtrzymanie boxów

### Overlay
- Transparentne okno always-on-top
- Click-through (można klikać przez nie)
- Kolorowanie wg confidence
- Debug HUD (FPS, liczba detekcji)

## 📁 Struktura Projektu

```
Radar-Win-Linux-Beta/
├── main.py                      # Główna aplikacja
├── requirements.txt             # Zależności Python
├── config/
│   └── default_config.json     # Domyślna konfiguracja
├── data/
│   ├── raw/                    # Surowe screenshoty
│   ├── labeled/                # Oznaczony dataset
│   │   ├── images/
│   │   │   ├── train/
│   │   │   └── val/
│   │   └── labels/
│   │       ├── train/
│   │       └── val/
│   ├── models/                 # Modele ONNX
│   └── dataset.yaml            # Konfiguracja datasetu
├── scripts/
│   ├── collect_dataset.py      # Zbieranie screensh otów
│   └── train_yolo.py           # Trening YOLO
└── src/
    ├── capture/
    │   └── screen_capture.py   # Screen capture (MSS)
    ├── detection/
    │   ├── yolo_detector.py    # Detektor YOLO ONNX
    │   └── stabilizer.py       # Stabilizacja detekcji
    ├── overlay/
    │   └── transparent_overlay.py  # Transparentny overlay
    └── utils/
        ├── config.py           # Zarządzanie konfiguracją
        └── hotkey_manager.py   # Obsługa hotkeys
```

## 🚀 Instalacja

### 1. Wymagania
- Python 3.8+
- pip

### 2. Instalacja zależności

**Windows (AMD GPU):**
```bash
pip install -r requirements.txt
```

**Linux (AMD GPU z ROCm):**
```bash
# Najpierw zainstaluj ROCm
pip install -r requirements.txt

# PyTorch z ROCm
pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm5.7
```

### 3. Struktura katalogów
```bash
python -c "import os; [os.makedirs(d, exist_ok=True) for d in ['data/raw', 'data/labeled/images/train', 'data/labeled/images/val', 'data/labeled/labels/train', 'data/labeled/labels/val', 'data/models', 'runs']]"
```

## 📊 Przygotowanie Datasetu

### Krok 1: Zbieranie Screenshotów

```bash
python scripts/collect_dataset.py --output data/raw --monitor 0
```

**Sterowanie:**
- `SPACJA` - Zapisz screenshot
- `P` - Pauza/wznów
- `Q` - Wyjdź

**Zalecana liczba screenshotów:**
- Minimum: 300-500
- Zalecane: 800-1500
- Bardzo dobre: 3000+

**Różnorodność:**
- Różne mapy
- Różne odległości
- Różne kąty kamery
- Różne warunki oświetlenia

### Krok 2: Oznaczanie (Labeling)

Użyj jednego z narzędzi:
- **LabelImg** - https://github.com/HumanSignal/labelImg
- **CVAT** - https://cvat.ai
- **Roboflow** - https://roboflow.com

**Format:** YOLO
```
<class_id> <x_center> <y_center> <width> <height>
```

**Klasy:**
- `0` - crate (skrzynka/loot)

**Umieść pliki:**
```
data/labeled/images/train/*.png  (80% zdjęć)
data/labeled/images/val/*.png    (20% zdjęć)
data/labeled/labels/train/*.txt  (etykiety)
data/labeled/labels/val/*.txt    (etykiety)
```

## 🎯 Trening Modelu

### Podstawowy trening (YOLOv8n)

```bash
python scripts/train_yolo.py --model n --epochs 100 --batch 16 --export
```

### Opcje treningu

```bash
# YOLOv8s (większy model, lepsza dokładność)
python scripts/train_yolo.py --model s --epochs 100 --batch 8 --export

# Niestandardowe parametry
python scripts/train_yolo.py \
  --model n \
  --epochs 150 \
  --batch 32 \
  --imgsz 640 \
  --workers 16 \
  --export
```

**Parametry:**
- `--model` - Rozmiar modelu: `n` (nano), `s` (small), `m` (medium)
- `--epochs` - Liczba epok (50-100 zalecane)
- `--batch` - Rozmiar batcha (8-32, dostosuj do RAM GPU)
- `--imgsz` - Rozmiar obrazu (640 zalecane)
- `--workers` - Liczba workerów (16 dla Ryzen 7 5700X3D)
- `--export` - Eksportuj do ONNX po treningu

### Cel metryk:
- **Precision** ≥ 0.90
- **Recall** ≥ 0.85
- **mAP50** ≥ 0.85

### Tylko eksport (bez treningu)

```bash
python scripts/train_yolo.py --export-only
```

Po treningu model ONNX będzie w: `data/models/best.onnx`

## 🎮 Uruchomienie Aplikacji

### Podstawowe uruchomienie

```bash
python main.py
```

### Z własną konfiguracją

```bash
python main.py --config my_config.json
```

## ⌨️ Sterowanie

| Klawisz | Akcja |
|---------|-------|
| **F9** | Przełącz overlay (pokaż/ukryj) |
| **F10** | Przełącz detekcję (włącz/wyłącz) |
| **F11** | Zwiększ próg confidence (+0.05) |
| **F12** | Zmniejsz próg confidence (-0.05) |
| **Ctrl+Q** | Zakończ program |

## ⚙️ Konfiguracja

Edytuj `config/default_config.json`:

### Model
```json
{
  "model": {
    "path": "data/models/best.onnx",
    "imgsz": 640,
    "confidence_threshold": 0.5,
    "nms_threshold": 0.45
  }
}
```

### Capture
```json
{
  "capture": {
    "fps": 60,
    "monitor": 0
  }
}
```

### Inference
```json
{
  "inference": {
    "enabled": true,
    "fps": 30,
    "use_gpu": true,
    "gpu_device": "DirectML"
  }
}
```

### Stabilizacja
```json
{
  "stabilization": {
    "enabled": true,
    "ema_alpha": 0.7,
    "iou_threshold": 0.5,
    "ttl_frames": 5,
    "min_box_size": 20
  }
}
```

### Overlay
```json
{
  "overlay": {
    "enabled": true,
    "show_boxes": true,
    "show_labels": true,
    "show_confidence": true,
    "show_center_dot": true,
    "box_thickness": 2
  }
}
```

### Wydajność
```json
{
  "performance": {
    "async_inference": true,
    "thread_count": 16
  }
}
```

## 🔧 Troubleshooting

### Problem: "DirectML niedostępny"
**Rozwiązanie:**
```bash
pip install onnxruntime-directml --upgrade
```

### Problem: "Model nie znaleziony"
**Rozwiązanie:**
1. Wytrenuj model: `python scripts/train_yolo.py --export`
2. Lub skopiuj gotowy model do `data/models/best.onnx`

### Problem: Niska wydajność
**Rozwiązanie:**
1. Zmniejsz `inference.fps` w konfiguracji (np. 15 zamiast 30)
2. Zmniejsz `capture.fps` (np. 30 zamiast 60)
3. Użyj mniejszego modelu (`yolov8n` zamiast `yolov8s`)

### Problem: Za dużo fałszywych detekcji
**Rozwiązanie:**
1. Zwiększ `confidence_threshold` (np. 0.7 zamiast 0.5)
2. Użyj F11 podczas działania programu

### Problem: Drgające boxy
**Rozwiązanie:**
1. Zwiększ `ema_alpha` w konfiguracji (np. 0.8)
2. Zwiększ `ttl_frames` (np. 10)

## 📈 Optymalizacja dla AMD GPU

### Windows (DirectML)
```python
# Automatycznie wykrywane
# Używa onnxruntime-directml
```

### Linux (ROCm)
```bash
# Zainstaluj ROCm
# https://rocmdocs.amd.com/

# Zainstaluj onnxruntime-rocm
pip install onnxruntime-rocm

# PyTorch z ROCm (dla treningu)
pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm5.7
```

## 🎯 Pipeline Działania

```
┌─────────────────┐
│  Screen Capture │ (60 FPS)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Preprocessing │ (Resize, Normalize)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  YOLO Inference │ (30 FPS, GPU)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      NMS        │ (Non-Maximum Suppression)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stabilization  │ (EMA, IoU, TTL)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Overlay     │ (Transparent Window)
└─────────────────┘
```

## 📝 Przykładowy Workflow

### 1. Zbieranie Datasetu (3-7 dni)
```bash
# Uruchom grę w oknie/borderless
python scripts/collect_dataset.py

# Graj normalnie, co chwilę wciskaj SPACJĘ przy skrzynkach
# Cel: 800-1500 screenshotów
```

### 2. Oznaczanie (2-4 dni)
```bash
# Użyj LabelImg lub CVAT
# Oznacz skrzynki bounding boxami
# Zapisz w formacie YOLO
```

### 3. Trening (1-2 dni)
```bash
# Trenuj model
python scripts/train_yolo.py --model n --epochs 100 --batch 16 --export

# Czekaj na zakończenie (kilka godzin na RX 7900 GRE)
# Model pojawi się w data/models/best.onnx
```

### 4. Uruchomienie
```bash
# Uruchom aplikację
python main.py

# Uruchom grę
# Ciesz się detekcją! 🎮
```

## 🛡️ Bezpieczeństwo

Ten system jest **w 100% bezpieczny** ponieważ:

1. **Nie modyfikuje gry** - tylko odczyt ekranu
2. **Nie czyta pamięci** - brak dostępu do procesu gry
3. **Nie hookuje** - brak DLL injection czy hooków
4. **Tylko overlay** - rysowanie na ekranie jak OBS

**Podobne do:**
- Discord overlay
- MSI Afterburner overlay
- Fraps FPS counter
- OBS Display Capture

## 📊 Wymagania Systemowe

### Minimalne
- CPU: 4 rdzenie
- RAM: 8 GB
- GPU: Zintegrowana (CPU mode)
- Dysk: 2 GB

### Zalecane (dla pełnej wydajności)
- CPU: AMD Ryzen 7 5700X3D lub lepszy
- RAM: 16 GB
- GPU: AMD RX 7900 GRE lub lepsze
- Dysk: 5 GB SSD

## 📄 Licencja

MIT License - używaj jak chcesz, ale na własną odpowiedzialność.

## ⚠️ Disclaimer

Ten software jest stworzony **wyłącznie w celach edukacyjnych** do nauki Computer Vision i Machine Learning.

Użytkownik ponosi pełną odpowiedzialność za sposób użycia tego oprogramowania.

---

**Autor:** Claude
**Data:** 2026
**Wersja:** 1.0.0