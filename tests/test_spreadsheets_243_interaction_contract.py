from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRID = (ROOT / 'apps/spreadsheets/view/grid-surface.js').read_text(encoding='utf-8')
UI = (ROOT / 'apps/spreadsheets/ui/editor-controller.js').read_text(encoding='utf-8')
ENGINE = (ROOT / 'apps/spreadsheets/engine/workbook-editor.js').read_text(encoding='utf-8')


def test_fill_handle_interaction_is_wired():
    assert "className='fill-handle'" in GRID
    assert 'onFill' in GRID
    assert 'editor.fillSelection' in UI


def test_fill_algorithm_has_copy_series_and_ctrl_inversion():
    assert 'fillSelection(target,ctrlKey=false)' in ENGINE
    assert "mode=ctrlKey?'copy':'series'" in ENGINE
    assert "seed.length===1" in ENGINE
    assert "Number.isFinite(step)" in ENGINE


def test_delete_and_backspace_clear_without_structural_delete():
    assert "e.key==='Delete'||e.key==='Backspace'" in UI
    assert "commands.execute('edit.clear')" in UI
    assert "mutate('Clear cells'" in ENGINE
    assert "cell.v=''" in ENGINE and "cell.f=''" in ENGINE


def test_fill_and_clear_are_single_history_mutations():
    assert "mutate('Fill cells'" in ENGINE
    assert "mutate('Clear cells'" in ENGINE
