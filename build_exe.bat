@echo off
TITLE Building YouTube Downloader EXE
ECHO.
ECHO ===============================================================================
ECHO                    Building YouTube Downloader EXE
ECHO ===============================================================================
ECHO.

:: Check if app is running and close it
ECHO [INFO] Checking for running instances...
tasklist /FI "IMAGENAME eq YT-Downloader-Pro.exe" 2>NUL | find /I /N "YT-Downloader-Pro.exe">NUL
if "%ERRORLEVEL%"=="0" (
    ECHO [WARNING] App is running. Attempting to close it...
    taskkill /F /IM "YT-Downloader-Pro.exe" >NUL 2>&1
    timeout /t 2 /nobreak >NUL
)

:: Check/Install Dependencies
ECHO [INFO] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install pyinstaller eel yt-dlp Pillow

:: Clean previous build with force
ECHO.
ECHO [INFO] Cleaning previous build files...
IF EXIST "dist" (
    ECHO Removing dist folder...
    rmdir /S /Q "dist" 2>NUL
    timeout /t 1 /nobreak >NUL
)
IF EXIST "build" (
    ECHO Removing build folder...
    rmdir /S /Q "build" 2>NUL
)
IF EXIST "*.spec" (
    ECHO Removing spec files...
    del /Q "*.spec" 2>NUL
)

:: Wait a moment for file system
timeout /t 1 /nobreak >NUL

:: Build EXE (windowed mode - no console)
ECHO.
ECHO [INFO] Building executable... This may take a minute.
ECHO.
python -m PyInstaller --noconfirm --onefile --windowed ^
    --name "YT-Downloader-Pro" ^
    --icon=icon.ico ^
    --version-file=version_info.txt ^
    --add-data "web;web" ^
    --hidden-import=eel ^
    --hidden-import=bottle_websocket ^
    --collect-all eel ^
    main.py

IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO [ERROR] Build Failed!
    ECHO.
    ECHO Troubleshooting:
    ECHO 1. Make sure the app is closed
    ECHO 2. Try running as Administrator
    ECHO 3. Check if antivirus is blocking
    PAUSE
    EXIT /B
)

ECHO.
ECHO ===============================================================================
ECHO [SUCCESS] Build Complete!
ECHO.
ECHO Your new executable is located in the "dist" folder!
ECHO File: dist\YT-Downloader-Pro.exe
ECHO ===============================================================================
ECHO.

:: Open dist folder
ECHO Opening dist folder...
start dist

PAUSE