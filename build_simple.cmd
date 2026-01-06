@echo off
REM ====================================================================
REM YOLO Object Detection - Simple Build Script
REM Kompilacja przy użyciu pliku .spec
REM ====================================================================

echo ====================================================================
echo YOLO OBJECT DETECTION - SIMPLE BUILD
echo ====================================================================
echo.

REM Utwórz katalog logów
if not exist "logs" mkdir "logs"

REM Nazwa logu z datą i czasem
set "BUILD_LOG=logs\build_simple_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"

echo Build rozpoczęty: %date% %time%
echo Build rozpoczęty: %date% %time% > "%BUILD_LOG%"
echo.

REM Wyczyść poprzednie buildy
echo Czyszczę poprzednie buildy...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul

echo.
echo Rozpoczynam kompilację...
echo Używam pliku: YOLODetection.spec
echo.

REM Kompiluj używając pliku .spec
pyinstaller YOLODetection.spec >> "%BUILD_LOG%" 2>&1

if errorlevel 1 (
    echo.
    echo [ERROR] Kompilacja nie powiodła się!
    echo Sprawdź logi: %BUILD_LOG%
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo BUILD ZAKOŃCZONY POMYŚLNIE!
echo ====================================================================
echo.
echo Plik: dist\YOLODetection.exe
echo Logi: %BUILD_LOG%
echo.

echo Build zakończony: %date% %time% >> "%BUILD_LOG%"

pause
