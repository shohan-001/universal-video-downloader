@echo off
echo ========================================
echo   Universal Video Downloader Build Script
echo ========================================
echo.

:: Check if Python is installed
python --version 2>NUL
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if PyInstaller is installed
pip show pyinstaller >NUL 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Clean previous builds
echo Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

:: Build the executable
echo.
echo Building Universal Video Downloader...
echo.

pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --icon=icon.ico ^
    --name="Universal-Video-Downloader" ^
    --add-data="web;web" ^
    --hidden-import=eel ^
    --hidden-import=yt_dlp ^
    --hidden-import=bottle_websocket ^
    main.py

:: Check if build was successful
if exist "dist\Universal-Video-Downloader.exe" (
    echo.
    echo ========================================
    echo   BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable location: dist\Universal-Video-Downloader.exe
    echo.
) else (
    echo.
    echo ========================================
    echo   BUILD FAILED!
    echo ========================================
    echo.
)

pause