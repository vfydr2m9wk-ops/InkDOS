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
PORT = 8798
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
                lambda msg: errors.append(f"console.error: {msg.text}")
                if msg.type == "error"
                else None,
            )
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function(
                "() => !!globalThis.InkDOS2Presentations?.PptxWriter && "
                "!!globalThis.InkDOS2Presentations?.PptxOpenController && "
                "!!globalThis.__inkdosPresentations"
            )

            decode = page.evaluate(
                """async() => {
                  const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel;
                  const src=new NS.PresentationSession();src.resetNew();
                  const setTitle=(slide,text)=>{const o=slide.objects[0];o.text=text;o.paragraphs=M.normalizeParagraphs(null,text,o)};
                  setTitle(src.slides[0],'Reuse slide 1');
                  for(let i=2;i<=44;i++){src.addSlide();setTitle(src.currentSlide,'Reuse slide '+i)}
                  src.setCurrentByIndex(0);
                  const bytes=await NS.PptxWriter.build(src);
                  let loads=0,crcLoads=0;
                  const real=JSZip.loadAsync;
                  JSZip.loadAsync=async function(input,options){
                    loads++;
                    if(options?.checkCRC32)crcLoads++;
                    return real.call(this,input,options);
                  };
                  try{
                    const decoded=await NS.PptxOpenController.decodePptx(bytes,'reuse-44.pptx');
                    return {slides:decoded.slides.length,loads,crcLoads};
                  }finally{
                    JSZip.loadAsync=real;
                  }
                }"""
            )
            assert decode["slides"] == 44, decode
            assert decode["loads"] == 1, decode
            assert decode["crcLoads"] == 1, decode

            opened = page.evaluate(
                """async() => {
                  const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel;
                  const app=globalThis.__inkdosPresentations;
                  const src=new NS.PresentationSession();src.resetNew();
                  const setTitle=(slide,text)=>{const o=slide.objects[0];o.text=text;o.paragraphs=M.normalizeParagraphs(null,text,o)};
                  setTitle(src.slides[0],'Open reuse slide 1');
                  for(let i=2;i<=44;i++){src.addSlide();setTitle(src.currentSlide,'Open reuse slide '+i)}
                  src.setCurrentByIndex(0);
                  const bytes=await NS.PptxWriter.build(src);
                  const file=new File([bytes],'open-reuse-44.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
                  const real=file.arrayBuffer.bind(file);
                  let reads=0;
                  Object.defineProperty(file,'arrayBuffer',{configurable:true,value:async()=>{reads++;return real()}});
                  const ok=await app.open(file);
                  return {ok,reads,slides:app.session.slides.length,kind:app.session.sourceKind};
                }"""
            )
            assert opened["ok"] is True, opened
            assert opened["reads"] == 1, opened
            assert opened["slides"] == 44, opened
            assert opened["kind"] == "pptx", opened

            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(
            f"PPTX validated-package reuse regression passed on {browser_name}: "
            "one file read and one CRC-validating ZIP load."
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
