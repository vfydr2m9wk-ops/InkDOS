# Project Status

InkDesk 0.19.0-beta is a **public beta** for focused, non-critical local Office workflows.

## Suitable current uses

- OOXML compatibility experiments;
- local and embedded editor prototypes;
- focused personal workflows where exported copies can be reopened and verified;
- community work on parsers, rendering, security limits, and regression fixtures.

## Not suitable without independent validation

- regulated, medical, legal, or financial production workflows;
- unattended conversion;
- documents requiring exact Microsoft Office formatting;
- files that depend on macros, SmartArt, advanced charts, embedded applications, proprietary fonts, external links, or exact pagination;
- deployments that have not been tested in their target browser/host.

## Current engineering priorities

1. native Safari/WebKit, iPadOS, Firefox, and embedded-host validation;
2. privacy-preserving crash/session recovery;
3. broader hostile-package and fuzz coverage;
4. incremental Presentation Workspace modularization;
5. compatibility improvements backed by redistributable fixtures.
