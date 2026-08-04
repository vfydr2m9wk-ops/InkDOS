# Focused MVP Scope

## Purpose

The MVP is a small, reviewable set of local OOXML workflows. It is intentionally narrower than a conventional office suite.

## Required workflows

A release may describe a component as working only when all applicable steps below pass with synthetic fixtures and at least one independently supplied public test file:

1. create a blank file;
2. add or edit basic content;
3. export a non-empty copy;
4. reopen the exported copy;
5. preserve the basic content added during the test;
6. fail clearly rather than silently when an unsupported structure is encountered.

## Documents

In scope:

- paragraphs and headings;
- basic inline styling;
- ordered and unordered lists;
- simple tables;
- raster images;
- page-like editing and DOCX copy export.

## Spreadsheets

In scope:

- `.xlsx` open/edit plus focused BIFF8 `.xls` import;
- values and basic formulas;
- common cell formatting;
- row and column insertion/deletion;
- multiple sheets;
- merges, widths and heights;
- XLSX copy export.

## Presentations

In scope:

- `.pptx` only;
- text, raster images and basic shapes;
- common slide layouts and masters;
- 4:3 and 16:9 geometry;
- presentation from first or current slide;
- PPTX copy export.

## Explicit non-goals before 1.0

- full OOXML coverage;
- pixel-identical Microsoft Office output;
- proprietary fonts or proprietary Office libraries;
- VBA/macros;
- real-time collaboration;
- cloud storage integration;
- SmartArt, advanced charts, OLE and embedded applications;
- automatic native integration with every host platform.

A proposed feature outside this list needs a written use case, a maintainer decision and a testing plan before implementation.
