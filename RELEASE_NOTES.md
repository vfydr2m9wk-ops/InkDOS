# InkDesk v0.20.3.0 — Visual Foundation

This release begins the visible 0.20.3 UX phase while keeping the v0.20.2.31 structural/data-safety baseline frozen.

## What changes

- Adds `shared/ui/visual-foundation-v0203.css`, a presentation-only layer loaded after existing workspace styles.
- Gives Home a calmer three-column launcher on desktop, two columns on tablet and a compact one-column phone layout.
- Standardizes native-system typography, focus rings, pressed/selected states, border radii, surfaces and shadows.
- Preserves the six product identities: Documents blue, Spreadsheets green, Presentations orange, PDF red, TXT yellow and EPUB purple.
- Harmonizes 44 px titlebar geometry and common toolbar/start-screen treatment without changing editor commands.
- Adds coarse-pointer and reduced-motion rules for iPhone/iPad/WebKit-friendly interaction.
- Adds a dedicated visual-foundation unit contract and an 18th Chromium regression script.

## Intentionally unchanged

DOCX/XLS/XLSX/PPTX/PDF parsers and writers, formula semantics, recovery, history, transactional Open/New/Discard, export safety and document models are unchanged apart from release identity/cache metadata.

Full notes: [`docs/releases/RELEASE_NOTES_0.20.3.0.md`](docs/releases/RELEASE_NOTES_0.20.3.0.md)

Historical notes: [`docs/releases/`](docs/releases/)
