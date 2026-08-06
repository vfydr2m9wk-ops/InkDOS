# Publishing InkDesk v0.20.0 on GitHub

v0.20.0 is a complete repository replacement, not another incremental
`0.19.4.x` package. It can be published even when the current repository has
not applied every previous development package.

## Files to upload

1. Place `publish-inkdesk-v0.20.0.yml` at:
   `.github/workflows/publish-inkdesk-v0.20.0.yml`.
2. Place `InkDesk_v0.20.0.zip` in the repository root without extracting it.
3. Remove older complete v0.20 ZIPs from the root so automatic selection is
   unambiguous.

## Recommended first run

Open **Actions → Publish InkDesk v0.20.0 → Run workflow** and use:

```text
package_name: InkDesk_v0.20.0.zip
create_backup_branch: true
create_tag: false
dry_run: true
```

A successful dry run safely extracts the source, verifies the release identity,
installs the pinned PDF.js files from npm into the staged tree, regenerates
checksums, and runs repository validation, source audit, and all unit/package
tests without changing the repository.

## Publication run

Run the workflow again with:

```text
package_name: InkDesk_v0.20.0.zip
create_backup_branch: true
create_tag: true
dry_run: false
```

The workflow creates a backup branch, replaces the repository with the staged
v0.20.0 tree, validates the installed tree again, commits it, pushes it, and
creates tag `v0.20.0`.

## PDF.js vendor step

The source ZIP pins `pdfjs-dist@3.11.174` in `VENDOR_SOURCES.json`. The workflow
retrieves that exact npm package during staging and commits its display script,
worker, and Apache-2.0 license. No PDF.js CDN is contacted by the published
runtime. The PDF workspace explicitly disables PDF.js eval support.

If npm is unavailable, the workflow fails before repository replacement.

## Recovery

When backup creation is enabled, the previous repository state is pushed to:

```text
backup/pre-v0.20.0-<workflow run id>
```

The complete package is only deleted from the root after staged validation has
passed and the replacement step begins.
