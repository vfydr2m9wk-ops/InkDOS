# Testing Guide

Every meaningful change requires repository validation, privacy audit, unit tests and browser regressions.

## Commands

```bash
npm run validate
npm run audit
npm test
npm run test:browser
npm run test:release
```

## Current automated coverage

- version, route, service-worker and local-reference consistency;
- absence of stale release assets and exact duplicate files;
- anonymized Office/PDF fixture metadata;
- DOCX A4/header/footer/table parsing;
- BIFF8 XLS borders, merges and sheet-level hidden-zero behavior;
- PPTX direct background images and slide tables;
- local PDF object-URL preview;
- deterministic release ZIP generation.

Real private samples are opened only from outside the repository and are never copied into the source or release package.
