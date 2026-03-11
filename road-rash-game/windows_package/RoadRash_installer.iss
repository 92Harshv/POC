[Setup]
AppName=Road Rash - Moto Brawler
AppVersion=1.0
DefaultDirName={autopf}\RoadRash
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
Source: "dist\RoadRash.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Road Rash - Moto Brawler"; Filename: "{app}\RoadRash.exe"
Name: "{autodesktop}\Road Rash - Moto Brawler"; Filename: "{app}\RoadRash.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\RoadRash.exe"; Description: "Launch Road Rash"; Flags: nowait postinstall skipifsilent
