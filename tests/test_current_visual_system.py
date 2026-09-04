from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAYERS = [
    ROOT / 'shared' / 'ui' / 'visual.css',
    ROOT / 'shared' / 'ui' / 'content.css',
    ROOT / 'shared' / 'ui' / 'workspace.css',
    ROOT / 'shared' / 'ui' / 'polish.css',
]


class CurrentVisualSystemTests(unittest.TestCase):
    def test_semantic_layers_replace_version_named_patch_stack(self):
        for path in LAYERS:
            self.assertTrue(path.is_file(), path)
            self.assertLessEqual(len(path.read_text(encoding='utf-8').splitlines()), 500, path)
        shell = (ROOT / 'shared' / 'office-shell.js').read_text(encoding='utf-8')
        positions = [shell.index(repr(path.name)) for path in LAYERS]
        self.assertEqual(positions, sorted(positions))
        for name in (
            'visual-foundation-' + 'v0203.css', 'content-workspaces-' + 'v02031.css',
            'workspace-unification-' + 'v02031.css', 'spreadsheets-' + 'beta1-polish.css',
            'light-' + 'only.css',
        ):
            self.assertFalse((ROOT / 'shared' / 'ui' / name).exists(), name)
            self.assertNotIn(name, shell)

    def test_layers_keep_cross_workspace_visual_contracts(self):
        css = '\n'.join(path.read_text(encoding='utf-8') for path in LAYERS)
        for marker in (
            'body.office-documents', 'body.office-spreadsheets',
            'body.office-presentations', 'body.office-pdf',
            'body.office-txt', 'body.office-epub',
            '#nameBox', '#sheetTabs > #addSheetBtn',
            'color-scheme: light !important',
        ):
            self.assertIn(marker, css)

    def test_inactive_future_theme_is_not_in_active_tree(self):
        self.assertFalse((ROOT / 'shared' / 'future').exists())
        worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
        self.assertNotIn('shared/future', worker)


if __name__ == '__main__':
    unittest.main()
