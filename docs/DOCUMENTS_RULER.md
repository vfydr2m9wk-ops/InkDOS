# Documents active-page ruler

Development sequence `0.19.4.7` replaces the fixed ruler presentation with a
page-aware ruler linked to the document currently visible or selected.

## Active page

The controller chooses the page containing the current text selection. When
there is no selection, it chooses the page with the largest visible area in the
Documents viewport.

The ruler updates when:

- the document is opened or repaginated;
- the visible page changes;
- the user changes zoom;
- Fit width is used;
- the sidebar changes the available viewport width;
- the viewport scrolls horizontally or vertically;
- the browser window changes size;
- a section with a different page width becomes active.

## Width and position

The ruler track uses the rendered width and horizontal position of the active
page. It is clipped by the ruler container, so horizontal document scrolling
moves the ruler together with the page rather than leaving it fixed in the
middle of the application.

The track reads the active page's computed left and right padding and displays
those areas as margin zones.

## Ticks and numbers

Ticks are generated as DOM elements at one-eighth-inch intervals using the
browser document convention of 96 CSS pixels per inch.

- major tick: one inch;
- half tick: one-half inch;
- quarter tick: one-quarter inch;
- minor tick: one-eighth inch.

Only major ticks receive numbers. The legacy pseudo-element containing one long
number string is disabled, preventing numbers from spilling into the lateral
application area.

## Indentation controls

The existing first-line, hanging, left-block, and right-indent handles remain
available. The shared controller intercepts their pointer interaction before
the legacy fixed-width conversion runs.

Pointer positions are converted through the active page's current zoom and
content width. The resulting paragraph styles use document pixels:

- `margin-left`;
- `text-indent`;
- `margin-right`.

The controller dispatches the existing Documents input event so dirty-state,
history, statistics, and export behavior remain under the editor's current
lifecycle.

## Scope

This milestone does not add vertical rulers, tab-stop editing, page-margin
editing, or print-layout redesign.
