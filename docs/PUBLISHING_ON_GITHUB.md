# Publishing on GitHub

## Repository source

Keep extracted source files directly on the `main` branch so visitors can inspect `apps/`, `shared/`, `tests/`, `scripts/`, and `docs/` without downloading an opaque package.

The root-level `InkDesk-source.zip` is a deliberate mobile-bootstrap exception. It is the validated source payload used by `.github/workflows/bootstrap-inkdesk.yml` to reconstruct the repository from a minimal two-file seed. Do not add generated test exports, Python bytecode, browser results, or unrelated archives to the source tree.

## Initial bootstrap from a phone or tablet

A blank repository needs only these two files:

- `InkDesk-source.zip` at the repository root.
- `.github/workflows/bootstrap-inkdesk.yml` at its exact workflow path.

Run **Bootstrap InkDesk repository** manually from the Actions tab on the `main` branch. The workflow performs guarded ZIP extraction, checksum verification, structural validation, source auditing, unit tests, JavaScript syntax checks, installation of the complete tree, a second validation pass, and a commit back to `main`.

The workflow preserves `InkDesk-source.zip` after extraction so the same validated payload can rebuild the repository again. It is manually triggered and does not run recursively after its own commit.

## Repository metadata

**Description**

> Local-first browser workspaces for focused DOCX, XLS/XLSX, PPTX and PDF workflows.

**Suggested topics**

`ooxml`, `local-first`, `offline`, `docx`, `xlsx`, `pptx`, `javascript`, `html-app`, `pwa`, `office-editor`

## GitHub Pages

The reconstructed repository includes `.github/workflows/pages.yml`. In **Settings → Pages**, select **GitHub Actions** as the source, then run **Deploy GitHub Pages** manually after the bootstrap commit.

Expected project URL:

`https://vfydr2m9wk-ops.github.io/InkDesk/`

GitHub Pages provides the HTTPS context required for service-worker registration. Verify the deployed manifest, service worker, workspace links, and offline reload in a real browser before describing the hosted build as installable.

## Quality validation

The reconstructed repository includes `.github/workflows/quality-gate.yml`. The bootstrap workflow already executes the repository checks before and after installation. Future source commits are validated by the quality gate according to its configured triggers.

## Release 0.19.3-beta.7

- Release asset: `InkDesk_v0.19.3-beta.7.zip`
- Checksum asset: `InkDesk_v0.19.3-beta.7.zip.sha256`
- Tag: `v0.19.3-beta.7`
- Release title: `InkDesk 0.19.3-beta.7 — Local-File PDF Recovery and Visible Loading`
- Keep this release marked as a pre-release until physical Safari/iPadOS validation is complete.

## Release 0.19.3-beta.6

- Release asset: `InkDesk_v0.19.3-beta.6.zip`
- Checksum asset: `InkDesk_v0.19.3-beta.6.zip.sha256`
- Tag: `v0.19.3-beta.6`
- Release title: `InkDesk 0.19.3-beta.6 — PDF WebKit Embedded Preview Recovery`
- Mark as a prerelease.
- State explicitly that physical iPadOS/WebKit rendering must be confirmed before promoting the build as a general stable release.

## Release 0.19.3-beta.3

- Source package: `InkDesk_v0.19.3-beta.3_full-source.zip`
- Tag: `v0.19.3-beta.3`
- Release title: `InkDesk 0.19.3-beta.3 — Release Packaging and Privacy Cleanup`
- Workflow: **Replace repository and publish prerelease**
- Confirmation: `REPLACE_ALL`
- Replacement model: delete the existing worktree and copy the archive contents in full; no comparison or merge with prior files.
