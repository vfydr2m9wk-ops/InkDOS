# InkDesk v0.20.2.6 — Presentations Slideshow Decomposition

Released: 2026-08-07

This patch is the fourth behavior-neutral Presentations decomposition step. It
moves slideshow/presentation-mode lifecycle, slide navigation, presentation
counter/help state, pointer gestures and Fullscreen API handling out of the
monolithic `apps/presentations/app.js`.

## Architecture changes

- Added `apps/presentations/presentation/slideshow-controller.js` as the owner
  of presentation-mode entry/exit, from-start/from-current actions, keyboard
  navigation, pointer/tap navigation, slide fitting and transition animation.
- Moved Fullscreen API state and fallback messaging into the slideshow
  controller while preserving presentation mode when full screen is unavailable
  or blocked by the host browser/web view.
- Kept transition editing in `app.js`; the new component consumes the current
  transition as an explicit dependency and does not change PPTX semantics.
- Added the slideshow controller to the offline shell and every browser harness
  that manually loads the Presentations runtime.
- Lowered the `apps/presentations/app.js` architecture ratchet again.

## Behavior contract

No visual redesign, new editing command, PPTX format change, save behavior,
recovery format or default panel state is intended. Existing Inspector,
thumbnails, presenter notes, selection and history components retain their
responsibilities.

The Presentations browser regression now explicitly checks presentation mode
from the current slide and from the first slide, slide counter updates, Home,
End, ArrowLeft, ArrowRight and Escape behavior, and the visible Exit control.
The browser test intentionally validates the non-fullscreen fallback path so it
does not depend on headless Fullscreen API policy.

## Scope

This remains a beta architecture-refactor patch. The next bounded Presentations
step should isolate file I/O/save/recovery responsibilities without combining
that work with UI or format-fidelity changes.
