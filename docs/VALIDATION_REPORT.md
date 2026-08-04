# Validation Report — InkDesk 0.19.1-beta

## Environment

- Date: 2026-08-04
- Baseline upstream commit: `538c99d7c09566644d2095aaf33305b890a4b4c7`
- Linux x86_64; Python 3.13.5; Node.js 22.16.0; npm 10.9.2
- Playwright 1.57.0 with system Chromium
- Firefox and WebKit executables were not installed locally
- Native Safari, native Firefox packaging, physical iPadOS, embedded hosts, and installed-PWA behavior were unavailable

## Executed results

| Area | Result |
|---|---:|
| Repository validation | Passed |
| Source audit | Passed |
| Python unit/package suite | 47/47 passed |
| JavaScript security-module assertions | 46/46 passed |
| Chromium browser scripts | 10/10 passed in five isolated groups |
| DOCX round-trip scenarios | Passed |
| XLS/XLSX round-trip scenarios | Passed |
| PPTX round-trip scenarios | 20/20 checks passed |
| Deterministic packaging test | Passed |
| Firefox local launch | Not executable; Playwright engine missing |
| WebKit local launch | Not executable; Playwright engine missing |

The local system Chromium became unreliable after many consecutive browser launches in one aggregate process. Each final Chromium group was therefore run independently, matching the CI matrix design. This is an environment limitation, not evidence of native device support.

## What the browser tests prove

The executed scenarios cover hostile DOM input without script execution or unexpected external requests; ZIP/XML failure paths; dirty/export state; blocked downloads; fingerprint-based reopen verification; failed-open preservation; cross-workspace isolation; representative DOCX/XLS/XLSX/PPTX edits; export; reopen; and expected package-part preservation.

They do not prove complete Office fidelity, arbitrary hostile-file safety, native iPadOS download behavior, large-file stability, crash/session recovery, or installed-PWA behavior.

## Conclusion

The evidence supports a **controlled beta**, not a release candidate or version 1.0. The highest remaining risks are native WebKit/iPadOS behavior, memory pressure, advanced OOXML fidelity, unsupported formulas/features, and browser-controlled save/download limitations.
