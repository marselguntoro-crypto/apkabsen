; ==============================================================================
; Script Inno Setup untuk SIAP (Sistem Informasi Administrasi Presensi)
; Versi: 1.0.0
; Arsitektur Target: Windows 10 & Windows 11 64-bit
; Output: installer/output/SIAP_Setup_v1.0.0.exe
; ==============================================================================

#define MyAppName "SIAP"
#define MyAppFullName "Sistem Informasi Administrasi Presensi"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Tim Pengembang SIAP"
#define MyAppExeName "SIAP.exe"
#define MyAppIcon "..\assets\icons\SIAP.ico"

[Setup]
; Informasi Identitas Aplikasi
AppId={{D814B2B3-78FA-4679-99E7-3E3B66E0C7A1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppFullName}
AllowNoIcons=yes
OutputDir=output
OutputBaseFilename=SIAP_Setup_v1.0.0
SetupIconFile={#MyAppIcon}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Konfigurasi 64-bit Windows
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Kontrol Versi & Update
DisableDirPage=no
DisableProgramGroupPage=no
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppFullName} Setup
VersionInfoCopyright=Copyright (C) 2026 {#MyAppPublisher}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
english.CreateDesktopIcon=Buat ikon di &Desktop
english.AdditionalIcons=Ikon Tambahan:

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Berkas biner dan aset dari hasil PyInstaller (dist/SIAP)
Source: "..\dist\SIAP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Shortcut Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\SIAP.ico"
Name: "{group}\Panduan Pengguna SIAP"; Filename: "{app}\PANDUAN_PENGGUNA_SIAP.pdf"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Shortcut Desktop
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\assets\icons\SIAP.ico"

[Run]
; Opsi jalankan setelah setup selesai
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Prosedur pembersihan saat uninstall
// Menjamin database pengguna (%LOCALAPPDATA%\SIAP) TIDAK terhapus saat update aplikasi
// dan hanya dihapus jika pengguna secara eksplisit mengonfirmasi ingin menghapus database.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
  MsgText: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{localappdata}\SIAP');
    if DirExists(DataDir) then
    begin
      MsgText := 'Apakah Anda juga ingin menghapus seluruh data pengguna, database transaksi, dan arsip backup di:' + #13#10 +
                 DataDir + #13#10#13#10 +
                 'PERINGATAN: Memilih "Yes" akan menghapus seluruh rekaman data presensi dan konfigurasi secara permanen.' + #13#10 +
                 'Pilih "No" jika Anda ingin mempertahankan basis data untuk instalasi aplikasi di masa mendatang.';
      if MsgBox(MsgText, mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;
