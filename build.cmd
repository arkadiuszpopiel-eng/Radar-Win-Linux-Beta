@echo off
REM ====================================================================
REM YOLO Object Detection - Build Script
REM Kompilacja aplikacji do pliku .exe
REM ====================================================================

setlocal enabledelayedexpansion

echo ====================================================================
echo YOLO OBJECT DETECTION - BUILD SCRIPT
echo ====================================================================
echo.

REM Ustawienia
set "BUILD_DIR=build"
set "DIST_DIR=dist"
set "LOG_DIR=logs"
set "BUILD_LOG=%LOG_DIR%\build_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "APP_NAME=YOLODetection"
set "VERSION=1.0.0"

REM Utwórz katalog logów
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Rozpocznij logowanie
echo [%date% %time%] Build started > "%BUILD_LOG%"
echo [%date% %time%] Build started
echo.

REM ====================================================================
REM KROK 1: Sprawdź Python
REM ====================================================================
echo [1/6] Sprawdzam instalację Python...
echo [%date% %time%] [1/6] Checking Python installation >> "%BUILD_LOG%"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python nie jest zainstalowany lub nie jest w PATH!
    echo [%date% %time%] [ERROR] Python not found >> "%BUILD_LOG%"
    goto :error
)

python --version
python --version >> "%BUILD_LOG%"
echo [OK] Python znaleziony
echo.

REM ====================================================================
REM KROK 2: Sprawdź pip
REM ====================================================================
echo [2/6] Sprawdzam pip...
echo [%date% %time%] [2/6] Checking pip >> "%BUILD_LOG%"

pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip nie jest zainstalowany!
    echo [%date% %time%] [ERROR] pip not found >> "%BUILD_LOG%"
    goto :error
)

pip --version
pip --version >> "%BUILD_LOG%"
echo [OK] pip znaleziony
echo.

REM ====================================================================
REM KROK 3: Instaluj zależności
REM ====================================================================
echo [3/6] Instaluję zależności...
echo [%date% %time%] [3/6] Installing dependencies >> "%BUILD_LOG%"

REM Użyj requirements-windows.txt dla Windows (lepsze dla kompilacji)
if exist "requirements-windows.txt" (
    echo Instalowanie requirements-windows.txt (Windows-specific)...
    pip install -r requirements-windows.txt >> "%BUILD_LOG%" 2>&1
) else (
    echo Instalowanie requirements.txt...
    pip install -r requirements.txt >> "%BUILD_LOG%" 2>&1
)

if errorlevel 1 (
    echo [ERROR] Błąd podczas instalacji zależności!
    echo.
    echo MOŻLIWE ROZWIĄZANIA:
    echo 1. Zainstaluj Microsoft Visual Studio Build Tools
    echo    https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
    echo.
    echo 2. Lub użyj stabilnej wersji Python (3.11 lub 3.12)
    echo    https://www.python.org/downloads/
    echo.
    echo 3. Lub zainstaluj pakiety ręcznie:
    echo    pip install numpy==1.26.4
    echo    pip install -r requirements-windows.txt
    echo.
    echo [%date% %time%] [ERROR] Failed to install dependencies >> "%BUILD_LOG%"
    goto :error
)

echo [OK] Zależności zainstalowane
echo.

REM ====================================================================
REM KROK 4: Wyczyść poprzednie buildy
REM ====================================================================
echo [4/6] Czyszczę poprzednie buildy...
echo [%date% %time%] [4/6] Cleaning previous builds >> "%BUILD_LOG%"

if exist "%BUILD_DIR%" (
    echo Usuwam katalog build...
    rmdir /s /q "%BUILD_DIR%" >> "%BUILD_LOG%" 2>&1
)

if exist "%DIST_DIR%" (
    echo Usuwam katalog dist...
    rmdir /s /q "%DIST_DIR%" >> "%BUILD_LOG%" 2>&1
)

if exist "*.spec" (
    echo Usuwam pliki .spec...
    del /q *.spec >> "%BUILD_LOG%" 2>&1
)

echo [OK] Poprzednie buildy wyczyszczone
echo.

REM ====================================================================
REM KROK 5: Kompiluj z PyInstaller
REM ====================================================================
echo [5/6] Kompiluję aplikację do .exe...
echo [%date% %time%] [5/6] Building with PyInstaller >> "%BUILD_LOG%"
echo To może zająć kilka minut...
echo.

pyinstaller ^
    --name=%APP_NAME% ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data="config;config" ^
    --add-data="data/classes.txt;data" ^
    --add-data="data/dataset.yaml;data" ^
    --hidden-import=PyQt5 ^
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
    echo [%date% %time%] [ERROR] PyInstaller failed >> "%BUILD_LOG%"
    goto :error
)

echo [OK] Kompilacja zakończona
echo.

REM ====================================================================
REM KROK 6: Sprawdź wynik
REM ====================================================================
echo [6/6] Sprawdzam wynik...
echo [%date% %time%] [6/6] Verifying build >> "%BUILD_LOG%"

if not exist "%DIST_DIR%\%APP_NAME%.exe" (
    echo [ERROR] Plik .exe nie został utworzony!
    echo [%date% %time%] [ERROR] .exe file not created >> "%BUILD_LOG%"
    goto :error
)

echo [OK] Plik .exe utworzony
echo.

REM ====================================================================
REM Informacje o wyniku
REM ====================================================================
echo ====================================================================
echo BUILD ZAKOŃCZONY POMYŚLNIE!
echo ====================================================================
echo.
echo Lokalizacja: %DIST_DIR%\%APP_NAME%.exe
echo.

dir "%DIST_DIR%\%APP_NAME%.exe" | find ".exe"

echo.
echo Logi buildu zapisane w: %BUILD_LOG%
echo.
echo Aby uruchomić aplikację:
echo   cd %DIST_DIR%
echo   %APP_NAME%.exe
echo.
echo ====================================================================

echo [%date% %time%] Build completed successfully >> "%BUILD_LOG%"
echo [%date% %time%] Output: %DIST_DIR%\%APP_NAME%.exe >> "%BUILD_LOG%"

goto :end

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

REM ====================================================================
REM Koniec
REM ====================================================================
:end
echo Naciśnij dowolny klawisz aby zakończyć...
pause >nul
exit /b 0
