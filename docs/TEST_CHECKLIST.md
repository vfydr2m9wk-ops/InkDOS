# Test Checklist

## Package and launchers

- [ ] Open `Office Suite.html`; all three cards load the correct application.
- [ ] Open each direct launcher from the package root.
- [ ] Confirm no launcher requires browsing into a versioned internal folder.

## Shared title bars

- [ ] New and Open appear on the upper-left.
- [ ] Undo and Redo follow Open.
- [ ] The document name is centered.
- [ ] Save appears on the upper-right and does not overlap the title.
- [ ] SVG icons render as icons rather than empty squares.

## Documents

- [ ] Create a new document and type text.
- [ ] Test undo/redo, formatting, lists, image insertion and tables.
- [ ] Open a DOCX and save a DOCX copy.
- [ ] Confirm the unsaved-change close warning.

## Spreadsheets

- [ ] Create a new workbook.
- [ ] Confirm the save icon is at the far upper-right, not beside the centered title.
- [ ] Enter values and formulas; test selection, formatting and row/column operations.
- [ ] Switch between Sheet and Page modes.
- [ ] Save an XLSX copy and reopen it.

## Presentations

- [ ] Create a new presentation and add slides.
- [ ] Open a modern PPTX and an older PPTX.
- [ ] In the Present tab, confirm both **From first slide** and **From current slide** are visible and labeled.
- [ ] Confirm the primary presentation button is orange with a visible play icon and text.
- [ ] Test presentation from the first and current slide.
- [ ] Confirm only one Exit control is shown during presentation.
- [ ] Test arrow keys, Space, Enter, click/tap and swipe navigation.
- [ ] Confirm editor placeholders and selection handles do not appear in presentation mode.

## Regression

- [ ] Documents and Spreadsheets core document engines behave as in the previous stable package.
