@echo off
REM ====================================================================
REM YOLO Object Detection - Instalacja dla Python 3.11
REM ====================================================================

echo ====================================================================
echo INSTALACJA ZALEŻNOŚCI - PYTHON 3.11
echo ====================================================================
echo.

REM Znajdź Python 3.11
set "PYTHON311=C:\Python311\python.exe"
if not exist "%PYTHON311%" set "PYTHON311=C:\Program Files\Python311\python.exe"
if not exist "%PYTHON311%" set "PYTHON311=py -3.11"

REM Sprawdź czy Python 3.11 istnieje
%PYTHON311% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Nie znaleziono Python 3.11!
    echo.
    echo Sprawdzane lokalizacje:
    echo - C:\Python311\python.exe
    echo - C:\Program Files\Python311\python.exe
    echo - py -3.11
    echo.
    echo Uruchom: py -0
    echo Aby zobaczyć wszystkie zainstalowane wersje Python.
    echo.
    pause
    exit /b 1
)

echo Używam Python:
%PYTHON311% --version
echo.

REM ====================================================================
REM KROK 1: Upgrade pip
REM ====================================================================
echo [1/3] Aktualizuję pip...
%PYTHON311% -m pip install --upgrade pip

echo.

REM ====================================================================
REM KROK 2: Instaluj zależności
REM ====================================================================
echo [2/3] Instaluję zależności...
echo To może zająć kilka minut...
echo.

if exist "requirements-windows.txt" (
    echo Używam requirements-windows.txt...
    %PYTHON311% -m pip install -r requirements-windows.txt
) else (
    echo Używam requirements.txt...
    %PYTHON311% -m pip install -r requirements.txt
)

if errorlevel 1 (
    echo.
    echo [ERROR] Błąd podczas instalacji!
    echo.
    pause
    exit /b 1
)

echo.

REM ====================================================================
REM KROK 3: Weryfikacja
REM ====================================================================
echo [3/3] Sprawdzam instalację...
echo.

%PYTHON311% -c "import numpy; print('NumPy:', numpy.__version__)"
%PYTHON311% -c "import torch; print('PyTorch:', torch.__version__)"
%PYTHON311% -c "import cv2; print('OpenCV:', cv2.__version__)"
%PYTHON311% -c "import onnxruntime; print('ONNX Runtime:', onnxruntime.__version__)"
%PYTHON311% -c "import PyQt5; print('PyQt5: OK')"

echo.
echo ====================================================================
echo INSTALACJA ZAKOŃCZONA POMYŚLNIE!
echo ====================================================================
echo.
echo Możesz teraz uruchomić:
echo   build_py311.cmd  - kompilacja do .exe
echo   python main.py   - uruchomienie aplikacji
echo.

pause
