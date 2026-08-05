# InkDesk 0.19.2-beta — Release Packaging and Privacy Cleanup

## Purpose

This beta packages the hardened 0.19.1 codebase as a self-consistent source replacement and removes avoidable identifying metadata from synthetic compatibility fixtures. It does not claim version 1.0 readiness.

## Packaging and release workflow

- Added a manual full-replacement workflow that does not compare or merge against prior repository files.
- The workflow safely extracts the selected ZIP, deletes the existing worktree except `.git`, copies the candidate tree in full, commits it, force-updates `main`, force-moves `v0.19.2-beta`, builds the deterministic runtime archive, and replaces release assets.
- Removed the previous multi-stage synchronization logic and backup-branch behavior.
- Included `SOURCE_PACKAGE_INFO.json` in `CHECKSUMS.sha256`, fixing the source package's self-verification failure.

## Privacy cleanup

- Removed default personal-name metadata embedded by document-generation tooling from DOCX/PPTX and converted legacy fixture files.
- Confirmed that the source archive contains no `.git` directory, OS metadata, editor state, private keys, access tokens, real email addresses, CPF/CNPJ values, phone numbers, absolute user paths, ZIP comments, or EXIF identity fields.
- The public GitHub handle `vfydr2m9wk-ops` remains in repository URLs and `CODEOWNERS`; it identifies the publishing account but contains no real-world identity in this package.

## Validation

- Repository validation passed.
- Source audit passed.
- 53 Python unit/package tests passed.
- 46 JavaScript security assertions passed.
- JavaScript syntax checks passed.
- Source checksum verification passed after regeneration.

## Release status

InkDesk remains a controlled public beta. Native Safari, physical iPadOS, installed-PWA behavior, Firefox/WebKit engine runs in the release environment, memory-pressure testing, and post-hardening real-corpus regression remain required before a 1.0 designation.
