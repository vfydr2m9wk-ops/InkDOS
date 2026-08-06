# Embedding and Integration

## Static deployment

Copy the complete repository to any static web host or embedded browser container. No server-side runtime is required.

## Stable launchers

The root redirect files provide stable entry points:

- `Office Suite.html`
- `Documents.html`
- `Spreadsheets.html`
- `Presentations.html`

A host product may register these as menu, desktop, dock or application shortcuts. The component entry points under `apps/` may also be opened directly.

## Recommended identifiers

Use identifiers controlled by the integrating product, for example:

- `com.example.localoffice`
- `com.example.localoffice.documents`
- `com.example.localoffice.spreadsheets`
- `com.example.localoffice.presentations`

## File behavior

- Opening uses `<input type="file">` and follows permissions exposed by the browser or host container.
- Export uses browser Blob/download behavior.
- Original files are not overwritten in place.
- Full-screen presentation depends on the standard or WebKit Fullscreen API. When unavailable, presentation mode fills the available viewport.

## Offline deployment

