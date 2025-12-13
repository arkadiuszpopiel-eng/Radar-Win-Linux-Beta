@echo off
REM ============================================================================
REM RadarSuite Windows V4 - Windows Build Script
REM Builds standalone Windows EXE using PyInstaller
REM Platform: Windows x64 ONLY
REM Requires: Python 3.11
REM ============================================================================

setlocal EnableDelayedExpansion

echo.
echo ========================================================================
echo   RadarSuite Windows V4.2.1 - Build System
echo   Building Windows standalone EXE with PyInstaller
echo   Platform: Windows x64 ONLY
echo ========================================================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM FIXED v4.2.1-k0008: Create centralized log directory
set "LOG_DIR=%SCRIPT_DIR%log"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Set version
set "VERSION=v4.2.1"
set "PLATFORM=Win64"
set "BUILD_DATE=%date:~-4%-%date:~3,2%-%date:~0,2%"
set "BUILD_TIME=%time:~0,2%-%time:~3,2%-%time:~6,2%"
set "BUILD_TIME=!BUILD_TIME: =0!"

REM Log file - FIXED v4.2.1-k0008: Moved to log directory
set "LOG_FILE=%LOG_DIR%\build_windows.log"

REM Start logging
echo [%date% %time%] ============================================================ >> "%LOG_FILE%"
echo [%date% %time%] BUILD STARTED - RadarSuite Windows V4 >> "%LOG_FILE%"
echo [%date% %time%] ============================================================ >> "%LOG_FILE%"
echo [%date% %time%] Version: %VERSION% >> "%LOG_FILE%"
echo [%date% %time%] Script Directory: %SCRIPT_DIR% >> "%LOG_FILE%"
echo [%date% %time%] Build Date: %BUILD_DATE% >> "%LOG_FILE%"
echo [%date% %time%] Build Time: %BUILD_TIME% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo [INFO] This is the WINDOWS-ONLY version
echo [INFO] Linux builds: Use RadarSuite_Linux_V4 directory
echo [INFO] All builds are separate and won't interfere
echo [%date% %time%] [INFO] Platform: Windows x64 only - separate build directory >> "%LOG_FILE%"
echo.

echo [STEP 1/6] Checking Python 3.11 installation...
echo [%date% %time%] [STEP 1/6] Checking Python 3.11... >> "%LOG_FILE%"

py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.11 is not installed or not in PATH!
    echo [%date% %time%] [ERROR] Python 3.11 not found >> "%LOG_FILE%"
    echo.
    echo Please install Python 3.11 from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('py -3.11 --version') do set PYTHON_VERSION=%%i
echo    - Found: %PYTHON_VERSION%
echo [%date% %time%] Found: %PYTHON_VERSION% >> "%LOG_FILE%"
echo.

echo [STEP 2/6] Creating/Activating virtual environment...
echo [%date% %time%] [STEP 2/6] Creating venv... >> "%LOG_FILE%"

if not exist ".venv" (
    echo    - Creating new venv...
    echo [%date% %time%] Creating new venv... >> "%LOG_FILE%"
    py -3.11 -m venv .venv >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        echo [%date% %time%] [ERROR] venv creation failed >> "%LOG_FILE%"
        pause
        exit /b 1
    )
) else (
    echo    - Using existing venv
    echo [%date% %time%] Using existing venv >> "%LOG_FILE%"
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo [%date% %time%] [ERROR] venv activation failed >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo    - Virtual environment activated
echo [%date% %time%] venv activated >> "%LOG_FILE%"
echo.

echo [STEP 3/6] Upgrading pip, setuptools, wheel...
echo [%date% %time%] [STEP 3/6] Upgrading pip... >> "%LOG_FILE%"

python -m pip install --upgrade pip setuptools wheel >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] pip upgrade had issues, continuing...
)

echo    - pip upgraded
echo.

echo [STEP 4/6] Installing requirements...
echo [%date% %time%] [STEP 4/6] Installing requirements... >> "%LOG_FILE%"
echo.

REM Install from requirements-windows.txt (WINDOWS-SPECIFIC)
if exist "requirements-windows.txt" (
    echo    - Installing from requirements-windows.txt (Windows optimized^)...
    echo [%date% %time%] Installing from requirements-windows.txt >> "%LOG_FILE%"
    pip install -r requirements-windows.txt >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements from requirements-windows.txt
        echo [%date% %time%] [ERROR] Requirements installation failed >> "%LOG_FILE%"
        pause
        exit /b 1
    )
) else if exist "requirements.txt" (
    echo    - Installing from requirements.txt...
    echo [%date% %time%] Installing from requirements.txt >> "%LOG_FILE%"
    pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements from requirements.txt
        echo [%date% %time%] [ERROR] Requirements installation failed >> "%LOG_FILE%"
        pause
        exit /b 1
    )
) else (
    echo [ERROR] No requirements file found!
    echo [%date% %time%] [ERROR] No requirements file found >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo.
echo    All Python requirements installed
echo [%date% %time%] All requirements installed >> "%LOG_FILE%"
echo.

echo [STEP 5/6] Verifying installation...
echo [%date% %time%] [STEP 5/6] Verifying installation... >> "%LOG_FILE%"

REM Verify modules without initializing native libraries (sounddevice/soundcard)
python -c "import sys; import importlib.util; modules=['PyQt5', 'pyqtgraph', 'OpenGL', 'numpy', 'scipy', 'sounddevice', 'soundcard', 'psutil', 'PyInstaller']; failed=[]; [failed.append(m) if importlib.util.find_spec(m) is None else print(f'OK: {m}') for m in modules]; sys.exit(1) if failed else print('All modules installed OK')" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Module verification failed!
    echo [%date% %time%] [ERROR] Module verification failed >> "%LOG_FILE%"
    echo.
    echo Some required modules could not be imported.
    echo Please check %LOG_FILE% for details.
    echo.
    echo Common fixes:
    echo   - Ensure you have Visual C++ Redistributable installed
    echo   - Try running as Administrator
    echo   - Check Windows Defender / Antivirus settings
    pause
    exit /b 1
)

REM Note: sounddevice may require PortAudio DLL at runtime
REM This verification only checks if the Python package is installed
echo    - All modules verified successfully (package check only)
echo    - Note: sounddevice/soundcard require PortAudio DLL at runtime
echo [%date% %time%] All modules verified (package check only) >> "%LOG_FILE%"
echo.

REM Verify PyInstaller is installed
echo    - Checking PyInstaller...
python -c "import PyInstaller; print(f'PyInstaller {PyInstaller.__version__}')" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller not available!
    echo [ERROR] Try: python -m pip install pyinstaller
    echo [%date% %time%] [ERROR] PyInstaller module not found >> "%LOG_FILE%"
    pause
    exit /b 1
)
python -c "import PyInstaller; print('   - PyInstaller version:', PyInstaller.__version__)"
echo [%date% %time%] PyInstaller available >> "%LOG_FILE%"
echo.
echo [STEP 6/6] Building EXE with PyInstaller...
echo [%date% %time%] [STEP 6/6] Building EXE... >> "%LOG_FILE%"
echo.

REM Clean previous build
if exist "build" (
    echo    - Cleaning old build directory...
    rmdir /s /q build
)

if exist "dist" (
    echo    - Cleaning old dist directory...
    rmdir /s /q dist
)

echo    - Running PyInstaller...
echo [%date% %time%] Running PyInstaller with spec file... >> "%LOG_FILE%"

python -m PyInstaller --clean --noconfirm build_tools\radarsuite_windows.spec >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed!
    echo [%date% %time%] [ERROR] PyInstaller failed >> "%LOG_FILE%"
    echo.
    echo Build failed. Check %LOG_FILE% for details.
    echo.
    echo Last 30 lines of log:
    powershell -Command "Get-Content '%LOG_FILE%' -Tail 30"
    pause
    exit /b 1
)

echo.
echo    - EXE built successfully!
echo [%date% %time%] PyInstaller build completed >> "%LOG_FILE%"

REM Verify EXE exists
set "APP_DIR=dist\RadarSuite_Windows"
if not exist "%APP_DIR%\RadarSuite_Windows.exe" (
    echo [ERROR] EXE not found in dist!
    echo [%date% %time%] [ERROR] EXE not found >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo    - EXE location: %APP_DIR%\RadarSuite_Windows.exe
echo [%date% %time%] EXE created: %APP_DIR%\RadarSuite_Windows.exe >> "%LOG_FILE%"

REM Get EXE size
for %%A in ("%APP_DIR%\RadarSuite_Windows.exe") do set "EXE_SIZE=%%~zA"
echo    - EXE size: !EXE_SIZE! bytes
echo [%date% %time%] EXE size: !EXE_SIZE! bytes >> "%LOG_FILE%"
echo.

REM ============================================================================
REM NOTE: ZIP packaging step removed (v4.2.1)
REM To create ZIP manually: powershell Compress-Archive -Path dist\RadarSuite_Windows\* -DestinationPath RadarSuite.zip
REM ============================================================================

echo.
echo ========================================================================
echo   BUILD COMPLETED SUCCESSFULLY!
echo ========================================================================
echo.
echo Build Information:
echo   - Version: %VERSION%
echo   - Date: %BUILD_DATE%
echo   - Time: %BUILD_TIME%
echo   - Python: %PYTHON_VERSION%
echo.
echo Output:
echo   - EXE Directory: %APP_DIR%
echo   - EXE File: RadarSuite_Windows.exe
echo   - EXE Size: !EXE_SIZE! bytes
echo.
echo Logs:
echo   - Build Log: %LOG_FILE%
echo   - Runtime log will be created as super_log.txt when you run the EXE
echo.
echo To run the application:
echo   1. Go to: %APP_DIR%
echo   2. Double-click: RadarSuite_Windows.exe
echo.
echo ========================================================================

echo [%date% %time%] ============================================================ >> "%LOG_FILE%"
echo [%date% %time%] BUILD COMPLETED SUCCESSFULLY >> "%LOG_FILE%"
echo [%date% %time%] ============================================================ >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

pause
