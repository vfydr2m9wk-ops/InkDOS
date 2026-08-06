# Spreadsheet in-cell formula editor

Development sequence `0.19.4.9` corrects formula authoring before the TXT
workspace is added.

## Starting from the selected cell

With a cell selected:

- typing `=` opens a formula input over that cell;
- `F2` opens the current cell value or formula;
- double-clicking a cell opens the same editor.

The in-cell editor and the formula bar are synchronized. Reference selection
continues to use the modular `formula-reference.js` controller, while the core
spreadsheet `app.js` remains unchanged.

## Suggestions

Suggestions follow these keyboard rules:

- Arrow Up and Arrow Down move through visible suggestions.
- Tab accepts the highlighted function.
- Pointer click accepts a function.
- Enter always confirms the formula.
- Escape closes suggestions first; a second Escape cancels editing.

The list is limited to six items.

A one-letter token inside a function argument is treated as the probable start
of a cell reference. Therefore:

```text
=SUM(A
```

does not select `AVERAGE`. Once the user types two letters in a valid nested
function position, matching nested functions may be shown.

## References and confirmation

Range selection no longer inserts a closing parenthesis during pointer drag:

```text
=SUM(
drag B2:B12
=SUM(B2:B12
```

Enter balances missing closing parentheses and then commits through the
existing spreadsheet editor:

```text
=SUM(B2:B12)
```

Ctrl/Command discontinuous references and the touch `+ Range` button remain
available.

## Formula bar layout

The formula row grows from 36 to 46 pixels. The formula input receives the
remaining horizontal width. Guidance moves to the bottom status bar so the
formula row contains only:

- cell address;
- `fx`;
- formula input;
- contextual `+ Range`.

## Scope

This milestone does not replace the calculation engine, workbook model, undo
history, XLS/XLSX import, or XLSX export.
