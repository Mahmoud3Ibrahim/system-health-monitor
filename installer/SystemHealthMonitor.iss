; Inno Setup script for the System Health Monitor agent

[Setup]
AppName=System Health Monitor
AppVersion=1.0.0
AppPublisher=Your Company
DefaultDirName={pf}\SystemHealthMonitor
DefaultGroupName=System Health Monitor
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=dist\installer
OutputBaseFilename=SystemHealthMonitor-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
; Core executable produced by PyInstaller
Source: "..\dist\SystemHealthMonitor.exe"; DestDir: "{app}"; Flags: ignoreversion
; Bundled NSSM helper to manage the Windows Service
Source: "..\tools\nssm\nssm.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\System Health Monitor"; Filename: "{app}\SystemHealthMonitor.exe"
Name: "{commondesktop}\System Health Monitor"; Filename: "{app}\SystemHealthMonitor.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
; Install the Windows Service via NSSM after copying files
Filename: "{app}\nssm.exe"; Parameters: "install SystemHealthMonitor ""{app}\SystemHealthMonitor.exe"""; StatusMsg: "Installing Windows Service..."; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set SystemHealthMonitor AppDirectory ""{app}"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set SystemHealthMonitor Start SERVICE_AUTO_START"; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "start SystemHealthMonitor"; StatusMsg: "Starting Windows Service..."; Flags: runhidden

[UninstallRun]
Filename: "{app}\nssm.exe"; Parameters: "stop SystemHealthMonitor"; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "remove SystemHealthMonitor confirm"; Flags: runhidden

