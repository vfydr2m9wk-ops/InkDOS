# InkDOS desktop (Tauri v2)

This directory contains the installable InkDOS desktop host. The browser/PWA source remains at the repository root and is not rewritten for desktop distribution.

## Architecture

`desktop/scripts/stage_web.py` copies the runtime web assets to the ignored `desktop/web-dist/` directory and injects `desktop-host.js` into the staged HTML only. The bridge uses Tauri native dialogs and scoped filesystem access while the existing InkDOS editors, parsers, writers and UI remain unchanged JavaScript.

## Local build

Prerequisites are Rust stable, the Tauri v2 CLI, and the platform prerequisites documented by Tauri.

```sh
python desktop/scripts/stage_web.py
cd desktop/src-tauri
cargo tauri icon ../../assets/icons/office.png
cargo tauri build
```

To validate staging without changing `web-dist`:

```sh
python desktop/scripts/stage_web.py --check
```

## CI artifacts

Pushes to `desktop-tauri` run `.github/workflows/desktop-tauri.yml` on native GitHub-hosted runners. Successful builds upload:

- `InkDOS-Windows`: NSIS setup `.exe` and WiX `.msi` bundles.
- `InkDOS-macOS`: `.app` and `.dmg` bundles.
- `InkDOS-Linux`: `.deb`, `.AppImage` and `.rpm` bundles.

The bundle files are produced under `desktop/src-tauri/target/release/bundle/` and uploaded as workflow artifacts. They are intentionally not committed to Git.

## Signing

Branch builds are unsigned development artifacts. Windows code signing and Apple Developer ID signing/notarization require platform credentials and are intentionally outside this branch's first implementation.
