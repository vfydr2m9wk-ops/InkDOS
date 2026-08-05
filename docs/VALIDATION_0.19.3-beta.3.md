# Validation — 0.19.3-beta.3

The complete source tree is checked for broken local references, duplicate files, stale release-specific paths, version mismatches, unexpected metadata and forbidden personal/build terms. Release fixtures are synthetic and use normalized metadata.

Automated Chromium regressions exercise four workspaces:

- DOCX: A4 geometry, header/footer images and tables, using both standard and UTF-8-BOM XML fixtures;
- BIFF8 XLS: styles, merges, explicit borders and hidden-zero sheet option;
- PPTX: direct image background, multiple slides and a table;
- PDF: main viewer object URL, three-page inspection, AcroForm detection, outline extraction, navigation controls and a local review annotation.

The synthetic PDF fixture contains three pages, mixed portrait/landscape orientation, five AcroForm fields and three outline entries. Its Author, Creator and Producer metadata are all `InkDesk QA`.

Separate local review used supplied real-world DOCX, XLS and PPTX files without copying them into the repository or release archive. The valid DOCX variant with BOM-prefixed XML motivated the BOM-normalization regression test. Browser-native PDF rendering and form persistence remain platform-dependent and require physical WebKit/iPadOS validation.
