#!/usr/bin/env python3
"""Materialize lightweight macOS workspace launch entries for the single InkDOS host.

Each generated helper bundle contains only a tiny native launcher stub and an
ICNS derived from the canonical workspace icon. The stub execs the one InkDOS
host binary with ``--workspace <id>``; it never embeds or duplicates InkDOS.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TAURI_DIR = ROOT / "desktop" / "src-tauri"
LAUNCHERS_PATH = ROOT / "desktop" / "launchers.json"
OUTPUT_ROOT = TAURI_DIR / "macos" / "workspace-launchers"

DISPLAY_NAMES = {
    "documents": "Documents",
    "spreadsheets": "Spreadsheets",
    "presentations": "Presentations",
    "pdf": "PDF",
    "epub": "EPUB",
    "txt": "Plain Text",
}

LAUNCHER_SOURCE = r'''#include <libgen.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifndef WORKSPACE
#error WORKSPACE must be defined
#endif

int main(int argc, char **argv) {
    char executable_path[PATH_MAX];
    uint32_t executable_path_size = sizeof(executable_path);
    if (_NSGetExecutablePath(executable_path, &executable_path_size) != 0) {
        fprintf(stderr, "InkDOS launcher path is too long\n");
        return 70;
    }

    char path_copy[PATH_MAX];
    if (snprintf(path_copy, sizeof(path_copy), "%s", executable_path) >= (int)sizeof(path_copy)) {
        return 70;
    }

    char *launcher_dir = dirname(path_copy);
    char host_candidate[PATH_MAX];
    if (snprintf(host_candidate, sizeof(host_candidate), "%s/../../../../MacOS/InkDOS", launcher_dir) >= (int)sizeof(host_candidate)) {
        return 70;
    }

    char host[PATH_MAX];
    if (realpath(host_candidate, host) == NULL) {
        perror("Unable to locate the InkDOS host");
        return 72;
    }

    char **host_argv = calloc((size_t)argc + 3, sizeof(char *));
    if (host_argv == NULL) {
        return 71;
    }
    host_argv[0] = host;
    host_argv[1] = "--workspace";
    host_argv[2] = WORKSPACE;
    for (int i = 1; i < argc; ++i) {
        host_argv[i + 2] = argv[i];
    }
    host_argv[argc + 2] = NULL;

    execv(host, host_argv);
    perror("Unable to launch InkDOS");
    free(host_argv);
    return 72;
}
'''


def _plist(workspace: str, display_name: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDisplayName</key>
  <string>InkDOS {display_name}</string>
  <key>CFBundleExecutable</key>
  <string>launcher</string>
  <key>CFBundleIconFile</key>
  <string>icon.icns</string>
  <key>CFBundleIdentifier</key>
  <string>com.inkdos.desktop.launcher.{workspace}</string>
  <key>CFBundleName</key>
  <string>InkDOS {display_name}</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>2.3</string>
  <key>LSMinimumSystemVersion</key>
  <string>10.13</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
'''


def main() -> None:
    launchers = json.loads(LAUNCHERS_PATH.read_text(encoding="utf-8"))
    if set(launchers) != set(DISPLAY_NAMES):
        raise SystemExit("macOS launcher display-name map must match desktop/launchers.json")

    with tempfile.TemporaryDirectory(prefix="inkdos-macos-launchers-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        source_path = temp_dir / "launcher.c"
        source_path.write_text(LAUNCHER_SOURCE, encoding="utf-8")

        for workspace, launcher in launchers.items():
            if launcher["executable"] != "InkDOS" or launcher["args"] != ["--workspace", workspace]:
                raise SystemExit(f"Unexpected launcher authority for {workspace}")

            source_icon = ROOT / launcher["icon"]
            if not source_icon.is_file():
                raise SystemExit(f"Missing canonical workspace icon source: {source_icon}")

            display_name = DISPLAY_NAMES[workspace]
            app_dir = OUTPUT_ROOT / f"InkDOS {display_name}.app"
            contents_dir = app_dir / "Contents"
            if contents_dir.exists():
                shutil.rmtree(contents_dir)
            macos_dir = contents_dir / "MacOS"
            resources_dir = contents_dir / "Resources"
            macos_dir.mkdir(parents=True, exist_ok=True)
            resources_dir.mkdir(parents=True, exist_ok=True)

            icon_output = temp_dir / workspace
            subprocess.run(
                ["cargo", "tauri", "icon", str(source_icon), "--output", str(icon_output)],
                cwd=ROOT,
                check=True,
            )
            native_icon = icon_output / "icon.icns"
            if not native_icon.is_file():
                raise SystemExit(
                    f"Tauri icon generation did not produce macOS ICNS for {workspace}: {native_icon}"
                )
            shutil.copy2(native_icon, resources_dir / "icon.icns")

            launcher_binary = macos_dir / "launcher"
            subprocess.run(
                [
                    "clang",
                    "-Os",
                    f'-DWORKSPACE="{workspace}"',
                    str(source_path),
                    "-o",
                    str(launcher_binary),
                ],
                cwd=ROOT,
                check=True,
            )
            launcher_binary.chmod(0o755)
            (contents_dir / "Info.plist").write_text(
                _plist(workspace, display_name), encoding="utf-8"
            )

    print(f"Generated {len(launchers)} lightweight macOS workspace launch entries.")


if __name__ == "__main__":
    main()
