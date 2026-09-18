from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "apps/documents/index.html").read_text(encoding="utf-8")
EDITOR = (ROOT / "apps/documents/ui/editor-controller.js").read_text(encoding="utf-8")
COMMANDS = (ROOT / "apps/documents/ui/command-controller.js").read_text(encoding="utf-8")
D1 = (ROOT / "apps/documents/ui/d1-tools.js").read_text(encoding="utf-8")
D2 = (ROOT / "apps/documents/ui/d2-tools.js").read_text(encoding="utf-8")
CSS = (ROOT / "apps/documents/ui/editor.css").read_text(encoding="utf-8")

TRANSIENT_EVENT = "inkdos:documents-transient-open"


def test_all_documents_transients_share_one_exclusivity_protocol():
    assert TRANSIENT_EVENT in COMMANDS
    assert TRANSIENT_EVENT in D1
    assert TRANSIENT_EVENT in D2
    assert "announceOpen('general')" in COMMANDS
    assert "announceOpen('context')" in COMMANDS
    assert "announceOpen('zoom')" in COMMANDS
    assert "owner:'d1'" in D1
    assert "owner:'d2'" in D2


def test_formatting_toggle_state_is_accessible_and_visually_latched():
    for command in ("bold", "italic", "underline"):
        needle = f'data-cmd="{command}" aria-pressed="false"'
        assert needle in INDEX
    assert "document.queryCommandState(command)" in COMMANDS
    assert "button.setAttribute('aria-pressed'" in COMMANDS
    assert "button.classList.toggle('is-active'" in COMMANDS
    assert '.fmt-btn[aria-pressed="true"]' in CSS


def test_saved_selection_preserves_reverse_direction():
    assert "savedBackward" in EDITOR
    assert "selectionIsBackward(sel)" in EDITOR
    assert "sel.setBaseAndExtent(r.endContainer,r.endOffset,r.startContainer,r.startOffset)" in EDITOR


def test_insert_table_cancel_guards_precede_mutation():
    function = EDITOR.split("function insertTable(){", 1)[1].split("}\n function selectedCell", 1)[0]
    rows_cancel = function.index("if(rowsInput===null)return")
    cols_cancel = function.index("if(colsInput===null)return")
    mutation = function.index("cmd('insertHTML'")
    assert rows_cancel < cols_cancel < mutation


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("Documents 2.4.3 interaction source contract: OK")
