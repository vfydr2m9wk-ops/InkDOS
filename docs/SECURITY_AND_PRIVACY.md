# Security and privacy

InkDesk is designed for local file processing. It does not include analytics, a project-operated upload endpoint, advertising code or remote document conversion.

## Release privacy controls

- Private reference documents are never copied into the source tree or release archive.
- Synthetic fixtures use generic content and normalized Office/PDF metadata.
- The release audit scans for personal names, email addresses, absolute build paths, stale project names and unsupported linked assets.
- Images distributed by the project are regenerated without EXIF or author metadata.
- Release ZIP entries use deterministic timestamps and do not preserve local filesystem ownership.

Opening a file may expose its contents to browser extensions or operating-system services installed by the user. InkDesk cannot control those external components.
