@echo off
REM ====================================================================
REM YOLO Object Detection - Instalacja Zależności (Windows Fix)
REM Naprawia problem z kompilacją numpy
REM ====================================================================

echo ====================================================================
echo INSTALACJA ZALEŻNOŚCI - WINDOWS FIX
echo ====================================================================
echo.

REM Sprawdź Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python nie jest zainstalowany!
    pause
    exit /b 1
)

echo Wersja Python:
python --version
echo.

echo UWAGA: Jeśli używasz Python 3.15 (alpha), zalecamy Python 3.11 lub 3.12
echo.

REM ====================================================================
REM KROK 1: Upgrade pip
REM ====================================================================
echo [1/4] Aktualizuję pip...
python -m pip install --upgrade pip

if errorlevel 1 (
    echo [WARNING] Nie udało się zaktualizować pip, kontynuuję...
)

echo.

REM ====================================================================
REM KROK 2: Instaluj numpy (prekompilowany)
REM ====================================================================
echo [2/4] Instaluję numpy (prekompilowany)...
echo Próbuję zainstalować numpy 1.26.4...

pip install numpy==1.26.4

if errorlevel 1 (
    echo.
    echo [ERROR] Nie udało się zainstalować numpy!
    echo.
    echo ROZWIĄZANIE:
    echo 1. Pobierz prekompilowany numpy ze strony:
    echo    https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
    echo.
    echo 2. Zainstaluj ręcznie:
    echo    pip install numpy-1.26.4+mkl-cp3XX-cp3XX-win_amd64.whl
    echo.
    echo 3. Lub zainstaluj Microsoft Visual Studio Build Tools:
    echo    https://visualstudio.microsoft.com/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] numpy zainstalowany
echo.

REM ====================================================================
REM KROK 3: Instaluj PyTorch
REM ====================================================================
echo [3/4] Instaluję PyTorch...
echo.

REM Sprawdź czy nvidia GPU
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo Nie wykryto NVIDIA GPU, instaluję CPU version...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
) else (
    echo Wykryto NVIDIA GPU, instaluję CUDA version...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
)

if errorlevel 1 (
    echo [WARNING] Nie udało się zainstalować PyTorch, kontynuuję...
)

echo.

REM ====================================================================
REM KROK 4: Instaluj pozostałe zależności
REM ====================================================================
echo [4/4] Instaluję pozostałe zależności...
echo.

if exist "requirements-windows.txt" (
    echo Używam requirements-windows.txt...
    pip install -r requirements-windows.txt --no-deps
    pip install -r requirements-windows.txt
) else (
    echo Używam requirements.txt...
    pip install -r requirements.txt --no-deps
    pip install -r requirements.txt
)

if errorlevel 1 (
    echo.
    echo [ERROR] Błąd podczas instalacji!
    echo Sprawdź błędy powyżej.
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo INSTALACJA ZAKOŃCZONA POMYŚLNIE!
echo ====================================================================
echo.
echo Sprawdź instalację:
echo.

python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import cv2; print('OpenCV:', cv2.__version__)"
python -c "import onnxruntime; print('ONNX Runtime:', onnxruntime.__version__)"

echo.
echo Wszystko gotowe! Możesz teraz uruchomić:
echo   build.cmd       - kompilacja do .exe
echo   run.cmd         - uruchomienie aplikacji
echo.

pause
