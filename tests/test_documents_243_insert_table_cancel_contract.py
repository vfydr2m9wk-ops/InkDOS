from pathlib import Path

EDITOR = Path('apps/documents/ui/editor-controller.js').read_text(encoding='utf-8')


def test_insert_table_cancel_is_non_mutating():
    function = EDITOR.split('function insertTable(){', 1)[1].split('}\n function selectedCell', 1)[0]
    assert "dialog.ask(" in function
    assert "if(input===null)return" in function
    assert "{name:'rows',label:'Rows',value:'3'" in function
    assert "{name:'cols',label:'Columns',value:'3'" in function
    assert "prompt(" not in function.replace('dialog.ask(', '')


def test_insert_table_only_dispatches_mutation_after_dialog_confirms():
    function = EDITOR.split('function insertTable(){', 1)[1].split('}\n function selectedCell', 1)[0]
    ask = function.index('dialog.ask(')
    cancel = function.index('if(input===null)return')
    mutation = function.index("cmd('insertHTML'")
    assert ask < cancel < mutation
