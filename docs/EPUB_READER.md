# EPUB Reader module

Development sequence `0.19.4.15` adds a local modular EPUB reader using the purple book identity.

## Reading workflow

- Open a local `.epub` file.
- Navigate generated lateral pages with buttons, arrow keys, Page Up/Page Down, or a horizontal swipe.
- Increase or decrease text from 13 to 30 pixels.
- Choose Paper, Sepia, Sage, or Night backgrounds.
- Open a three-dimensional table-of-contents panel; it is closed by default.
- View local JPEG, PNG, GIF, WebP, and SVG images.

InkDesk reads `META-INF/container.xml`, locates the package document, follows the spine, sanitizes XHTML, and replaces local image references with temporary object URLs. Scripts, forms, iframes, embedded objects, audio, video, remote URLs, event attributes, and publisher styles are not retained.

The filename is editable. Book content is read-only; Save downloads the unchanged original EPUB bytes under the edited filename. Renaming without saving uses the shared unsaved-change warning.

The local limit is 100 MB. Fixed-layout, DRM-protected, interactive, audio, video, and exact publisher pagination are outside this simple reader's scope.
