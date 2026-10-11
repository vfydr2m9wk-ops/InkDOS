#!/usr/bin/env python3
"""PDF: a password-protected PDF asks for its password when opened (both open paths), instead of failing."""
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "apps/pdf/io/file-open-controller.js").read_text(encoding="utf-8")


def main():
    assert "task.onPassword=" in SOURCE, "PDF open must answer pdf.js password requests"
    assert "global.prompt" not in SOURCE, "web views such as XeOS block window.prompt: ask in the page"
    assert "function askPassword(" in SOURCE and "input.type='password'" in SOURCE
    assert "INCORRECT_PASSWORD" in SOURCE, "a wrong password must ask again"
    assert "Password entry was cancelled." in SOURCE, "Cancel must stop the open with a clear error"
    assert SOURCE.count("await withPassword(task)") == 2, "both the range open and the bytes open must ask for the password"
    save = (Path(__file__).resolve().parents[1] / "apps/pdf/io/save-adapter.js").read_text(encoding="utf-8")
    assert "NS.PdfPasswords.set(doc,given)" in SOURCE, "the accepted password must stay with its document"
    assert "NS.PdfPasswords?.get(pdfDocument)" in save and "password:password??undefined" in save, "the save check must reopen an encrypted copy with its password"
    print("PDF password open contract: OK")


if __name__ == "__main__":
    main()
