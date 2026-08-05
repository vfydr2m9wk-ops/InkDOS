# Validation — 0.19.3-beta.7

Date: 2026-08-05

## Reproduced beta.6 failure

With normal Edge security settings and no automation bypass, opening `apps/pdf/index.html` through `file://` left `window.InkDeskPdfDebug` undefined. Edge reported that the module `app.js` was blocked by the opaque local origin. This matched the inactive **Open PDF** button and transfer-timeout screenshot.

## Corrective evidence

- Direct `file://` launch registered the **Open PDF** file chooser and opened the synthetic three-page PDF.
- The same run rendered 30 selectable text spans, five AcroForm controls and three outline entries without JavaScript errors.
- Hub-to-PDF transfer through the local iframe opened the PDF without a timeout dialog.
- The synthetic 4,000-page PDF opened directly from `file://`, jumped to page 3,500 and retained five full page canvases.
- Hub-to-Presentation transfer displayed the determinate opening overlay immediately, completed a two-slide PPTX and removed the overlay without errors.
- Pressing `=` on a selected spreadsheet cell focused the formula bar, displayed ten suggestions, and keyboard selection inserted `=AVERAGE(`.

Physical Safari/iPadOS, Firefox and embedded third-party hosts remain manual validation targets. Only synthetic fixtures were used.
