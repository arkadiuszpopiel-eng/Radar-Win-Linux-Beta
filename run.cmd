@echo off
REM ====================================================================
REM YOLO Object Detection - Run Script
REM Uruchamia aplikację z logowaniem
REM ====================================================================

echo ====================================================================
echo YOLO OBJECT DETECTION - URUCHAMIANIE
echo ====================================================================
echo.

REM Sprawdź Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python nie jest zainstalowany!
    echo.
    echo Zainstaluj Python z: https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Utwórz katalog logów
if not exist "logs" mkdir "logs"

echo Uruchamianie aplikacji...
echo.
echo Logi zapisywane w: logs/
echo.
echo ====================================================================
echo.

REM Uruchom aplikację
python main.py

REM Obsługa wyjścia
if errorlevel 1 (
    echo.
    echo ====================================================================
    echo Aplikacja zakończona z błędem!
    echo Sprawdź logi w katalogu: logs/
    echo ====================================================================
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo Aplikacja zakończona pomyślnie
echo ====================================================================
echo.
