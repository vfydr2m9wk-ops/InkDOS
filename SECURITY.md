# Security Policy

InkDesk treats imported Office documents as untrusted ZIP/XML input. It does not intentionally execute VBA, ActiveX, embedded JavaScript, add-ins, or remote document instructions. Core processing is local and the project includes no telemetry or document-upload backend.

## Import defenses

Before JSZip receives an OOXML package, `shared/office-runtime.js` validates:

- duplicate names, case-insensitive collisions, and Unicode-normalization collisions;
- absolute, drive-qualified, traversal, backslash, control-character, and malformed paths;
- local-header/central-directory name and method consistency;
- overlapping data regions, truncated directories, unsupported methods, encryption, multi-disk ZIP, and ZIP64;
- configurable compressed, expanded, per-entry, entry-count, and compression-ratio limits;
- unnecessary nested `.zip` entries;
- internal relationship targets and narrowly allowed external hyperlink relationships.

XML parsing rejects DTD/entity declarations and applies configurable size, aggregate-size, depth, node, attribute-count, per-element attribute, and attribute-length limits. The current implementation performs these checks synchronously; moving expensive validation to a worker remains a follow-up.

DOCX-derived editable content is reconstructed by `shared/safe-dom.js` through an element, attribute, style, class, protocol, and image-source allowlist. Event attributes, active SVG/MathML/embedded HTML, `srcdoc`, external resources, dangerous protocols, CSS `url(...)`, and clobbering IDs/names are not copied into the editable DOM.

Spreadsheet arithmetic is evaluated by `shared/formula-engine.js`, a deterministic recursive-descent parser with limits. Imported unsupported formulas retain their OOXML formula and cached result when available; InkDesk does not silently reinterpret them as JavaScript.

## Export integrity

A browser download request is unverified. Dirty-state protection remains active until the exact exported bytes are reopened and matched by SHA-256. This does not prove that another application will preserve or interpret every Office feature correctly.

## Current limits

The controls have regression coverage but are not a formal proof of safety. Native Safari/WebKit, physical iPadOS, very large files, malformed Unicode edge cases, decompressor implementation bugs, and exhaustive ZIP/XML fuzzing remain risk areas. Use backup copies and avoid opening sensitive untrusted documents in an environment where browser compromise would be consequential.

## Reporting

Use GitHub Security Advisories when available. Include the affected version, browser/platform, minimal synthetic reproduction, expected/actual behavior, and whether any network request or script execution occurred. Do not include private user documents.
