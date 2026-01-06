# 🚀 QUICK START - Szybki Start

Skrócona instrukcja szybkiego uruchomienia systemu.

## ⚡ Szybka Instalacja (5 min)

```bash
# 1. Sklonuj / pobierz repozytorium

# 2. Zainstaluj zależności
pip install -r requirements.txt

# 3. Utwórz katalogi
python -c "import os; [os.makedirs(d, exist_ok=True) for d in ['data/raw', 'data/labeled/images/train', 'data/labeled/images/val', 'data/labeled/labels/train', 'data/labeled/labels/val', 'data/models', 'runs']]"
```

## 📸 Krok 1: Zbierz Dataset (30-60 min)

```bash
# Uruchom collector screenshotów
python scripts/collect_dataset.py

# W grze:
# - Graj normalnie
# - Gdy widzisz skrzynkę/loot - wciśnij SPACJĘ
# - Zbierz min. 500 zdjęć (zalecane: 1000+)
# - Wciśnij Q aby zakończyć
```

**Tipy:**
- Różne mapy, kąty, odległości
- Różne warunki oświetlenia
- Im więcej tym lepiej!

## 🏷️ Krok 2: Oznacz Zdjęcia (2-4 godz)

### Opcja A: LabelImg (zalecane dla początkujących)

```bash
# Instalacja
pip install labelImg

# Uruchom
labelImg data/raw data/classes.txt

# W LabelImg:
# 1. Zaznacz skrzynkę prostokątem (W)
# 2. Wybierz klasę "crate"
# 3. Zapisz (Ctrl+S)
# 4. Następne zdjęcie (D)
```

### Opcja B: Roboflow (łatwiejsze, online)

1. Wejdź na https://roboflow.com
2. Stwórz projekt (Object Detection, YOLO)
3. Upload zdjęcia z `data/raw`
4. Oznacz skrzynki
5. Eksportuj w formacie YOLO
6. Rozpakuj do `data/labeled/`

## 🎯 Krok 3: Trenuj Model (2-4 godz)

```bash
# Podstawowy trening (RX 7900 GRE: ~2-3 godz)
python scripts/train_yolo.py --model n --epochs 100 --batch 16 --export

# Czekaj...
# Model pojawi się w: data/models/best.onnx
```

## 🎮 Krok 4: Uruchom! (10 sek)

```bash
# Uruchom program
python main.py

# Uruchom grę
# Gotowe! 🎉
```

## ⌨️ Podstawowe Sterowanie

- **F9** - Pokaż/ukryj overlay
- **F10** - Włącz/wyłącz detekcję
- **F11/F12** - Dostosuj sensitivity
- **Ctrl+Q** - Wyjdź

## 🔧 Szybkie Rozwiązania Problemów

### "DirectML niedostępny"
```bash
pip install onnxruntime-directml --upgrade
```

### "Model nie znaleziony"
Wytrenuj model w Kroku 3 lub pobierz gotowy model.

### Za dużo/za mało detekcji
Użyj **F11/F12** aby dostosować sensitivity w czasie rzeczywistym.

### Wolno działa
W `config/default_config.json` zmień:
```json
{
  "inference": {
    "fps": 15
  },
  "capture": {
    "fps": 30
  }
}
```

## 📊 Minimalny Dataset

- **Absolutne minimum:** 300 zdjęć
- **Zalecane:** 800-1500 zdjęć
- **Profesjonalne:** 3000+ zdjęć

Więcej = lepsza dokładność!

## 🎯 Cel Treningu

Po treningu sprawdź metryki w `runs/train/.../results.png`:

- ✅ **mAP50 > 0.85** - Bardzo dobrze!
- ⚠️ **mAP50: 0.70-0.85** - Średnio, zbierz więcej danych
- ❌ **mAP50 < 0.70** - Za mało danych lub zły dataset

## 💡 Pro Tips

1. **Quality > Quantity** - Lepiej 500 dobrych zdjęć niż 1000 złych
2. **Różnorodność** - Różne mapy, kąty, oświetlenie
3. **Dokładne labeling** - Ciasne bounding boxy
4. **Testuj często** - Trenuj na małym datasecie, testuj, zbieraj więcej
5. **GPU = Speed** - RX 7900 GRE to 10x szybciej niż CPU

## 🚀 Całkowity Czas

- Konfiguracja: **5 min**
- Zbieranie: **1-2 godz** (podczas grania)
- Oznaczanie: **2-4 godz**
- Trening: **2-4 godz**
- **RAZEM: ~1 dzień pracy**

## 📞 Potrzebujesz Pomocy?

Sprawdź pełną dokumentację w `README.md`.

---

**Powodzenia! 🎮🤖**
