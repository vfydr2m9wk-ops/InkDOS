#!/usr/bin/env python3
"""Generate the classic-script InkDOS module registry.

The browser registry is generated instead of fetched at runtime so the same
module discovery works on HTTPS, ordinary static servers, and direct file://
opening. Optional missing modules are isolated and reported without preventing
required workspaces from loading.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "modules" / "module-config.json"
DEFAULT_OUTPUT = ROOT / "modules" / "module-registry.js"
ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
EXT_RE = re.compile(r"^[a-z0-9]+$")


class ModuleRegistryError(RuntimeError):
    pass


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ModuleRegistryError(f"Required file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ModuleRegistryError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ModuleRegistryError(f"Expected a JSON object in {path}")
    return value


def repository_path(raw: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ModuleRegistryError("Repository paths must be non-empty strings")
    if "\\" in raw or raw.startswith("/") or ".." in Path(raw).parts:
        raise ModuleRegistryError(f"Unsafe repository path: {raw!r}")
    path = ROOT / raw
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ModuleRegistryError(f"Repository path escapes the project: {raw!r}") from exc
    return path


def string_list(value, field: str, *, pattern: re.Pattern[str] | None = None) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ModuleRegistryError(f"{field} must be a non-empty array")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ModuleRegistryError(f"{field} contains an invalid value")
        normalized = item.strip()
        if pattern and not pattern.fullmatch(normalized):
            raise ModuleRegistryError(f"{field} contains an invalid value: {item!r}")
        if normalized in result:
            raise ModuleRegistryError(f"{field} contains a duplicate value: {item!r}")
        result.append(normalized)
    return result


def validate_manifest(manifest: dict, expected_id: str, *, required: bool) -> dict:
    required_fields = {
        "schemaVersion", "id", "name", "description", "version", "enabled",
        "optional", "order", "entryPoint", "icon", "badge", "themeClass",
        "accent", "extensions", "mimeTypes", "capabilities"
    }
    missing = sorted(required_fields - set(manifest))
    if missing:
        raise ModuleRegistryError(
            f"Module {expected_id!r} is missing fields: {', '.join(missing)}"
        )
    if manifest["schemaVersion"] != 1:
        raise ModuleRegistryError(f"Module {expected_id!r} uses an unsupported schema")
    if manifest["id"] != expected_id or not ID_RE.fullmatch(str(manifest["id"])):
        raise ModuleRegistryError(f"Module ID mismatch or invalid ID: {expected_id!r}")
    for field in ("name", "description", "version", "entryPoint", "icon", "badge", "themeClass"):
        if not isinstance(manifest[field], str) or not manifest[field].strip():
            raise ModuleRegistryError(f"Module {expected_id!r} has invalid {field}")
    if not ID_RE.fullmatch(manifest["themeClass"]):
        raise ModuleRegistryError(f"Module {expected_id!r} has invalid themeClass")
    if not HEX_RE.fullmatch(str(manifest["accent"])):
        raise ModuleRegistryError(f"Module {expected_id!r} has invalid accent")
    if not isinstance(manifest["enabled"], bool) or not isinstance(manifest["optional"], bool):
        raise ModuleRegistryError(f"Module {expected_id!r} has invalid boolean fields")
    if required and manifest["optional"]:
        raise ModuleRegistryError(f"Required module {expected_id!r} cannot declare optional=true")
    if not isinstance(manifest["order"], int) or manifest["order"] < 0:
        raise ModuleRegistryError(f"Module {expected_id!r} has invalid order")
    manifest = dict(manifest)
    manifest["extensions"] = string_list(
        manifest["extensions"], f"{expected_id}.extensions", pattern=EXT_RE
    )
    manifest["mimeTypes"] = string_list(manifest["mimeTypes"], f"{expected_id}.mimeTypes")
    manifest["capabilities"] = string_list(
        manifest["capabilities"], f"{expected_id}.capabilities", pattern=ID_RE
    )
    entry = repository_path(manifest["entryPoint"])
    icon = repository_path(manifest["icon"])
    if manifest["enabled"] and not entry.is_file():
        raise ModuleRegistryError(
            f"Enabled module {expected_id!r} entry point is missing: {manifest['entryPoint']}"
        )
    if manifest["enabled"] and not icon.is_file():
        raise ModuleRegistryError(
            f"Enabled module {expected_id!r} icon is missing: {manifest['icon']}"
        )
    return manifest


def build_registry(config_path: Path = DEFAULT_CONFIG) -> dict:
    config = read_json(config_path)
    if config.get("schemaVersion") != 1:
        raise ModuleRegistryError("Unsupported module configuration schema")
    registry_version = config.get("registryVersion")
    paths = config.get("modulePaths")
    overrides = config.get("overrides", {})
    if not isinstance(registry_version, str) or not registry_version:
        raise ModuleRegistryError("module-config.json requires registryVersion")
    if not isinstance(paths, list) or not paths:
        raise ModuleRegistryError("module-config.json requires modulePaths")
    if not isinstance(overrides, dict):
        raise ModuleRegistryError("module-config.json overrides must be an object")

    modules: list[dict] = []
    missing: list[dict] = []
    seen_ids: set[str] = set()
    seen_extensions: dict[str, str] = {}

    for item in paths:
        if not isinstance(item, dict):
            raise ModuleRegistryError("modulePaths entries must be objects")
        module_id = item.get("id")
        manifest_rel = item.get("manifest")
        required = item.get("required")
        if not isinstance(module_id, str) or not ID_RE.fullmatch(module_id):
            raise ModuleRegistryError(f"Invalid configured module ID: {module_id!r}")
        if module_id in seen_ids:
            raise ModuleRegistryError(f"Duplicate configured module ID: {module_id}")
        seen_ids.add(module_id)
        if not isinstance(required, bool):
            raise ModuleRegistryError(f"Module {module_id!r} requires a boolean required flag")
        manifest_path = repository_path(manifest_rel)
        if not manifest_path.is_file():
            if required:
                raise ModuleRegistryError(f"Required module manifest is missing: {manifest_rel}")
            missing.append({"id": module_id, "manifest": manifest_rel})
            continue

        manifest = validate_manifest(read_json(manifest_path), module_id, required=required)
        override = overrides.get(module_id, {})
        if not isinstance(override, dict):
            raise ModuleRegistryError(f"Override for {module_id!r} must be an object")
        unknown = set(override) - {"enabled", "order"}
        if unknown:
            raise ModuleRegistryError(
                f"Override for {module_id!r} has unsupported fields: {', '.join(sorted(unknown))}"
            )
        if "enabled" in override:
            if not isinstance(override["enabled"], bool):
                raise ModuleRegistryError(f"Override enabled for {module_id!r} must be boolean")
            manifest["enabled"] = override["enabled"]
        if "order" in override:
            if not isinstance(override["order"], int) or override["order"] < 0:
                raise ModuleRegistryError(f"Override order for {module_id!r} must be non-negative")
            manifest["order"] = override["order"]

        for extension in manifest["extensions"]:
            owner = seen_extensions.get(extension)
            if owner:
                raise ModuleRegistryError(
                    f"Extension {extension!r} is claimed by both {owner!r} and {module_id!r}"
                )
            seen_extensions[extension] = module_id
        modules.append(manifest)

    modules.sort(key=lambda item: (item["order"], item["name"].casefold(), item["id"]))
    return {
        "schemaVersion": 1,
        "registryVersion": registry_version,
        "modules": modules,
        "missingModules": missing
    }


def render_registry(registry: dict) -> str:
    data = json.dumps(registry, indent=2, ensure_ascii=False)
    return (
        "(function(global){\n"
        "'use strict';\n"
        f"const registry={data};\n"
        "global.InkDOSModuleRegistry=Object.freeze(registry);\n"
        "})(typeof window!=='undefined'?window:globalThis);\n"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        rendered = render_registry(build_registry(args.config))
        if args.check:
            current = args.output.read_text(encoding="utf-8") if args.output.is_file() else ""
            if current != rendered:
                print("ERROR: generated module registry is out of date.", file=sys.stderr)
                return 1
            print("OK: generated module registry is current.")
            return 0
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"OK: generated {args.output.relative_to(ROOT)}.")
        return 0
    except (ModuleRegistryError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
