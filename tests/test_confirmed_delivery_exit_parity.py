from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPUB_CONTROLS = (ROOT / "apps/epub/ui/reader-controls.js").read_text()
EPUB_BINDINGS = (ROOT / "apps/epub/ui/reader-bindings.js").read_text()
DOCUMENTS_SAVE = (ROOT / "apps/documents/io/save-controller.js").read_text()
SHEETS_SAVE = (ROOT / "apps/spreadsheets/io/save-controller.js").read_text()
SHEETS_OPEN = (ROOT / "apps/spreadsheets/io/file-open-controller.js").read_text()
TXT_SOURCE = (ROOT / "apps/txt/io/txt-file-controller.js").read_text()


def test_epub_replacement_save_requires_confirmed_delivery():
    assert "return r" in EPUB_CONTROLS
    assert "deliveryConfirmed" in EPUB_BINDINGS
    assert "Save delivery was not confirmed" in EPUB_BINDINGS


def test_documents_replacement_save_requires_confirmed_delivery():
    assert "receipt.deliveryConfirmed" in DOCUMENTS_SAVE
    assert "Save delivery was not confirmed" in DOCUMENTS_SAVE


def test_spreadsheets_replacement_save_requires_confirmed_delivery():
    assert "deliveryConfirmed" in SHEETS_SAVE
    assert "confirmedOnly" in SHEETS_SAVE
    assert "confirmedOnly:true" in SHEETS_OPEN


def test_txt_modular_source_replacement_save_requires_confirmed_delivery():
    assert "receipt.deliveryConfirmed" in TXT_SOURCE
    assert "Save delivery was not confirmed" in TXT_SOURCE
