@echo off
REM ====================================================================
REM YOLO Object Detection - Build z Python 3.11
REM ====================================================================

echo ====================================================================
echo YOLO OBJECT DETECTION - BUILD (Python 3.11)
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
    echo Sprawdź lokalizację instalacji Python 3.11 i edytuj ten skrypt.
    echo Lub użyj: py -3.11 --version
    echo.
    pause
    exit /b 1
)

echo Używam Python:
%PYTHON311% --version
echo.

REM Utwórz katalog logów
if not exist "logs" mkdir "logs"

set "BUILD_LOG=logs\build_py311_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"

echo [%date% %time%] Build started with Python 3.11 > "%BUILD_LOG%"
echo.

REM ====================================================================
REM KROK 1: Upgrade pip
REM ====================================================================
echo [1/5] Aktualizuję pip...
%PYTHON311% -m pip install --upgrade pip >> "%BUILD_LOG%" 2>&1

REM ====================================================================
REM KROK 2: Instaluj zależności
REM ====================================================================
echo [2/5] Instaluję zależności...
echo To może zająć kilka minut...
echo.

if exist "requirements-windows.txt" (
    %PYTHON311% -m pip install -r requirements-windows.txt >> "%BUILD_LOG%" 2>&1
) else (
    %PYTHON311% -m pip install -r requirements.txt >> "%BUILD_LOG%" 2>&1
)

if errorlevel 1 (
    echo [ERROR] Błąd podczas instalacji zależności!
    echo Sprawdź logi: %BUILD_LOG%
    echo.
    pause
    exit /b 1
)

echo [OK] Zależności zainstalowane
echo.

REM ====================================================================
REM KROK 3: Wyczyść poprzednie buildy
REM ====================================================================
echo [3/5] Czyszczę poprzednie buildy...

if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul

echo [OK] Wyczyszczone
echo.

REM ====================================================================
REM KROK 4: Kompiluj z PyInstaller
REM ====================================================================
echo [4/5] Kompiluję aplikację do .exe...
echo To może zająć 5-10 minut...
echo.

%PYTHON311% -m PyInstaller ^
    --name=YOLODetection ^
    --onefile ^
    --windowed ^
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
    echo Sprawdź logi: %BUILD_LOG%
    echo.
    pause
    exit /b 1
)

echo [OK] Kompilacja zakończona
echo.

REM ====================================================================
REM KROK 5: Sprawdź wynik
REM ====================================================================
echo [5/5] Sprawdzam wynik...

if not exist "dist\YOLODetection.exe" (
    echo [ERROR] Plik .exe nie został utworzony!
    echo Sprawdź logi: %BUILD_LOG%
    echo.
    pause
    exit /b 1
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
echo Lokalizacja: dist\YOLODetection.exe
echo.

dir "dist\YOLODetection.exe" | find ".exe"

echo.
echo Logi buildu: %BUILD_LOG%
echo.
echo ====================================================================

echo [%date% %time%] Build completed successfully >> "%BUILD_LOG%"

pause
