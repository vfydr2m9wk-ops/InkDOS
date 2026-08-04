# Release Checklist

- [ ] Version metadata is consistent across `VERSION.json`, `RELEASE_MANIFEST.json`, `app-manifest.json`, `package.json`, runtime labels, and service-worker cache.
- [ ] README, changelog, release notes, security, compatibility, testing, architecture, known limitations, upgrade notes, and manual matrix are current.
- [ ] `python3 scripts/verify_checksums.py` passes.
- [ ] `python3 scripts/validate_repository.py` passes.
- [ ] `python3 scripts/audit_source.py` passes with no unreviewed dynamic-code path.
- [ ] Unit/package tests pass.
- [ ] Browser regressions pass in each actually available Playwright engine; unavailable engines remain “Not tested.”
- [ ] DOCX/XLSX/PPTX open-edit-export-reopen tests verify edits, package inventory, and no unexpected network.
- [ ] Dirty/unverified/failure/blocked-download/beforeunload/fingerprint states pass in all workspaces.
- [ ] Service-worker cache inventory and update behavior are checked.
- [ ] `scripts/build_release.py` produces byte-identical archives for the same commit/tag.
- [ ] Runtime ZIP excludes development artifacts and includes licenses/notices, release docs, build info, and runtime checksums.
- [ ] ZIP SHA-256, exact tag, and commit are recorded.
- [ ] GitHub source archive is used as the source artifact; no manually generated source ZIP is committed.
- [ ] Native/manual device results are recorded as Passed, Failed, Partially passed, or Not tested.
- [ ] Release remains prerelease/beta and does not claim 1.0.
