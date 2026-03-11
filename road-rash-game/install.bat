@echo off
setlocal EnableDelayedExpansion
title Road Rash - Moto Brawler Installer
color 0A

echo.
echo  ========================================================
echo    ROAD RASH - MOTO BRAWLER  ^|  Windows Installer
echo  ========================================================
echo.

:: ── Set install directory ─────────────────────────────────────────────────
set "INSTALL_DIR=%LOCALAPPDATA%\RoadRash"
set "GAME_EXE=%INSTALL_DIR%\RoadRash.bat"
set "DESKTOP=%USERPROFILE%\Desktop"

:: ── Step 1: Check Python ──────────────────────────────────────────────────
echo [1/5] Checking for Python...
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%V in ('python --version 2^>^&1') do set PY_VER=%%V
    echo       Found: !PY_VER!
    goto :check_pip
)

py --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%V in ('py --version 2^>^&1') do set PY_VER=%%V
    echo       Found via py launcher: !PY_VER!
    set "PYTHON_CMD=py"
    goto :check_pip
)

:: Python not found — download and install it
echo       Python not found. Downloading Python 3.11...
echo.
echo  NOTE: Python will be installed silently (no admin needed).
echo        If download fails, visit: https://www.python.org/downloads/
echo.
set "PY_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
set "PY_INSTALLER=%TEMP%\python-3.11-setup.exe"

powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%PY_INSTALLER%' -UseBasicParsing }" 2>nul
if not exist "%PY_INSTALLER%" (
    echo  [ERROR] Could not download Python.
    echo          Please install Python 3.9+ from https://www.python.org/downloads/
    echo          then re-run this installer.
    pause & exit /b 1
)
echo       Installing Python (silent, no admin required)...
"%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del "%PY_INSTALLER%" >nul 2>&1

:: Reload PATH
for /f "tokens=*" %%P in ('powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable(\"PATH\",\"User\")"') do set "PATH=%%P;%PATH%"

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Python installation failed. Please install manually.
    pause & exit /b 1
)
echo       Python installed OK.

:check_pip
if not defined PYTHON_CMD set "PYTHON_CMD=python"

:: ── Step 2: Ensure pip ────────────────────────────────────────────────────
echo.
echo [2/5] Checking pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo       Installing pip...
    %PYTHON_CMD% -m ensurepip --upgrade >nul 2>&1
)
%PYTHON_CMD% -m pip install --upgrade pip --quiet >nul 2>&1
echo       pip OK.

:: ── Step 3: Install pygame ────────────────────────────────────────────────
echo.
echo [3/5] Installing pygame...
%PYTHON_CMD% -m pip install "pygame>=2.5.0" --quiet
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] pygame installation failed.
    echo          Try running:  pip install pygame
    pause & exit /b 1
)
echo       pygame installed OK.

:: ── Step 4: Copy game files ───────────────────────────────────────────────
echo.
echo [4/5] Installing game files to:
echo       %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

copy /Y "game.py" "%INSTALL_DIR%\game.py" >nul
if %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Could not copy game files. Run installer from its extracted folder.
    pause & exit /b 1
)

:: Write a launcher batch
(
echo @echo off
echo cd /d "%INSTALL_DIR%"
echo %PYTHON_CMD% game.py
) > "%INSTALL_DIR%\RoadRash.bat"

:: Write a VBS wrapper so it launches without a console window
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.Run """%INSTALL_DIR%\RoadRash.bat""", 0, False
) > "%INSTALL_DIR%\RoadRash.vbs"

echo       Files installed.

:: ── Step 5: Desktop shortcut ─────────────────────────────────────────────
echo.
echo [5/5] Creating desktop shortcut...
powershell -NoProfile -Command ^
  "$WS = New-Object -ComObject WScript.Shell; ^
   $SC = $WS.CreateShortcut('%DESKTOP%\Road Rash - Moto Brawler.lnk'); ^
   $SC.TargetPath = '%INSTALL_DIR%\RoadRash.vbs'; ^
   $SC.WorkingDirectory = '%INSTALL_DIR%'; ^
   $SC.Description = 'Road Rash - Moto Brawler'; ^
   $SC.Save()" >nul 2>&1

:: Also add to Start Menu
set "START_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Road Rash"
if not exist "%START_DIR%" mkdir "%START_DIR%"
powershell -NoProfile -Command ^
  "$WS = New-Object -ComObject WScript.Shell; ^
   $SC = $WS.CreateShortcut('%START_DIR%\Road Rash - Moto Brawler.lnk'); ^
   $SC.TargetPath = '%INSTALL_DIR%\RoadRash.vbs'; ^
   $SC.WorkingDirectory = '%INSTALL_DIR%'; ^
   $SC.Description = 'Road Rash - Moto Brawler'; ^
   $SC.Save()" >nul 2>&1

echo       Shortcut created on Desktop and Start Menu.

:: ── Write uninstaller ─────────────────────────────────────────────────────
(
echo @echo off
echo echo Uninstalling Road Rash - Moto Brawler...
echo rmdir /S /Q "%INSTALL_DIR%"
echo del "%DESKTOP%\Road Rash - Moto Brawler.lnk" ^>nul 2^>^&1
echo rmdir /S /Q "%START_DIR%" ^>nul 2^>^&1
echo echo Uninstall complete.
echo pause
) > "%INSTALL_DIR%\uninstall.bat"

:: ── Done ──────────────────────────────────────────────────────────────────
echo.
echo  ========================================================
echo    Installation complete!
echo.
echo    Launch: Desktop shortcut  OR  Start Menu ^> Road Rash
echo.
echo    To uninstall: %INSTALL_DIR%\uninstall.bat
echo  ========================================================
echo.

set /p "LAUNCH=Launch game now? [Y/N]: "
if /i "%LAUNCH%"=="Y" (
    start "" "%INSTALL_DIR%\RoadRash.vbs"
)

endlocal
pause
