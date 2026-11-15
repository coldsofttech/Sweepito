; Shared setup behaviour for cli.nsi: pages, install, shortcuts, PATH, uninstall and silent options.
;
; A product file defines what is specific to it, then includes this file:
;
;   GUID          stable id of the product (upgrades replace an earlier install), "{...}"
;   MAIN_EXE      the program the Start Menu shortcut starts, e.g. "example-ui.exe"
;   HAS_PATH      optional: offer to add the install folder to PATH (command line product)
;   HAS_DESKTOP   optional: offer a desktop shortcut and "run now" (window product)
;   INSTALL_SUBDIR  optional: a folder under <PUBLISHER>\<FOLDER_NAME> for products that share a name
;
; scripts/build_installer.py passes the rest, from pyproject.toml and the code, with /D:
;
;   APP_NAME      product name; also the shortcut name
;   FOLDER_NAME   optional: Start Menu folder and install folder shared by the products (default: APP_NAME)
;   APP_VERSION   e.g. 0.1.0 (APP_VERSION_NUMERIC "0.1.0.0" is derived if not given)
;   SOURCE_DIR    the PyInstaller folder to install (build/installer/example-cli)
;   OUT_FILE      the installer to write (e.g. dist/example-cli-0.1.0.setup.exe)
;   PUBLISHER (default: APP_NAME; also the install folder's parent), URL (home page),
;   SUPPORT_URL (help link), ICON_FILE (.ico), LICENSE_FILE   optional
;   HEADER_IMAGE (.bmp, 150x57), WELCOME_IMAGE (.bmp, 164x314)   optional, from brand/
;   USER_DATA_DIR optional: folder with settings and data; the uninstaller asks before removing it
;
; Silent use: Setup.exe /S [/allusers | /currentuser] [/NOPATH] [/DESKTOP] [/D=C:\folder]
;             uninstall.exe /S [/PURGE]    (/PURGE also removes USER_DATA_DIR)
; The default choice is a per-user install; "all users" needs administrator rights (UAC).

!ifndef GUID
  !error "Define GUID in the product file."
!endif
!ifndef MAIN_EXE
  !error "Define MAIN_EXE in the product file."
!endif
!ifndef APP_NAME
  !error "Pass /DAPP_NAME=... (scripts/build_installer.py does)."
!endif
!ifndef APP_VERSION
  !error "Pass /DAPP_VERSION=..."
!endif
!ifndef SOURCE_DIR
  !error "Pass /DSOURCE_DIR=... (the PyInstaller output folder)."
!endif
!ifndef OUT_FILE
  !error "Pass /DOUT_FILE=..."
!endif
!ifndef APP_VERSION_NUMERIC
  !define APP_VERSION_NUMERIC "${APP_VERSION}.0"
!endif
!ifndef FOLDER_NAME
  !define FOLDER_NAME "${APP_NAME}"
!endif
!ifndef PUBLISHER
  !define PUBLISHER "${APP_NAME}"
!endif

; INSTALL_SUBDIR is optional: a product that shares its folder with another one sets it.
!ifdef INSTALL_SUBDIR
  !define INSTALL_REL "${PUBLISHER}\${FOLDER_NAME}\${INSTALL_SUBDIR}"
  !define INSTALL_DEPTH 2
!else
  !define INSTALL_REL "${PUBLISHER}\${FOLDER_NAME}"
  !define INSTALL_DEPTH 1
!endif

!ifdef HAS_PATH
  !define HAS_OPTIONS
!endif
!ifdef HAS_DESKTOP
  !ifndef HAS_OPTIONS
    !define HAS_OPTIONS
  !endif
!endif

!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${GUID}"
!define UNINSTALLER "uninstall.exe"

Name "${APP_NAME}"
OutFile "${OUT_FILE}"
Unicode true
; The marker is still in $INSTDIR in .onInit unless the user gave /D=folder.
!define NO_INSTDIR "<default folder>"
InstallDir "${NO_INSTDIR}"
SetCompressor /SOLID lzma
BrandingText "${APP_NAME} ${APP_VERSION}"
ManifestDPIAware true
ManifestSupportedOS Win10

VIProductVersion "${APP_VERSION_NUMERIC}"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "FileDescription" "${APP_NAME} setup"
VIAddVersionKey "CompanyName" "${PUBLISHER}"
VIAddVersionKey "LegalCopyright" "${PUBLISHER}"

; ---- install mode: this user (default) or all users --------------------------------------------
; Highest: an administrator is asked once (UAC) at start; a standard user runs unelevated and is
; asked for an administrator only after choosing "all users".
!define MULTIUSER_EXECUTIONLEVEL Highest
!define MULTIUSER_MUI
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!define MULTIUSER_INSTALLMODE_ALLOW_ELEVATION
!define MULTIUSER_INSTALLMODE_DEFAULT_CURRENTUSER
!define MULTIUSER_USE_PROGRAMFILES64
!define MULTIUSER_INSTALLMODE_INSTDIR "${INSTALL_REL}"
!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_KEY "Software\${APP_NAME}"
!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_VALUENAME "InstallLocation"
!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_KEY "Software\${APP_NAME}"
!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_VALUENAME "InstallLocation"

!include MUI2.nsh
!include MultiUser.nsh
!include FileFunc.nsh
!include LogicLib.nsh
!include Sections.nsh

!insertmacro GetParameters
!insertmacro GetOptions
!insertmacro un.GetParameters
!insertmacro un.GetOptions
!insertmacro un.GetParent

!ifdef ICON_FILE
  !define MUI_ICON "${ICON_FILE}"
  !define MUI_UNICON "${ICON_FILE}"
!endif
!ifdef HEADER_IMAGE
  !define MUI_HEADERIMAGE
  !define MUI_HEADERIMAGE_BITMAP "${HEADER_IMAGE}"
  !define MUI_HEADERIMAGE_UNBITMAP "${HEADER_IMAGE}"
!endif
!ifdef WELCOME_IMAGE
  !define MUI_WELCOMEFINISHPAGE_BITMAP "${WELCOME_IMAGE}"
  !define MUI_UNWELCOMEFINISHPAGE_BITMAP "${WELCOME_IMAGE}"
!endif
!define MUI_ABORTWARNING

; ---- pages ---------------------------------------------------------------------------------------
!insertmacro MUI_PAGE_WELCOME
!ifdef LICENSE_FILE
  !insertmacro MUI_PAGE_LICENSE "${LICENSE_FILE}"
!endif
!insertmacro MULTIUSER_PAGE_INSTALLMODE
!ifdef HAS_OPTIONS
  !insertmacro MUI_PAGE_COMPONENTS
!endif
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!ifdef HAS_DESKTOP
  ; Started through Explorer so the program runs as the user, not elevated like the installer.
  !define MUI_FINISHPAGE_RUN
  !define MUI_FINISHPAGE_RUN_TEXT "Start ${APP_NAME}"
  !define MUI_FINISHPAGE_RUN_FUNCTION LaunchApp
!endif
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Function un.onInit
  !insertmacro MULTIUSER_UNINIT
FunctionEnd

!ifdef HAS_DESKTOP
Function LaunchApp
  Exec '"$WINDIR\explorer.exe" "$INSTDIR\${MAIN_EXE}"'
FunctionEnd
!endif

; ---- install -------------------------------------------------------------------------------------
Section "!${APP_NAME}" SecMain
  SectionIn RO
  SetRegView 64

  ; An upgrade replaces the old files; stale ones from an earlier version must not stay behind.
  RMDir /r "$INSTDIR\lib"

  SetOutPath "$INSTDIR"
  File /r "${SOURCE_DIR}\*.*"
  !ifdef LICENSE_FILE
    File "/oname=LICENSE.txt" "${LICENSE_FILE}"
  !endif
  !ifdef HAS_PATH
    File "path.ps1"
  !endif

  WriteUninstaller "$INSTDIR\${UNINSTALLER}"

  ; Start Menu > Programs > <folder name>, shared by the products. No uninstall shortcut: both
  ; products are listed in Settings > Apps.
  CreateDirectory "$SMPROGRAMS\${FOLDER_NAME}"
  !ifdef HAS_PATH
    ; A prompt where the command already works, even if it was not added to PATH.
    CreateShortcut "$SMPROGRAMS\${FOLDER_NAME}\${APP_NAME}.lnk" "$SYSDIR\cmd.exe" \
      '/K set "PATH=$INSTDIR;%PATH%"' "$INSTDIR\${MAIN_EXE}" 0
  !else
    CreateShortcut "$SMPROGRAMS\${FOLDER_NAME}\${APP_NAME}.lnk" "$INSTDIR\${MAIN_EXE}"
  !endif

  ; Where it is installed (also tells a later setup, and the uninstaller, which mode this was).
  WriteRegStr SHCTX "Software\${APP_NAME}" "InstallLocation" "$INSTDIR"

  ; Apps & features
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME}"
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "Publisher" "${PUBLISHER}"
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\${UNINSTALLER}"'
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "QuietUninstallString" '"$INSTDIR\${UNINSTALLER}" /S'
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${MAIN_EXE}"
  !ifdef URL
    WriteRegStr SHCTX "${UNINSTALL_KEY}" "URLInfoAbout" "${URL}"
  !endif
  !ifdef SUPPORT_URL
    WriteRegStr SHCTX "${UNINSTALL_KEY}" "HelpLink" "${SUPPORT_URL}"
  !endif
  WriteRegDWORD SHCTX "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD SHCTX "${UNINSTALL_KEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD SHCTX "${UNINSTALL_KEY}" "EstimatedSize" "$0"
SectionEnd

!ifdef HAS_PATH
Section "Add to PATH" SecPath
  ${If} $MultiUser.InstallMode == "AllUsers"
    StrCpy $0 "Machine"
  ${Else}
    StrCpy $0 "User"
  ${EndIf}
  nsExec::ExecToLog '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive \
    -ExecutionPolicy Bypass -File "$INSTDIR\path.ps1" -Action Add -Scope $0 -Dir "$INSTDIR"'
  Pop $1
  ${If} $1 != 0
    DetailPrint "Could not add $INSTDIR to PATH (code $1)."
  ${Else}
    WriteRegDWORD SHCTX "Software\${APP_NAME}" "OnPath" 1
  ${EndIf}
SectionEnd
!endif

!ifdef HAS_DESKTOP
Section /o "Desktop shortcut" SecDesktop
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${MAIN_EXE}"
SectionEnd
!endif

!ifdef HAS_OPTIONS
  LangString DESC_Main ${LANG_ENGLISH} "The program files."
  !ifdef HAS_PATH
    LangString DESC_Path ${LANG_ENGLISH} "Lets you run ${MAIN_EXE} from any terminal."
  !endif
  !ifdef HAS_DESKTOP
    LangString DESC_Desktop ${LANG_ENGLISH} "Adds a shortcut to the desktop."
  !endif
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_Main)
    !ifdef HAS_PATH
      !insertmacro MUI_DESCRIPTION_TEXT ${SecPath} $(DESC_Path)
    !endif
    !ifdef HAS_DESKTOP
      !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_Desktop)
    !endif
  !insertmacro MUI_FUNCTION_DESCRIPTION_END
!endif

; ---- start up (after the sections, whose constants it uses) ------------------------------
Function .onInit
  ; MultiUser sets $INSTDIR for the chosen mode and would discard a folder given with /D=, so
  ; keep that folder (anything but the marker below) and put it back afterwards.
  StrCpy $R8 $INSTDIR
  !insertmacro MULTIUSER_INIT
  ${If} $R8 != "${NO_INSTDIR}"
    StrCpy $INSTDIR $R8
  ${EndIf}
  ${GetParameters} $R0
  !ifdef HAS_PATH
    ${GetOptions} $R0 "/NOPATH" $R1
    ${IfNot} ${Errors}
      SectionSetFlags ${SecPath} 0
    ${EndIf}
    ClearErrors
  !endif
  !ifdef HAS_DESKTOP
    ${GetOptions} $R0 "/DESKTOP" $R1
    ${IfNot} ${Errors}
      SectionSetFlags ${SecDesktop} ${SF_SELECTED}
    ${EndIf}
    ClearErrors
  !endif
FunctionEnd

; ---- uninstall -----------------------------------------------------------------------------------
Section "Uninstall"
  SetRegView 64

  !ifdef HAS_PATH
    ReadRegDWORD $1 SHCTX "Software\${APP_NAME}" "OnPath"
    ${If} $1 == 1
      ${If} $MultiUser.InstallMode == "AllUsers"
        StrCpy $0 "Machine"
      ${Else}
        StrCpy $0 "User"
      ${EndIf}
      nsExec::ExecToLog '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive \
        -ExecutionPolicy Bypass -File "$INSTDIR\path.ps1" -Action Remove -Scope $0 -Dir "$INSTDIR"'
      Pop $1
    ${EndIf}
  !endif

  ; Only what setup installed is removed, so a folder chosen by hand keeps anything else in it.
  RMDir /r "$INSTDIR\lib"
  Delete "$INSTDIR\${MAIN_EXE}"
  Delete "$INSTDIR\LICENSE.txt"
  Delete "$INSTDIR\path.ps1"
  Delete "$INSTDIR\${UNINSTALLER}"
  RMDir "$INSTDIR"
  ; The folders above it are setup's own only in the default location (not after /D= or a custom
  ; folder). RMDir leaves them while the other product, or anything else, is in them.
  StrCpy $0 "\${INSTALL_REL}"
  StrLen $1 $0
  StrCpy $2 $INSTDIR "" -$1
  ${If} $2 == $0
    ${un.GetParent} "$INSTDIR" $3
    RMDir "$3"
    !if ${INSTALL_DEPTH} == 2
      ${un.GetParent} "$3" $3
      RMDir "$3"
    !endif
  ${EndIf}

  ; Only this product's shortcuts: the folder is shared, so no RMDir /r. RMDir leaves it while the
  ; other product's shortcut is in it. The uninstall shortcut is from older setups.
  Delete "$SMPROGRAMS\${FOLDER_NAME}\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${FOLDER_NAME}\${APP_NAME} prompt.lnk"
  Delete "$SMPROGRAMS\${FOLDER_NAME}\Uninstall ${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\${FOLDER_NAME}"
  !ifdef HAS_DESKTOP
    Delete "$DESKTOP\${APP_NAME}.lnk"
  !endif

  DeleteRegKey SHCTX "${UNINSTALL_KEY}"
  DeleteRegKey SHCTX "Software\${APP_NAME}"

  ; Settings and data stay unless the user opts in (or passes /PURGE when silent).
  !ifdef USER_DATA_DIR
    ${un.GetParameters} $R0
    ${un.GetOptions} $R0 "/PURGE" $R1
    ${IfNot} ${Errors}
      RMDir /r "${USER_DATA_DIR}"
    ${ElseIfNot} ${Silent}
      MessageBox MB_YESNO|MB_ICONQUESTION|MB_DEFBUTTON2 \
        "Also remove your ${APP_NAME} settings and data?$\r$\n${USER_DATA_DIR}" IDNO +2
      RMDir /r "${USER_DATA_DIR}"
    ${EndIf}
  !endif
SectionEnd
