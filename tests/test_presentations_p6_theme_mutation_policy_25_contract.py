from pathlib import Path

SRC=Path(__file__).parents[1]/"apps/presentations/io/ppt-p2-package.js"

def test_p6_theme_mutation_is_single_theme_only():
    s=SRC.read_text(encoding="utf-8")
    assert "function themeMutationPolicy(ownership)" in s
    assert "mode:'shared-single-theme'" in s
    assert "mode:'preserve-only'" in s
    assert "Multiple theme parts are preserved; theme editing is disabled" in s

def test_p6_theme_writer_mutates_owned_theme_part_only():
    s=SRC.read_text(encoding="utf-8")
    assert "async function applyThemeMutation(bytes,slideParts,patch)" in s
    assert "const ownership=await resolveThemeOwnership(bytes,slideParts)" in s
    assert "if(!policy.writable)throw new Error(policy.reason)" in s
    assert "zip.file(policy.themePart,serialize(doc)" in s
    assert "themeMutationPolicy,applyThemeMutation" in s
