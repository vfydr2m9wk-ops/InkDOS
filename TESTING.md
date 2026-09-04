# InkDOS testing

The release gate is intentionally layered:

1. repository/static validation;
2. source and architecture audits;
3. Python unit/package tests;
4. Chromium behavioral regressions;
5. checksum verification.

Run everything with:

```bash
python3 scripts/run_release_validation.py
```

Use `python3 scripts/run_browser_matrix.py` when installed Firefox/WebKit engines are available. Native Safari/iPadOS and installed-PWA behavior still require real-device verification.

Tests should protect current behavior, data safety and visual interaction. They should not freeze obsolete file names, patch layering or historical implementation choices.
