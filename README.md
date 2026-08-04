InkDesk

InkDesk is a local-first, offline Office suite built with standard web technologies.

It provides three independent workspaces:

* Documents — open, view, create, edit, and export text documents.
* Spreadsheets — open, view, create, edit, calculate, and export spreadsheets.
* Presentations — open, view, create, edit, present, and export slide decks.

InkDesk is designed for situations where privacy, offline availability, portability, and local file control are more important than cloud collaboration.

Project status

Current version: 0.19.0-beta

InkDesk is currently considered beta-quality software.

It is suitable for testing, personal workflows, document viewing, and basic editing. It should not yet be considered a complete replacement for Microsoft Office, LibreOffice, or other full desktop office suites.

Important documents should always be backed up before editing.

Main principles

* Local-first operation
* Fully offline usage after download or installation
* No backend server
* No user accounts
* No authentication system
* No telemetry or analytics
* No document uploads
* No remote document processing
* No mandatory cloud services
* No macros or active document content
* No unnecessary framework or build-system dependency

Supported workspaces

Document Workspace

The Document Workspace is intended for basic document viewing and editing.

Current capabilities include:

* Create new documents
* Open supported Word documents
* Edit text
* Basic text formatting
* Paragraph alignment
* Lists
* Undo and redo
* Rename documents
* Save and export documents
* Reopen exported documents
* Page-oriented document display
* Local image and content handling

Primary format:

* .docx

Spreadsheet Workspace

The Spreadsheet Workspace is intended for basic spreadsheet viewing, editing, and calculation.

Current capabilities include:

* Create new spreadsheets
* Open supported Excel files
* Edit text and numeric cells
* Basic formulas
* Multiple worksheets
* Add and remove rows or columns
* Basic formatting
* Images
* Undo and redo
* Rename spreadsheets
* Save and export spreadsheets
* Reopen exported spreadsheets
* Formula results containing zero
* Separation between empty, zero, false, and missing values

Primary formats:

* .xlsx
* .xls for supported legacy BIFF8 files

Legacy .xls support is limited and may not preserve every workbook feature.

Presentation Workspace

The Presentation Workspace is intended for basic slide viewing, editing, and presentation.

Current capabilities include:

* Create new presentations
* Open supported PowerPoint presentations
* Add slides
* Duplicate slides
* Delete slides
* Reorder slides
* Edit text elements
* Move and resize elements
* Manage basic images and shapes
* Undo and redo
* Rename presentations
* Presentation mode
* Save and export presentations
* Reopen exported presentations

Primary format:

* .pptx

Offline operation

InkDesk does not require a backend or remote server.

The application can operate from locally downloaded project files in compatible browser environments.

When served through HTTPS or localhost, supported browsers may also install InkDesk as a Progressive Web App.

Service workers are not available when the application is opened directly through file://. This does not prevent the main application from operating locally, but PWA installation and service-worker caching require a compatible web origin.

Running InkDesk

Local file mode

1. Download or clone the repository.
2. Extract all project files.
3. Open index.html in a compatible browser or embedded browser environment.
4. Select the required workspace.

Some browsers restrict local-file access, downloads, storage, or communication between files. Behavior may therefore differ between browsers and operating systems.

Local static server

A local static server provides the most consistent browser behavior.

Example using Python:

python3 -m http.server 8080

Then open:

http://localhost:8080

No application backend is started. Python is used only to serve the static files locally.

GitHub Pages or another static host

InkDesk can be deployed to any static hosting service that preserves the project directory structure.

No server-side processing is required.

Browser compatibility

InkDesk is designed with compatibility fallbacks for:

* Chromium-based desktop browsers
* Firefox
* Safari and WebKit-based environments
* iPadOS browsers
* Embedded browser environments
* Local static hosting
* Restricted browser APIs
* Environments without the File System Access API

Browser support may vary for:

* Direct local-file access
* IndexedDB
* Local storage
* Clipboard access
* Fullscreen mode
* Service workers
* Progressive Web App installation
* File downloads on iPadOS
* Before-unload confirmation dialogs
* Private browsing or restricted storage modes

Chromium is currently the most extensively automated test environment.

Native Firefox, Safari, physical iPadOS, and embedded-browser testing may require additional manual validation for each release.

Data and privacy

InkDesk processes documents locally in the browser.

The project does not intentionally:

* Upload documents
* Track users
* Send analytics
* Create user profiles
* Require accounts
* Use advertising services
* Execute Office macros
* Execute embedded scripts from imported documents
* Follow remote instructions contained in Office files

Imported files must still be treated as untrusted input.

InkDesk includes defensive checks for malformed or unreasonable Office packages, but no parser should be assumed to be completely immune to malicious files.

Saving files

InkDesk uses browser-supported download and file-access mechanisms.

Depending on the platform, saving may:

* Download a new copy
* Open the browser download interface
* Use the File System Access API
* Require confirmation through the operating system file picker

A download request does not guarantee that the operating system completed the write successfully. Users should confirm that the exported file exists and can be reopened before closing important work.

File compatibility

InkDesk focuses on basic compatibility and preservation of commonly used Office document structures.

It does not claim complete compatibility with Microsoft Office.

Advanced or unsupported features may be ignored, simplified, converted, or preserved without being editable. Examples may include:

* Macros
* ActiveX controls
* Embedded scripts
* Complex charts
* External data connections
* Advanced formulas
* Pivot tables
* Complex page layouts
* SmartArt
* Advanced transitions
* Animations
* Protected or encrypted documents
* Digital signatures
* Embedded applications
* Remote templates
* Unsupported fonts

Always verify exported documents in the application that will ultimately be used to present, print, or distribute them.

Project structure

.
├── apps/
│   ├── documents/
│   ├── spreadsheets/
│   └── presentations/
├── assets/
├── docs/
├── scripts/
├── shared/
│   └── vendor/
├── tests/
├── index.html
├── manifest.webmanifest
├── service-worker.js
├── VERSION.json
├── CHECKSUMS.sha256
├── LICENSE
└── README.md

The three workspaces maintain separate document state, filename state, editing history, temporary data, and export flows.

Shared modules should contain only behavior that is genuinely equivalent across workspaces.

Development guidelines

All source code, comments, filenames, internal identifiers, documentation, and developer-facing messages must remain in English.

Development should follow these principles:

* Preserve currently working behavior
* Prefer small and reversible changes
* Avoid unnecessary dependencies
* Maintain offline operation
* Avoid Chromium-only assumptions
* Preserve browser compatibility fallbacks
* Keep workspace state isolated
* Treat data loss and silent save failures as critical defects
* Validate imported files as untrusted input
* Do not introduce telemetry or remote processing
* Do not report a defect as fixed without rerunning the relevant tests

Testing

The repository includes lightweight validation scripts and browser-oriented regression tests.

Typical checks include:

* JavaScript syntax
* JSON and manifest validity
* Missing files
* Broken relative paths
* Duplicate element IDs
* Unsafe package paths
* Package-size limits
* Office package preservation
* Document export and reopen
* Spreadsheet formulas returning zero
* Corrupted-file handling
* Presentation undo and redo
* Workspace state isolation
* Restricted browser API fallbacks
* Internal file checksums

Run the available validation scripts from the project root according to the instructions in the scripts and tests directories.

A release should not be considered validated unless the complete regression suite passes repeatedly without intermittent failures.

Known limitations

Current technical limitations include:

* Incomplete Microsoft Office feature compatibility
* Limited support for advanced formatting and embedded objects
* Limited legacy .xls compatibility
* Browser-dependent saving behavior
* Browser-dependent fullscreen behavior
* Service-worker limitations under file://
* Limited automated validation outside Chromium
* No guarantee of recovery after every unexpected browser or operating-system termination
* Potential performance limitations with very large documents
* Partial support for fonts unavailable on the local system

See the project documentation and release notes for version-specific limitations.

Security

InkDesk does not intentionally execute macros, embedded JavaScript, remote Office instructions, or active content from imported documents.

Security-sensitive code should validate:

* ZIP entry paths
* Package size
* Entry count
* Compression ratios
* XML structure
* External URLs
* Imported HTML
* Message origins
* Object URLs
* Browser storage failures
* Unsupported or encrypted packages

Security issues should not be disclosed through public documents containing private user files.

Third-party libraries

Third-party libraries required by InkDesk are distributed locally so that the application can operate offline.

Their original license notices and attribution files must remain intact.

Dependencies should not be removed, updated, or replaced without confirming:

* Their actual use
* Their version
* Their license
* Offline compatibility
* Browser compatibility
* Security implications
* Regression-test results

Contributing

Contributions should be focused, reversible, and supported by testing.

A contribution should clearly describe:

1. The problem being corrected.
2. The affected files.
3. The practical consequence.
4. The proposed solution.
5. The regression risk.
6. The validation performed.

Unrelated changes should not be combined in the same pull request.

License

See the LICENSE file for the project license.

Third-party components may use different licenses. Their notices and attribution files remain applicable to those components.

Disclaimer

InkDesk is provided without a guarantee of complete document fidelity or compatibility with every Office file.

Users are responsible for maintaining backups and verifying exported files before relying on them for critical, legal, financial, medical, academic, or professional use.
