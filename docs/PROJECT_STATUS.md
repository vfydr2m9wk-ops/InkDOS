# Project status — InkDOS v1.0.0-beta.2

InkDOS v1.0.0-beta.2 is a maintenance **1.0 public beta**. The application is feature-frozen
while the project collects real-device evidence and fixes only defects whose
reliability benefit clearly exceeds regression risk.

## Beta contract

- six independent local-first workspaces: Documents, Spreadsheets, Presentations, PDF, Plain Text and EPUB Reader;
- explicit workspace-first file opening;
- focused, partial Office compatibility rather than full Microsoft Office parity;
- generated-copy saving for browser-safe workflows;
- private local recovery for supported editing workspaces;
- automated repository, source, architecture, unit/package and Chromium regression gates.

## Appropriate uses

- focused personal document work with exported copies reviewed after saving;
- compatibility experiments and community development;
- local-first reading/editing where InkDOS's documented subset is sufficient.

## Not suitable without independent validation

- regulated or safety-critical production workflows;
- files requiring exact Microsoft Office fidelity;
- unattended/bulk conversion;
- encrypted Office files or unsupported legacy formats;
- deployments not tested in their target browser, host and device.

## Remaining release evidence

1. Native Safari/WebKit and iPadOS smoke testing.
2. Firefox/Edge spot validation when those engines are available.
3. Installed-PWA/offline behavior on a real target device.
4. Real-world beta use with representative DOCX/XLSX/PPTX/PDF files.

The next milestone after beta stabilization is `1.0.0-rc.1`, not feature expansion.
