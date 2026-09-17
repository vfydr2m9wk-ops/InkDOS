#!/usr/bin/env python3
from __future__ import annotations

import base64
import io
import os
import socket
import subprocess
import sys
import time
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8791
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


def unsafe_path_zip() -> str:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("../evil.xml", "<evil/>")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def case_collision_zip() -> str:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ppt/a.xml", "<a/>")
        archive.writestr("PPT/A.XML", "<b/>")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


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
                lambda msg: errors.append(f"console.error: {msg.text}")
                if msg.type == "error"
                else None,
            )
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function(
                "() => !!globalThis.InkDOS2Presentations?.PptxSecurity && "
                "!!globalThis.InkDOS2Presentations?.PptxOpenController && "
                "!!globalThis.__inkdosPresentations"
            )
            page.click("#startNew")
            page.wait_for_function(
                "() => !!globalThis.__inkdosPresentations?.session?.active"
            )

            valid = page.evaluate(
                """async() => {
                    const NS=globalThis.InkDOS2Presentations;
                    const app=globalThis.__inkdosPresentations;
                    const bytes=await NS.PptxWriter.build(app.session);
                    const decoded=await NS.PptxOpenController.decodePptx(bytes,'Valid.pptx');
                    return {
                      slides:decoded.slides.length,
                      limits:NS.PptxSecurity.LIMITS
                    };
                }"""
            )
            assert valid["slides"] >= 1, valid
            assert valid["limits"]["maxEntries"] == 4096, valid

            dtd = page.evaluate(
                """async() => {
                    const NS=globalThis.InkDOS2Presentations;
                    const app=globalThis.__inkdosPresentations;
                    const base=await NS.PptxWriter.build(app.session);
                    const zip=await JSZip.loadAsync(base);
                    const part='ppt/presentation.xml';
                    const xml=await zip.file(part).async('text');
                    zip.file(part,'<!DOCTYPE x [<!ENTITY payload "blocked">]>'+xml);
                    const bytes=await zip.generateAsync({type:'uint8array',compression:'DEFLATE'});
                    try{
                      await NS.PptxOpenController.decodePptx(bytes,'DTD.pptx');
                      return {accepted:true};
                    }catch(error){
                      return {accepted:false,code:error.code||'',message:String(error.message||error)};
                    }
                }"""
            )
            assert dtd["accepted"] is False, dtd
            assert dtd["code"] == "PPTX_XML_DTD", dtd

            bomb = page.evaluate(
                """async() => {
                    const NS=globalThis.InkDOS2Presentations;
                    const zip=new JSZip();
                    zip.file('ppt/presentation.xml','A'.repeat(2*1024*1024));
                    const bytes=await zip.generateAsync({
                      type:'uint8array',
                      compression:'DEFLATE',
                      compressionOptions:{level:9}
                    });
                    try{
                      await NS.PptxOpenController.decodePptx(bytes,'Bomb.pptx');
                      return {accepted:true,size:bytes.length};
                    }catch(error){
                      return {accepted:false,code:error.code||'',message:String(error.message||error),size:bytes.length};
                    }
                }"""
            )
            assert bomb["accepted"] is False, bomb
            assert bomb["code"] == "PPTX_COMPRESSION_RATIO", bomb

            for encoded, expected in (
                (unsafe_path_zip(), "PPTX_ZIP_PATH"),
                (case_collision_zip(), "PPTX_ZIP_COLLISION"),
            ):
                result = page.evaluate(
                    """async({encoded}) => {
                        const NS=globalThis.InkDOS2Presentations;
                        const raw=atob(encoded);
                        const bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
                        try{
                          await NS.PptxOpenController.decodePptx(bytes,'Hostile.pptx');
                          return {accepted:true};
                        }catch(error){
                          return {accepted:false,code:error.code||'',message:String(error.message||error)};
                        }
                    }""",
                    {"encoded": encoded},
                )
                assert result["accepted"] is False, result
                assert result["code"] == expected, result

            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PPTX hostile-container security regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
