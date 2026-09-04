# Home and document-session refinement

Sequence `0.19.4.13` reduces visual noise on the launcher and establishes a
shared contract for names and unsaved work.

## Launcher order

The launcher now presents the InkDOS identity, enabled workspace cards,
universal local Open action, product principles, a compact stabilization note,
and finally build information with project links.

The universal Open panel no longer lists every extension in descriptive text.
Its privacy line is simply: `The selected file stays on this device.`

## Editable filenames

The title bar filename is editable in Documents (`.docx`), Spreadsheets
(`.xlsx`), Presentations (`.pptx`), and PDF (`.pdf`). Missing extensions are
restored automatically, unsupported filename characters are replaced, and the
edited name becomes the basis for the next exported copy.

## Unsaved-change contract

`shared/file-lifecycle.js` registers lifecycle controllers in a shared unload
guard. Any controller with unverified changes triggers the browser's native
leave or reload confirmation.

PDF joins the same lifecycle after a review annotation, bookmark, inserted
text, or filename change. Future TXT and editable EPUB modules must use
`InkDOSFileLifecycle.create()` to receive the same protection.
