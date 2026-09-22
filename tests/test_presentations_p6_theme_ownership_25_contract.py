from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_p6_theme_ownership_resolver_is_package_scoped():
    s=(ROOT/'apps/presentations/io/ppt-p2-package.js').read_text()
    assert 'async function resolveThemeOwnership(bytes,slideParts)' in s
    assert "relatedPart(zip,slidePart,'/slideLayout')" in s
    assert "relatedPart(zip,layout,'/slideMaster')" in s
    assert "relatedPart(zip,master,'/theme')" in s
    assert 'singleTheme:themeParts.length===1' in s
    assert 'readThemeMetadata,resolveThemeOwnership' in s
    assert 'applySlideTransitions' in s
