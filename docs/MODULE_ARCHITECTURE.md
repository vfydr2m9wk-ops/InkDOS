# InkDOS module architecture

InkDOS 0.19.4.2 introduces the module-discovery foundation without rewriting
the existing workspaces. Documents, Spreadsheets, Presentations, and PDF retain
their direct HTML entry pages and current internal behavior.

## Files

- `apps/<module>/module.json` describes one workspace.
- `modules/module-config.json` defines discovery order, required modules, and
  small enable/order overrides.
- `modules/module-schema.json` documents the manifest contract.
- `scripts/generate_module_registry.py` validates manifests and creates the
  direct-file-compatible browser registry.
- `modules/module-registry.js` is the generated classic-script registry.
- `modules/module-loader.js` exposes the runtime API and renders the home cards.

The JavaScript registry is generated rather than fetched at startup. Browsers
commonly restrict local JSON requests from `file://`, while an ordinary classic
script can still load. This preserves the direct-file workflow.

## Runtime API

`window.InkDOSModules` provides:

- `list()` — all valid registered modules.
- `listEnabled()` — enabled modules in display order.
- `get(id)` and `isEnabled(id)`.
- `resolveExtension(extension)` and `resolveFile(file)`.
- `buildAccept()` for the shared file picker.
- `errors` and `missingModules` for isolated discovery failures.

If the generated registry or loader fails, the static launcher cards remain in
the HTML. Workspace pages such as `apps/documents/index.html` and
`apps/documents/index.html` are not removed.

## Disable a module

Add an override to `modules/module-config.json`:

```json
{
  "overrides": {
    "pdf": {
      "enabled": false
    }
  }
}
```

Then regenerate and validate:

```text
python3 scripts/generate_module_registry.py
python3 scripts/generate_module_registry.py --check
```

A disabled module is not shown on the generated launcher and its extensions are
removed from the shared file picker's generated accept list. Its direct page is
kept so disabling the launcher does not delete code.

## Add an optional module

1. Create `apps/<id>/module.json` and its entry page.
2. Add its manifest path to `modulePaths`.
3. Use `"required": false` while the module is optional.
4. Regenerate the registry.
5. Add the runtime files to the service-worker shell when offline installation
   is expected.

A missing optional manifest is recorded in `missingModules`; it does not prevent
the other workspaces from loading. A missing required manifest stops registry
generation and therefore fails validation.

## Scope of this milestone

This milestone does not introduce the shared visual shell, TXT, EPUB, formula
reference selection, or the new PDF interaction modes. Those remain assigned to
later ordered packages.
