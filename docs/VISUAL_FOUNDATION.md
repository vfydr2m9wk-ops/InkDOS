# InkDesk visual foundation

Development sequence `0.19.4.11` establishes the visual language that current
and future workspaces share.

## Typography

The interface uses the operating system's native human-interface font first:

```text
-apple-system, BlinkMacSystemFont, SF Pro Text, SF Pro Display,
Segoe UI Variable Text, Segoe UI, system-ui, sans-serif
```

Apple platforms therefore use their native San Francisco family without
bundling or redistributing Apple font files. Windows and other platforms use
compatible system fonts.

## Buttons

All workspace buttons use the same rounded geometry and interaction language:

- default raised surface;
- slight upward movement on hover;
- small color shift for selected controls;
- downward movement and reduced shadow while pressed;
- consistent disabled opacity;
- larger touch targets on coarse-pointer devices.

Open and New actions on Documents, Spreadsheets, Presentations, and PDF use a
shared 50-pixel height, 210-pixel minimum width, 15-pixel radius, and identical
spacing.

## Rounded surfaces

Start cards, dialogs, save panels, form fields, dropdowns, tab controls, and
other interactive surfaces use larger radii to move InkDesk away from rigid
traditional office chrome.

## Retractable panels

Documents and PDF sidebars, Presentation thumbnails, the Presentation format
inspector, and presenter notes use raised shadows, rounded inner corners, and a
small illuminated edge grip. This gives open/retractable panels the appearance
of a three-dimensional tab attached to the workspace.

## Scope

The milestone changes shared visual behavior without replacing document,
spreadsheet, presentation, or PDF editing logic.
