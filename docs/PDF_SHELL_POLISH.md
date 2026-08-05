# PDF shell polish

Development sequence `0.19.4.5` is a stabilization milestone before new
workspaces are added.

## Navigation panel

The PDF navigation panel now:

- opens closed when no session preference exists;
- contributes zero desktop grid width while closed;
- moves completely off-screen and becomes non-interactive on narrow screens;
- updates `aria-expanded` and `aria-hidden`;
- changes its title between Show and Hide navigation panel;
- remembers an explicit choice only for the current browser session;
- remains in the chosen state while a PDF is opened and rendered.

The shared workspace controller intercepts the legacy toggle in the capture
phase. This avoids two handlers toggling the same class in opposite directions.

## PDF identity

The PDF module uses one red accent (`#b42318`) in:

- module metadata;
- generated module registry;
- home launcher card;
- start-screen badge and primary action;
- active PDF commands;
- title badge and selected navigation items.

The document canvas remains neutral gray and white.

## Scope

This milestone does not yet change annotation geometry. Highlight, underline,
and comment selection based on actual PDF text remains assigned to
`0.19.4.6`, where it can be tested independently from shell behavior.
