# Upgrade Notes — 0.19.2-beta

- Replace the previous repository contents with the complete `InkDesk_v0.19.2-beta_full-source.zip` source package; do not merge it with older files.
- The manual replacement workflow deletes every repository-root entry except `.git`, copies the package contents as the new source tree, commits the result, force-updates `main`, recreates the version tag, and replaces release assets.
- Upload `InkDesk_v0.19.2-beta_full-source.zip` to the repository root before running **Replace repository and publish prerelease**.
- Use `expected_version` = `0.19.2-beta`, tag = `v0.19.2-beta`, and confirmation = `REPLACE_ALL`.
- The workflow requires the `INKDESK_RELEASE_PAT` repository secret with permission to write repository contents and releases. Branch rules must allow that token to bypass or force-update `main`.
- Hosted/PWA users should reload after the new service worker activates. The cache name changes to `inkdesk-shell-v0.19.2-beta-router2`.
- No persisted user-document schema migration is required.
