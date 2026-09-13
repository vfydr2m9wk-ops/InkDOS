; InkDOS workspace launch entries.
; All shortcuts target the single InkDOS host and pass only a workspace selector.
; Workspace ICOs are generated from the canonical assets/icons sources before bundling.
; Capture the hook directory at include time: macro expansion happens from Tauri's generated script.
!define HOOK_FILE_DIR "${__FILEDIR__}"

!macro NSIS_HOOK_POSTINSTALL
  CreateDirectory "$SMPROGRAMS\InkDOS"

  CreateDirectory "$INSTDIR\workspace-icons\documents"
  SetOutPath "$INSTDIR\workspace-icons\documents"
  File /oname=icon.ico "${HOOK_FILE_DIR}\workspace-icons\documents\icon.ico"

  CreateDirectory "$INSTDIR\workspace-icons\spreadsheets"
  SetOutPath "$INSTDIR\workspace-icons\spreadsheets"
  File /oname=icon.ico "${HOOK_FILE_DIR}\workspace-icons\spreadsheets\icon.ico"

  CreateDirectory "$INSTDIR\workspace-icons\presentations"
  SetOutPath "$INSTDIR\workspace-icons\presentations"
  File /oname=icon.ico "${HOOK_FILE_DIR}\workspace-icons\presentations\icon.ico"

  CreateDirectory "$INSTDIR\workspace-icons\pdf"
  SetOutPath "$INSTDIR\workspace-icons\pdf"
  File /oname=icon.ico "${HOOK_FILE_DIR}\workspace-icons\pdf\icon.ico"

  CreateDirectory "$INSTDIR\workspace-icons\epub"
  SetOutPath "$INSTDIR\workspace-icons\epub"
  File /oname=icon.ico "${HOOK_FILE_DIR}\workspace-icons\epub\icon.ico"

  CreateDirectory "$INSTDIR\workspace-icons\txt"
  SetOutPath "$INSTDIR\workspace-icons\txt"
  File /oname=icon.ico "${HOOK_FILE_DIR}\workspace-icons\txt\icon.ico"

  SetOutPath "$INSTDIR"
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS Documents.lnk" "$INSTDIR\InkDOS.exe" "--workspace documents" "$INSTDIR\workspace-icons\documents\icon.ico" 0
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS Spreadsheets.lnk" "$INSTDIR\InkDOS.exe" "--workspace spreadsheets" "$INSTDIR\workspace-icons\spreadsheets\icon.ico" 0
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS Presentations.lnk" "$INSTDIR\InkDOS.exe" "--workspace presentations" "$INSTDIR\workspace-icons\presentations\icon.ico" 0
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS PDF.lnk" "$INSTDIR\InkDOS.exe" "--workspace pdf" "$INSTDIR\workspace-icons\pdf\icon.ico" 0
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS EPUB.lnk" "$INSTDIR\InkDOS.exe" "--workspace epub" "$INSTDIR\workspace-icons\epub\icon.ico" 0
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS Plain Text.lnk" "$INSTDIR\InkDOS.exe" "--workspace txt" "$INSTDIR\workspace-icons\txt\icon.ico" 0
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  Delete "$SMPROGRAMS\InkDOS\InkDOS Documents.lnk"
  Delete "$SMPROGRAMS\InkDOS\InkDOS Spreadsheets.lnk"
  Delete "$SMPROGRAMS\InkDOS\InkDOS Presentations.lnk"
  Delete "$SMPROGRAMS\InkDOS\InkDOS PDF.lnk"
  Delete "$SMPROGRAMS\InkDOS\InkDOS EPUB.lnk"
  Delete "$SMPROGRAMS\InkDOS\InkDOS Plain Text.lnk"
  RMDir "$SMPROGRAMS\InkDOS"

  Delete "$INSTDIR\workspace-icons\documents\icon.ico"
  Delete "$INSTDIR\workspace-icons\spreadsheets\icon.ico"
  Delete "$INSTDIR\workspace-icons\presentations\icon.ico"
  Delete "$INSTDIR\workspace-icons\pdf\icon.ico"
  Delete "$INSTDIR\workspace-icons\epub\icon.ico"
  Delete "$INSTDIR\workspace-icons\txt\icon.ico"
  RMDir "$INSTDIR\workspace-icons\documents"
  RMDir "$INSTDIR\workspace-icons\spreadsheets"
  RMDir "$INSTDIR\workspace-icons\presentations"
  RMDir "$INSTDIR\workspace-icons\pdf"
  RMDir "$INSTDIR\workspace-icons\epub"
  RMDir "$INSTDIR\workspace-icons\txt"
  RMDir "$INSTDIR\workspace-icons"
!macroend
