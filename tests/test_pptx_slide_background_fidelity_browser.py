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
PORT = 8796
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
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.session")
            page.click("#startNew")
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.active && "
                "!!globalThis.InkDOS2Presentations?.PptxWriter"
            )

            synthetic = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const base=await NS.PptxWriter.build(app.session);
                    const zip=await JSZip.loadAsync(base,{checkCRC32:true});
                    let slide=await zip.file('ppt/slides/slide1.xml').async('text');
                    slide=slide.replace(
                      /<p:cSld([^>]*)>/,
                      '<p:cSld$1><p:bg><p:bgPr><a:solidFill><a:srgbClr val="241E1C"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'
                    );
                    zip.file('ppt/slides/slide1.xml',slide,{createFolders:false});
                    const out=await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}});
                    return Array.from(out);
                }"""
            )

            page.evaluate(
                """async bytes => {
                    const file=new File([new Uint8Array(bytes)],'background-regression.pptx',{
                        type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    });
                    await globalThis.__inkdosPresentations.open(file);
                }""",
                synthetic,
            )
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.sourceKind === 'pptx'"
            )

            imported = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations;
                    const slide=app.session.currentSlide;
                    const canvas=document.querySelector('#slideCanvas');
                    return {
                        background:slide?.background||null,
                        rendered:canvas ? getComputedStyle(canvas).backgroundColor : null,
                        sourcePart:slide?.sourcePart||null
                    };
                }"""
            )
            assert imported["background"] == "#241E1C", imported
            assert imported["rendered"] == "rgb(36, 30, 28)", imported
            assert imported["sourcePart"] == "ppt/slides/slide1.xml", imported

            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PPTX slide background fidelity regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
