# 🔧 Fix Instalacji - Rozwiązanie Problemów

## ❌ Problem: Błąd kompilacji NumPy

Jeśli widzisz taki błąd:

```
ERROR: Unknown compiler(s): [['cl'], ['gcc'], ['clang']]
Running `cl /?` gave "[WinError 2] Nie można odnaleźć określonego pliku"
```

**Przyczyna:** NumPy próbuje się skompilować ze źródeł, ale brakuje kompilatora C.

## ✅ ROZWIĄZANIE - Wybierz najlepsze dla siebie:

### 🚀 Opcja 1: Automatyczny Fix (ZALECANE - 2 minuty)

Użyj naszego skryptu naprawczego:

```cmd
install_deps.cmd
```

**Co robi:**
1. ✅ Aktualizuje pip
2. ✅ Instaluje prekompilowany NumPy 1.26.4
3. ✅ Instaluje PyTorch (CPU lub CUDA)
4. ✅ Instaluje pozostałe zależności
5. ✅ Weryfikuje instalację

**To rozwiązuje 99% problemów!** 🎉

---

### 🔨 Opcja 2: Ręczna Instalacja (5 minut)

#### Krok 1: Zainstaluj NumPy ręcznie

```cmd
pip install numpy==1.26.4
```

#### Krok 2: Zainstaluj PyTorch

**Dla AMD GPU:**
```cmd
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

**Dla NVIDIA GPU:**
```cmd
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

#### Krok 3: Zainstaluj resztę

```cmd
pip install -r requirements-windows.txt
```

---

### 🏗️ Opcja 3: Zainstaluj Visual Studio Build Tools (20 minut)

Jeśli chcesz kompilować ze źródeł:

1. **Pobierz:** https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

2. **Zainstaluj** z komponentami:
   - ✅ Desktop development with C++
   - ✅ MSVC v143 - VS 2022 C++ x64/x86 build tools
   - ✅ Windows 11 SDK

3. **Restart** komputera

4. **Zainstaluj** pakiety:
   ```cmd
   pip install -r requirements.txt
   ```

**UWAGA:** To zajmuje ~10 GB na dysku!

---

### 🐍 Opcja 4: Downgrade Python (15 minut)

Twoja wersja Python: **3.15.0a3** (alpha - niestabilna!)

**Zalecamy stabilną wersję:**

1. **Odinstaluj** Python 3.15

2. **Pobierz i zainstaluj:**
   - **Python 3.11.9** (najbardziej stabilny): https://www.python.org/downloads/release/python-3119/
   - **Python 3.12.7** (nowszy): https://www.python.org/downloads/release/python-3127/

3. **Zaznacz:** "Add Python to PATH"

4. **Zainstaluj** zależności:
   ```cmd
   pip install -r requirements.txt
   ```

**To najpewniejsze rozwiązanie!** ✅

---

## 🎯 Jak Sprawdzić Co Poszło Źle?

Uruchom test:

```cmd
python -c "import numpy; print('NumPy OK:', numpy.__version__)"
```

**Wyniki:**
- ✅ `NumPy OK: 1.26.4` - Działa!
- ❌ `ModuleNotFoundError: No module named 'numpy'` - Nie zainstalowane
- ❌ `ImportError: DLL load failed` - Zły kompilator/wersja

---

## 📋 Pełny Test Instalacji

```cmd
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import cv2; print('OpenCV:', cv2.__version__)"
python -c "import onnxruntime; print('ONNX:', onnxruntime.__version__)"
python -c "import PyQt5; print('PyQt5: OK')"
```

Wszystkie powinny zadziałać bez błędów.

---

## 🆘 Dalej Nie Działa?

### Problem: "pip: command not found"

**Rozwiązanie:**
```cmd
python -m pip install --upgrade pip
```

### Problem: "Access denied" / "Permission error"

**Rozwiązanie:** Uruchom jako Administrator lub użyj:
```cmd
pip install --user <pakiet>
```

### Problem: PyTorch za duży / za długo się instaluje

**Rozwiązanie:** Użyj CPU version (mniejszy):
```cmd
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Problem: "No matching distribution found"

**Rozwiązanie:** Zaktualizuj pip:
```cmd
python -m pip install --upgrade pip
pip install <pakiet>
```

---

## 🎓 Dlaczego To Się Dzieje?

**NumPy** jest napisany w **C** dla wydajności. Gdy instalujesz przez pip:

1. **Jeśli są prekompilowane "wheels" (.whl)** → Szybka instalacja ✅
2. **Jeśli NIE ma wheels** → Kompilacja ze źródeł → Wymaga kompilatora C ❌

**Python 3.15** jest alpha → Mało pakietów ma gotowe wheels → Próba kompilacji → Błąd!

**Rozwiązanie:** Użyj starszego NumPy (1.26.4) lub stabilnego Pythona (3.11/3.12).

---

## 📞 Potrzebujesz Pomocy?

1. Sprawdź logi: `logs/build_*.log`
2. Przeczytaj: [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)
3. GitHub Issues: https://github.com/your-repo/issues

---

**TL;DR:** Uruchom `install_deps.cmd` i problem zniknie! 🚀
