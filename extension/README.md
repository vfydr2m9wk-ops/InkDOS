# InkDOS browser extension (beta)

A thin compatibility layer for Chrome, Edge, Brave and other Chromium browsers. It adds no copy of the apps and needs no build step: it opens the hosted InkDOS web apps (https://vfydr2m9wk-ops.github.io/InkDOS/) and hands them files from links, so it follows every InkDOS web update automatically.

## What it does

- **Toolbar button**: opens InkDOS.
- **PDFs open in InkDOS instead of the browser's PDF viewer**: clicking a PDF link or opening a PDF in a tab goes straight to the InkDOS PDF workspace. If InkDOS cannot fetch it, the page offers "Open in the browser instead".
- **Downloads open in InkDOS**: downloading a DOCX, DOC, RTF, XLSX, XLS, CSV, TSV, PPTX, PPT, PDF or EPUB opens it in InkDOS instead of saving it. Text and data files, files over 40 MB and files InkDOS itself saves download as usual.
- Both behaviors are on by default and can be turned off in the extension's **Options** (right-click the toolbar icon → Options, or Extensions → InkDOS → Extension options).
- **Right-click a link → "Open with InkDOS"**: on links to supported files (DOCX, DOC, RTF, XLSX, XLS, CSV, TSV, PPTX, PPT, PDF, EPUB, TXT, MD, JSON, XML, YAML, …) and on Google Drive / Google Docs links.
- **Right-click a Google Drive file page or a Google Docs, Sheets or Slides editor → "Open this file in InkDOS"**.
  - Drive files open as they are.
  - Google Docs, Sheets and Slides open as a DOCX, XLSX or PPTX copy.

The file is downloaded with the browser's own session, so anything you can open while signed in to Google (or another site) can be opened, and nothing passes through a third-party server. The extension routes the file with the same rules as InkDOS Home and passes it to the workspace through the same launch path the operating system uses. The workspaces are unchanged.

Saving goes to your computer (Save / Save a copy). Writing back to Google Drive would need the Google Drive API and an OAuth client registered by the owner; it is not part of this layer. With Google Drive for desktop, saving into the synced Drive folder uploads the file automatically.

## Install (unpacked, no account needed)

1. Download this repository (Code → Download ZIP) and extract it, or clone it.
2. Open `chrome://extensions` (Edge: `edge://extensions`), turn on **Developer mode**.
3. Click **Load unpacked** and choose the `extension` folder.
4. Pin the InkDOS icon to the toolbar.

Chromium shows a reminder for unpacked extensions at startup. Publishing to the Chrome Web Store removes it; that requires a Chrome Web Store developer account.

## Permissions

- `contextMenus`: the "Open with InkDOS" menu items.
- `downloads`: open downloaded documents in InkDOS (the download is paused while its name and type are checked, then cancelled or resumed).
- `declarativeNetRequestWithHostAccess`: one rule that sends tabs whose response is a PDF (GET only) to the InkDOS PDF workspace instead of the browser's viewer.
- `storage`: remembers the two options.
- Access to all sites (`<all_urls>`): needed to download the file behind a link you choose, with your session, from whatever site hosts it. The extension only downloads when you pick the menu item, and only runs its bridge scripts on the InkDOS workspace pages.

## Files

- `manifest.json`: Manifest V3.
- `background.js`: menus, format routing, Drive/Docs download mapping, file download.
- `open.html`, `open.js`: the short page a redirected PDF passes through on its way to InkDOS.
- `options.html`, `options.js`: the two options.
- `bridge-isolated.js`, `bridge-main.js`: on the InkDOS workspace page, receive the file and hand it to the workspace launch bridge (`InkDOSFileLaunch.routeFile`).
- `icons/inkdos.png`: the InkDOS icon.

Test: `python tests/test_extension_bridge_browser.py` loads the extension into Chromium and opens linked files, PDFs opened in a tab and downloads end to end.
