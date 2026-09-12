# InkDOS Tauri Desktop Distribution Design

## Goal

Add an installable desktop distribution of InkDOS for Windows, macOS and Linux without replacing the existing browser/PWA product or rewriting workspace engines. The desktop edition must reuse the current HTML/CSS/JavaScript workspaces and use Tauri only as a host and native platform bridge.

## Scope

The first desktop implementation targets the existing Home launcher plus all six workspaces. The initial native bridge is limited to platform services that are already browser-host-sensitive: opening files, saving files, filesystem persistence, native dialogs, external-link handling and application metadata. Workspace-specific parsing, editing, rendering and serialization remain in JavaScript and remain physically owned by their existing `apps/<workspace>/` trees.

The web/PWA behavior must continue to work unchanged when InkDOS is opened in a normal browser.

## Architecture

InkDOS keeps its current workspace ownership model. Tauri is introduced as a second host, not as a replacement application architecture.

```text
InkDOS HTML/CSS/JS
        |
workspace-local platform adapter
        |
   +----+----+
   |         |
Browser    Tauri
   |         |
Web APIs   native dialog/filesystem
```

No cross-workspace document engine or shared mutable runtime is introduced. Where practical, host detection and platform calls live under each workspace's existing `runtime/platform/` or `io/` boundary. A small root-level desktop bootstrap may expose host capability metadata, but it must not contain DOCX/XLSX/PPTX/PDF/EPUB/TXT business logic.

## Desktop shell

Create `desktop/src-tauri/` as the Tauri application root. The Tauri shell loads the repository's existing root `index.html` and packaged assets. The Home launcher continues to navigate to `apps/<workspace>/index.html` using relative paths.

The desktop shell must:

- use Tauri v2;
- package the existing static site as application assets;
- disable dependence on the root service worker in the desktop host;
- use native open/save dialogs and scoped filesystem access;
- use least-privilege Tauri capabilities;
- preserve the current CSP model, adding only directives required by Tauri's local asset protocol and commands actually used;
- open external HTTPS project links in the system browser rather than inside the application shell where appropriate.

## Platform behavior

### Browser host

Existing browser paths remain available:

- `showSaveFilePicker` when supported;
- `<input type="file">` for opening;
- Web Share where supported;
- Blob/object-URL download fallback;
- service worker/PWA shell over HTTP(S).

### Tauri host

Desktop host behavior uses Tauri plugins or commands for:

- native Open dialog;
- native Save As dialog;
- reading selected files as bytes;
- writing generated output bytes to the selected path;
- returning explicit success, cancellation and failure results to the workspace;
- opening external URLs through the OS.

The native bridge must preserve InkDOS's existing confirmed-delivery semantics: dirty state is cleared only after a successful filesystem write. Cancellation or write failure must leave the document dirty and block destructive navigation exactly as the web path does today.

## Workspace integration

The first implementation must adapt Plain Text and Documents end-to-end because they cover the core host boundary: open, edit, dirty state, save, cancel and Home navigation. After that contract is proven, the same adapter pattern is applied to Spreadsheets, Presentations, EPUB and PDF.

PDF requires a dedicated compatibility check for PDF.js worker loading, Blob URLs, CSP and large-document memory behavior. No PDF engine migration to Rust is in scope.

## Build and distribution

Add a GitHub Actions workflow that builds on native runners:

- Windows: `windows-latest`, producing NSIS `.exe` and/or WiX `.msi` bundles;
- macOS: `macos-latest`, producing `.app` and `.dmg` bundles;
- Linux: `ubuntu-latest`, producing at minimum `.deb` and `.AppImage`, and `.rpm` if supported by the configured Tauri bundler/toolchain.

Artifacts are uploaded to each workflow run. A tag/release path may later publish those artifacts to GitHub Releases; automatic public release publication is not required for the first branch unless explicitly enabled.

Unsigned development artifacts are acceptable for the first branch. Production signing/notarization is a separate release-hardening task because it requires platform-specific credentials and secrets.

## Versioning and naming

The desktop application name is `InkDOS`. The desktop bundle version should derive from `VERSION.json` where practical; until automation is added, configuration must match the repository release version being built. Bundle identifiers must be stable and unique.

Recommended initial bundle identifier:

`com.inkdos.desktop`

## Testing

The branch must preserve the existing repository test suite and add desktop-specific contract tests covering:

- presence and validity of Tauri configuration;
- least-privilege capability files;
- desktop host detection without changing browser behavior;
- Plain Text native open/save result mapping;
- Documents native open/save result mapping;
- confirmed-delivery semantics on success/cancel/failure;
- build workflow matrix for Windows, macOS and Linux;
- no introduction of Electron or bundled Node runtime.

Browser regression tests remain authoritative for the web edition. Desktop smoke tests should verify Home navigation and at least Plain Text and Documents opening/saving on native runners where feasible.

## Performance acceptance

The desktop edition is not declared lightweight solely because it is installable. Record benchmark procedures for:

- cold startup time;
- idle RSS/memory footprint;
- Plain Text open/edit idle memory;
- DOCX open/edit idle memory;
- representative XLSX and PPTX workloads;
- a representative 20-page PDF workload;
- installed package size.

Results should be compared with the same InkDOS workload in a normal browser. No fixed numeric target is imposed in this first implementation because measurements depend on OS and WebView version.

## Security

Tauri permissions must be explicit and scoped. The desktop shell must not expose arbitrary shell execution, unrestricted filesystem access or broad command invocation to workspace JavaScript. Only the minimum file/dialog/external-link capabilities required by InkDOS are permitted.

Existing file parsers continue to treat opened documents as untrusted input and retain their current validation/security contracts.

## Non-goals

This project does not:

- rewrite editors or document engines in Rust;
- replace the browser/PWA edition;
- add Electron;
- add a backend or telemetry service;
- guarantee lower RAM than native office suites without measurement;
- include production code-signing certificates, Apple notarization credentials or Linux repository packaging infrastructure.

## Success criteria

The branch is ready for review when:

1. InkDOS launches from a Tauri desktop shell using the existing Home and workspaces.
2. Plain Text and Documents can open and save through native desktop dialogs while browser behavior remains intact.
3. Existing web tests continue to pass.
4. A native-runner GitHub Actions matrix produces Windows, macOS and Linux installable artifacts.
5. The produced artifacts are uploaded to the workflow run and their exact filenames are documented.
6. No workspace engine is duplicated or moved into a shared desktop engine.
7. Desktop filesystem permissions remain least-privilege.
