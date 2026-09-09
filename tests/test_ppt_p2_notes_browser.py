#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8787
BASE = f"http://127.0.0.1:{PORT}"


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1360, "height": 900})
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on(
                "console",
                lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None,
            )
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.p2Tools")
            page.click("#startNew")
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.active && "
                "globalThis.__inkdosPresentations.hasCommand('slide.notes.set')"
            )

            probe = page.evaluate(
                """() => ({
                    commands: globalThis.__inkdosPresentations.listCommands(),
                    button: !!document.getElementById('pptP2NotesBtn'),
                    panel: !!document.getElementById('pptP2NotesPanel'),
                    binding: document.getElementById('pptP2NotesInput')?.dataset.command || null
                })"""
            )
            assert "slide.notes.set" in probe["commands"], probe
            assert probe["button"] and probe["panel"], probe
            assert probe["binding"] == "slide.notes.set", probe

            page.click("#pptP2NotesBtn")
            page.fill("#pptP2NotesInput", "First speaker note")
            page.locator("#pptP2NotesInput").blur()
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.currentSlide.notes === 'First speaker note'"
            )
            first = page.evaluate(
                """() => {
                    const s=globalThis.__inkdosPresentations.session.currentSlide;
                    return {notes:s.notes,edited:s.notesEdited,dirty:globalThis.__inkdosPresentations.session.dirty};
                }"""
            )
            assert first == {"notes": "First speaker note", "edited": True, "dirty": True}, first

            assert page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('history.undo')") is True
            page.wait_for_function(
                "() => (globalThis.__inkdosPresentations.session.currentSlide.notes || '') === ''"
            )
            assert page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('history.redo')") is True
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.currentSlide.notes === 'First speaker note'"
            )

            page.evaluate(
                """() => {
                    document.getElementById('pptP2NotesBtn')?.remove();
                    document.getElementById('pptP2NotesPanel')?.remove();
                }"""
            )
            semantic_note = "Presenter note <alpha> & beta\nSecond line"
            changed = page.evaluate(
                "(value) => globalThis.__inkdosPresentations.executeCommand('slide.notes.set', value)",
                semantic_note,
            )
            assert changed is True
            assert page.evaluate(
                "() => globalThis.__inkdosPresentations.session.currentSlide.notes"
            ) == semantic_note

            package_probe = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const base=await NS.PptxWriter.build(app.session);
                    const out=await NS.PptP2Package.applySlideCompletion(app.session,base,{});
                    const zip=await JSZip.loadAsync(out,{checkCRC32:true});
                    const slideRels=await zip.file('ppt/slides/_rels/slide1.xml.rels').async('text');
                    const contentTypes=await zip.file('[Content_Types].xml').async('text');
                    const presentation=await zip.file('ppt/presentation.xml').async('text');
                    const presentationRels=await zip.file('ppt/_rels/presentation.xml.rels').async('text');
                    const notes=await NS.PptP2Package.readSlideNotes(out,['ppt/slides/slide1.xml']);
                    const noteFiles=Object.keys(zip.files).filter(n=>/^ppt\/notesSlides\/notesSlide\d+\.xml$/i.test(n));
                    const masterFiles=Object.keys(zip.files).filter(n=>/^ppt\/notesMasters\/notesMaster\d+\.xml$/i.test(n));
                    const noteXml=noteFiles.length?await zip.file(noteFiles[0]).async('text'):'';
                    return {
                        notes:notes[0],
                        noteFiles,
                        masterFiles,
                        hasSlideRel:/relationships\/notesSlide/.test(slideRels),
                        hasMasterRel:/relationships\/notesMaster/.test(presentationRels),
                        hasMasterList:/notesMasterIdLst/.test(presentation),
                        hasNotesType:/presentationml\.notesSlide\+xml/.test(contentTypes),
                        hasMasterType:/presentationml\.notesMaster\+xml/.test(contentTypes),
                        escaped:noteXml.includes('&lt;alpha&gt;') && noteXml.includes('&amp; beta'),
                        bytes:Array.from(out)
                    };
                }"""
            )
            assert package_probe["notes"] == semantic_note, package_probe
            assert len(package_probe["noteFiles"]) == 1, package_probe
            assert len(package_probe["masterFiles"]) == 1, package_probe
            assert package_probe["hasSlideRel"] is True, package_probe
            assert package_probe["hasMasterRel"] is True, package_probe
            assert package_probe["hasMasterList"] is True, package_probe
            assert package_probe["hasNotesType"] is True, package_probe
            assert package_probe["hasMasterType"] is True, package_probe
            assert package_probe["escaped"] is True, package_probe

            page.evaluate(
                """async bytes => {
                    const file=new File([new Uint8Array(bytes)],'notes-roundtrip.pptx',{
                        type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    });
                    await globalThis.__inkdosPresentations.open(file);
                }""",
                package_probe["bytes"],
            )
            page.wait_for_function(
                f"() => globalThis.__inkdosPresentations.session.sourceKind === 'pptx' && "
                f"globalThis.__inkdosPresentations.session.currentSlide.notes === {semantic_note!r}"
            )
            imported = page.evaluate(
                """() => {
                    const s=globalThis.__inkdosPresentations.session.currentSlide;
                    return {notes:s.notes,edited:s.notesEdited,part:s.sourcePart};
                }"""
            )
            assert imported["notes"] == semantic_note, imported
            assert imported["edited"] is False, imported
            assert imported["part"] == "ppt/slides/slide1.xml", imported

            edited_note = "Imported note edited locally"
            assert page.evaluate(
                "(value) => globalThis.__inkdosPresentations.executeCommand('slide.notes.set', value)",
                edited_note,
            ) is True
            imported_roundtrip = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const out=await NS.PptP2Package.applySlideCompletion(app.session,app.session.sourceBytes,{});
                    const notes=await NS.PptP2Package.readSlideNotes(out,app.session.slides.map(s=>s.sourcePart));
                    return {notes,bytes:out.length};
                }"""
            )
            assert imported_roundtrip["notes"] == [edited_note], imported_roundtrip
            assert imported_roundtrip["bytes"] > 0, imported_roundtrip

            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PPT-P2 speaker notes regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
