from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pdfjs_eval_and_scripting_are_explicitly_disabled():
    source = (ROOT / "apps/pdf/io/file-open-controller.js").read_text(encoding="utf-8")
    assert "isEvalSupported:false" in source or "isEvalSupported: false" in source
    assert "isEvalSupported:true" not in source
    assert "isEvalSupported: true" not in source
    assert "enableScripting:false" in source or "enableScripting: false" in source
    assert "enableScripting:true" not in source
    assert "enableScripting: true" not in source


def test_pdfjs_vendor_provenance_is_declared():
    provenance = (ROOT / "apps/pdf/vendor/pdfjs/VENDOR-PROVENANCE.txt").read_text(encoding="utf-8")
    assert "Upstream project: Mozilla PDF.js" in provenance
    assert "Vendored display/runtime version:" in provenance


def test_every_pdfjs_open_disables_eval():
    import re
    for path in [*ROOT.glob("apps/**/*.js"), *ROOT.glob("labs/**/*.js")]:
        if "vendor" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        for call in re.findall(r"getDocument\(\{[^}]*\}", source):
            assert re.search(r"isEvalSupported\s*:\s*false", call), (path, call)


def test_vendored_scripts_match_inventory():
    import hashlib
    import json
    inventory = json.loads((ROOT / "config/vendor-inventory.json").read_text(encoding="utf-8"))
    listed = {f["path"]: f["sha256"] for f in inventory["files"]}
    shipped = sorted(p.relative_to(ROOT).as_posix() for pattern in ("apps/*/vendor/**/*.js", "apps/*/vendor/**/*.mjs", "apps/*/vendor/**/*.wasm", "labs/*/vendor/**/*.js") for p in ROOT.glob(pattern))
    assert sorted(listed) == shipped, "update config/vendor-inventory.json when adding or removing vendored code"
    for rel, digest in listed.items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, f"{rel} changed: record the new version in config/vendor-inventory.json"


if __name__ == "__main__":
    for _name, _test in list(globals().items()):
        if _name.startswith("test_") and callable(_test):
            _test()
    print("PDF.js eval guard and vendored-code inventory: OK")
