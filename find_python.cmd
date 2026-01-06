@echo off
REM ====================================================================
REM Znajdź wszystkie wersje Python w systemie
REM ====================================================================

echo ====================================================================
echo ZNAJDOWANIE WERSJI PYTHON
echo ====================================================================
echo.

echo Sprawdzam zainstalowane wersje Python...
echo.

REM Użyj Python Launcher
py -0 2>nul
if not errorlevel 1 (
    echo.
    echo Aby użyć konkretnej wersji:
    echo   py -3.11 --version
    echo   py -3.12 --version
    echo.
) else (
    echo Python Launcher (py) niedostępny.
)

echo ====================================================================
echo Sprawdzam standardowe lokalizacje:
echo ====================================================================
echo.

if exist "C:\Python311\python.exe" (
    echo [ZNALEZIONO] C:\Python311\python.exe
    C:\Python311\python.exe --version
    echo.
)

if exist "C:\Python312\python.exe" (
    echo [ZNALEZIONO] C:\Python312\python.exe
    C:\Python312\python.exe --version
    echo.
)

if exist "C:\Program Files\Python311\python.exe" (
    echo [ZNALEZIONO] C:\Program Files\Python311\python.exe
    "C:\Program Files\Python311\python.exe" --version
    echo.
)

if exist "C:\Program Files\Python312\python.exe" (
    echo [ZNALEZIONO] C:\Program Files\Python312\python.exe
    "C:\Program Files\Python312\python.exe" --version
    echo.
)

if exist "C:\Program Files\Python315\python.exe" (
    echo [ZNALEZIONO] C:\Program Files\Python315\python.exe
    "C:\Program Files\Python315\python.exe" --version
    echo.
)

echo ====================================================================
echo Domyślna wersja (python):
echo ====================================================================
echo.

python --version 2>nul
if errorlevel 1 (
    echo Python nie znaleziony w PATH
)

echo.
echo ====================================================================
echo ZALECENIE:
echo ====================================================================
echo.
echo Użyj Python 3.11.9 dla najlepszej stabilności:
echo   install_deps_py311.cmd
echo   build_py311.cmd
echo.

pause
