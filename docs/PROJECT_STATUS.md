# Project status — InkDesk v0.20.0

InkDesk v0.20.0 is a **consolidated public beta**. It replaces the internal
`0.19.4.x` package chain with one complete source tree and six workspaces:
Documents, Spreadsheets, Presentations, PDF, Plain Text, and EPUB Reader.

## Appropriate uses

- local compatibility experiments;
- focused personal document work where exported copies are reopened and
  verified;
- community development of parsers, rendering, interface consistency, and
  regression fixtures;
- non-critical TXT editing and EPUB reading.

## Not suitable without independent validation

- regulated, medical, legal, or financial production workflows;
- files requiring exact Microsoft Office fidelity;
- unattended or bulk conversion;
- DRM-protected or fixed-layout EPUB workflows;
- deployments not tested in their target browser, host, and device.

## Current engineering priorities

1. Native Safari/WebKit, iPadOS, Firefox, and embedded-host validation.
2. PDF.js migration to a current module-based release.
3. Privacy-preserving crash and session recovery.
4. Refactoring the large PDF and shared layout controllers.
5. Compatibility improvements backed by redistributable fixtures.

The project remains beta and is not presented as a stable 1.0 release.
