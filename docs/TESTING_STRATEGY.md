# Testing Strategy

Static checks alone cannot validate document fidelity. Testing is split into four layers.

## 1. Repository checks

- JSON and HTML references;
- duplicate IDs;
- JavaScript syntax;
- version consistency;
- no device-specific absolute paths;
- no automatic remote runtime scripts;
- no obvious stubs or unimplemented markers.

## 2. Synthetic fixtures

The repository contains small, redistributable DOCX, XLSX and PPTX fixtures generated from public OOXML structure. They verify that package plumbing and expected parts remain intact.

## 3. Workflow regression tests

Each component should be tested for create → edit → export → reopen. Any bug fix should add the smallest possible redistributable fixture or a deterministic generation script.

## 4. Visual and host matrix

Before a tagged release, test at minimum:

| Runtime | Chromium | WebKit |
|---|---:|---:|
| HTTPS/static server | Required | Required when available |
| `file://` compatible host | Recommended | Required for target WebViews |
| Desktop viewport | Required | Recommended |
| Touch/tablet viewport | Recommended | Required for iPad-oriented fixes |

Screenshots are useful evidence but do not replace checking exported file contents.
