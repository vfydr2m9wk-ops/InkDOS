from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
HOST = (ROOT / 'desktop/desktop-host.js').read_text(encoding='utf-8')
MAIN = (ROOT / 'desktop/src-tauri/src/main.rs').read_text(encoding='utf-8')
WORKSPACES = json.loads((ROOT / 'desktop/workspaces.json').read_text(encoding='utf-8'))


def test_native_injection_selects_compatible_input_not_first_input():
    assert 'document.querySelectorAll(\'input[type="file"]\')' in HOST
    assert 'allowed.includes(extension)' in HOST
    assert 'const input = compatibleFileInput(file);' in HOST
    assert 'document.querySelector(\'input[type="file"]\')' not in HOST


def test_documents_image_input_precedes_document_input_regression_fixture():
    html = (ROOT / 'apps/documents/index.html').read_text(encoding='utf-8')
    assert html.index('id="imageInput"') < html.index('id="fileInput"')
    assert '.docx' in html[html.index('id="fileInput"'):html.index('id="fileInput"') + 300]


def test_desktop_routes_core_associated_formats_to_correct_workspaces():
    expected = {
        'documents': {'docx'},
        'spreadsheets': {'xls', 'xlsx'},
        'presentations': {'ppt', 'pptx'},
        'pdf': {'pdf'},
    }
    for workspace, extensions in expected.items():
        assert extensions <= set(WORKSPACES[workspace]['extensions'])
        route = WORKSPACES[workspace]['route']
        assert (ROOT / route).is_file()
    assert 'workspace_for_path(&path)' in MAIN
    assert 'open_file_window_at_route(app, &workspace, route, path)' in MAIN
    assert 'handle_launch_args(app.handle(), std::env::args())' in MAIN
    assert 'tauri_plugin_single_instance::init(|app, args, _cwd|' in MAIN


def test_associated_file_token_is_one_shot_and_handed_to_web_workspace():
    assert 'window.__INKDOS_OPEN_TOKEN__' in MAIN
    assert "core.invoke('inkdos_read_open_file', { token })" in HOST
    assert '.remove(&token)' in MAIN
    assert "input.dispatchEvent(new Event('change', { bubbles: true }))" in HOST
