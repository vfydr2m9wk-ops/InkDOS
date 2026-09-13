; InkDOS workspace launch entries.
; All shortcuts target the single InkDOS host and pass only a workspace selector.
; Workspace ICOs are generated from the canonical assets/icons sources before bundling.

!macro NSIS_HOOK_POSTINSTALL
  CreateDirectory "$SMPROGRAMS\InkDOS"
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
!macroend
