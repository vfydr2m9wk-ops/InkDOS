#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (ROOT / "apps/presentations/ui/command-controller.js").read_text(encoding="utf-8")
SAVE = (ROOT / "apps/presentations/io/save-controller.js").read_text(encoding="utf-8")


def test_presentations_has_three_way_unsaved_decision_contract():
    assert "Save" in COMMANDS and "Discard" in COMMANDS and "Cancel" in COMMANDS
    assert "decideUnsaved" in COMMANDS


def test_presentations_blocks_replacement_until_save_completes():
    assert "saveForReplacement" in SAVE
    assert "await save.saveForReplacement" in COMMANDS


def test_presentations_replacement_requires_confirmed_delivery():
    assert "delivery.deliveryConfirmed" in SAVE
    assert "Save delivery was not confirmed" in SAVE


def test_presentations_guards_home_and_browser_unload():
    assert "aria-label=\"Home\"" in (ROOT / "apps/presentations/index.html").read_text(encoding="utf-8")
    assert "beforeunload" in COMMANDS
    assert "homeLink" in COMMANDS


def test_presentations_authorized_home_exit_bypasses_native_beforeunload_prompt():
    assert "let authorizedUnload=false" in COMMANDS
    assert "if(await authorizeReplacement('leave')){authorizedUnload=true;global.location.assign(href)}" in COMMANDS
    assert "if(authorizedUnload){authorizedUnload=false;return}" in COMMANDS


if __name__ == "__main__":
    test_presentations_has_three_way_unsaved_decision_contract()
    test_presentations_blocks_replacement_until_save_completes()
    test_presentations_replacement_requires_confirmed_delivery()
    test_presentations_guards_home_and_browser_unload()
    test_presentations_authorized_home_exit_bypasses_native_beforeunload_prompt()
    print("Presentations unsaved-exit contract: OK")
