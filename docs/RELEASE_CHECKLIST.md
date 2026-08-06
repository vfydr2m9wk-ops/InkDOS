# Release Checklist

- [ ] Update `VERSION.json`, `RELEASE_MANIFEST.json`, `app-manifest.json`, and `package.json`.
- [ ] Update README, changelog, release notes, compatibility, and validation report.
- [ ] Run checksum verification, repository validation, source audit, and all tests.
- [ ] Run browser round trips and repeat the full logical suite three times.
- [ ] Verify new/open/edit/undo/redo/rename/save/reopen in every workspace.
- [ ] Verify cross-workspace filename, history, image, toolbar, and storage isolation.
- [ ] Test offline behavior and document unavailable browser/device environments.
- [ ] Generate ZIP, internal checksums, ZIP SHA-256, extract, and verify again.
- [ ] Confirm no unsupported compatibility claim or unexplained console error remains.
