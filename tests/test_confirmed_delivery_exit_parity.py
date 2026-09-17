from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPUB_DELIVERY = (ROOT / "apps/epub/io/file-delivery.js").read_text()
EPUB_BINDINGS = (ROOT / "apps/epub/ui/reader-bindings.js").read_text()
DOCUMENTS_SAVE = (ROOT / "apps/documents/io/save-controller.js").read_text()
SHEETS_SAVE = (ROOT / "apps/spreadsheets/io/save-controller.js").read_text()
SHEETS_OPEN = (ROOT / "apps/spreadsheets/io/file-open-controller.js").read_text()
TXT_SAVE = (ROOT / "apps/txt/io/txt-file-controller.js").read_text()


def test_epub_replacement_save_requires_confirmed_delivery_without_clearing_dirty_early():
    assert "requireConfirmed" in EPUB_DELIVERY
    assert "confirmedDepth" in EPUB_DELIVERY
    assert "lastReceipt=Object.freeze" in EPUB_DELIVERY
    assert "requireConfirmed(()=>reader.saveCopy())" in EPUB_BINDINGS
    assert "Save delivery was not confirmed" in EPUB_BINDINGS


def test_documents_replacement_save_requires_confirmed_delivery():
    assert "receipt?.deliveryConfirmed" in DOCUMENTS_SAVE
    assert "Save delivery was not confirmed" in DOCUMENTS_SAVE


def test_spreadsheets_replacement_save_requires_confirmed_delivery():
    assert "confirmedOnly" in SHEETS_SAVE
    assert "result?.deliveryConfirmed" in SHEETS_SAVE
    assert "confirmedOnly:true" in SHEETS_OPEN
    assert "result?.deliveryConfirmed" in SHEETS_OPEN


def test_txt_replacement_save_requires_confirmed_delivery():
    assert "confirmedOnly" in TXT_SAVE
    assert "receipt?.deliveryConfirmed" in TXT_SAVE
    assert "save({confirmedOnly:true})" in TXT_SAVE
    assert "Save delivery was not confirmed" in TXT_SAVE
