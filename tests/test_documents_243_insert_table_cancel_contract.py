from pathlib import Path

EDITOR = Path('apps/documents/ui/editor-controller.js').read_text(encoding='utf-8')


def test_insert_table_cancel_is_non_mutating():
    assert "if(rowsInput===null)return" in EDITOR
    assert "if(colsInput===null)return" in EDITOR
    assert "prompt('Rows','3')" in EDITOR
    assert "prompt('Columns','3')" in EDITOR


def test_insert_table_only_dispatches_mutation_after_both_prompts_confirm():
    function = EDITOR.split('function insertTable(){', 1)[1].split('}\n function selectedCell', 1)[0]
    rows_cancel = function.index('if(rowsInput===null)return')
    cols_cancel = function.index('if(colsInput===null)return')
    mutation = function.index("cmd('insertHTML'")
    assert rows_cancel < cols_cancel < mutation
