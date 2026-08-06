# Plain Text module

Development sequence `0.19.4.14` adds the first new workspace built directly
on the InkDesk modular and visual foundations.

## Scope

The Plain Text workspace provides:

- New and Open TXT actions.
- Local editing in a notebook-style surface.
- Editable filename in the title bar.
- Save as a local TXT copy.
- Undo and redo history.
- Find next and previous.
- Word-wrap toggle.
- Text-size choices.
- Live line, word, and character counts.
- Shared warning before leaving with unsaved changes.

## Encodings and line endings

Opening supports:

- UTF-8, with or without BOM.
- UTF-16 little endian.
- UTF-16 big endian.

Saving uses UTF-8. The editor remembers whether the opened file used LF, CRLF,
or CR line endings and applies that line ending to the downloaded copy.

## Limits

The local editor rejects files larger than 20 MB to avoid excessive browser
memory use. It is a plain-text editor and intentionally does not add rich-text
formatting, images, tables, or document pagination.

## Modular behavior

`apps/txt/module.json` declares TXT as an enabled optional module. Removing the
module from `modules/module-config.json` and regenerating the registry disables
it without changing Documents, Spreadsheets, Presentations, or PDF.
