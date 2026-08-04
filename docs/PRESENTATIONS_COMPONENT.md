# Presentations Component

## Entry point

`apps/presentations/index.html`

## Main source files

- `app.js` — presentation state, PPTX parsing, package-preserving export, editing and presentation rendering.
- `engine/compatibility.js` — local font and theme compatibility helpers.
- `styles.css` — editor, side panels, object controls and presentation overlay.
- `vendor/` — local JSZip and pako browser builds.

## Imported PPTX workflow

Version 0.19.0-beta keeps the original OOXML package in memory. Saving a copy reloads that package and patches only supported changes in the existing slide set. Unrecognized parts are retained rather than recreated.

The relationship path for any part is derived as:

```text
ppt/slides/slide1.xml
→ ppt/slides/_rels/slide1.xml.rels
```

The same rule applies to layouts, masters, themes and notes parts.

## Supported preservation in imported files

- Slide text edited through the local editor.
- Object geometry for directly owned slide objects.
- Existing presenter-note bodies.
- Existing or changed basic transitions.
- Added text, shape and raster-image objects on an existing slide.
- Unedited tables, charts, groups, media, themes, masters, layouts and unknown parts.

Unsupported content remains in the package whenever it is not directly modified.

## Preview support

- Raster images, including basic DrawingML cropping.
- Layout/master artwork and placeholder inheritance.
- Groups and common shapes.
- DrawingML tables.
- Cached bar and column chart data.
- Presenter notes.
- Basic fade, slide and zoom transition preview.
- 4:3 and 16:9 slide geometry.

## Current safety boundary

Changing the slide set of an imported package—insert, delete or duplicate—is blocked during preservation-mode save. The application displays an explicit error rather than silently rebuilding and losing relationships. New presentations can still add, duplicate and delete slides using the compact generated writer.

Presenter notes are preserved and editable when an imported PPTX already contains notes parts. Creating a complete notes-master relationship graph for notes added to a new presentation remains deferred.

## Presentation controls

- **From first slide** starts at slide 1.
- **From current slide** starts at the selected slide.
- Presentation mode has one Exit control.
- Fullscreen is requested only when the host exposes the standard or WebKit API.
