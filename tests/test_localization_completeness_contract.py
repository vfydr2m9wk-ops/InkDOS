#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALE_DIR = ROOT / "shared" / "localization" / "locales"
HELP_FILES = [
    "apps/documents/help/help.js",
    "apps/spreadsheets/help/help.js",
    "apps/presentations/help/help.js",
    "apps/pdf/help/help.js",
    "apps/epub/help/help.js",
    "apps/txt/help/help.js",
]
REQUIRED_DOCUMENTS_KEYS = {
    "Documents",
    "Create a document or open a DOCX, RTF, or legacy DOC file locally.",
    "Documents Help",
    "Close Help",
    "Use this guide to create, open, edit, format, and save word-processing documents locally.",
    "Getting started",
    "Editing text",
    "Formatting",
    "Navigation and zoom",
    "Opening and saving",
    "Local-first behavior",
    "Create a blank document from the hamburger menu or open a DOCX, RTF, or legacy DOC file. The document opens in the paged editing surface.",
    "Click inside the document to place the caret, then type normally. Select text before applying formatting. Undo and redo are available from the editing toolbar.",
    "Use the toolbar for font family and size, emphasis, paragraph alignment, lists, indentation, and other document tools. Page and section controls are available when the document structure supports them.",
    "Use the document navigation controls to move through longer files. Zoom changes only the workspace view and does not change the saved document content.",
    "Opening a new file while the current document has unsaved changes may ask for confirmation. Saving creates a local copy in a supported document format; keep the downloaded copy if you want to preserve your edits.",
    "Document processing happens in the browser. InkDOS does not need to upload the document to a remote editor to display or edit it.",
    "Document tools",
    "Proofing",
    "Browser spellcheck",
    "Spelling suggestions are provided locally by the host browser when available.",
    "Comments",
    "Comment",
    "Comment on selected text",
    "Add",
    "No comments in this document.",
    "Commented text",
    "Remove",
    "Footnotes",
    "Footnote text",
    "Table of contents",
    "Insert / Update TOC",
    "The TOC is regenerated from document headings and current page positions.",
    "Paragraph styles",
    "Style",
    "Heading 3",
    "Subtitle",
    "Quote",
    "Apply",
    "Table tools",
    "Merge right",
    "Delete row",
    "Delete column",
    "Browser spellcheck enabled",
    "Browser spellcheck disabled",
    "Enter a comment first",
    "Select text for the comment",
    "Comments currently require a selection inside one paragraph",
    "Comment added",
    "Comment could not be added to this selection",
    "Comment removed",
    "Enter footnote text first",
    "Place the cursor where the footnote belongs",
    "Place the cursor inside document text",
    "Footnote inserted",
    "Add headings before creating a table of contents",
    "Table of contents updated",
    "Place the cursor in a paragraph",
    "Paragraph style applied",
    "Place the cursor in a cell with a cell to its right",
    "Cells merged",
    "Place the cursor inside a table",
    "A table must keep at least one row",
    "Row deleted",
    "A table must keep at least one column",
    "Column deleted",
    "TOC update failed",
    "New document created",
    "Page {current} of {total}",
    "word",
    "words",
    "character",
    "characters",
    "selected",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def locale_keys(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    marker = "translations:Object.freeze({"
    assert marker in text, path
    body = text.split(marker, 1)[1].rsplit("})", 2)[0]
    return {key.replace("\\'", "'") for key, _ in re.findall(r"'((?:\\'|[^'])*)':'((?:\\'|[^'])*)'", body)}


def main() -> None:
    version = json.loads(read("VERSION.json"))["version"]
    assert version == "2.4.2", f"expected 2.4.2 candidate, got {version}"

    runtime = read("shared/localization/ui-localization.js")
    assert "[data-inkdos-i18n-root]" in runtime
    assert "function t(" in runtime
    assert "interpolate" in runtime

    for path in HELP_FILES:
        source = read(path)
        assert "data-inkdos-i18n-root" in source, f"{path} is not an explicit translation root"

    d2 = read("apps/documents/ui/d2-tools.js")
    assert "data-inkdos-i18n-root" in d2
    assert "InkDOSLocalization" in d2
    if re.search(r"chrome\.status\(\s*['\"]", d2):
        raise AssertionError("Documents dynamic status text still bypasses localization")

    start = read("apps/documents/index.html")
    app = read("apps/documents/app.js")
    surface = read("apps/documents/view/page-surface.js")
    assert "Create a document or open a DOCX, RTF, or legacy DOC file locally." in start
    assert "startCopy.textContent" not in app, "boot must not overwrite translated start copy"
    assert "Page {current} of {total}" in surface
    assert "InkDOSLocalization" in surface

    locale_files = sorted(LOCALE_DIR.glob("*.js"))
    assert locale_files
    keysets = {path.name: locale_keys(path) for path in locale_files}
    reference = next(iter(keysets.values()))
    for name, keys in keysets.items():
        assert keys == reference, f"locale key mismatch: {name}"
        missing = REQUIRED_DOCUMENTS_KEYS - keys
        assert not missing, f"{name} missing Documents translations: {sorted(missing)}"

    pt = read("shared/localization/locales/pt-BR.js")
    for translated in (
        "Documentos",
        "Ajuda de Documentos",
        "Ferramentas do documento",
        "Revisão",
        "Verificação ortográfica do navegador",
        "Comentários",
        "Notas de rodapé",
        "Sumário",
        "Estilos de parágrafo",
        "Ferramentas de tabela",
    ):
        assert translated in pt, f"Portuguese visible coverage missing: {translated}"

    print("InkDOS 2.4.2 localization completeness contract: OK")


if __name__ == "__main__":
    main()
