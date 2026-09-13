#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "txt"

SUPPORTED = [
    ".txt", ".xml", ".md", ".markdown", ".json", ".jsonl", ".ndjson",
    ".yaml", ".yml", ".log", ".ini", ".cfg", ".conf", ".toml", ".properties",
]


def require(text: str, needle: str, message: str) -> None:
    if needle not in text:
        raise SystemExit(message)


def main() -> None:
    policy = (APP / "txt-policy.js").read_text(encoding="utf-8")
    controller = (APP / "io" / "txt-file-controller.js").read_text(encoding="utf-8")
    editor = (APP / "editor" / "editor-controller.js").read_text(encoding="utf-8")
    template = (APP / "page.template.html").read_text(encoding="utf-8")

    # Exercise the shared policy as JavaScript rather than merely matching a regex.
    node_script = r'''
const fs = require('fs');
const vm = require('vm');
globalThis.InkDOS2 = {};
vm.runInThisContext(fs.readFileSync(process.argv[1], 'utf8'));
const P = globalThis.InkDOS2.TxtPolicy;
const supported = JSON.parse(process.argv[2]);
for (const ext of supported) {
  if (!P.isSupportedName('sample' + ext)) {
    throw new Error('expected supported Plain Text extension: ' + ext);
  }
}
for (const name of ['sample.docx', 'sample.xlsx', 'sample.pptx', 'sample.pdf', 'sample.epub', 'sample.bin']) {
  if (P.isSupportedName(name)) throw new Error('unexpected Plain Text support: ' + name);
}
if (!P.isXmlName('sample.XML')) throw new Error('XML safeguard detection regressed');
'''
    import json
    subprocess.run(
        ["node", "-e", node_script, str(APP / "txt-policy.js"), json.dumps(SUPPORTED)],
        cwd=ROOT,
        check=True,
    )

    require(controller, "P.isSupportedName(file.name", "Plain Text open path must enforce the shared format allowlist")
    require(controller, "Unsupported file format", "Plain Text must reject unsupported files explicitly")
    require(editor, "P.isSupportedName(n)?n:n+'.txt'", "Plain Text rename/save path must preserve approved original extensions")

    accept = ",".join(SUPPORTED)
    require(template, f'accept="{accept}"', "Plain Text file picker must expose exactly the approved extension allowlist")

    print("Plain Text 2.3 format expansion contract passed")


if __name__ == "__main__":
    main()
