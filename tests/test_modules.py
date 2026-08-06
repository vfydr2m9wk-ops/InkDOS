from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_generator():
    path = ROOT / "scripts" / "generate_module_registry.py"
    spec = importlib.util.spec_from_file_location("inkdesk_module_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ModuleRegistryTests(unittest.TestCase):
    def test_module_registry_is_generated_and_current(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_module_registry.py"), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_required_modules_have_valid_manifests_and_direct_entries(self):
        config = json.loads((ROOT / "modules" / "module-config.json").read_text())
        self.assertEqual(config["schemaVersion"], 1)
        self.assertEqual(
            [item["id"] for item in config["modulePaths"]],
            ["documents", "spreadsheets", "presentations", "pdf", "txt"],
        )
        extensions = set()
        for item in config["modulePaths"]:
            manifest_path = ROOT / item["manifest"]
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["id"], item["id"])
            self.assertTrue((ROOT / manifest["entryPoint"]).is_file())
            self.assertTrue((ROOT / manifest["icon"]).is_file())
            self.assertTrue(manifest["enabled"])
            for extension in manifest["extensions"]:
                self.assertNotIn(extension, extensions)
                extensions.add(extension)
        self.assertEqual(extensions, {"docx", "xls", "xlsx", "pptx", "pdf", "txt"})

    def test_launcher_uses_registry_with_static_fallbacks(self):
        html = (ROOT / "index.html").read_text()
        registry_pos = html.index("./modules/module-registry.js")
        loader_pos = html.index("./modules/module-loader.js")
        router_pos = html.index("./shared/file-router.js")
        self.assertLess(registry_pos, loader_pos)
        self.assertLess(loader_pos, router_pos)
        self.assertIn("data-module-grid", html)
        for route in (
            "./apps/documents/index.html",
            "./apps/spreadsheets/index.html",
            "./apps/presentations/index.html",
            "./apps/pdf/index.html",
            "./apps/txt/index.html",
        ):
            self.assertIn(route, html)

    def test_disabled_and_missing_optional_modules_are_isolated(self):
        generator = load_generator()
        original_root = generator.ROOT
        try:
            import tempfile
            with tempfile.TemporaryDirectory(prefix="module-test-") as temp_name:
                root = Path(temp_name)
                (root / "modules").mkdir()
                (root / "apps" / "sample").mkdir(parents=True)
                (root / "apps" / "sample" / "index.html").write_text("<!doctype html>")
                (root / "assets").mkdir()
                (root / "assets" / "sample.png").write_bytes(b"PNG")
                manifest = {
                    "schemaVersion": 1,
                    "id": "sample",
                    "name": "Sample",
                    "description": "Synthetic module for registry tests.",
                    "version": "test",
                    "enabled": True,
                    "optional": False,
                    "order": 1,
                    "entryPoint": "apps/sample/index.html",
                    "icon": "assets/sample.png",
                    "badge": "S",
                    "themeClass": "sample",
                    "accent": "#123456",
                    "extensions": ["sample"],
                    "mimeTypes": ["application/x-sample"],
                    "capabilities": ["open"],
                }
                (root / "apps" / "sample" / "module.json").write_text(json.dumps(manifest))
                config = {
                    "schemaVersion": 1,
                    "registryVersion": "test",
                    "modulePaths": [
                        {
                            "id": "sample",
                            "manifest": "apps/sample/module.json",
                            "required": True,
                        },
                        {
                            "id": "missing",
                            "manifest": "apps/missing/module.json",
                            "required": False,
                        },
                    ],
                    "overrides": {"sample": {"enabled": False}},
                }
                config_path = root / "modules" / "module-config.json"
                config_path.write_text(json.dumps(config))
                generator.ROOT = root
                registry = generator.build_registry(config_path)
                self.assertFalse(registry["modules"][0]["enabled"])
                self.assertEqual(registry["missingModules"][0]["id"], "missing")
        finally:
            generator.ROOT = original_root

    def test_loader_runtime_filters_disabled_modules(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = """
require('./modules/module-registry.js');
require('./modules/module-loader.js');
if(globalThis.InkDeskModules.listEnabled().length!==5)process.exit(10);
const create=globalThis.InkDeskCreateModuleRuntime;
const runtime=create({registryVersion:'test',modules:[{
  schemaVersion:1,id:'sample',name:'Sample',description:'Sample module',
  version:'test',enabled:false,optional:true,order:1,
  entryPoint:'apps/sample/index.html',icon:'assets/sample.png',
  badge:'S',themeClass:'sample',accent:'#123456',
  extensions:['sample'],mimeTypes:['application/x-sample'],capabilities:['open']
}]});
if(runtime.listEnabled().length!==0)process.exit(11);
if(runtime.resolveExtension('sample')!==null)process.exit(12);
if(runtime.errors.length!==0)process.exit(13);
"""
        result = subprocess.run(
            [node, "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_service_worker_caches_module_foundation(self):
        worker = (ROOT / "service-worker.js").read_text()
        for path in (
            "./modules/module-registry.js",
            "./modules/module-loader.js",
            "./modules/module-config.json",
            "./modules/module-schema.json",
            "./apps/documents/module.json",
            "./apps/spreadsheets/module.json",
            "./apps/presentations/module.json",
            "./apps/pdf/module.json",
            "./apps/txt/module.json",
        ):
            self.assertIn(repr(path), worker)


if __name__ == "__main__":
    unittest.main()
