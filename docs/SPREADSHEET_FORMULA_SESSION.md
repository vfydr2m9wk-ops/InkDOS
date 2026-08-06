# Persistent spreadsheet formula session

Development sequence `0.19.4.10` replaces the wide floating cell input from
`0.19.4.9` with a persistent draft session inside the real grid cell.

## Normal cell dimensions

A formula draft uses the selected cell's existing `contenteditable` surface.
The cell keeps its original row height and column width, clips long text, and
mirrors the complete formula in the formula bar.

## Drafts survive cell changes

An incomplete formula is stored by worksheet and cell reference for the current
page session. A user may type `=S` in C1, select A1 and enter a number, return to
C1, and continue the draft. Grid rerenders reapply the visible draft.

A click on another cell has two meanings:

- before the formula expects a reference, the draft is suspended and the new
  cell can be edited normally;
- after an operator or an open function parenthesis, the click becomes a formula
  reference without changing the target cell.

## Suggestions

Suggestions appear only after two function letters at a valid function boundary:

- `=`: no list;
- `=S`: no list;
- `=SU`: SUM suggestions;
- `=SUM(A`: no AVERAGE suggestion.

Tab or pointer click accepts a suggestion. Enter confirms the formula.

## References

After `=SUM(`, clicking A1 inserts A1. Clicking B1 next inserts `,B1` without
requiring Ctrl. Pointer dragging inserts a range such as `A1:A10`. Ctrl/Command
and the touch `+ Range` control remain available.

## Operators

The arithmetic engine supports `+`, `-`, `*`, `/`, `^`, parentheses, and
postfix percentage. `10%` evaluates to `0.1`; remainder remains available as
`MOD(number, divisor)`.
