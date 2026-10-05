"""PDF OCR (web edition): the OCR engine is integrity-checked offline but never precached.

Every file under apps/pdf/vendor/tesseract must be listed in the service worker's ON_DEMAND list
(hashed, cached on first use) and none in APP_SHELL (downloaded at install by every visitor); the
two small OCR scripts belong to APP_SHELL like the other page tools; the desktop app does not ship
the engine and the action is hidden there.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def listed(name: str) -> list[str]:
    return json.loads(re.search(r"const " + name + r"=(\[.*?\]);", SW, re.S)[1])


def test_ocr_engine_is_on_demand_only():
    engine = sorted("./" + p.relative_to(ROOT).as_posix() for p in (ROOT / "apps/pdf/vendor/tesseract").rglob("*") if p.is_file() and p.suffix != ".txt")
    assert engine and sorted(listed("ON_DEMAND")) == engine
    shell = listed("APP_SHELL")
    assert not any("/vendor/tesseract/" in p for p in shell)
    assert "./apps/pdf/features/ocr/ocr-engine.js" in shell and "./apps/pdf/features/page-tools/actions/ocr-document.js" in shell
    for path in engine:
        assert f'"{path}":' in SW, f"{path} has no offline hash"
    # installation precaches APP_SHELL only
    install = SW[SW.index("addEventListener('install'"):SW.index("addEventListener('activate'")]
    assert "APP_SHELL" in install and "ON_DEMAND" not in install


def test_desktop_does_not_ship_or_offer_ocr():
    stage = (ROOT / "desktop/scripts/stage_web.py").read_text(encoding="utf-8")
    assert '"apps/pdf/vendor/tesseract"' in stage and "const ON_DEMAND=[];" in stage
    action = (ROOT / "apps/pdf/features/page-tools/actions/ocr-document.js").read_text(encoding="utf-8")
    assert "available=()=>!global.InkDOSDesktop" in action


if __name__ == "__main__":
    test_ocr_engine_is_on_demand_only()
    test_desktop_does_not_ship_or_offer_ocr()
    print("PDF OCR offline/desktop contract: OK")
