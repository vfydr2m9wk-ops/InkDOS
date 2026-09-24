# Known limitations — InkDOS 2.6.0

InkDOS is intentionally narrower than Microsoft Office, LibreOffice or Acrobat. Accepting a file extension does not imply exhaustive support for every construct permitted by that format.

## General

- The desktop host uses the operating system WebView rather than a bundled browser engine.
- Service-worker/PWA caching requires HTTP(S); direct `file://` execution depends on host policy.
- Browser and embedded-WebKit behavior can differ. Repository tests do not substitute for every real-device/OS combination.
- Share and Save are different operations. A Share Sheet handoff does not itself prove persistent storage.
- Mobile/browser process termination can bypass normal unload hooks; save before intentionally terminating the host.

## Documents

- DOCX is the primary editable format.
- RTF is imported into the editable document model rather than maintained as a native RTF-preserving editing format.
- Legacy DOC is import-only and is promoted to an editable DOCX copy.
- Complex Word features outside implemented parser/writer contracts may render or round-trip differently.

## Spreadsheets

- XLSX is the primary editable workbook format.
- Legacy XLS is imported locally and saved through the XLSX path.
- Formula coverage, macros, external links, specialized objects and advanced formatting are not equivalent to Excel.

## Presentations

- PPTX is the primary editable presentation format.
- Legacy PPT is imported locally and can be promoted to an editable PPTX copy; native PPT write-back is not provided.
- Fonts, text metrics, unsupported drawings, transitions/animations and embedded objects can differ from PowerPoint/LibreOffice.

## EPUB

- EPUB support is local/offline and includes compatibility fallbacks, but not every valid or malformed publication is guaranteed to render identically to dedicated commercial readers.
- DRM, remote dependencies and uncommon scripted publication features are outside the maintained scope.

## PDF

- PDF support covers local reading, annotations, page tools and export.
- It is not a general-purpose editor for arbitrary existing PDF text/content streams.
- Advanced forms, signatures, password/encryption UI and Acrobat-class editing are not certified.

## Plain Text

- TXT editing is intentionally format-light and does not provide rich-text/media/layout semantics.
- Very large files remain subject to host memory/performance limits even where large-file safeguards are present.

## Release and device validation

The maintained release workflow validates source contracts and builds native packages on Windows, macOS and Linux runners. That does not constitute manual acceptance on every OS distribution, device or embedded WebView. Real-device findings remain authoritative when they differ from synthetic browser tests.
