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
PORT = 8822
BASE = f"http://127.0.0.1:{PORT}"
CASES = [
    ("documents", "/apps/documents/index.html?suite=1", "sample.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("spreadsheets", "/apps/spreadsheets/index.html?suite=1", "sample.csv", "text/csv"),
    ("presentations", "/apps/presentations/index.html?suite=1", "sample.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    ("pdf", "/apps/pdf/index.html?suite=1", "sample.pdf", "application/pdf"),
    ("epub", "/apps/epub/index.html?suite=1", "sample.epub", "application/epub+zip"),
    ("txt", "/apps/txt/index.html?suite=1", "sample.yaml", "application/yaml"),
]


def wait_port() -> None:
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
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
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 820})
            context.add_init_script(
                """(() => {
                  const queue = {
                    consumer: null,
                    setConsumer(fn) { this.consumer = fn; }
                  };
                  Object.defineProperty(globalThis, 'launchQueue', {
                    value: queue,
                    configurable: true
                  });
                })();"""
            )
            page = context.new_page()

            for app, path, name, mime in CASES:
                page.goto(BASE + path, wait_until="load")
                page.wait_for_function("() => !!globalThis.InkDOSFileLaunch && typeof globalThis.launchQueue?.consumer === 'function'")
                result = page.evaluate(
                    """async ({name,mime}) => {
                      const launch = globalThis.InkDOSFileLaunch;
                      const input = document.querySelector('#fileInput');
                      const routed = {name:'', type:''};
                      launch.setOpenHandler(file => {
                        routed.name = file?.name || '';
                        routed.type = file?.type || '';
                        return true;
                      });

                      const launchHandle = {
                        kind: 'file',
                        async getFile() { return new File([new Uint8Array([1,2,3,4])], name, {type:mime}); }
                      };
                      await globalThis.launchQueue.consumer({files:[launchHandle]});

                      let fsaCapture = null;
                      const block = event => {
                        const target = event.target;
                        if (!(target instanceof HTMLInputElement) || target !== input) return;
                        if (event.type === 'change') {
                          fsaCapture = {
                            id: target.id,
                            name: target.files?.[0]?.name || '',
                            count: target.files?.length || 0
                          };
                        }
                        event.stopImmediatePropagation();
                      };
                      document.addEventListener('input', block, true);
                      document.addEventListener('change', block, true);
                      globalThis.showOpenFilePicker = () => Promise.resolve([{
                        kind: 'file',
                        async getFile() { return new File([new Uint8Array([5,6,7])], name, {type:mime}); }
                      }]);
                      const fsaStarted = launch.requestPicker(input);
                      await new Promise(resolve => setTimeout(resolve, 30));
                      delete globalThis.showOpenFilePicker;
                      const unsupportedFallback = launch.requestPicker(input);
                      document.removeEventListener('input', block, true);
                      document.removeEventListener('change', block, true);

                      return {
                        routed,
                        direct: launch.compatibleInput({name,mime})?.id || '',
                        fsaCapture,
                        fsaStarted,
                        unsupportedFallback
                      };
                    }""",
                    {"name": name, "mime": mime},
                )
                assert result["direct"] == "fileInput", (app, result)
                assert result["routed"]["name"] == name, (app, result)
                assert result["fsaStarted"] is True, (app, result)
                assert result["fsaCapture"], (app, "File System Access picker did not inject a file", result)
                assert result["fsaCapture"]["id"] == "fileInput", (app, result)
                assert result["fsaCapture"]["name"] == name, (app, result)
                assert result["fsaCapture"]["count"] == 1, (app, result)
                assert result["unsupportedFallback"] is False, (app, result)
                if app == "documents":
                    assert result["direct"] != "imageInput", result

            context.close()
            browser.close()

        print(f"InkDOS 2.6 launchQueue and File System Access routing ({browser_name}): OK")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
