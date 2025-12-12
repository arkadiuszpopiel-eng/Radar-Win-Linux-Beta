@echo off
REM ============================================================================
REM RadarSuite Final - Ulepszona wersja skryptu budowania
REM Obsługuje różne konfiguracje Pythona i lepiej wykrywa błędy
REM ============================================================================

setlocal EnableDelayedExpansion

echo.
echo ========================================================================
echo   RadarSuite Final v2.3.0 - Ulepszona wersja buildu
echo   Wykrywanie i naprawa problemow z PyInstaller
echo ========================================================================
echo.

REM FIXED v4.2.1-k0008: Create centralized log directory
set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%SCRIPT_DIR%log"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "LOG_FILE=%LOG_DIR%\build_fixed.log"
echo [%date% %time%] Build started >> "%LOG_FILE%"

REM ============================================================================
REM KROK 1: Znajdz Python 3.11
REM ============================================================================
echo [KROK 1/8] Szukanie Python 3.11...

set "PYTHON_CMD="

REM Probuj: py -3.11
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -3.11"
    goto :FOUND_PYTHON
)

REM Probuj: python3.11
python3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3.11"
    goto :FOUND_PYTHON
)

REM Probuj: python (sprawdz wersje)
python --version 2>&1 | findstr "3.11" >nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :FOUND_PYTHON
)

REM Python 3.11 nie znaleziony
echo [ERROR] Python 3.11 nie jest zainstalowany!
echo.
echo Pobierz Python 3.11 z: https://www.python.org/downloads/
echo WAZNE: Podczas instalacji zaznacz "Add Python to PATH"
echo.
pause
exit /b 1

:FOUND_PYTHON
for /f "tokens=*" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo    [OK] Znaleziono: %PYTHON_VERSION%
echo    [OK] Komenda: %PYTHON_CMD%
echo [%date% %time%] Using: %PYTHON_VERSION% (%PYTHON_CMD%) >> "%LOG_FILE%"
echo.

REM ============================================================================
REM KROK 2: Sprawdz pip
REM ============================================================================
echo [KROK 2/8] Sprawdzanie pip...

%PYTHON_CMD% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip nie jest dostepny!
    echo Zainstaluj pip: %PYTHON_CMD% -m ensurepip --upgrade
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('%PYTHON_CMD% -m pip --version 2^>^&1') do set PIP_VERSION=%%i
echo    [OK] pip: %PIP_VERSION%
echo.

REM ============================================================================
REM KROK 3: Utworz srodowisko wirtualne
REM ============================================================================
echo [KROK 3/8] Tworzenie srodowiska wirtualnego...

if exist ".venv" (
    echo    [INFO] Uzywam istniejacego venv
    echo [%date% %time%] Using existing venv >> "%LOG_FILE%"
) else (
    echo    [INFO] Tworze nowy venv...
    echo [%date% %time%] Creating new venv >> "%LOG_FILE%"
    %PYTHON_CMD% -m venv .venv >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Nie udalo sie utworzyc venv!
        echo Sprobuj uruchomic jako Administrator.
        pause
        exit /b 1
    )
    echo    [OK] venv utworzony
)
echo.

REM ============================================================================
REM KROK 4: Aktywuj venv
REM ============================================================================
echo [KROK 4/8] Aktywacja venv...

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Plik activate.bat nie istnieje!
    echo venv moze byc uszkodzony. Usun folder .venv i sprobuj ponownie.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Nie udalo sie aktywowac venv!
    pause
    exit /b 1
)

echo    [OK] venv aktywny
echo.

REM ============================================================================
REM KROK 5: Upgrade pip
REM ============================================================================
echo [KROK 5/8] Aktualizacja pip, setuptools, wheel...

python -m pip install --upgrade pip setuptools wheel >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] Problemy z aktualizacja pip, kontynuuje...
) else (
    echo    [OK] pip zaktualizowany
)
echo.

REM ============================================================================
REM KROK 6: Instalacja zaleznosci
REM ============================================================================
echo [KROK 6/8] Instalacja zaleznosci...
echo    (To moze potrwac kilka minut...)
echo.

if exist "requirements.txt" (
    echo    [INFO] Instaluje z requirements.txt...
    pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Blad podczas instalacji zaleznosci!
        echo Sprawdz super_log.txt po szczegoly.
        echo.
        echo Czeste przyczyny:
        echo   - Brak Visual C++ Redistributable
        echo   - Problem z polaczeniem internetowym
        echo   - Antywirus blokuje instalacje
        pause
        exit /b 1
    )
    echo    [OK] Zaleznosci zainstalowane
) else (
    echo [WARNING] requirements.txt nie znaleziony!
    echo    [INFO] Instaluje recznie...

    pip install PyQt5 >> "%LOG_FILE%" 2>&1
    pip install pyqtgraph >> "%LOG_FILE%" 2>&1
    pip install PyOpenGL PyOpenGL_accelerate >> "%LOG_FILE%" 2>&1
    pip install numpy scipy >> "%LOG_FILE%" 2>&1
    pip install sounddevice soundcard >> "%LOG_FILE%" 2>&1
    pip install psutil >> "%LOG_FILE%" 2>&1
    pip install pyinstaller >> "%LOG_FILE%" 2>&1

    echo    [OK] Pakiety zainstalowane
)
echo.

REM ============================================================================
REM KROK 7: Weryfikacja PyInstaller
REM ============================================================================
echo [KROK 7/8] Weryfikacja PyInstaller...

REM Metoda 1: Bezposrednia komenda
pyinstaller --version >> "%LOG_FILE%" 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('pyinstaller --version 2^>^&1 ^| findstr /r "[0-9]"') do set PYINSTALLER_VERSION=%%i
    echo    [OK] PyInstaller !PYINSTALLER_VERSION! (komenda: pyinstaller)
    set "PYINSTALLER_CMD=pyinstaller"
    goto :PYINSTALLER_OK
)

REM Metoda 2: Przez modul Python
python -m PyInstaller --version >> "%LOG_FILE%" 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python -m PyInstaller --version 2^>^&1 ^| findstr /r "[0-9]"') do set PYINSTALLER_VERSION=%%i
    echo    [OK] PyInstaller !PYINSTALLER_VERSION! (komenda: python -m PyInstaller)
    set "PYINSTALLER_CMD=python -m PyInstaller"
    goto :PYINSTALLER_OK
)

REM PyInstaller nie dziala - probuj przeinstalowac
echo [WARNING] PyInstaller nie jest dostepny, instaluje...
pip uninstall -y pyinstaller >> "%LOG_FILE%" 2>&1
pip install --no-cache-dir pyinstaller >> "%LOG_FILE%" 2>&1

python -m PyInstaller --version >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller nie moze zostac zainstalowany!
    echo.
    echo Sprawdz super_log.txt po szczegoly.
    echo.
    echo Mozliwe rozwiazania:
    echo   1. Uruchom jako Administrator
    echo   2. Zainstaluj Visual C++ Redistributable:
    echo      https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo   3. Sprawdz ustawienia antywirusa
    pause
    exit /b 1
)

set "PYINSTALLER_CMD=python -m PyInstaller"
for /f "tokens=*" %%i in ('python -m PyInstaller --version 2^>^&1 ^| findstr /r "[0-9]"') do set PYINSTALLER_VERSION=%%i
echo    [OK] PyInstaller !PYINSTALLER_VERSION! zainstalowany

:PYINSTALLER_OK
echo.

REM ============================================================================
REM KROK 8: Build z PyInstaller
REM ============================================================================
echo [KROK 8/8] Budowanie aplikacji z PyInstaller...
echo.

REM Wyczysc stare buildy
if exist "build" (
    echo    [INFO] Czyszczenie build/...
    rmdir /s /q build 2>nul
)

if exist "dist" (
    echo    [INFO] Czyszczenie dist/...
    rmdir /s /q dist 2>nul
)

echo    [INFO] Uruchamiam PyInstaller...
echo [%date% %time%] Running PyInstaller >> "%LOG_FILE%"

%PYINSTALLER_CMD% --clean --noconfirm build_tools\radarsuite.spec >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [ERROR] Build PyInstaller zakonczyl sie bledem!
    echo.
    echo Sprawdz ostatnie linie z super_log.txt:
    echo ----------------------------------------
    powershell -Command "Get-Content super_log.txt -Tail 30"
    echo ----------------------------------------
    echo.
    pause
    exit /b 1
)

echo.
echo    [OK] Build zakonczony pomyslnie!
echo.

REM ============================================================================
REM Weryfikacja wyniku
REM ============================================================================
echo [WERYFIKACJA] Sprawdzanie wyniku buildu...

set "APP_DIR=dist\RadarSuite_Final"
if not exist "%APP_DIR%\RadarSuite_Final.exe" (
    echo [ERROR] RadarSuite_Final.exe nie zostal utworzony!
    echo.
    echo Sprawdz super_log.txt po szczegoly.
    pause
    exit /b 1
)

echo    [OK] Plik EXE znaleziony: %APP_DIR%\RadarSuite_Final.exe

REM Rozmiar pliku
for %%A in ("%APP_DIR%\RadarSuite_Final.exe") do set "EXE_SIZE=%%~zA"
set /a EXE_SIZE_MB=!EXE_SIZE! / 1048576
echo    [OK] Rozmiar: !EXE_SIZE! bytes (~!EXE_SIZE_MB! MB)
echo.

REM ============================================================================
REM Podsumowanie
REM ============================================================================
echo ========================================================================
echo   BUILD ZAKONCZONY POMYSLNIE!
echo ========================================================================
echo.
echo Informacje:
echo   - Python: %PYTHON_VERSION%
echo   - PyInstaller: %PYINSTALLER_VERSION%
echo   - Rozmiar EXE: !EXE_SIZE_MB! MB
echo.
echo Lokalizacja:
echo   %CD%\%APP_DIR%\RadarSuite_Final.exe
echo.
echo Aby uruchomic aplikacje:
echo   1. Przejdz do: %APP_DIR%
echo   2. Kliknij dwukrotnie: RadarSuite_Final.exe
echo.
echo Lub uruchom teraz:
echo   cd %APP_DIR% ^&^& RadarSuite_Final.exe
echo.
echo Logi:
echo   - Build log: %LOG_FILE%
echo   - Runtime log: super_log.txt (tworzony przy uruchomieniu)
echo.
echo ========================================================================

echo [%date% %time%] Build completed successfully >> "%LOG_FILE%"
echo.

REM Zapytaj czy uruchomic aplikacje
set /p RUN_NOW="Czy chcesz uruchomic aplikacje teraz? (T/N): "
if /i "%RUN_NOW%"=="T" (
    echo.
    echo Uruchamiam RadarSuite_Final.exe...
    start "" "%APP_DIR%\RadarSuite_Final.exe"
)

echo.
pause
