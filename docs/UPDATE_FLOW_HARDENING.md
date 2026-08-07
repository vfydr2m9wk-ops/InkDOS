# Update flow hardening — InkDesk 0.20.2.7

This patch hardens the development/update path before further runtime
refactoring. It intentionally does not change editor UI, file-format behavior,
save semantics or recovery formats.

## 1. Dry-run now validates the actual candidate

Before 0.20.2.7, `--dry-run` validated package metadata and printed the planned
copy/delete operations, then returned before applying the candidate tree or
running the declared validation profile.

From 0.20.2.7 onward, dry-run:

1. validates package identity, order, paths and workflow restrictions against
   the real checkout;
2. copies the checkout to a disposable temporary repository tree;
3. applies the package payload and DEVELOPMENT_STATE update to that copy;
4. runs the package validation profile against the candidate copy;
5. discards the copy and leaves the source checkout unchanged.

A failed dry-run therefore means the candidate itself failed validation. It is
not described as a rollback because the source tree was never modified.

## 2. Incremental checksum updates

`scripts/update_checksums_incrementally.py` edits only explicitly declared
manifest paths. Every checksum entry not named by the patch author is preserved
byte-for-byte.

This is the required approach when the local authoring tree is incomplete or
contains reconstructed copies of files that are authoritative only in the
published GitHub tree. In particular, do not regenerate the full checksum
manifest merely to prepare a small incremental update.

Example:

```bash
python3 scripts/update_checksums_incrementally.py \
  --changed scripts/apply_update_package.py \
  --changed tests/test_update_package.py \
  --changed tests/browser/revalidate_presentations_slideshow.py
```

Use `--delete PATH` only for intentional repository deletions.

## 3. Browser scenario isolation

The slideshow/presentation-mode checks now run in
`tests/browser/revalidate_presentations_slideshow.py`, a separate process with a
fresh browser context and explicitly established Home/View/Present tab state.
The broader Presentations controls script no longer leaves hidden state for the
slideshow scenario to inherit.

The normal Chromium release gate therefore contains thirteen independent
browser scripts beginning with this release.

## 4. Package identity

Every Actions run exposes the selected update ZIP SHA-256 before validation.
Correction packages should use an unambiguous filename while being tested, and
the SHA shown by Actions must match the SHA delivered for that attempt before a
failure is attributed to the candidate.

## Scope boundary

No runtime application behavior is intentionally changed by this hardening
patch. The next bounded runtime refactor is Presentations I/O/save/recovery.
