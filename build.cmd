@echo off
REM ====================================================================
REM YOLO Object Detection - Universal Build Script
REM Kompilacja aplikacji do pliku .exe
REM Automatycznie wykrywa najlepszą wersję Python i instaluje zależności
REM ====================================================================

setlocal enabledelayedexpansion

echo ====================================================================
echo YOLO OBJECT DETECTION - UNIVERSAL BUILD SCRIPT
echo ====================================================================
echo.

REM Ustawienia
set "BUILD_DIR=build"
set "DIST_DIR=dist"
set "LOG_DIR=logs"
set "BUILD_LOG=%LOG_DIR%\build_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "APP_NAME=YOLODetection"
set "VERSION=1.0.0"
set "PYTHON_CMD="

REM Utwórz katalog logów
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Rozpocznij logowanie
echo [%date% %time%] Build started > "%BUILD_LOG%"

REM ====================================================================
REM KROK 1: Znajdź najlepszą wersję Python
REM ====================================================================
echo [1/8] Wyszukiwanie najlepszej wersji Python...
echo [%date% %time%] [1/8] Finding best Python version >> "%BUILD_LOG%"
echo.

REM Priorytet: 3.11 -> 3.12 -> 3.10 -> py -> python
py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.11"
    goto :python_found
)

py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.12"
    goto :python_found
)

py -3.10 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.10"
    goto :python_found
)

py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    goto :python_found
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :python_found
)

REM Nie znaleziono Python
echo [ERROR] Python nie jest zainstalowany!
echo.
echo Zainstaluj Python z: https://www.python.org/downloads/
echo Zalecane: Python 3.11.9
echo.
echo [%date% %time%] [ERROR] Python not found >> "%BUILD_LOG%"
pause
goto :error

:python_found
echo Znaleziono Python:
%PYTHON_CMD% --version
%PYTHON_CMD% --version >> "%BUILD_LOG%"
echo [OK] Używam: %PYTHON_CMD%
echo [%date% %time%] Using: %PYTHON_CMD% >> "%BUILD_LOG%"
echo.

REM ====================================================================
REM KROK 2: Upgrade pip
REM ====================================================================
echo [2/8] Aktualizuję pip...
echo [%date% %time%] [2/8] Upgrading pip >> "%BUILD_LOG%"

%PYTHON_CMD% -m pip install --upgrade pip >> "%BUILD_LOG%" 2>&1
echo [OK] pip zaktualizowany
echo.

REM ====================================================================
REM KROK 3: Instaluj NumPy (prekompilowany)
REM ====================================================================
echo [3/7] Instaluję NumPy (prekompilowany)...
echo [%date% %time%] [3/7] Installing NumPy >> "%BUILD_LOG%"

%PYTHON_CMD% -m pip install numpy==1.26.4 >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] Nie udało się zainstalować NumPy!
    echo.
    echo ROZWIĄZANIE:
    echo Zainstaluj Visual Studio Build Tools lub użyj starszej wersji Python.
    echo.
    pause
    goto :error
)
echo [OK] NumPy zainstalowany
echo.

REM ====================================================================
REM KROK 4: Instaluj pozostałe zależności
REM ====================================================================
echo [4/7] Instaluję pozostałe zależności...
echo [%date% %time%] [4/7] Installing other dependencies >> "%BUILD_LOG%"
echo To może zająć kilka minut przy pierwszym uruchomieniu...
echo.

REM Użyj requirements-windows.txt dla Windows (lepsze dla kompilacji)
if exist "requirements-windows.txt" (
    echo Instalowanie requirements-windows.txt (Windows)...
    %PYTHON_CMD% -m pip install -r requirements-windows.txt >> "%BUILD_LOG%" 2>&1
) else (
    echo Instalowanie requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt >> "%BUILD_LOG%" 2>&1
)

if errorlevel 1 (
    echo [WARNING] Niektóre pakiety mogły nie zainstalować się poprawnie
    echo Kontynuuję...
    echo [%date% %time%] [WARNING] Some packages failed >> "%BUILD_LOG%"
)

echo [OK] Zależności zainstalowane
echo.

REM ====================================================================
REM KROK 5: Weryfikacja instalacji
REM ====================================================================
echo [5/8] Weryfikuję instalację...
echo [%date% %time%] [5/8] Verifying installation >> "%BUILD_LOG%"

%PYTHON_CMD% -c "import numpy; import torch; import cv2; import onnxruntime; import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Niektóre pakiety mogą nie być zainstalowane poprawnie
    echo Kontynuuję...
) else (
    echo [OK] Wszystkie pakiety zainstalowane
)
echo.

REM ====================================================================
REM KROK 6: Wyczyść poprzednie buildy
REM ====================================================================
echo [6/8] Czyszczę poprzednie buildy...
echo [%date% %time%] [6/8] Cleaning previous builds >> "%BUILD_LOG%"

if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%" 2>nul
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%" 2>nul
if exist "*.spec" del /q *.spec 2>nul

echo [OK] Poprzednie buildy wyczyszczone
echo.

REM ====================================================================
REM KROK 7: Kompiluj z PyInstaller
REM ====================================================================
echo [7/8] Kompiluję aplikację do .exe...
echo [%date% %time%] [7/8] Building with PyInstaller >> "%BUILD_LOG%"
echo To może zająć 5-10 minut...
echo.

%PYTHON_CMD% -m PyInstaller ^
    --name=%APP_NAME% ^
    --onefile ^
    --console ^
    --add-data="config;config" ^
    --add-data="data/classes.txt;data" ^
    --add-data="data/dataset.yaml;data" ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=onnxruntime ^
    --hidden-import=mss ^
    --hidden-import=keyboard ^
    --hidden-import=ultralytics ^
    --collect-all=onnxruntime ^
    --collect-all=PyQt5 ^
    --noconfirm ^
    --clean ^
    main.py >> "%BUILD_LOG%" 2>&1

if errorlevel 1 (
    echo [ERROR] Błąd podczas kompilacji!
    echo Sprawdź logi: %BUILD_LOG%
    echo.
    echo [%date% %time%] [ERROR] PyInstaller failed >> "%BUILD_LOG%"
    pause
    goto :error
)

echo [OK] Kompilacja zakończona
echo.

REM ====================================================================
REM KROK 8: Sprawdź wynik
REM ====================================================================
echo [8/8] Sprawdzam wynik...
echo [%date% %time%] [8/8] Verifying build >> "%BUILD_LOG%"

if not exist "%DIST_DIR%\%APP_NAME%.exe" (
    echo [ERROR] Plik .exe nie został utworzony!
    echo Sprawdź logi: %BUILD_LOG%
    echo.
    echo [%date% %time%] [ERROR] .exe file not created >> "%BUILD_LOG%"
    pause
    goto :error
)

echo [OK] Plik .exe utworzony
echo.

REM ====================================================================
REM Sukces
REM ====================================================================
echo ====================================================================
echo BUILD ZAKOŃCZONY POMYŚLNIE!
echo ====================================================================
echo.
echo Lokalizacja: %DIST_DIR%\%APP_NAME%.exe
echo.

dir "%DIST_DIR%\%APP_NAME%.exe" | find ".exe"

echo.
echo Logi buildu: %BUILD_LOG%
echo.
echo Aby uruchomić:
echo   cd %DIST_DIR%
echo   %APP_NAME%.exe
echo.
echo ====================================================================

echo [%date% %time%] Build completed successfully >> "%BUILD_LOG%"
echo [%date% %time%] Output: %DIST_DIR%\%APP_NAME%.exe >> "%BUILD_LOG%"

pause
exit /b 0

REM ====================================================================
REM Obsługa błędów
REM ====================================================================
:error
echo.
echo ====================================================================
echo BUILD FAILED!
echo ====================================================================
echo.
echo Sprawdź logi w: %BUILD_LOG%
echo.
echo [%date% %time%] Build failed >> "%BUILD_LOG%"
pause
exit /b 1
