"""Shared Playwright browser selection for InkDesk regression scripts."""
from __future__ import annotations

import os
from pathlib import Path

SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}


def selected_browser_name() -> str:
    name = os.environ.get("PLAYWRIGHT_BROWSER", "chromium").strip().lower()
    if name not in SUPPORTED_BROWSERS:
        raise RuntimeError(f"Unsupported PLAYWRIGHT_BROWSER value: {name}")
    return name


def launch_browser(playwright, *, headless: bool = True):
    """Launch a selected Playwright engine without mislabeling emulation as native testing."""
    name = selected_browser_name()
    browser_type = getattr(playwright, name)
    kwargs: dict[str, object] = {"headless": headless}
    if name == "chromium":
        configured = os.environ.get("CHROMIUM_PATH", "").strip()
        default_path = Path("/usr/bin/chromium")
        executable = Path(configured) if configured else default_path
        if executable.is_file():
            kwargs["executable_path"] = str(executable)
            kwargs["args"] = ["--no-sandbox"]
    return browser_type.launch(**kwargs)

