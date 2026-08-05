# InkDesk visual system

Development sequence `0.19.4.4` applies the first visible shared layout across
Documents, Spreadsheets, Presentations, and PDF.

The supplied Word, Excel, and PowerPoint screenshots are used as references for
hierarchy and placement. InkDesk does not copy Microsoft logos, proprietary
icons, trademarks, or visual assets.

## Common structure

The shared layer standardizes:

- a 44-pixel application title bar;
- predictable left, center, and right title-bar regions;
- consistent command-control sizes;
- common hover, focus, active, and disabled states;
- uniform surface, border, spacing, and status-bar tokens;
- module accent colors without changing the complete interface;
- bottom-right zoom placement where the workspace already supports zoom;
- content-first workspaces with optional panels consuming space only while open.

The implementation remains an overlay loaded by `shared/office-shell.js`.
Program-specific editing code is not moved or rewritten in this milestone.

## Default panel states

The first session opening uses:

| Workspace | Default |
| --- | --- |
| Documents navigation sidebar | Closed |
| Presentation thumbnails | Open |
| Presentation format inspector | Closed |
| Presentation presenter notes | Closed |

A user's explicit panel changes are remembered only for the current browser
session. Storage failures in direct-file or privacy modes are ignored safely.

## PDF empty state

The PDF start card and its `Open PDF` action are centered relative to the actual
start-screen content area. The home button remains anchored separately in the
upper-left corner.

The primary action does not use a fixed horizontal margin and remains centered
when the browser window changes size.

## Responsive behavior

At reduced widths:

- title regions shrink without moving global commands into the document area;
- command bars remain horizontally scrollable;
- presentation formatting stays closed;
- presentation thumbnails become narrower;
- labels on secondary presentation actions may collapse;
- touch targets grow on coarse-pointer devices.

## Deliberate limits

This milestone does not:

- introduce TXT or EPUB;
- change spreadsheet formula-selection behavior;
- redesign PDF annotation modes;
- create a pixel-perfect Microsoft Office clone;
- replace existing editor logic.

Those changes remain assigned to later ordered packages.
