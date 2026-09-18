; ==============================================================================
; SKRIP NSIS (Nullsoft Scriptable Install System)
; NAMA APLIKASI : SIAP (Sistem Informasi Administrasi Presensi)
; ==============================================================================

!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "SIAP - Sistem Informasi Administrasi Presensi"
OutFile "Output\SIAP_Presensi_Setup_NSIS.exe"
InstallDir "$LOCALAPPDATA\SIAP_Presensi"
InstallDirRegKey HKCU "Software\SIAP_Presensi" "Install_Dir"
RequestExecutionLevel user

!define MUI_ABORTWARNING
!define MUI_ICON "resources\icons\app_icon.ico"
!define MUI_UNICON "resources\icons\app_icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\SIAP_Presensi.exe"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Indonesian"
!insertmacro MUI_LANGUAGE "English"

Section "SIAP Application (Required)" SecCore
  SetOutPath "$INSTDIR"
  File /r "..\dist\SIAP_Presensi\*.*"

  ; Create AppData working directories
  CreateDirectory "$APPDATA\SIAP_Presensi\database"
  CreateDirectory "$APPDATA\SIAP_Presensi\backups"
  CreateDirectory "$APPDATA\SIAP_Presensi\reports"
  CreateDirectory "$APPDATA\SIAP_Presensi\logs"

  WriteRegStr HKCU "Software\SIAP_Presensi" "Install_Dir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Shortcuts
  CreateDirectory "$SMPROGRAMS\SIAP Presensi"
  CreateShortcut "$SMPROGRAMS\SIAP Presensi\SIAP Presensi.lnk" "$INSTDIR\SIAP_Presensi.exe"
  CreateShortcut "$SMPROGRAMS\SIAP Presensi\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  CreateShortcut "$DESKTOP\SIAP Presensi.lnk" "$INSTDIR\SIAP_Presensi.exe"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\SIAP Presensi.lnk"
  Delete "$SMPROGRAMS\SIAP Presensi\*.*"
  RMDir "$SMPROGRAMS\SIAP Presensi"

  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\SIAP_Presensi"
SectionEnd
