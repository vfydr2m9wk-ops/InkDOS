# Proposal: replace the GitHub runtime with InkDesk 0.19.3-beta.7

## Proposed update to `main`

**Commit title:** `Replace legacy InkDesk runtime with 0.19.3-beta.7`

### Summary

Replace the repository contents with the complete, audited InkDesk 0.19.3-beta.7 release tree instead of layering another PDF hotfix over the previous implementation.

The replacement removes the retired browser-native PDF viewer path and adopts one supported configuration:

- classic local PDF.js 3.11.174, compatible with direct `file://` startup;
- PDF.js canvas, text and AcroForm layers;
- synchronized page, thumbnail and outline navigation;
- five-page full-canvas window for long PDFs;
- page-relative InkDesk review data with explicitly separate JSON and supported PDF exports;
- determinate PPTX opening progress;
- spreadsheet drag selection and visible formula suggestions when `=` is pressed.

### Why full replacement is required

The beta.6 ZIP combined a new PDF implementation with an ES-module entry point. Edge blocks that module when the downloaded application is opened through `file://`, so the PDF button never receives its event handler and the hub transfer expires after 30 seconds. Copying only selected beta.7 files risks leaving the old `.mjs` worker, stale service-worker cache entries, native-viewer CSS, old tests or obsolete release metadata.

The update must therefore be reviewed as a complete runtime replacement, with deletions included in the diff.

## Migration procedure

1. Extract `InkDesk_v0.19.3-beta.7.zip` into a separate staging directory.
2. Verify its SHA-256 against the `.zip.sha256` sidecar before copying anything.
3. Synchronize the staged tree into `main`, preserving only `.git/` and repository administration that is intentionally retained.
4. Delete tracked files that are absent from the beta.7 `SOURCE_MANIFEST.json`; do not leave old runtime files beside their replacements.
5. Confirm these retired paths are deleted if they exist:
   - `shared/vendor/pdfjs/pdf.min.mjs`
   - `shared/vendor/pdfjs/pdf.worker.min.mjs`
   - duplicate or historical PDF.js distributions outside `shared/vendor/pdfjs/`
   - generated release directories and obsolete ZIP assets committed inside the source tree
6. Stage additions, modifications and deletions together with `git add -A` and review the complete deletion list before committing.
7. Commit and push the complete replacement to `main` as one coherent update; do not publish beta.7 as a sequence of partial pushes that temporarily mixes old and new PDF runtimes.

## Simple `main` workflow

`.github/workflows/main.yml` runs on every push to `main` and can also be started manually. It:

- rejects `object`, `embed`, PDF iframe, `#page=` fragment navigation, `.mjs` PDF assets and retired native-viewer identifiers;
- verifies that only the approved classic PDF.js files exist;
- runs repository unit tests, structural validation and the privacy audit;
- regenerates release metadata;
- builds the release ZIP and SHA-256 sidecar;
- publishes both files as the `InkDesk-v0.19.3-beta.7` workflow artifact.

Local equivalent:

```text
python scripts/check_no_legacy_runtime.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_release_metadata.py
python scripts/validate_repository.py
python scripts/audit_source.py
python scripts/build_release.py --output-dir dist
```

## Manual acceptance before publishing

- Open the extracted package by double-clicking `index.html` in Edge/Chromium.
- Open a PDF from the hub and from the PDF workspace button; neither path may show a transfer timeout.
- Confirm selectable text, at least one form fixture and an outline fixture.
- Open the synthetic 4,000-page PDF and jump to page 3,500; full page canvases must remain at five or fewer.
- Open a large PPTX and confirm visible byte/stage/slide progress.
- Select a spreadsheet cell, press `=`, confirm suggestions appear, and insert one using arrows plus Enter.
- Repeat the device checklist on Safari/iPadOS before promoting the beta to a stable release.

## Update and release policy

- Push the complete replacement to `main`; do not force-push over repository history.
- Preserve the prior release tags and assets as historical records, but remove obsolete runtime files from the default branch.
- Confirm that the `Build InkDesk main` workflow succeeds before creating the release tag.
- Create pre-release tag `v0.19.3-beta.7` from the tested commit and attach only the ZIP and matching checksum produced by the successful workflow.
- Promote to stable only after physical Safari/iPadOS validation is recorded.
