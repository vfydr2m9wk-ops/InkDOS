# Roadmap

## 0.19.x — Cross-format fidelity

- Stabilize A4 DOCX headers, footers, margins and tables.
- Improve XLS/XLSX page-oriented forms and BIFF8 decoding.
- Improve PPTX backgrounds, transforms and tables.
- Validate the local PDF.js worker, page virtualization, forms and review layer on WebKit/iPadOS and embedded hosts.
- Keep fixtures synthetic and release metadata reproducible.

## 0.20.x — Compatibility and hardening

- Add more redistributable regression fixtures and corrupted-file cases.
- Improve PowerPoint text autofit, groups and theme effects.
- Improve spreadsheet print areas, formulas and drawing anchors.
- Validate native Safari/WebKit, Firefox, iPadOS, form-value persistence and installed PWA behavior.

## 1.0.0 criteria

- No known critical save, corruption or workspace-isolation defect.
- Repeated deterministic full-regression builds.
- Verified Chromium, Firefox and Safari/WebKit behavior.
- iPadOS and offline/PWA validation documented.
- Documentation, licenses, checksums and release manifests synchronized.
