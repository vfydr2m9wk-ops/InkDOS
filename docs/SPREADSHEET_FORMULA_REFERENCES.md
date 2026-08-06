# Spreadsheet formula-reference selection

Development sequence `0.19.4.10` adds mouse, pointer, and touch-assisted cell
reference selection while a formula is being edited.

## Target cell preservation

The existing spreadsheet editor normally changes the active cell whenever a
grid cell receives a pointer-down event. It also refreshes the formula bar from
that newly active cell.

The formula-reference controller runs in the capture phase while the formula
bar contains a formula. It prevents the ordinary selection handler from
running, so:

- the formula target cell remains active;
- the name box keeps the target address;
- the formula text is not replaced by the clicked source cell;
- Enter commits through the editor's existing formula workflow.

The core spreadsheet application remains unchanged.

## Selection modes

### Single cell

Type or choose a formula, then click a cell:

```text
=ABS(B2)
```

### Dragged range

Type a function such as `=SUM(`, then drag from B2 to B12:

```text
=SUM(B2:B12)
```

The helper balances a missing closing parenthesis and leaves the caret before
that closing parenthesis.

### Discontinuous references

Hold Ctrl on Windows/Linux or Command on macOS while selecting another cell or
range:

```text
=SUM(B2:B12,D4,F7:F9)
```

Each retained reference uses a distinct outline.

### Touch fallback

The formula row exposes a `+ Range` button while formula-reference mode is
active. Pressing it makes the next cell or dragged range additive, without
requiring a hardware keyboard.

## Interaction

- Dragging updates the reference live in the formula bar.
- The target cell remains visually distinct from reference cells.
- Enter confirms the formula.
- Escape cancels formula editing through the existing editor behavior.
- The controller does not replace calculation, parsing, undo, export, or file
  lifecycle code.
- Formula suggestions remain available before range selection begins.

## Scope

This milestone does not add cross-workbook references, named-range creation,
structured-table formula authoring, or automatic formula translation.


## 0.19.4.10 persistent formula session

Reference selection now cooperates with the real in-cell draft session. A
single click, dragged range, successive click, Ctrl/Command selection, or the
touch Add Range control updates the formula draft without expanding the cell or
closing the editing session. Parentheses are balanced only when Enter confirms
the formula.
