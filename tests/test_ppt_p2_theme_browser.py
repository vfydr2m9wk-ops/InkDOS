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
PORT = 8788
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
                "!!globalThis.InkDOS2Presentations?.PptP2Package"
            )

            default_theme = page.evaluate(
                """() => {
                    const s=globalThis.__inkdosPresentations.session.currentSlide;
                    return {theme:s.theme,model:globalThis.InkDOS2Presentations.PresentationModel.DEFAULT_THEME};
                }"""
            )
            assert default_theme["theme"]["name"] == "InkDOS", default_theme
            assert default_theme["theme"]["colors"]["accent1"] == "#DF542C", default_theme
            assert default_theme["theme"]["major"] == "Aptos Display", default_theme

            themed = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const base=await NS.PptxWriter.build(app.session);
                    const zip=await JSZip.loadAsync(base,{checkCRC32:true});
                    let theme=await zip.file('ppt/theme/theme1.xml').async('text');
                    theme=theme.replace('name="InkDOS"','name="Custom Theme"')
                               .replace('<a:clrScheme name="InkDOS">','<a:clrScheme name="Custom Colors">')
                               .replace('<a:fontScheme name="InkDOS">','<a:fontScheme name="Custom Fonts">')
                               .replace('val="DF542C"','val="112233"')
                               .replace('typeface="Aptos Display"','typeface="Georgia"')
                               .replace('typeface="Aptos"','typeface="Verdana"');
                    zip.file('ppt/theme/theme1.xml',theme,{createFolders:false});
                    let slide=await zip.file('ppt/slides/slide1.xml').async('text');
                    slide=slide.replace(/<a:rPr ([^>]*)\/>/, '<a:rPr $1><a:solidFill><a:schemeClr val="accent1"/></a:solidFill><a:latin typeface="+mj-lt"/></a:rPr>');
                    zip.file('ppt/slides/slide1.xml',slide,{createFolders:false});
                    const out=await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}});
                    return {bytes:Array.from(out),theme};
                }"""
            )

            page.evaluate(
                """async bytes => {
                    const file=new File([new Uint8Array(bytes)],'custom-theme.pptx',{
                        type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    });
                    await globalThis.__inkdosPresentations.open(file);
                }""",
                themed["bytes"],
            )
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.currentSlide?.theme?.name === 'Custom Theme'"
            )

            imported = page.evaluate(
                """() => {
                    const slide=globalThis.__inkdosPresentations.session.currentSlide;
                    const text=slide.objects.find(o=>o.type==='text');
                    return {
                        theme:slide.theme,
                        text:{color:text?.color||null,fontFamily:text?.fontFamily||null},
                        sourcePart:slide.sourcePart
                    };
                }"""
            )
            assert imported["theme"]["name"] == "Custom Theme", imported
            assert imported["theme"]["colorSchemeName"] == "Custom Colors", imported
            assert imported["theme"]["fontSchemeName"] == "Custom Fonts", imported
            assert imported["theme"]["part"] == "ppt/theme/theme1.xml", imported
            assert imported["theme"]["colors"]["accent1"] == "#112233", imported
            assert imported["theme"]["major"] == "Georgia", imported
            assert imported["theme"]["minor"] == "Verdana", imported
            assert imported["text"] == {"color": "#112233", "fontFamily": "Georgia"}, imported
            assert imported["sourcePart"] == "ppt/slides/slide1.xml", imported

            preserved = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const result=await NS.PptxPreservationWriter.build(app.session);
                    const zip=await JSZip.loadAsync(result.bytes,{checkCRC32:true});
                    const xml=await zip.file('ppt/theme/theme1.xml').async('text');
                    const parts=app.session.slides.map(s=>s.sourcePart);
                    const themes=await NS.PptP2Package.readThemeMetadata(result.bytes,parts);
                    return {xml,themes,bytes:Array.from(result.bytes)};
                }"""
            )
            assert 'name="Custom Theme"' in preserved["xml"], preserved
            assert 'val="112233"' in preserved["xml"], preserved
            assert 'typeface="Georgia"' in preserved["xml"], preserved
            assert preserved["themes"][0]["colors"]["accent1"] == "#112233", preserved
            assert preserved["themes"][0]["major"] == "Georgia", preserved

            assert page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('slide.add')") is True
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length === 2")
            inherited = page.evaluate(
                """() => ({
                    index:globalThis.__inkdosPresentations.session.currentIndex,
                    theme:globalThis.__inkdosPresentations.session.currentSlide.theme
                })"""
            )
            assert inherited["index"] == 1, inherited
            assert inherited["theme"]["name"] == "Custom Theme", inherited
            assert inherited["theme"]["colors"]["accent1"] == "#112233", inherited
            assert inherited["theme"]["major"] == "Georgia", inherited

            assert page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('history.undo')") is True
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length === 1")
            assert page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('history.redo')") is True
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.slides.length === 2")
            redo_theme = page.evaluate(
                "() => globalThis.__inkdosPresentations.session.currentSlide.theme"
            )
            assert redo_theme["name"] == "Custom Theme", redo_theme
            assert redo_theme["colors"]["accent1"] == "#112233", redo_theme

            structural = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const result=await NS.PptxPreservationWriter.build(app.session);
                    const parts=result.receipt.slideMappings.map(x=>x.slidePart);
                    const themes=await NS.PptP2Package.readThemeMetadata(result.bytes,parts);
                    return {themes,parts,bytes:result.bytes.length};
                }"""
            )
            assert structural["bytes"] > 0, structural
            assert len(structural["themes"]) == 2, structural
            assert all(t and t["colors"]["accent1"] == "#112233" for t in structural["themes"]), structural
            assert all(t and t["major"] == "Georgia" for t in structural["themes"]), structural

            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PPT-P2 theme foundation regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
