# Desktop update model

InkDOS desktop updates use the signed Tauri updater for Windows, macOS and Linux.

## Version authority

`VERSION.json` is the product version authority. Desktop configuration is checked against it by `desktop/scripts/release_version.py`.

A public desktop release uses a matching immutable tag such as `v2.4.0`.

## Build and publication path

1. `.github/workflows/promote-release-tag.yml` creates or verifies the intended release tag and dispatches the unified release workflow.
2. `.github/workflows/release.yml` validates the tagged source without write credentials.
3. Native runners build Windows, macOS and Linux installers/updater artifacts.
4. Tauri updater artifacts are signed with the configured signing key.
5. Build provenance is recorded and verified before publication.
6. `desktop/scripts/build_updater_manifest.py` creates `latest.json`.
7. The verified release assets and `latest.json` are published to the matching GitHub Release.

The installed application checks:

`https://github.com/vfydr2m9wk-ops/InkDOS/releases/latest/download/latest.json`

The updater public key is embedded through the release configuration; private signing material remains in GitHub Actions secrets and is not stored in the repository.

## User action

Update checking is explicit. Finding an update does not itself install it. Installation is a separate user action and can be cancelled.

## Retired repository updater

The former repository `InkDOS-update-v*.zip` transaction mechanism is not part of the maintained desktop update path. Its workflow, ledger, trust-boundary tests and source-snapshot metadata have been removed from `main`.
