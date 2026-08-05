# InkDesk 1.0 Preparation — Hardening Stage 1

**Base:** InkDesk `0.19.1-beta` source package  
**Package classification:** source hardening candidate; not an official tagged release and not a 1.0 candidate  
**Execution date:** 2026-08-04

## Implemented in this stage

### Frame handoff security

The HTTP(S) embedded handoff now calculates and uses the exact destination origin. Incoming messages require the expected `event.origin`, the expected `event.source`, protocol version `1`, the correct random token, and an unexpired deadline. Tokens are consumed once. Parent and child listeners and timers are removed after receipt, failure, or timeout.

The only wildcard `targetOrigin` remains inside one named helper for opaque `file://` origins. That helper refuses execution outside local-file mode and is marked as the single audited exception.

### Static audit

The previous comma-sensitive regular expression was replaced by a conservative call scanner. It tracks nested parentheses, brackets, braces, strings, templates, comments, multiline calls, optional chaining, and commas inside expressions. CI fails for wildcard `postMessage` targets except the one documented local-file exception.

### Temporary handoff storage

Expired IndexedDB handoff entries are purged when the hub or a workspace starts. Records are removed after consumption and on expired retrieval. `InkDeskFileRouter.clearTemporaryData()` provides an explicit API for clearing the handoff store.

### Service worker

The service worker now:

- uses explicit canonical cache keys instead of global `ignoreSearch` matching;
- strips queries only for the known workspace navigation HTML entries;
- caches only declared application-shell assets;
- removes an incomplete cache when installation fails;
- reports cache-update failures instead of silently swallowing them;
- removes old versioned caches during activation;
- exposes an `inkdesk:clear-app-cache` recovery message;
- does not cache user documents or arbitrary same-origin resources.

### Official build guard

`scripts/build_release.py` now requires:

- a valid Git checkout whose root matches the source tree;
- a clean working tree;
- tag `v<version>` present and pointing to `HEAD`;
- commit and tag derived from Git, not supplied manually;
- two byte-identical in-process archive builds;
- `SOURCE_MANIFEST.json` with path, size, and SHA-256 for included files;
- `SBOM.spdx.json` for InkDesk, JSZip, and pako;
- runtime checksums and external archive checksum.

A ZIP assembled outside a clean tagged checkout remains a source/local-test package, not an official release artifact.

## Executed validation

| Validation | Result |
|---|---|
| Repository validator | Passed |
| Syntax-aware source audit | Passed; one documented opaque-origin exception |
| Python unit/package tests | 53/53 passed |
| JavaScript security assertions | 46/46 passed |
| JavaScript syntax checks | Passed |
| Chromium package-security group | 2/2 scripts passed |
| Chromium lifecycle group | 3/3 scripts passed |
| Chromium isolation/offline group | 2/2 scripts passed |
| Chromium documents/presentations group | 2/2 scripts passed |
| Chromium spreadsheets group | 2/2 scripts passed |
| Total Chromium browser scripts | 11/11 passed |

The full synthetic two-origin browser navigation path could not run locally because the environment blocked HTTP(S), localhost, and `file://` navigation. The regression recorded this and executed its trusted-versus-hostile origin-policy fallback. The full path remains configured for ordinary CI environments and must be observed there before release approval.

## Deliberately not claimed

This stage does not provide:

- Web Worker parsing or model construction;
- adaptive memory and complexity budgets by device class;
- a universal progress/cancellation coordinator;
- presentation workspace decomposition;
- PDF viewing;
- Office-to-PDF fallback providers;
- native Safari or physical iPadOS approval;
- installed-PWA offline/update approval;
- proof that the private 170-file corpus still passes after these changes;
- version 1.0 readiness.

## Next mandatory stage

The next stage should introduce a versioned worker protocol and move package inventory, decompression, XML parsing, BIFF8 processing, complexity analysis, and initial model construction off the main thread. It must preserve the currently open document on cancellation, timeout, memory pressure, or parser failure.
