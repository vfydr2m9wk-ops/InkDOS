# Testing Guide

Every meaningful change requires static validation, targeted tests, and broader regression. Data corruption, silent save failure, stale export, and cross-workspace contamination are release-blocking defects.

## Automated checks

- Repository structure, HTML, CSS references, JSON, web manifest, service-worker paths, version consistency, filename casing, and JavaScript syntax.
- Source audit for automatic remote requests, insecure URLs, empty catches, prototype pollution markers, wildcard `postMessage`, and risky dynamic-code markers.
- 43 Python unit and OOXML package-preservation tests.
- Eight Chromium/Playwright regression scripts covering DOCX, XLS/XLSX, BIFF8 XLS, PPTX, zero-valued formulas, transactional failure recovery, package guards, restricted APIs, and cross-workspace isolation.
- Release checksum verification.

## Commands

```bash
npm run validate
npm run audit
npm test
npm run test:browser
npm run test:release
```

`npm run audit` reports the intentionally restricted spreadsheet arithmetic evaluator as a manual-review item. The expression is accepted only after a strict character/function allowlist; it is not treated as imported JavaScript.

## Release loop

After each meaningful batch:

1. Run targeted tests.
2. Run repository validation and source audit.
3. Run the unit/package suite.
4. Run all browser regressions.
5. Verify checksums.
6. Repeat the complete release cycle three consecutive times after the final source and documentation changes.

Record unavailable browsers or devices as **Not performed**. Never infer compatibility from another engine.
