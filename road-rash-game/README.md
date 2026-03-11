# Road Rash - Moto Brawler

A Python/Pygame clone of the classic Road Rash motorcycle racing game with combat mechanics.

## Features

- **Pseudo-3D road rendering** with curves, hills, and depth perspective
- **3 levels** of increasing difficulty and track complexity
- **Combat system** — punch and kick rival racers off the road
- **Combo multiplier** for chaining hits
- **Nitro boost** (3 charges per race)
- **Rubber-band AI** — enemies keep the race competitive
- **Particle effects** for sparks and impacts
- **HUD** with speed bar, health bar, position, timer, and cash
- **Procedurally generated** roadside trees and track layout

## Controls

| Action | Keys |
|---|---|
| Accelerate | ↑ / W |
| Brake / Reverse | ↓ / S |
| Steer Left | ← / A |
| Steer Right | → / D |
| Punch Left | Z |
| Punch Right | X |
| Kick Left | Q |
| Kick Right | E |
| Nitro Boost | Left / Right Shift |
| Pause | P / ESC |

## Requirements

- Python 3.9+
- Pygame 2.5+

## Run Directly (any OS)

```bash
pip install pygame
python game.py
```

## Build Windows Executable

### On Windows

```bat
pip install -r requirements.txt
build_windows.bat
```

The standalone `RoadRash.exe` will be in the `dist/` folder.

### Create a Windows Installer (Inno Setup)

1. Run `build_windows.bat` to generate `dist/RoadRash.exe`
2. Download and install [Inno Setup](https://jrsoftware.org/isinfo.php)
3. Open `RoadRash_installer.iss` in Inno Setup and click **Compile**
4. The installer `installer/RoadRash_Setup.exe` will be created

Alternatively, run the Python helper which does steps automatically:

```bash
python build_windows.py
```

## Project Structure

```
road-rash-game/
├── game.py                  # Main game (all-in-one)
├── requirements.txt         # Python dependencies
├── build_windows.bat        # Windows build script
├── build_windows.py         # Cross-platform build helper
├── generate_icon.py         # Icon generator script
├── RoadRash.spec            # PyInstaller spec (auto-generated)
├── RoadRash_installer.iss   # Inno Setup script (auto-generated)
└── assets/
    ├── icon.png
    └── icon.ico
```

## Gameplay Tips

- **Attack enemies near you** — move close and punch/kick in their direction
- **Build combos** — hit 3+ enemies quickly to deal bonus damage
- **Use nitro wisely** — save it for straightaways
- **Stay on the road** — going off-road slows you down significantly
- **Earn cash** by finishing high and knocking down rivals
