# InkDOS — Ink Desk Offline Suite

InkDOS is a local-first, offline and private browser productivity suite for focused DOCX, XLS/XLSX, PPTX, PDF, TXT and EPUB workflows.

## 1.0.0-beta.7

Beta 4 is the current functional-hardening baseline. It adds private recovery to Plain Text, removes redundant redirect/visual patch layers, and keeps current code and documentation focused on the product that ships now.

The engineering rule is simple: Git preserves history; `main` preserves the best current implementation. Compatibility is defined by user-visible behavior and data fidelity, not by preserving old internal names, wrappers or patch layers.

## Product priorities

- local-first and offline operation;
- broad, explicit document-format support without pretending to full Office parity;
- safe local recovery and generated-copy saving;
- stable visual hierarchy and predictable interaction;
- small, cohesive runtime modules with no unnecessary compatibility layers;
- aggressive refactoring only behind reproducible tests and candidate-tree validation.

## Run

Open `index.html` directly or use GitHub Pages. HTTP(S) is preferred for service workers, PWA installation and predictable browser behavior.

## Validate

```bash
npm run validate
npm run audit
npm test
npm run test:browser
npm run test:release
```

The GitHub update workflow applies packages only after a disposable candidate tree passes the configured validation profile.

## Status

This is **1.0 beta**. Supported behavior and known limits are documented in [`COMPATIBILITY.md`](COMPATIBILITY.md) and [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md).

## License

InkDOS original code is licensed under the MIT License. Bundled third-party components retain their upstream licenses; see `docs/THIRD_PARTY_NOTICES.md`.
