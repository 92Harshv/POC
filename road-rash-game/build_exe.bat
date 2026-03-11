@echo off
setlocal
title Road Rash - Build Windows EXE
color 0B

echo.
echo  ========================================================
echo    ROAD RASH - MOTO BRAWLER  ^|  Build Windows EXE
echo  ========================================================
echo.
echo  This script builds a standalone RoadRash.exe using
echo  PyInstaller (no Python needed on the target machine).
echo.

:: Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    py --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Python not found. Run install.bat first.
        pause & exit /b 1
    )
    set "PY=py"
) else (
    set "PY=python"
)

echo [1/3] Installing build dependencies...
%PY% -m pip install "pygame>=2.5.0" "pyinstaller>=6.0" --quiet
echo       Done.

echo.
echo [2/3] Building EXE with PyInstaller...
%PY% -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name RoadRash ^
    --clean ^
    game.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed! Check output above.
    pause & exit /b 1
)

echo.
echo [3/3] Build successful!
echo.
echo  ┌─────────────────────────────────────────────────────┐
echo  │  Standalone EXE:  dist\RoadRash.exe                 │
echo  │                                                      │
echo  │  Share this single file — no Python required!        │
echo  │                                                      │
echo  │  To create an installer EXE:                         │
echo  │    1. Install Inno Setup (jrsoftware.org/isinfo.php) │
echo  │    2. Open RoadRash_installer.iss                     │
echo  │    3. Press Compile (Ctrl+F9)                         │
echo  │    4. Find installer in: installer\RoadRash_Setup.exe │
echo  └─────────────────────────────────────────────────────┘
echo.

set /p "OPEN=Open dist folder now? [Y/N]: "
if /i "%OPEN%"=="Y" explorer dist

endlocal
pause
