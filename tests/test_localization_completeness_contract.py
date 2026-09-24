#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
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
    "Page",
    "Page layout",
    "Text color and effects",
    "Text formatting",
    "Text",
    "Highlight",
    "Strikethrough",
    "Subscript",
    "Superscript",
    "Paper size",
    "Letter",
    "Legal",
    "Orientation",
    "Portrait",
    "Landscape",
    "Top margin (cm)",
    "Right margin (cm)",
    "Bottom margin (cm)",
    "Left margin (cm)",
    "Header",
    "Footer",
    "Optional header text",
    "Optional footer text",
    "Show page number in footer",
    "Apply layout",
    "Insert page break",
    "Print / Export PDF",
    "Print / Export PDF opens the browser print sheet; choose Save as PDF when the host provides it.",
    "Sections and columns",
    "Columns",
    "Gap (px)",
    "Section break",
    "Section break starts the next section on a new page. Imported continuous sections are normalized to this next-page model while editing.",
    "Page {page}",
    "No headings were found.",
    "0 results",
    "{count} result",
    "{count} results",
    "{current} of {total}",
    "Replace with",
    "Replace",
    "All",
    "Settings",
    "InkDOS keeps workspace editing local-first and offline-capable. Interface language changes presentation only; file content is never translated.",
}

REQUIRED_WORKSPACE_HELP_KEYS = {
    "Spreadsheets",
    "Spreadsheets Help",
    "Use this guide for workbook basics, formulas, supported functions, and local file handling.",
    "Cells and ranges",
    "Writing formulas",
    "Supported functions",
    "Formula errors",
    "Editing tools",
    "Create a new workbook or open an XLS/XLSX file from the hamburger menu. Select a cell and type directly, or use the formula bar above the grid.",
    "Saving creates an XLSX copy; the original source file is not overwritten.",
    "A cell reference combines a column and row, such as A1. A range joins two references with a colon, such as A1:A10.",
    "Formulas can also reference another worksheet, for example Sheet2!B4. Sheet names with spaces can be quoted.",
    "Start a formula with =. Examples: =A1+B1, =A1*2, =SUM(A1:A10), and =IF(A1,10,0).",
    "Arithmetic supports +, -, *, /, %, parentheses, and cell references.",
    "SUM adds numbers. AVERAGE calculates the mean. MIN and MAX return the smallest and largest numeric values. COUNT counts numeric values. PRODUCT multiplies numeric values. IF chooses between two values based on a condition.",
    "Arguments may use commas or semicolons. Functions can accept individual cells, values, or ranges.",
    "#REF! means a reference is invalid. #DIV/0! means a calculation has no valid divisor/value set. #VALUE! means the expression could not be evaluated. #CYCLE! means cells depend on each other in a circular reference.",
    "The toolbar includes undo/redo, font controls, alignment, merge/unmerge, row and column insertion/deletion, gridline visibility, and common selection operations. The Functions menu inserts common function names into the formula workflow.",
    "Presentations",
    "Presentations Help",
    "Use this guide to create or open presentations, edit slides and objects, and export or present the result.",
    "Slides",
    "Editing objects",
    "Formatting and layout",
    "Transitions and notes",
    "Presenting",
    "Saving",
    "Create a new presentation from the hamburger menu or open a supported PowerPoint file. The slide panel shows the presentation structure and the main canvas shows the active slide.",
    "Use the slide panel and slide commands to navigate, add, duplicate, reorder, or remove slides when those commands are available for the current presentation.",
    "Select text, shapes, tables, or other supported slide objects before using the editing tools. Selection determines which formatting and structure commands are active.",
    "The editing toolbar provides supported text, object, layout, table, and presentation tools. Zoom affects the workspace view only; it does not change the saved slide size.",
    "Transition and notes tools are available for supported PowerPoint content. Use them from the presentation editing controls and verify the slide state before exporting.",
    "Use Present from start to enter slideshow mode. Navigate through the deck using the slideshow controls, then exit to return to editing.",
    "Save creates a local presentation copy containing the supported edits. Keep the exported file if you want to preserve changes outside the current browser session.",
    "PDF Workspace",
    "PDF Workspace Help",
    "Use this guide for opening PDFs, navigating pages, changing the view, reviewing content, and using page tools.",
    "Opening a PDF",
    "Pages and navigation",
    "View and reader tools",
    "Review and annotations",
    "Page tools",
    "Use Open from the hamburger menu or start screen to choose a PDF. The file is parsed and rendered locally in the browser.",
    "Use the page controls and navigation panel to move through the document. Zoom changes the workspace view without changing the PDF page dimensions.",
    "Use Reader tools when you want a reading-oriented workflow. View controls can change how pages are presented without modifying the source document.",
    "Review tools operate on the active PDF editing session. Commit or finish the current edit before switching files so the session state remains clear.",
    "Page tools include supported operations such as moving, rotating, deleting, extracting, splitting, and merging pages. These operations create an edited document state and can affect the exported PDF.",
    "Use Save when you want a local copy containing supported edits. InkDOS keeps the source file separate rather than silently overwriting it.",
    "PDF rendering and editing are performed in the local app runtime. The document does not need to be sent to a remote PDF editor for the core workflow.",
    "EPUB Reader",
    "EPUB Reader Help",
    "Use this guide to open EPUB books, navigate chapters, adjust reading appearance, and work with reading tools.",
    "Opening a book",
    "Navigation",
    "Reading modes",
    "Search, bookmarks, and highlights",
    "Saving and sharing",
    "Use Open from the hamburger menu or the start screen to choose an EPUB file. InkDOS reads the book locally in the browser.",
    "Use Previous and Next to move through the book. The progress control lets you move through the current reading flow, while the table of contents provides structured chapter navigation when the EPUB includes one.",
    "Use the page and scroll controls to choose the reading flow that is most comfortable for the current book and screen size.",
    "The appearance tools adjust the reading view, including text size and font options. These controls change the reader presentation and do not rewrite the original EPUB content.",
    "Use Search to find text when available, Bookmark to mark a reading position, and Highlight for supported text selections. The annotation indicator shows the current annotation state for the book.",
    "When editing or annotation features create a changed book state, use the available Save or Share actions to export a local copy. Keep the exported file if you want those changes outside the current browser session.",
    "Plain Text Help",
    "Use this guide to edit TXT/XML files, control the editor view, work with outlines, and save a local copy.",
    "Editing",
    "Find",
    "View controls",
    "Lists and outlines",
    "Encoding and line endings",
    "Create a new text document or open a TXT/XML file from the hamburger menu. The editor keeps the document as plain text rather than applying rich-text formatting.",
    "Type directly in the editor. Undo and redo track text changes. Select All, Copy, Paste, indentation, and list/outline controls operate on the current text selection or line.",
    "Use Find to search the current document. Previous and Next move between matches, and the status indicator shows the active match state.",
    "Wrap changes whether long lines wrap visually. The text-size controls change only the editor view; they do not add font information to the TXT/XML file.",
    "The list tool inserts plain-text outline prefixes such as dashes, bullets, or numbered patterns. Because the file remains plain text, these markers are stored as normal characters.",
    "The status bar shows the active encoding and line-ending mode. Keep these indicators in mind when working with files shared between operating systems or XML tooling.",
    "Save copy exports the current text as a local file. Share uses the available platform sharing path when supported. The source file is not silently overwritten.",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def locale_keys(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    marker = "translations:Object.freeze({"
    assert marker in text, path
    body = text.split(marker, 1)[1].rsplit("})", 2)[0]
    return {key.replace("\\'", "'") for key, _ in re.findall(r"'((?:\\'|[^'])*)':'((?:\\'|[^'])*)'", body)}


def validate_locale_syntax(locale_files: list[Path]) -> None:
    for path in locale_files:
        syntax = subprocess.run(
            ["node", "--check", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        assert syntax.returncode == 0, f"invalid locale JavaScript: {path.name}\n{syntax.stderr}"


def main() -> None:
    runtime = read("shared/localization/ui-localization.js")
    assert "[data-inkdos-i18n-root]" in runtime
    assert "function t(" in runtime
    assert "interpolate" in runtime

    for path in HELP_FILES:
        source = read(path)
        assert "data-inkdos-i18n-root" in source, f"{path} is not an explicit translation root"

    d1 = read("apps/documents/ui/d1-tools.js")
    navigation = read("apps/documents/ui/navigation-panel.js")
    assert d1.count("data-inkdos-i18n-root") >= 2
    assert "InkDOSLocalization" in navigation
    assert "Page {page}" in navigation
    assert "inkdos:language" in navigation

    spreadsheet_help = read("apps/spreadsheets/help/help.js")
    assert "<code>" not in spreadsheet_help, "Spreadsheets Help must keep translatable paragraphs intact"

    d2 = read("apps/documents/ui/d2-tools.js")
    assert "data-inkdos-i18n-root" in d2
    assert "InkDOSLocalization" in d2
    assert "data-inkdos-user-content" in d2, "comment excerpts and bodies must never be translated"
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
    validate_locale_syntax(locale_files)
    keysets = {path.name: locale_keys(path) for path in locale_files}
    reference = next(iter(keysets.values()))
    for name, keys in keysets.items():
        assert keys == reference, f"locale key mismatch: {name}"
        missing = (REQUIRED_DOCUMENTS_KEYS | REQUIRED_WORKSPACE_HELP_KEYS) - keys
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

    print("InkDOS localization completeness contract: OK")


if __name__ == "__main__":
    main()
