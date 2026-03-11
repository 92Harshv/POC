@echo off
REM ============================================================
REM  Road Rash - Moto Brawler  |  Windows Build Script
REM  Run this from the project root to produce an installer
REM ============================================================

echo.
echo ====================================================
echo   Building Road Rash - Moto Brawler for Windows
echo ====================================================
echo.

REM Install dependencies
pip install -r requirements.txt

REM Build standalone executable with PyInstaller
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "RoadRash" ^
    --icon "assets/icon.ico" ^
    game.py

echo.
echo Build complete!  Find your executable in:  dist\RoadRash.exe
pause
