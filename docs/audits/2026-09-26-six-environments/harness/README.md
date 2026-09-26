# Audit harness (not part of the product or CI)

Scripts used for the 2026-09-26 six-environment audit (`../REPORT.md`). They are evidence, not maintained tests.

- `gen_fixtures.py` builds synthetic fixtures; DOC/XLS/PPT were converted from them with LibreOffice.
- `fw.py` is shared Playwright helpers: save-picker stub (`fs` profile) and no-File-System-API profile (`nofs`).
- `f_<app>.py` is a functional script per app; `visual.py`, `cross*.py`, `offline.py` and `perf*.py` cover the other stages.
- `repro_*.py` are minimal reproductions of the FAIL findings.

The paths `S`/`FX` in `fw.py` point to the auditor's scratch directory. Edit them and serve the repository at `http://127.0.0.1:18431/InkDOS/` before running.
