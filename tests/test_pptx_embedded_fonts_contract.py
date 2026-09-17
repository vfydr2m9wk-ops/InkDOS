from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "apps/presentations/io/pptx-text-columns.js"


def test_pptx_embedded_fonts_are_loaded_locally_from_eot_payloads():
    source = MODULE.read_text(encoding="utf-8")

    # Keep this inside the existing local PPTX fidelity module: no backend,
    # external font CDN, or new dependency is introduced.
    for needle in [
        "embeddedFontLst",
        "ppt/presentation.xml",
        "ppt/_rels/presentation.xml.rels",
        "FontFace",
        "document.fonts.add",
        "extractSfntFromEot",
        "fontSize=view.getUint32(4,true)",
        "const start=eotSize-fontSize",
        "session.sourceBytes!==candidate",
        "MAX_TOTAL_FONT_BYTES",
    ]:
        assert needle in source, f"embedded-font fidelity contract missing: {needle}"

    # Font registrations are session-scoped and removed when the source
    # presentation changes or the installer is disposed.
    assert "document.fonts.delete(face)" in source
    assert "clearFonts()" in source

    # Embedded font resolution must remain package-local/offline and must not
    # grow a network fallback that could leak document typography metadata.
    assert "http://" not in source
    assert "https://" not in source

    subprocess.run(["node", "--check", str(MODULE)], check=True)


if __name__ == "__main__":
    test_pptx_embedded_fonts_are_loaded_locally_from_eot_payloads()
