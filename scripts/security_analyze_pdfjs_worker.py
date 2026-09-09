#!/usr/bin/env python3
"""Identify the exact InkDOS delta against upstream PDF.js 3.11.174.

Read-only security migration diagnostic. The upstream npm tarball is accepted
only after its published SHA-512 SRI has been verified.
"""
from __future__ import annotations

import base64
import hashlib
import io
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "apps/pdf/vendor/pdfjs/pdf.worker.min.js"
URL = "https://registry.npmjs.org/pdfjs-dist/-/pdfjs-dist-3.11.174.tgz"
EXPECTED_SRI = "TdTZPf1trZ8/UFu5Cx/GXB7GZM30LT+wWUNfsi6Bq8ePLnb+woNKtDymI2mxZYBpMbonNFqKmiz684DIfnd8dA=="
MEMBER = "package/build/pdf.worker.min.js"


def fetch() -> bytes:
    with urllib.request.urlopen(URL, timeout=60) as response:
        data = response.read()
    actual = base64.b64encode(hashlib.sha512(data).digest()).decode("ascii")
    if actual != EXPECTED_SRI:
        raise SystemExit(f"npm SRI mismatch: expected {EXPECTED_SRI}, got {actual}")
    return data


def extract(tgz: bytes) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(tgz), mode="r:gz") as archive:
        member = archive.getmember(MEMBER)
        fh = archive.extractfile(member)
        if fh is None:
            raise SystemExit(f"missing {MEMBER}")
        return fh.read()


def common_prefix(a: bytes, b: bytes) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def common_suffix(a: bytes, b: bytes, prefix: int) -> int:
    max_n = min(len(a), len(b)) - prefix
    i = 0
    while i < max_n and a[len(a) - 1 - i] == b[len(b) - 1 - i]:
        i += 1
    return i


def printable(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").replace("\n", "\\n")


def main() -> None:
    current = CURRENT.read_bytes()
    upstream = extract(fetch())
    prefix = common_prefix(current, upstream)
    suffix = common_suffix(current, upstream, prefix)
    cur_end = len(current) - suffix if suffix else len(current)
    up_end = len(upstream) - suffix if suffix else len(upstream)
    before = 700
    after = 700
    print(f"current_bytes={len(current)}")
    print(f"upstream_bytes={len(upstream)}")
    print(f"current_sha256={hashlib.sha256(current).hexdigest()}")
    print(f"upstream_sha256={hashlib.sha256(upstream).hexdigest()}")
    print(f"common_prefix={prefix}")
    print(f"common_suffix={suffix}")
    print(f"current_changed_bytes={cur_end-prefix}")
    print(f"upstream_changed_bytes={up_end-prefix}")
    print("--- upstream context ---")
    print(printable(upstream[max(0, prefix-before):min(len(upstream), up_end+after)]))
    print("--- InkDOS context ---")
    print(printable(current[max(0, prefix-before):min(len(current), cur_end+after)]))


if __name__ == "__main__":
    main()
