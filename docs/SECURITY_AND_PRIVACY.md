# Security and Privacy

- Document parsing and editing occur in the browser process.
- The suite does not require an account or application server for its core editors.
- No telemetry, analytics, tracking, or remote document-processing code is included.
- Selected files and active document models are held in memory; the application does not intentionally persist document content to local storage or IndexedDB.
- The service worker caches application assets only and does not cache user documents.
- Saving creates a browser-generated local copy and never silently overwrites the selected source file.
- Imported Office documents are treated as untrusted ZIP/XML input.
- Macros, ActiveX, embedded JavaScript, add-ins, and remote document instructions are not executed.
- Package guards reject unsafe paths, encrypted/ZIP64 archives, malformed headers, excessive counts/sizes/ratios, and invalid XML before state commit.
- Unsupported or corrupt input should fail with a controlled message while preserving the previous active document.

These controls reduce practical risk but do not establish that every hostile document is safe. Use the browser sandbox, keep the host updated, and avoid opening sensitive untrusted files in critical environments.
