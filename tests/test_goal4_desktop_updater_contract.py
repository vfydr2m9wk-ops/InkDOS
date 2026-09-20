#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARGO = ROOT / "desktop" / "src-tauri" / "Cargo.toml"
MAIN = ROOT / "desktop" / "src-tauri" / "src" / "main.rs"
CONFIG = ROOT / "desktop" / "src-tauri" / "tauri.conf.json"
HOST = ROOT / "desktop" / "desktop-host.js"
WEB_HOME = ROOT / "index.html"

ENDPOINT = "https://github.com/vfydr2m9wk-ops/InkDOS/releases/latest/download/latest.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    cargo = CARGO.read_text(encoding="utf-8")
    rust = MAIN.read_text(encoding="utf-8")
    host = HOST.read_text(encoding="utf-8")
    web_home = WEB_HOME.read_text(encoding="utf-8")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))

    updater_dep = re.search(r'^tauri-plugin-updater\s*=\s*\"(?:=)?(2(?:\.\d+){0,2})\"$', cargo, re.M)
    require(updater_dep is not None, "Goal 4 must use a compatible official Tauri v2 updater plugin")
    require("use tauri_plugin_updater::UpdaterExt;" in rust, "Rust updater commands must use UpdaterExt")
    require("inkdos_check_for_updates" in rust, "manual update-check command is missing")
    require("inkdos_install_update" in rust, "explicit update-install command is missing")
    require("tauri_plugin_updater::Builder::new().build()" in rust, "updater plugin is not registered")
    require("tauri::generate_handler![" in rust and "inkdos_check_for_updates" in rust and "inkdos_install_update" in rust, "updater commands must be registered through the Tauri invoke handler")

    setup_match = re.search(r"\.setup\(\|app\|\s*\{(?P<body>.*?)\n\s*\}\)\s*\n\s*\.run", rust, re.S)
    require(setup_match is not None, "could not inspect Tauri startup setup block")
    setup_body = setup_match.group("body")
    require("updater().check" not in setup_body and "updater_builder" not in setup_body, "Goal 4 must not check for updates at startup")

    updater = config.get("plugins", {}).get("updater", {})
    require(updater.get("endpoints") == [ENDPOINT], "desktop updater must use the static HTTPS GitHub Releases endpoint")
    require(isinstance(updater.get("pubkey"), str) and updater.get("pubkey"), "updater configuration must fail closed with an explicit public-key value")
    require(updater.get("dangerousInsecureTransportProtocol") is not True, "insecure updater transport must not be enabled")

    require("Check for updates" in host, "desktop bridge must expose an explicit Check for updates control")
    require("inkdos_check_for_updates" in host, "desktop UI must invoke the manual check command")
    require("inkdos_install_update" in host, "desktop UI must invoke install only after confirmation")
    require("setInterval" not in host, "desktop updater must not poll")
    require("inkdos_check_for_updates" not in web_home and "latest.json" not in web_home, "web/PWA Home must not contain updater behavior")

    print("Goal 4 manual desktop updater contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
