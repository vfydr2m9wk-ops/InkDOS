from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "shared/ui/start-actions-unified.css"

TWO = {
    "documents": ("newWelcomeBtn", "open"),
    "spreadsheets": ("newEmptyBtn", "openEmptyBtn"),
    "presentations": ("newBtn", "openBtn"),
    "txt": ("newStartBtn", "openStartBtn"),
}
ONE = {"pdf": "openBtn", "epub": "openStartBtn"}
COLORS = {
    "documents": "#2f6fed",
    "spreadsheets": "#267a45",
    "presentations": "#d64a24",
    "pdf": "#b42318",
    "txt": "#d9a514",
    "epub": "#7655c7",
}

def soup(module):
    return BeautifulSoup((ROOT / f"apps/{module}/index.html").read_text(), "html.parser")

def text(el):
    return " ".join(el.stripped_strings)

def test_all_apps_load_shared_start_action_contract():
    for module in (*TWO, *ONE):
        html=(ROOT / f"apps/{module}/index.html").read_text()
        assert "../../shared/ui/start-actions-unified.css" in html

def test_two_action_apps_use_identical_labels_order_and_icons():
    for module,(new_id,open_id) in TWO.items():
        doc=soup(module)
        new=doc.find(id=new_id)
        # Documents uses a label tied to fileInput rather than an id for open.
        open_el=(doc.select_one('.inkdos-start-open') if module == 'documents' else doc.find(id=open_id))
        assert new and open_el
        assert text(new) == "+ New document"
        assert text(open_el) == "Open document"
        assert "inkdos-start-new" in new.get("class", [])
        assert "inkdos-start-open" in open_el.get("class", [])
        assert new.select_one('.inkdos-plus') is not None
        assert open_el.select_one('.inkdos-folder svg') is not None

def test_one_action_apps_expose_only_uniform_open_action():
    for module,open_id in ONE.items():
        doc=soup(module); open_el=doc.find(id=open_id)
        assert open_el
        assert text(open_el) == "Open document"
        assert "inkdos-start-open" in open_el.get("class", [])
        assert open_el.select_one('.inkdos-folder svg') is not None
        parent=open_el.find_parent(class_='inkdos-start-actions')
        assert parent and "inkdos-start-actions-single" in parent.get("class", [])
        assert parent.select_one('.inkdos-start-new') is None

def test_shared_css_preserves_current_app_colors_and_button_contrast():
    css=CSS.read_text()
    for module,color in COLORS.items():
        assert f"body.office-{module}" in css
        assert color in css
    assert "background:#fff!important" in css
    assert "color:#171b22!important" in css
    assert "background:var(--inkdos-start-accent)!important" in css
    assert "color:#fff!important" in css
