# InkDOS 2.0 architecture

InkDOS 2.0 is a launcher plus five independent applications.

```text
Home
 ├─ Documents
 ├─ Spreadsheets
 ├─ Presentations
 ├─ PDF Workspace (placeholder only)
 ├─ Plain Text
 └─ EPUB Reader
```

Home has no file-opening, editing, recent-files, or global-suite runtime. It only routes to the installed app entry points.

Each application owns its own runtime, IO, state, view and vendor dependencies. Cross-app runtime imports are not required. Deliberate redundancy is preserved rather than centralized.

## Integration boundary

The canonical FINAL package source tree for each app is copied into `apps/<app>/`. Integration may modify only `apps/<app>/index.html`, solely to add a Home icon linking to `../../index.html`. `SOURCE_LOCK.json` pins the source package SHA-256, the original app-tree digest, the non-index tree digest, and the integrated index hash.

## PDF boundary

`apps/pdf/` does not exist in 2.0.0. The Home card is a non-interactive placeholder. A later PDF update must add an app-private runtime instead of reviving the retired 1.x PDF tree.
