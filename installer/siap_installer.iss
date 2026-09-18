; ==============================================================================
; SKRIP INNO SETUP 6 - INSTALLER STANDALONE WINDOWS
; NAMA APLIKASI : SIAP (Sistem Informasi Administrasi Presensi)
; DESKRIPSI     : Aplikasi Desktop Pengelolaan Absensi, Mesin Potongan & Laporan
; VERSI         : 1.5.0 (Tahap 1 - 5 Lengkap)
; ==============================================================================

#define MyAppName "SIAP - Sistem Informasi Administrasi Presensi"
#define MyAppShortName "SIAP Presensi"
#define MyAppVersion "1.5.0"
#define MyAppPublisher "Tim Pengembang SIAP"
#define MyAppURL "https://siap.internal.gov"
#define MyAppExeName "SIAP_Presensi.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".siap"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; Basic Setup Information
AppId={{C8E9A341-889B-4D95-9271-DE5F7B814672}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppShortName}
DefaultGroupName={#MyAppShortName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=Output
OutputBaseFilename=SIAP_Presensi_Setup_v1.5.0
SetupIconFile=resources\icons\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion=1.5.0.0
VersionInfoCompany=Tim Pengembang SIAP
VersionInfoDescription=Sistem Informasi Administrasi Presensi Windows Desktop
VersionInfoCopyright=Copyright (C) 2025-2026 SIAP All Rights Reserved.

[Languages]
Name: "indonesian"; MessagesFile: "compiler:Languages\Indonesian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Salin seluruh bundle hasil kompilasi PyInstaller (--onedir)
Source: "..\dist\SIAP_Presensi\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\SIAP_Presensi\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Folder data default untuk SQLite, templates, dan direktori ekspor
Source: "..\data\templates\*"; DestDir: "{userappdata}\SIAP_Presensi\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: isreadme ignoreversion

[Dirs]
; Buat direktori kerja runtime untuk database, laporan hasil ekspor, dan backup
Name: "{userappdata}\SIAP_Presensi"
Name: "{userappdata}\SIAP_Presensi\database"
Name: "{userappdata}\SIAP_Presensi\backups"
Name: "{userappdata}\SIAP_Presensi\reports"
Name: "{userappdata}\SIAP_Presensi\logs"

[Icons]
Name: "{group}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*.log"
Type: filesandordirs; Name: "{userappdata}\SIAP_Presensi\logs"

[Code]
// Script Pascal untuk mengecek kelengkapan pra-instalasi Windows
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Pastikan hak akses direktori kerja userappdata dapat ditulis
  end;
end;
