# Validation report — InkDOS v0.20.0 source package

Review date: 2026-08-06

## Package-construction checks

The consolidated source tree passed:

- retired PDF runtime-token detection;
- repository validation in explicit vendor-bootstrap mode;
- source audit, including documented plans for the two inherited files above
  the preferred 1,000-line limit;
- JavaScript syntax checks for first-party scripts;
- generated module-registry consistency;
- checksum generation and verification;
- 170 Python unit and package tests in a structural validation copy.

The structural test copy used temporary, non-distributed PDF.js existence
markers solely because the artifact environment could not download the pinned
npm package. Those markers are not included in the source ZIP and do not count
as a PDF rendering test.

## Publication validation

The included GitHub workflow performs the authoritative release validation:

1. safely extracts the source ZIP;
2. installs `pdfjs-dist@3.11.174` from npm into the staged source;
3. regenerates checksums;
4. runs strict repository validation without bootstrap allowances;
5. runs the source audit and all unit/package tests;
6. optionally stops as a dry run;
7. validates the replaced repository a second time before commit/tag.

## Security note

The existing classic PDF workspace depends on PDF.js 3.11.174 for compatibility.
`apps/pdf/app.js` sets `isEvalSupported: false`. Migration to a current
module-based PDF.js release remains planned for 0.20.x.

## Not performed in this artifact environment

- actual download of the npm PDF.js package;
- real PDF rendering with the vendored runtime;
- native Firefox and Safari/WebKit testing;
- physical iPadOS touch, keyboard, orientation, background/return, and download
  behavior;
- installed PWA/offline reload in a target browser;
- complete Microsoft Office fidelity or exhaustive hostile-file fuzzing.

## Conclusion

The source package is suitable for a guarded beta publication workflow. It is
not evidence for a stable 1.0 designation. The GitHub dry run must pass before
the repository is replaced.
