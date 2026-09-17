# Desktop update model

InkDOS desktop updates use the signed Tauri updater for Windows, macOS and Linux.

## Version authority

`VERSION.json` is the product version authority. Desktop configuration is checked against it by `desktop/scripts/release_version.py`.

A public desktop release uses a matching immutable tag such as `v2.4.0`.

## Build and publication path

1. An immutable `vX.Y.Z` tag is pushed for a commit already contained in `main`.
2. `.github/workflows/release.yml` validates the tagged source without write credentials.
3. Native runners build the supported packages: NSIS/EXE on Windows, DMG on macOS and AppImage on Linux, plus the signed Tauri updater artifacts required by each platform.
4. The release workflow records provenance for the tagged commit and artifacts produced by that same workflow run.
5. Tauri updater artifacts are signed with the configured signing key.
6. `desktop/scripts/build_updater_manifest.py` creates `latest.json`.
7. The verified release assets and `latest.json` are uploaded to a draft GitHub Release and checked before that release is made public.

There is no separate release-promotion workflow, promotion-state file, manual release dispatch or cross-run artifact-reuse path. `.github/workflows/desktop-tauri.yml` performs desktop contract/staging validation only; native release builds are owned exclusively by `.github/workflows/release.yml`.

The installed application checks:

`https://github.com/vfydr2m9wk-ops/InkDOS/releases/latest/download/latest.json`

The updater public key is embedded through the release configuration; private signing material remains in GitHub Actions secrets and is not stored in the repository.

## Reproducible release toolchain

Release CI pins the Rust toolchain to 1.98.1 and the Tauri CLI to 2.11.4, matching the last verified successful native build used to establish this baseline. Direct Tauri/Rust dependencies in `desktop/src-tauri/Cargo.toml` are pinned to the versions resolved by that build.

## User action

Update checking is explicit. Finding an update does not itself install it. Installation is a separate user action and can be cancelled.

## Retired repository updater

The former repository `InkDOS-update-v*.zip` transaction mechanism is not part of the maintained desktop update path. Its workflow, ledger, trust-boundary tests and source-snapshot metadata have been removed from `main`.
