# 🔨 Instrukcje Kompilacji - Build Instructions

Instrukcje kompilacji aplikacji YOLO Object Detection do pliku .exe.

## 📋 Wymagania

- **Windows** (dla plików .cmd)
- **Python 3.8+** zainstalowany i w PATH
- **pip** zainstalowany
- **git** (opcjonalnie)

## ⚠️ WAŻNE - Przed Kompilacją!

### Problem z NumPy i Python 3.15

Jeśli używasz **Python 3.15** (alpha/beta) lub widzisz błąd kompilacji NumPy:

```
ERROR: Unknown compiler(s): [['cl'], ['gcc'], ['clang']]
```

**ROZWIĄZANIE - Wybierz jedno:**

#### Opcja 1: Użyj skryptu instalacyjnego (ZALECANE)

```cmd
install_deps.cmd
```

Ten skrypt:
- ✅ Instaluje prekompilowany NumPy
- ✅ Rozwiązuje problemy z kompilatorami
- ✅ Instaluje wszystkie zależności poprawnie

#### Opcja 2: Zainstaluj Visual Studio Build Tools

1. Pobierz: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
2. Zainstaluj "Desktop development with C++"
3. Uruchom ponownie `build.cmd`

#### Opcja 3: Downgrade Python (najbardziej stabilne)

Użyj stabilnej wersji:
- **Python 3.11.x** - https://www.python.org/downloads/
- **Python 3.12.x** - https://www.python.org/downloads/

## 🚀 Szybka Kompilacja

### Jeden skrypt robi wszystko!

```cmd
build.cmd
```

**Co robi:**
1. ✅ Automatycznie znajduje najlepszą wersję Python (priorytet 3.11)
2. ✅ Aktualizuje pip
3. ✅ Instaluje wszystkie zależności
4. ✅ Weryfikuje instalację pakietów
5. ✅ Czyści poprzednie buildy
6. ✅ Kompiluje aplikację do .exe
7. ✅ Zapisuje logi do `logs/build_*.log`

**Czas kompilacji:**
- Pierwsze uruchomienie: 5-10 minut
- Kolejne: 3-5 minut

### Opcjonalnie: Instalacja zależności osobno

Jeśli chcesz tylko zainstalować zależności bez kompilacji:

```cmd
install_deps.cmd
```

Ten skrypt tylko instaluje pakiety (nie kompiluje).

## 📂 Wynik Kompilacji

Po udanej kompilacji znajdziesz:

```
dist/
└── YOLODetection.exe    # Skompilowana aplikacja
```

Dodatkowo:
```
build/                   # Pliki tymczasowe (można usunąć)
logs/
└── build_*.log         # Logi kompilacji
```

## 🎯 Ręczna Kompilacja (Zaawansowana)

### Krok 1: Instalacja zależności

```cmd
pip install -r requirements.txt
```

### Krok 2: Kompilacja

**Opcja A - Jeden plik (onefile):**
```cmd
pyinstaller --onefile --windowed --name=YOLODetection main.py
```

**Opcja B - Z plikiem .spec:**
```cmd
pyinstaller YOLODetection.spec
```

**Opcja C - Pełna konfiguracja:**
```cmd
pyinstaller ^
    --name=YOLODetection ^
    --onefile ^
    --windowed ^
    --add-data="config;config" ^
    --add-data="data/classes.txt;data" ^
    --add-data="data/dataset.yaml;data" ^
    --hidden-import=PyQt5 ^
    --hidden-import=cv2 ^
    --collect-all=onnxruntime ^
    --noconfirm ^
    --clean ^
    main.py
```

## 📝 Parametry PyInstaller

| Parametr | Opis |
|----------|------|
| `--onefile` | Tworzy jeden plik .exe |
| `--windowed` | Ukrywa okno konsoli (dla GUI) |
| `--console` | Pokazuje okno konsoli (dla debugowania) |
| `--name=NAME` | Nazwa pliku .exe |
| `--add-data` | Dodaje pliki danych |
| `--hidden-import` | Importy, które PyInstaller może pominąć |
| `--collect-all` | Zbiera wszystkie pliki pakietu |
| `--clean` | Czyści cache przed buildem |
| `--noconfirm` | Nadpisuje bez pytania |

## 🐛 Debugowanie

### Problem: "Python nie jest zainstalowany"
**Rozwiązanie:**
1. Zainstaluj Python z https://www.python.org/
2. Zaznacz "Add Python to PATH" podczas instalacji

### Problem: "pip nie jest zainstalowany"
**Rozwiązanie:**
```cmd
python -m ensurepip --upgrade
```

### Problem: "ModuleNotFoundError" w .exe
**Rozwiązanie:**
Dodaj brakujący moduł do `hiddenimports` w `YOLODetection.spec`:
```python
hiddenimports = [
    'modul_name',  # Dodaj tutaj
    ...
]
```

### Problem: .exe jest za duży
**Rozwiązanie:**
1. Usuń nieużywane pakiety z `requirements.txt`
2. Dodaj wykluczenia w `.spec`:
```python
excludes=[
    'matplotlib',
    'pandas',
    'scipy',
]
```

### Problem: .exe działa wolno
**Rozwiązanie:**
Użyj `--onedir` zamiast `--onefile`:
```cmd
pyinstaller --onedir --name=YOLODetection main.py
```

## 📊 Rozmiar Pliku

Typowe rozmiary:
- **Onefile:** ~500-800 MB (wszystko w jednym)
- **Onedir:** ~1-1.5 GB (rozpakowane)

Duży rozmiar wynika z:
- PyTorch (~400 MB)
- ONNX Runtime (~200 MB)
- OpenCV (~100 MB)
- PyQt5 (~50 MB)

## 🔍 Weryfikacja Buildu

Po kompilacji sprawdź:

```cmd
# Przejdź do katalogu dist
cd dist

# Uruchom aplikację
YOLODetection.exe

# Sprawdź logi
type ..\logs\build_*.log
```

## 📦 Dystrybucja

### Co wysłać użytkownikom:

**Opcja 1 - Onefile:**
```
YOLODetection.exe
config/default_config.json
data/models/best.onnx         # Wytrenowany model
```

**Opcja 2 - Package:**
```
dist/
├── YOLODetection.exe
├── _internal/               # Biblioteki
config/
data/
README.md
```

### Instalacja dla użytkownika:

1. Skopiuj pliki
2. Umieść wytrenowany model w `data/models/best.onnx`
3. Uruchom `YOLODetection.exe`
4. Gotowe! 🎉

## ⚙️ Konfiguracja .spec

Edytuj `YOLODetection.spec` aby:

**Ukryć konsolę:**
```python
console=False,  # Zmień True na False
```

**Dodać ikonę:**
```python
exe = EXE(
    ...
    icon='icon.ico',  # Dodaj plik icon.ico
    ...
)
```

**Wykluczyć moduły:**
```python
excludes=[
    'matplotlib',
    'pandas',
    'scipy',
    'jupyter',
]
```

## 🚀 Automatyzacja

### Skrypt CI/CD

Przykład dla GitHub Actions:

```yaml
name: Build

on: [push]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pyinstaller YOLODetection.spec
      - uses: actions/upload-artifact@v2
        with:
          name: YOLODetection
          path: dist/YOLODetection.exe
```

## 📌 Best Practices

1. **Zawsze testuj .exe** przed dystrybucją
2. **Zapisuj logi** każdego buildu
3. **Versionuj .spec** w git
4. **Dokumentuj zmiany** w buildzie
5. **Testuj na czystym systemie** bez Pythona

## 🔗 Linki

- PyInstaller Docs: https://pyinstaller.org/
- PyInstaller Spec: https://pyinstaller.org/en/stable/spec-files.html
- Common Issues: https://github.com/pyinstaller/pyinstaller/wiki

---

**Uwaga:** Pierwsze kompilacje mogą trwać dłużej (10-15 min) ze względu na cache PyInstallera.
