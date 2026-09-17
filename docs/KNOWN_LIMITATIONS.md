# Known limitations

These limitations describe InkDOS 2.2.0. They distinguish an implemented code path from compatibility that has actually been confirmed on a specific host or file.

## General

- InkDOS 2.2.0 includes an installable Tauri desktop host. Windows installation has been manually confirmed; macOS/Linux packages are built on native CI runners, but that CI result is not a claim of manual acceptance on every desktop distribution or OS configuration.
- The desktop host uses the operating system WebView rather than a custom rendering engine. Memory usage therefore includes the platform WebView/runtime in addition to InkDOS application code.
- InkDOS is intentionally narrower than a full desktop office suite. Accepting a file extension does not imply exhaustive support for every construct permitted by that format.
- Automated regression coverage includes Chromium, Firefox and WebKit, but an automated WebKit run is not equivalent to every embedded iPad/WebKit host. XeOS/iPad-specific behavior such as Share Sheet routing, native picker fallbacks and host download policy still requires real-device confirmation.
- Service-worker/PWA caching requires HTTP(S). Direct `file://` execution depends on the host browser's local-file policy and does not provide the same offline-installation guarantees.
- Mobile/browser process termination can bypass normal unload hooks. Save before intentionally closing the host application.
- Share and Save are different operations. A Share Sheet handoff does not itself prove that a persistent destination was written.

## Documents

- DOCX is the primary editable document format.
- RTF is imported into the editable document model and is subsequently exported through the supported editable-copy path rather than written back as an RTF-preserving editor.
- Legacy DOC is import-only. It is opened through the local legacy reader and must be promoted to an editable DOCX copy for normal editing/saving; InkDOS does not write back to `.doc`.
- Complex Word features outside the implemented parser/writer contracts can be preserved only partially or may render differently from Microsoft Word/LibreOffice.

## Spreadsheets

- XLSX is the primary editable workbook format.
- Legacy XLS is imported locally into the workbook model and saved through the XLSX path; InkDOS does not provide native XLS write-back.
- Formula coverage and advanced workbook features are not equivalent to Excel. Unsupported formulas, macros, external links, specialized objects and complex formatting may not evaluate or round-trip exactly.

## Presentations

- PPTX is the primary editable presentation format.
- Legacy PPT is imported through the local legacy reader and can be promoted to an editable PPTX copy; native PPT write-back is not provided.
- Legacy presentation fidelity has dedicated compatibility handling, but fonts, text metrics, clipping, unsupported drawing features, transitions/animations and complex embedded objects can still differ from PowerPoint/LibreOffice.
- Real-device confirmation remains important for legacy PPT/PPTX visual fidelity after synthetic browser validation.

## EPUB

- EPUB support is local and offline, with compatibility fallbacks for several ZIP/path/package cases. It is not a guarantee that every valid or malformed EPUB in the ecosystem will open identically to a dedicated commercial reader.
- The reader supports navigation, themes and annotations, but highly specialized scripting, DRM, remote dependencies and uncommon publication features are outside the certified scope.
- iPad/XeOS opening/rendering remains a real-device acceptance target for files that previously exercised WebKit-specific package/deflate/path behavior.

## PDF

- PDF uses the accepted local PDF.js-based reading/rendering stack plus InkDOS annotation/page-tool layers.
- InkDOS can read, annotate and export supported PDF changes, but it is not a general-purpose editor for arbitrary existing PDF text/content streams.
- Advanced forms, signatures, password/encryption UI and all Acrobat-class editing features are not certified.
- PDF changes remain in the active session until an export/save delivery is completed. Host file-delivery behavior can differ across browsers and embedded WebKit containers.

## Plain Text

- Plain Text is intentionally format-light. Rich-text formatting, embedded media and document-layout semantics are not part of TXT editing.
- Very large files remain subject to browser memory/performance limits even where large-file safeguards are present.

## Save and device confirmation

- The current code includes single-flight/single-delivery guards and confirmed-delivery gating. Those protections are regression-backed, but any previously observed iPad/XeOS symptom involving duplicate files or an unexpected secondary file is considered fully closed only after confirmation on the affected real-device path.
- Failed, cancelled, stale or unconfirmed destructive-save flows are designed to retain dirty state and block destructive navigation; host termination outside the page lifecycle is not something a web application can reliably intercept.

This document is the current limitation reference. Historical freeze/audit documents remain unchanged when they describe earlier releases or earlier validation states.
