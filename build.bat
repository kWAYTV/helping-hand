@echo off

echo Building Binary...

:: Build executable
echo Starting PyInstaller...
call pyinstaller --onefile --noconsole --icon="assets\icon.ico" --name helping-hand main.py
echo PyInstaller finished

:: Clean build artifacts
echo Cleaning build artifacts...
rmdir /s /q build
echo Removed build directory
del /f /q helping-hand.spec
echo Removed spec file

:: Verify output
echo Verifying output...
if exist "dist\helping-hand.exe" (
    echo SUCCESS: dist\helping-hand.exe created
) else (
    echo ERROR: Build failed - executable not found
)

echo Done.
