#define MyAppVersion "1.1.4"
#define MyAppName "Label Printing " + MyAppVersion + " (тест)"
#define MyAppExeName "label_printing.exe"

[Setup]
AppId=LabelPrinting.SideBySide.{#MyAppVersion}.Test
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName=C:\LabelPrinting-{#MyAppVersion}-test
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=..\release
OutputBaseFilename=label_printing_{#MyAppVersion}_setup
SetupIconFile=..\ico.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "..\dist\label_printing\*"; DestDir: "{app}"; Excludes: "_internal\.env"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\LabelPrinting\_internal\.env"; DestDir: "{app}\_internal"; Flags: external skipifsourcedoesntexist onlyifdoesntexist uninsneveruninstall
Source: "..\dist\label_printing\_internal\.env"; DestDir: "{app}\_internal"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\ico.ico"; Comment: "Тестовая версия печати этикеток"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить {#MyAppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
