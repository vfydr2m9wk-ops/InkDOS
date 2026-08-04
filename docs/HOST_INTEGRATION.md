# Host Integration Boundary

The core project is a static web application. Native integration is optional and host-specific.

## Core responsibilities

The core runtime owns:

- editor UI;
- in-browser parsing and rendering;
- download-based copy export;
- relative application entry points.

## Optional host responsibilities

A native or embedded host may provide:

- managed installation directories;
- launcher icons;
- native file pickers;
- direct save or autosave;
- fullscreen control;
- recent files;
- platform permissions.

## Bridge rule

A bridge is considered implemented only when it calls a documented host API and has an observable test. Empty methods, mock success responses and comments describing future native work must not be presented as working integration.

The core app must continue to work without a bridge, using browser file selection and downloaded copy export.
