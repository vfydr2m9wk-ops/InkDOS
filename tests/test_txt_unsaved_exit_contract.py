#!/usr/bin/env python3
from pathlib import Path

# Exact-state regression for destructive Plain Text navigation.
ROOT = Path(__file__).resolve().parents[1]
FILES = (ROOT / "apps/txt/io/txt-file-controller.js").read_text(encoding="utf-8")
CONTROLS = (ROOT / "apps/txt/ui/txt-controls.js").read_text(encoding="utf-8")
COMMANDS = (ROOT / "apps/txt/commands/txt-commands.js").read_text(encoding="utf-8")


def test_txt_has_three_way_unsaved_decision_contract():
    assert "decideUnsaved" in FILES
    assert "discardSave" in CONTROLS and "Save" in CONTROLS
    assert "resolveDiscard('save')" in CONTROLS
    assert "resolveDiscard('discard')" in CONTROLS
    assert "resolveDiscard('cancel')" in CONTROLS


def test_txt_blocks_replacement_until_exact_save_completes():
    assert "saveForReplacement" in FILES
    assert "await saveForReplacement()" in FILES
    assert "decision==='save'" in FILES
    assert "decision==='discard'" in FILES
    assert "decision==='cancel'" in FILES
    assert "state.session.revision!==snap.revision" in FILES
    assert "confirmedOnly" in FILES
    assert "receipt?.deliveryConfirmed" in FILES
    assert "Save delivery was not confirmed" in FILES
    assert "save({confirmedOnly:true})" in FILES
    assert "state.session.dirty=false" in FILES


def test_txt_guards_home_and_browser_unload():
    assert "file.leave" in COMMANDS
    assert "homeLink" in CONTROLS
    assert "beforeunload" in CONTROLS


def test_txt_authorized_home_exit_bypasses_only_the_followup_native_unload_guard():
    assert "authorizedUnload" in CONTROLS
    assert "if(ok){authorizedUnload=true;g.location.href=E.homeLink.href}" in CONTROLS
    assert "if(authorizedUnload)return" in CONTROLS
    assert CONTROLS.index("if(ok){authorizedUnload=true;g.location.href=E.homeLink.href}") < CONTROLS.index("if(authorizedUnload)return")
    assert "if(ok){authorizedUnload=true" in CONTROLS
    assert "if(!ok)authorizedUnload" not in CONTROLS


if __name__ == "__main__":
    test_txt_has_three_way_unsaved_decision_contract()
    test_txt_blocks_replacement_until_exact_save_completes()
    test_txt_guards_home_and_browser_unload()
    test_txt_authorized_home_exit_bypasses_only_the_followup_native_unload_guard()
    print("Plain Text unsaved-exit contract: OK")
