# UI Design System

## Control placement

Every editor follows the same primary title-bar pattern: New, Open, Undo, Redo, centered title and Save on the upper-right.

## Icons

Primary toolbar icons are inline SVG. External icon fonts and Unicode presentation symbols are avoided because some WebKit-based embedded web views display them as empty squares.

## Surfaces

The shared shell defines:

- subtle top-to-bottom gradients for title and tool bars;
- thin neutral borders;
- soft inset highlights;
- raised side-panel shadows;
- app accent colors: blue for Documents, green for Spreadsheets and orange for Presentations.

## App-specific exceptions

Presentations adds presentation actions to the upper-right before Save. Spreadsheets uses a fixed upper-right save container because the centered title is absolutely positioned. These exceptions are documented and tested to avoid title overlap.
