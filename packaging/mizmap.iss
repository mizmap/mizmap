; Inno Setup script for MizMap. Builds a per-user installer that drops the
; PyInstaller --onedir output under %LOCALAPPDATA%\Programs\MizMap\ and adds a
; Start menu shortcut. No admin elevation, no PATH pollution, no registry
; mess beyond what Inno Setup needs to remember the install for uninstall.
;
; Build with: scripts/build_windows.ps1 (which runs pyinstaller first, then
; ISCC over this file). Or invoke ISCC directly once pyinstaller has produced
; packaging/dist/mizmap/.
;
; The version is overridden by /DAppVersion=x.y.z on the ISCC command line so
; we don't have to edit two places when bumping mizmap/__init__.py.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define AppName       "MizMap"
#define AppPublisher  "MizMap Project"
#define AppExeName    "mizmap.exe"
#define SourceDist    "dist\mizmap"

[Setup]
AppId={{BF50A684-F032-4F6C-A0C7-BE86290ED951}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist
OutputBaseFilename=mizmap-setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
UninstallDisplayName={#AppName} {#AppVersion}
UninstallDisplayIcon={app}\{#AppExeName}
SetupIconFile=..\mizmap\data\mizmap.ico
; Show the GPL during install (informational — GPL grants rights, it isn't a
; EULA, but the wizard page is the conventional place to surface it).
LicenseFile=..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; \
  GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; Pull the entire one-folder PyInstaller bundle. recursesubdirs walks all of
; _internal/ (which contains the Python runtime, native exts, web assets,
; units.yaml, proto_gen/, etc.). createallsubdirs preserves the layout the
; frozen runtime expects.
Source: "{#SourceDist}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; License texts at the install root, sourced from the repo (not the bundle) so
; they're easy to find post-install and the binary ships with its terms.
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_LICENSES.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSES\AGPL-3.0.txt"; DestDir: "{app}\LICENSES"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Clear MizMap tile cache"; Filename: "{app}\{#AppExeName}"; \
  Parameters: "clear-cache"; \
  Comment: "Wipe the local map-tile cache (%LOCALAPPDATA%\MizMap\tiles)"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Per-user data (config.toml, tile cache) lives outside {app} and stays put
; through uninstall on purpose — re-installs pick up where the user left off,
; and an accidental uninstall doesn't wipe a 2 GB tile cache they just primed.
; Users who want a clean removal can delete %APPDATA%\MizMap and
; %LOCALAPPDATA%\MizMap manually.
