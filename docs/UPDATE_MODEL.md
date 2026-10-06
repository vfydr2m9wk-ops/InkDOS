# Desktop update model

InkDOS desktop updates use the signed Tauri updater for Windows. macOS and Linux desktop builds are discontinued after 2.7.8: those installs keep working but receive no further desktop updates (use the web/PWA edition).

## Version authority

`VERSION.json` is the product version authority. Desktop configuration is checked against it by `desktop/scripts/release_version.py`.

A public desktop release uses a matching immutable `vX.Y.Z` tag. The stable 2.7 line is released as `v2.7.8` (`v2.7.7`, `v2.7.6`, `v2.7.5`, `v2.7.4`, `v2.7.3`, `v2.7.2`, `v2.7.1` and `v2.7.0` preserved as earlier 2.7 stables); `v2.6.2` remains preserved as the last 2.6 beta checkpoint and `v2.6.1` as the previous stable fallback.

## Build and publication path

1. An immutable `vX.Y.Z` tag is pushed for a commit already contained in `main`.
2. `.github/workflows/release.yml` validates the tagged source without write credentials.
3. A Windows runner builds the supported package (NSIS/EXE) plus the signed Tauri updater artifacts.
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

## Beta tools channel

Beta tools (today the PDF tools from `labs/`) reach the desktop app without a desktop release.

- `.github/workflows/beta-channel.yml` runs on `main` changes to the beta tools: it tests them, builds a bundle with `scripts/build_beta_bundle.py` (contents listed in `config/beta-channel.json`), signs its manifest with the beta-channel key and publishes it as an immutable `beta-tools-<run number>` prerelease. Prereleases never become `releases/latest`, so the desktop updater is unaffected.
- The desktop app (Settings → Beta tools) checks for a newer bundle when a tool is opened. It installs one only if the manifest signature matches the public key pinned in `desktop/src-tauri/beta-channel.pub`, the version is newer than the installed one, the app is at least the manifest's `minDesktop`, and every file matches the SHA-256 the signed manifest lists. Otherwise it keeps the installed bundle.
- Beta tools open in their own `beta-*` windows through the `inkdos-beta` scheme. No capability names those windows and every InkDOS command refuses them, so beta code has no file-system, dialog, updater or other native access; external `https` links open in the system browser. When the PDF workspace opens a beta tool, the host hands that window the open PDF and takes the tool's result back through the window's own scheme (`/__inkdos/file`, `/__inkdos/result`), scoped to that window and delivered only to the window that opened it; older desktop builds simply open the tool without the PDF.
- The beta signing key is separate from the updater key. Its private key and password are the `INKDOS_BETA_SIGNING_KEY` and `INKDOS_BETA_SIGNING_KEY_PASSWORD` Actions secrets. Until they and the public key exist, the workflow publishes nothing and the desktop menu reports that beta tools are not configured.

## Retired repository updater

The former repository `InkDOS-update-v*.zip` transaction mechanism is not part of the maintained desktop update path. Its workflow, ledger, trust-boundary tests and source-snapshot metadata have been removed from `main`.
