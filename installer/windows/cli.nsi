; NSIS installer for the Sweepito command line. Windows only; see common.nsh for the options.
;
;   makensis /DAPP_NAME="Sweepito" /DAPP_VERSION=0.1.0 /DSOURCE_DIR=build\installer\sweepito ^
;            /DOUT_FILE=dist\installer\sweepito-0.1.0.setup.exe installer\windows\cli.nsi
; scripts/build_installer.py does this from the project's own metadata.
;
; Silent use: sweepito-<version>.setup.exe /S [/allusers | /currentuser] [/NOPATH] [/D=C:\folder]
;             uninstall.exe /S

; Stable id of this product: keep it for the life of the project, so a newer setup replaces an
; older install.
!define GUID "{B3C41F7A-52D8-4E69-A0B1-7D9E3C6A8F24}"
!define MAIN_EXE "sweepito.exe"
!define HAS_PATH

!include "common.nsh"
