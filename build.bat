@echo off
setlocal enabledelayedexpansion

echo.
echo ====================================
echo   Helping Hand - Build Script
echo ====================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if PyInstaller is available
pip show pyinstaller >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] PyInstaller is not installed
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
)

:: Check for required files
echo [INFO] Checking required files...
if not exist "main.py" (
    echo [ERROR] main.py not found
    pause
    exit /b 1
)

if not exist "assets\icon.ico" (
    echo [WARNING] Icon file not found - building without icon
    set ICON_FLAG=
) else (
    echo [INFO] Icon file found
    set ICON_FLAG=--icon="assets\icon.ico"
)

:: Clean previous build
echo [INFO] Cleaning previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "helping-hand.spec" del /f /q "helping-hand.spec"

:: Build executable
echo [INFO] Building executable...
pyinstaller --onefile --noconsole !ICON_FLAG! --name helping-hand main.py

if !errorlevel! neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

:: Clean up build artifacts
echo [INFO] Cleaning build artifacts...
if exist "build" rmdir /s /q "build"
if exist "helping-hand.spec" del /f /q "helping-hand.spec"

:: Verify build
if exist "dist\helping-hand.exe" (
    echo [SUCCESS] Build completed successfully
    echo [INFO] Executable location: dist\helping-hand.exe
) else (
    echo [ERROR] Build failed - executable not found
    pause
    exit /b 1
)

echo.
echo ====================================
echo   Build Complete
echo ====================================
echo.
pause
