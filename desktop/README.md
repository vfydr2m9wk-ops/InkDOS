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

## Release artifacts

The single production pipeline is `.github/workflows/release.yml`, triggered only by a version tag (`v*.*.*`). It validates the tagged candidate, builds on native GitHub-hosted runners, signs Tauri updater artifacts, and publishes only artifacts produced by that same workflow run:

- `InkDOS-Windows`: NSIS setup `.exe` plus updater signature.
- `InkDOS-macOS`: `.dmg` plus `.app.tar.gz` updater bundle and signature.
- `InkDOS-Linux`: `.AppImage` plus updater signature.

The bundle files are produced under `desktop/src-tauri/target/release/bundle/`, uploaded as workflow artifacts, and are intentionally not committed to Git.

## Signing

Release builds require the configured Tauri updater signing key/password and updater public key. The release workflow performs a signing preflight before native builds and publishes only after validation and artifact-provenance checks succeed.
