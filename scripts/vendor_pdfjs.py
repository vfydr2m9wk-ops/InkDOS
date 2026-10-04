#!/usr/bin/env python3
"""Vendor PDF.js (pdfjs-dist legacy build) into apps/pdf/vendor/pdfjs with the InkDOS worker patch.

Input is the npm tarball downloaded by a maintainer (no network access here):
  npm pack pdfjs-dist@6.4.299
The tarball must match the pinned npm integrity. The worker patch is applied at anchored, unique
locations and fails loudly if the upstream code differs; nothing else in PDF.js is modified.

Worker patch (InkDOS review annotations): AnnotationFactory.saveNewAnnotations also writes the
InkDOS records stored by apps/pdf/extensions/review-annotations.js (annotation types 1109
Highlight, 1110 Underline, 1101 Text) as plain PDF markup annotations, so PDFDocumentProxy
.saveDocument() keeps them in the incremental update.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "apps" / "pdf" / "vendor" / "pdfjs"
VERSION = "6.4.299"
INTEGRITY = "sha512-AVl138zALtfaAPvADulE0PZThbYzCBS79nL4pOSL/6Sm/4AH5A21BD9VHt97OlCuzJuCpmeZtAtkinisF4Vb1g=="

FILES = {
    "package/legacy/build/pdf.min.mjs": "pdf.min.mjs",
    "package/legacy/build/pdf.worker.min.mjs": "pdf.worker.min.mjs",
    "package/LICENSE": "LICENSE-PDFJS.txt",
    # image decoders (JPEG 2000, JBIG2) and ICC color: WebAssembly with pure-JS fallbacks
    "package/wasm/openjpeg.wasm": "wasm/openjpeg.wasm",
    "package/wasm/openjpeg_nowasm_fallback.js": "wasm/openjpeg_nowasm_fallback.js",
    "package/wasm/jbig2.wasm": "wasm/jbig2.wasm",
    "package/wasm/jbig2_nowasm_fallback.js": "wasm/jbig2_nowasm_fallback.js",
    "package/wasm/qcms_bg.wasm": "wasm/qcms_bg.wasm",
    "package/wasm/LICENSE_OPENJPEG": "wasm/LICENSE_OPENJPEG",
    "package/wasm/LICENSE_PDFJS_OPENJPEG": "wasm/LICENSE_PDFJS_OPENJPEG",
    "package/wasm/LICENSE_JBIG2": "wasm/LICENSE_JBIG2",
    "package/wasm/LICENSE_PDFJS_JBIG2": "wasm/LICENSE_PDFJS_JBIG2",
    "package/wasm/LICENSE_QCMS": "wasm/LICENSE_QCMS",
    "package/wasm/LICENSE_PDFJS_QCMS": "wasm/LICENSE_PDFJS_QCMS",
}

SAVE_ANCHOR = (
    'static async saveNewAnnotations(e,t,n,a,r,s){let i;const o=[],{isOffscreenCanvasSupported:l}=e.options;'
    'for(const f of a)if(!f.deleted)switch(f.annotationType){case Sn:'
)
SAVE_PATCH = (
    'static async saveNewAnnotations(e,t,n,a,r,s){let i;const o=[],{isOffscreenCanvasSupported:l}=e.options;'
    # InkDOS: markup annotation dictionary for a review record; returns {ref} like createNewAnnotation
    'const inkdosMarkup=(f,k)=>{const r=f.ref||=t.getNewTemporaryRef(),d=new Dict(t);'
    'd.setIfName("Type","Annot");d.setIfName("Subtype",k);d.set("CreationDate",`D:${getModificationDate()}`);'
    'd.set("Rect",f.rect);d.set("F",4);f.color&&d.set("C",Array.from(f.color,(e=>e/255)));'
    'Number.isFinite(f.opacity)&&d.set("CA",f.opacity);f.quadPoints&&d.set("QuadPoints",f.quadPoints);'
    'f.contents&&d.set("Contents",stringToAsciiOrUTF16BE(f.contents));f.title&&d.set("T",stringToAsciiOrUTF16BE(f.title));'
    'f.name&&d.setIfName("Name",f.name);f.nm&&d.set("NM",stringToAsciiOrUTF16BE(f.nm));s.put(r,{data:d});return{ref:r}};'
    'for(const f of a)if(!f.deleted)switch(f.annotationType){'
    'case 1109:o.push(inkdosMarkup(f,"Highlight"));break;case 1110:o.push(inkdosMarkup(f,"Underline"));break;'
    'case 1101:o.push(inkdosMarkup(f,"Text"));break;case Sn:'
)
# the helpers the patch relies on must exist under these names in the minified worker
REQUIRED = ("class Dict", "function getModificationDate(", "function stringToAsciiOrUTF16BE(", "getNewTemporaryRef()")
BANNER = "/* InkDOS-patched PDF.js worker: see scripts/vendor_pdfjs.py and VENDOR-PROVENANCE.txt */\n"


def patch_worker(text: str) -> str:
    if text.count(SAVE_ANCHOR) != 1:
        raise SystemExit("worker patch anchor not found exactly once; review the patch for this PDF.js version")
    for name in REQUIRED:
        if name not in text:
            raise SystemExit(f"worker helper missing: {name}")
    return BANNER + text.replace(SAVE_ANCHOR, SAVE_PATCH, 1)


def outputs(tgz: bytes) -> dict[str, bytes]:
    digest = "sha512-" + base64.b64encode(hashlib.sha512(tgz).digest()).decode()
    if digest != INTEGRITY:
        raise SystemExit(f"pdfjs-dist tarball does not match the pinned npm integrity for {VERSION}")
    out: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(tgz), mode="r:gz") as archive:
        for member, target in FILES.items():
            data = archive.extractfile(member).read()
            if target == "pdf.worker.min.mjs":
                data = patch_worker(data.decode("utf-8")).encode("utf-8")
            out[target] = data
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tarball", type=Path, help=f"pdfjs-dist-{VERSION}.tgz from npm pack")
    parser.add_argument("--check", action="store_true", help="fail if the vendored files differ")
    args = parser.parse_args()
    files = outputs(args.tarball.read_bytes())
    if args.check:
        stale = [name for name, data in files.items() if not (DEST / name).is_file() or (DEST / name).read_bytes() != data]
        if stale:
            raise SystemExit(f"vendored PDF.js differs: {stale}")
        print(f"vendored PDF.js {VERSION} matches the pinned tarball and patch")
        return 0
    for name, data in files.items():
        path = DEST / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for name, data in sorted(files.items()):
        print(f"{hashlib.sha256(data).hexdigest()}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
