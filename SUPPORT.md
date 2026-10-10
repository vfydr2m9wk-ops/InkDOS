# Support policy

InkDOS is maintained for **Chromium-based browsers (Chrome, Edge)** and **iOS/iPadOS WebKit (Safari, XeOS)**, plus the
Windows app, which runs on Chromium (WebView2).

## Why Firefox was dropped (2026-10-10)

InkDOS is a small personal project. Testing and fixing every change in a third browser engine (Gecko) multiplied the
CI time and the fixes needed, for an engine its owner does not use. From 2026-10-10 the CI, the tests and the audits
run only in Chromium and WebKit. Firefox may still work, but it is not tested and its issues are not fixed.

## Why there are no published versions

The versions published on GitHub until 2.9.0 no longer reflected the project, so their tags and releases were removed
to keep people from downloading them. Their notes and small files are kept in the
[`legacy` branch](https://github.com/vfydr2m9wk-ops/InkDOS/tree/legacy/releases), which also keeps the project as it
was before Firefox was dropped. The web app (https://vfydr2m9wk-ops.github.io/InkDOS/) always has the current version.
