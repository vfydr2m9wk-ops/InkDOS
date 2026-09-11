from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_epub_container_selects_an_existing_opf_rootfile_instead_of_blindly_using_the_first_entry():
    source = (ROOT / "apps/epub/engine/book-model.js").read_text(encoding="utf-8")
    assert "function selectRootfile(cdoc,pkg)" in source
    assert "mediaType==='application/oebps-package+xml'&&pkg.has(x.path)" in source
    assert "||candidates.find(x=>pkg.has(x.path))" in source
    assert "root=selectRootfile(cdoc,pkg)" in source
    assert "rootfile=els(cdoc,'rootfile')[0]" not in source


def test_epub_container_rootfile_selection_keeps_path_validation_and_missing_package_failure():
    source = (ROOT / "apps/epub/engine/book-model.js").read_text(encoding="utf-8")
    assert "normalizeResolved(safeDecode(fullPath))" in source
    assert "if(!candidates.length)fail('package','EPUB rootfile is missing')" in source
    assert "if(!preferred)fail('package','EPUB package document is missing: '+candidates[0].path)" in source
