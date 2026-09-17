# PPT-P1 closure and integration audit

Status: **FUNCTIONAL BASELINE FROZEN / READY FOR INTEGRATION** once the branch CI and pull-request gates are green.

Phase: **PPT-P1 — PPTX Home Editing**.

PPT-P1 extends only the Presentations workspace. It does not introduce a shared presentation engine, backend service, telemetry, remote conversion path, or runtime dependency on another InkDOS workspace. The existing App Frame, Home relationship, appearance bridge, editing toolbar, slide rail, central canvas, status bar and presentation mode remain structurally intact.

## Confirmed home-editing scope

- Add, duplicate, delete and reorder slides in new presentations and imported PPTX files.
- Insert and edit text boxes.
- Insert local PNG, JPEG and WebP images within the app-local presentation model.
- Insert basic shapes: rectangle, rounded rectangle, ellipse and line.
- Contextual object move, resize and rotation controls without adding a permanent secondary toolbar.
- Basic fill and border colors.
- Text color.
- Basic bullet lists.
- Basic domestic layouts: Title + Content, Two Content and Section Header.
- Save/Share as PPTX.

Legacy `.ppt` remains read-only in PPT-P1 and is not re-exported as `.ppt`.

## Imported PPTX preservation model

Imported PPTX editing uses app-local package-preserving writers rather than flattening the entire source presentation into the simplified new-presentation writer.

For slide-structure operations, the writer preserves the original package and updates the presentation slide list and relationships. Existing slide parts are reused when retained; duplicated/import-derived slides are copied into new local slide parts; newly authored slides receive new PPTX slide parts.

For supported object authoring, the writer updates supported text objects and inserts basic text, shapes and local images into the relevant slide parts. Local image payloads are stored under `ppt/media/` and connected through slide relationships. Output packages are reopened through the production PPTX decoder after serialization.

Existing unsupported or complex PPTX content is preserved in source package parts where possible rather than rewritten merely to increase feature count.

## Geometry and interaction safety

PPT-P1 provides contextual move, resize and rotate handles for objects that InkDOS can map safely to its editable model. The interaction path is protected by history transactions so successful gestures become undoable model changes.

Imported image/shape objects that do not yet have a safe writable source mapping are deliberately marked as unmapped and are not given geometry-edit handles. This prevents a visual edit from implying persistence that the package writer cannot safely guarantee.

## Verification evidence

PPT-P1 is protected by static/syntax/isolation checks and Chromium browser round-trip tests.

1. Imported structure round-trip: an imported PPTX is modified with add/duplicate/delete/reorder operations, serialized through the package-preserving writer, inspected for presentation relationships/order, decoded and reopened.
2. Objects and geometry round-trip: a PPTX is opened through the real file-input path; a basic shape is inserted and moved/resized/rotated through browser hit-tested controls; fill/border are applied; text color and bullets are authored; a basic layout is applied; a local image is inserted; the PPTX is serialized, ZIP/XML inspected, decoded and reopened.
3. New-presentation round-trip: the generated-PPTX writer is checked with basic shape, rotation, image and text/list content so PPT-P1 does not regress presentations created from scratch.
4. Offline-shell contract: `ppt-p1-structure-writer.js`, `ppt-p1-object-writer.js` and `ppt-p1-tools.js` are required members of the suite service-worker application shell so the supported workflow remains available after installation without a network dependency.

The repository release validation also checks source isolation, checksums, generated metadata and suite contracts.

## Limitations intentionally retained

- PPT-P1 does not implement speaker notes, tables, themes, transitions or PDF export; those belong to PPT-P2.
- PPT-P1 does not claim full editing fidelity for charts, SmartArt, OLE, macros, advanced animations or arbitrary corporate template resources.
- Unsupported complex objects are preserved when possible but are not converted into fake editable equivalents.
- Existing imported images/shapes without a verified writable source mapping remain protected from geometry editing.
- Legacy `.ppt` is still import/read-only in this phase; modernized legacy import with PPTX output belongs to PPT-P2.
- No `.ppt` export is planned.

## Freeze and next phase

PPT-P1 is frozen when this branch is integrated into `main` after all required branch and pull-request gates are green. Further PPT-P1 functional work then requires either an objective regression fix or a separately authorized compatibility cycle.

The next permitted functional cycle after integration is **PPT-P2 — Presentation Completion + PPT Import**.