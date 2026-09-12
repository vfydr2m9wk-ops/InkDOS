# Security

InkDOS processes supported files locally in the browser. Do not attach confidential files to public bug reports.

## Public QA privacy

Do not attach real user documents, screenshots, recordings, or private source material to public Issues or Pull Requests.

All repository fixtures and public reproduction material must be synthetic and privacy-safe. Never publish personal, medical, or educational data from a user's source files, and do not publish original private filenames or identifying document metadata.

Private QA material must not be committed to the repository or copied into release assets, GitHub Actions artifacts, workflow logs, Issues, or Pull Requests. Reproduce defects with synthetic fixtures that preserve only the minimum technical structure needed to exercise the bug.

If a report cannot be reproduced without confidential material, keep that material outside the public repository and reduce the report to an anonymized technical description before publication.

## Update trust boundary

Update packages cannot create, modify or delete `.github/workflows/`. Full-snapshot updates are validated in a disposable candidate before the checkout is changed.
