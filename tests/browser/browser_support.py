"""Shared Playwright browser selection for InkDOS browser regressions."""
from __future__ import annotations

import os
from pathlib import Path

SUPPORTED_BROWSERS = ("chromium", "firefox", "webkit")


def requested_browser_name() -> str:
    name = os.environ.get("INKDOS_BROWSER", "chromium").strip().lower()
    if name not in SUPPORTED_BROWSERS:
        raise RuntimeError(f"Unsupported INKDOS_BROWSER={name!r}; choose one of {SUPPORTED_BROWSERS}")
    return name


def launch_browser(playwright, **overrides):
    """Launch the requested Playwright engine with conservative CI defaults."""
    name = requested_browser_name()
    browser_type = getattr(playwright, name)
    options = {"headless": True}
    if name == "chromium":
        configured = os.environ.get("CHROMIUM_PATH", "").strip()
        fallback = Path("/usr/bin/chromium")
        if configured and Path(configured).is_file():
            options["executable_path"] = configured
        elif fallback.is_file():
            options["executable_path"] = str(fallback)
        options["args"] = ["--no-sandbox"]
    options.update(overrides)
    return browser_type.launch(**options)


def browser_is_installed(playwright, name: str) -> bool:
    if name == "chromium":
        configured = os.environ.get("CHROMIUM_PATH", "").strip()
        if configured and Path(configured).is_file():
            return True
        if Path("/usr/bin/chromium").is_file():
            return True
    executable = Path(getattr(playwright, name).executable_path)
    return executable.is_file()
