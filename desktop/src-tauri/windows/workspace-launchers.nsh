; InkDOS workspace launch entries.
; All shortcuts target the single InkDOS host and pass only a workspace selector.

!macro NSIS_HOOK_POSTINSTALL
  CreateDirectory "$SMPROGRAMS\InkDOS"
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS Documents.lnk" "$INSTDIR\InkDOS.exe" "--workspace documents"
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS Spreadsheets.lnk" "$INSTDIR\InkDOS.exe" "--workspace spreadsheets"
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS Presentations.lnk" "$INSTDIR\InkDOS.exe" "--workspace presentations"
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS PDF.lnk" "$INSTDIR\InkDOS.exe" "--workspace pdf"
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS EPUB.lnk" "$INSTDIR\InkDOS.exe" "--workspace epub"
  CreateShortCut "$SMPROGRAMS\InkDOS\InkDOS Plain Text.lnk" "$INSTDIR\InkDOS.exe" "--workspace txt"
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
