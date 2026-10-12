# InkDOS desktop (Tauri v2)

This directory contains the InkDOS desktop host. **It is not published at present**: no installer, updater or
GitHub release is produced (see `SUPPORT.md`). The code stays in the repository, validated by CI, so desktop
releases can resume later. The browser/PWA source remains at the repository root and is not rewritten for desktop
distribution.

## Architecture

`desktop/scripts/stage_web.py` copies the runtime web assets to the ignored `desktop/web-dist/` directory and injects `desktop-host.js` into the staged HTML only. The bridge uses Tauri native dialogs and scoped filesystem access while the existing InkDOS editors, parsers, writers and UI remain unchanged JavaScript.

## Local build

Prerequisites are Rust (the release workflow pins 1.98.1), the Tauri v2 CLI (2.11.4), and the platform prerequisites documented by Tauri.

```sh
python desktop/scripts/stage_web.py
cd desktop/src-tauri
cargo tauri icon ../../assets/icons/office.png
cargo tauri build --bundles nsis
```

To validate staging without changing `web-dist`:

```sh
python desktop/scripts/stage_web.py --check
```

## CI and releases

`.github/workflows/desktop-tauri.yml` runs the desktop contracts and the staging check on pushes to `main`; it builds
no native package. Native builds belong only to `.github/workflows/release.yml`, which builds the Windows NSIS
installer and its signed updater artifacts from an immutable `vX.Y.Z` tag (see `docs/UPDATE_MODEL.md`). macOS and
Linux desktop builds were discontinued after 2.7.8; their launcher files and contracts are kept for a possible return.

Bundle files are produced under `desktop/src-tauri/target/release/bundle/` and are never committed to Git.

## Signing

Updater artifacts are signed with the Tauri signing key kept in GitHub Actions secrets. Windows Authenticode signing is not configured.
