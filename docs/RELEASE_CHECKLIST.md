# Release Checklist

- [ ] Version metadata, runtime labels and service-worker cache key match `VERSION.json`.
- [ ] README, changelog, release notes, compatibility, privacy, testing and upgrade notes are current.
- [ ] `python3 scripts/validate_repository.py` passes.
- [ ] `python3 scripts/audit_source.py` passes, including release-specific forbidden terms supplied on the command line.
- [ ] Unit tests and Chromium browser regressions pass.
- [ ] DOCX, XLS/XLSX, PPTX and PDF synthetic fixtures open successfully.
- [ ] Private reference documents are absent from the source tree and ZIP.
- [ ] PNG and document fixture metadata is normalized.
- [ ] The service-worker shell contains every current workspace, including PDF.
- [ ] `scripts/build_release.py` produces byte-identical archives on two consecutive builds.
- [ ] `unzip -t` and the final SHA-256 check pass.
- [ ] Unavailable native browsers/devices remain documented as **Not tested**.
- [ ] Release remains prerelease/beta and does not claim 1.0.
