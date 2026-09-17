#!/usr/bin/env python3
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
APPS = ("documents", "spreadsheets", "presentations", "txt", "epub", "pdf")


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise SystemExit(message)


version = load("VERSION.json")
VERSION = version.get("version")
DATE = version.get("date")
DEVELOPMENT_VERSION = version.get("developmentVersion")
require(VERSION and DATE, "VERSION.json must define the current release version and date")
require(version.get("releaseName") == f"InkDOS {VERSION}", "VERSION.json releaseName mismatch")
require(version.get("releaseChannel") == "stable", f"InkDOS {VERSION} must remain on the stable channel")
if DEVELOPMENT_VERSION is not None:
    require(re.fullmatch(r"\d+\.\d+", DEVELOPMENT_VERSION) is not None, "developmentVersion must use major.minor form")
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
require(f"InkDOS {VERSION}" in home, f"Home footer must show InkDOS {VERSION}")
for app in APPS:
    require(f"./apps/{app}/index.html?v={VERSION}&amp;suite=1" in home, f"Home route is not versioned for {VERSION}: {app}")
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
if DEVELOPMENT_VERSION:
    require(
        f"inkdos-v{DEVELOPMENT_VERSION}-dev-" in service_worker,
        f"Service-worker development cache must match InkDOS {DEVELOPMENT_VERSION} dev",
    )
else:
    require(f"inkdos-v{VERSION}-" in service_worker, f"Service-worker cache must match InkDOS {VERSION}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
status = (ROOT / "docs/PROJECT_STATUS.md").read_text(encoding="utf-8")
limitations = (ROOT / "docs/KNOWN_LIMITATIONS.md").read_text(encoding="utf-8")
changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
require(readme.startswith(f"# InkDOS {VERSION}\n"), f"README must describe InkDOS {VERSION}")
require("real-device acceptance" in readme.lower(), "README must distinguish automated validation from real-device acceptance")
require(f"Release: **InkDOS {VERSION}**" in status, "Project status release identity mismatch")
require("real-device acceptance" in status.lower(), "Project status must identify the current acceptance stage")
require("browser rendering matrix were not completed" not in limitations, "Known limitations contains a stale browser-matrix statement")
require(f"## {VERSION} — {DATE}" in changelog, f"CHANGELOG must contain the {VERSION} release entry")

print(f"InkDOS {VERSION} release identity and documentation contract passed.")
