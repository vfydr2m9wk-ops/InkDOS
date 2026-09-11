#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2.1.0"
DATE = "2026-09-11"
APPS = ("documents", "spreadsheets", "presentations", "txt", "epub", "pdf")


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise SystemExit(message)


version = load("VERSION.json")
require(version.get("version") == VERSION, "VERSION.json must identify InkDOS 2.1.0")
require(version.get("releaseName") == f"InkDOS {VERSION}", "VERSION.json releaseName mismatch")
require(version.get("date") == DATE, "VERSION.json release date mismatch")
require(version.get("releaseChannel") == "stable", "InkDOS 2.1.0 must remain on the stable channel")
require(version.get("components", {}).get("documents", {}).get("format") == "DOC / DOCX / RTF", "Documents format scope must include DOC, DOCX and RTF")

build = load("BUILD_INFO.json")
source = load("SOURCE_MANIFEST.json")
release = load("RELEASE_MANIFEST.json")
for name, data, key in (
    ("BUILD_INFO.json", build, "version"),
    ("SOURCE_MANIFEST.json", source, "version"),
    ("RELEASE_MANIFEST.json", release, "version"),
):
    require(data.get(key) == VERSION, f"{name} must identify InkDOS {VERSION}")
require(build.get("buildDate") == DATE, "BUILD_INFO.json buildDate mismatch")
require(source.get("generatedAt") == DATE, "SOURCE_MANIFEST.json generatedAt mismatch")
require(release.get("releaseDate") == DATE, "RELEASE_MANIFEST.json releaseDate mismatch")

home = (ROOT / "index.html").read_text(encoding="utf-8")
require(f"InkDOS {VERSION}" in home, "Home footer must show InkDOS 2.1.0")
for app in APPS:
    require(f"./apps/{app}/index.html?v={VERSION}&amp;suite=1" in home, f"Home route is not versioned for 2.1.0: {app}")
for text in (
    "Edit DOCX files locally; import RTF and legacy DOC into editable DOCX copies.",
    "Edit XLSX files locally; import legacy XLS workbooks into editable XLSX copies.",
    "Edit PPTX files locally; import legacy PPT presentations into editable PPTX copies.",
    "Read, annotate and export PDF copies locally.",
    "Create and edit plain-text files locally.",
    "Read local EPUB books with navigation, themes and annotations.",
):
    require(text in home, f"Home capability copy missing: {text}")

service_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
require("inkdos-v2.1.0-" in service_worker, "Service-worker cache must rotate to InkDOS 2.1.0")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
status = (ROOT / "docs/PROJECT_STATUS.md").read_text(encoding="utf-8")
limitations = (ROOT / "docs/KNOWN_LIMITATIONS.md").read_text(encoding="utf-8")
changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
require(readme.startswith("# InkDOS 2.1.0\n"), "README must describe InkDOS 2.1.0")
require("real-device acceptance" in readme.lower(), "README must distinguish automated validation from real-device acceptance")
require("Release: **InkDOS 2.1.0**" in status, "Project status release identity mismatch")
require("real-device acceptance" in status.lower(), "Project status must identify the current acceptance stage")
require("browser rendering matrix were not completed" not in limitations, "Known limitations contains a stale browser-matrix statement")
require("## 2.1.0 — 2026-09-11" in changelog, "CHANGELOG must contain the 2.1.0 release entry")

print("InkDOS 2.1.0 release identity and documentation contract passed.")
