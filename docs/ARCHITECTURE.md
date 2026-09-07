# InkDOS 2.0.3 architecture

Home is a small launcher for six independent apps. It owns no document session, editor, shared file router or cross-app engine. Integration is ordinary navigation to each `apps/<app>/index.html` and back to Home.

Every app retains its own runtime, UI, IO, state, view and vendor dependencies. Deliberate duplication is preserved for failure isolation. The five pre-existing app trees are byte-identical to 2.0.2.

## PDF physical ownership

| Location within apps/pdf | Responsibility |
| --- | --- |
| runtime/frame/ | App frame, menu and chrome styles |
| runtime/platform/ | ContentViewport measurement |
| runtime/tokens/ | App-local visual tokens |
| engine/ | PDF geometry policy and document session |
| view/ | Page scheduling, canvas rendering, layout and zoom |
| pdfjs/ | Native annotation/editor/text-layer adapters |
| extensions/ | Highlight, underline and comment records |
| io/ | Local file opening, worker setup, copy validation and delivery |
| state/ | App appearance preference |
| modes/, ui/ | View/Annotate mode and tool/navigation controls |
| vendor/pdfjs/ | App-private pinned display engine and worker |
| app.js | Composition of private app instances |
| index.html | Entry markup, Home anchor and first-open presentation |

These are separate files loaded by the PDF entry, not headings inside a shared suite engine. PDF runtime resources resolve entirely inside its own directory. The only upward navigation is the Home anchor. Direct entry to the PDF app does not require loading Home or any sibling app. Browser policies still determine whether multi-file apps may run under file://; a local/static HTTP host is supported.

## Frozen integration boundary

SOURCE_LOCK.json preserves all existing app locks and adds the PDF hashes. Compared with the user-accepted P4.2 app source, the distribution removes only its internal global instance-inspection hook from app.js. The entry index adds a Home anchor and an EPUB-style one-button startup card. No PDF engine, annotation, saving, viewport or toolbar module is modified by this integration.

## First-open contract

Documents, Spreadsheets, Presentations and Plain Text have New/Open. EPUB and PDF use one centered Open action. PDF's card uses app-local red theme tokens. File picker cancellation or invalid input retains the card; the app's committed title update dismisses it after successful opening. Home remains a six-card grid with the existing mobile single-column behavior.
