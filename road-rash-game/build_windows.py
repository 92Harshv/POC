"""
Cross-platform build helper.
Run from Linux/Mac to produce a Windows installer spec and instructions.

Usage:
    python build_windows.py
"""

import subprocess
import sys
import os

SPEC_CONTENT = '''# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Road Rash - Moto Brawler

block_cipher = None

a = Analysis(
    ['game.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pygame'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RoadRash',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''

INNO_SCRIPT = '''[Setup]
AppName=Road Rash - Moto Brawler
AppVersion=1.0
DefaultDirName={autopf}\\RoadRash
DefaultGroupName=Road Rash
OutputDir=installer
OutputBaseFilename=RoadRash_Setup
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\\RoadRash.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\Road Rash - Moto Brawler"; Filename: "{app}\\RoadRash.exe"
Name: "{autodesktop}\\Road Rash - Moto Brawler"; Filename: "{app}\\RoadRash.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\\RoadRash.exe"; Description: "Launch Road Rash"; Flags: nowait postinstall skipifsilent
'''


def main():
    print("=" * 60)
    print("  Road Rash - Moto Brawler  |  Windows Build Helper")
    print("=" * 60)

    # Write spec file
    with open("RoadRash.spec", "w") as f:
        f.write(SPEC_CONTENT)
    print("[OK] Generated RoadRash.spec")

    # Write Inno Setup script
    with open("RoadRash_installer.iss", "w") as f:
        f.write(INNO_SCRIPT)
    print("[OK] Generated RoadRash_installer.iss")

    # Try to run PyInstaller if available
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "pygame>=2.5.0", "pyinstaller>=6.0.0"],
                              stdout=subprocess.DEVNULL)
        print("[OK] Dependencies installed")

        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--clean", "RoadRash.spec"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[OK] PyInstaller build successful!")
            exe_path = os.path.join("dist", "RoadRash.exe")
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"     Executable: {exe_path}  ({size_mb:.1f} MB)")
        else:
            print("[!]  PyInstaller failed (expected when cross-compiling to Windows).")
            print("     Copy project to a Windows machine and run:")
            print("     > pip install -r requirements.txt")
            print("     > pyinstaller --clean RoadRash.spec")
    except Exception as e:
        print(f"[!]  {e}")

    print()
    print("─" * 60)
    print("To create a full Windows installer:")
    print("  1. Copy this project to a Windows machine")
    print("  2. Run: build_windows.bat  (or python build_windows.py)")
    print("  3. Install Inno Setup (https://jrsoftware.org/isinfo.php)")
    print("  4. Open RoadRash_installer.iss in Inno Setup → Compile")
    print("  5. Find installer in:  installer\\RoadRash_Setup.exe")
    print("─" * 60)


if __name__ == "__main__":
    main()
