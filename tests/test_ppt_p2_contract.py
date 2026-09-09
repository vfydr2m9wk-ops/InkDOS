#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main() -> None:
    package = read("apps/presentations/io/ppt-p2-package.js")
    tools = read("apps/presentations/ui/ppt-p2-tools.js")
    session = read("apps/presentations/engine/presentation-session.js")
    save = read("apps/presentations/io/save-controller.js")

    for needle in (
        "readSlideMetadata",
        "readSlideNotes",
        "readThemeMetadata",
        "themeMetadata",
        "themeForSlide",
        "'/slideLayout'",
        "'/slideMaster'",
        "'/theme'",
        "applySpeakerNotes",
        "applySlideCompletion",
        "notesSlideXml",
        "notesMasterXml",
        "'/notesSlide'",
        "'/notesMaster'",
        "presentationml.notesSlide+xml",
        "presentationml.notesMaster+xml",
    ):
        require(package, needle, "PPT-P2 package contract")

    for needle in (
        "commands.register('slide.transition.set'",
        "commands.register('slide.notes.set'",
        "history.transact('Speaker notes'",
        "pptP2NotesBtn",
        "pptP2NotesInput",
        "notesInput.dataset.command='slide.notes.set'",
        "slide.theme=themeOf",
        "themes.push(slide.theme)",
    ):
        require(tools, needle, "PPT-P2 tools contract")

    for needle in (
        "const DEFAULT_THEME=Object.freeze",
        "function cloneTheme",
        "theme:cloneTheme(theme)",
        "theme:this.currentSlide?.theme||DEFAULT_THEME",
        "DEFAULT_THEME,cloneTheme",
    ):
        require(session, needle, "PPT-P2 theme model contract")

    require(save, "PptP2Package.applySlideCompletion", "PPT-P2 save contract")
    require(save, "slide.notesEdited=false", "PPT-P2 confirmed PPTX baseline contract")
    require(save, "session.sourceKind==='pptx'", "PPT-P2 generated-package persistence contract")

    print("PPT-P2 completion contract: OK")


if __name__ == "__main__":
    main()
