#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'apps'/'documents'

def require(text,needle,message):
    if needle not in text:
        raise SystemExit(message)

def main():
    files=[APP/'app.js',APP/'ui'/'d2-tools.js',APP/'ui'/'d2-sections.js',APP/'engine'/'d2-docx-extension.js',APP/'engine'/'d2-sections-extension.js',APP/'engine'/'page-spec.js',APP/'view'/'page-surface.js',APP/'view'/'pagination-engine.js',APP/'io'/'rtf-importer.js',APP/'io'/'file-open-controller.js']
    for path in files:
        subprocess.run(['node','--check',str(path)],cwd=ROOT,check=True)
    tools=(APP/'ui'/'d2-tools.js').read_text(encoding='utf-8')
    sections=(APP/'ui'/'d2-sections.js').read_text(encoding='utf-8')
    ext=(APP/'engine'/'d2-docx-extension.js').read_text(encoding='utf-8')
    sect_ext=(APP/'engine'/'d2-sections-extension.js').read_text(encoding='utf-8')
    spec=(APP/'engine'/'page-spec.js').read_text(encoding='utf-8')
    surface=(APP/'view'/'page-surface.js').read_text(encoding='utf-8')
    pagination=(APP/'view'/'pagination-engine.js').read_text(encoding='utf-8')
    rtf=(APP/'io'/'rtf-importer.js').read_text(encoding='utf-8')
    opener=(APP/'io'/'file-open-controller.js').read_text(encoding='utf-8')
    app=(APP/'app.js').read_text(encoding='utf-8')
    for needle in ['d2Spellcheck','d2CommentText','d2FootnoteText','d2UpdateToc','Heading3','Subtitle','Quote','d2MergeRight','d2DeleteRow','d2DeleteColumn']:
        require(tools,needle,f'DOC-D2 P1 tool contract missing: {needle}')
    for needle in ['comments.xml','footnotes.xml','commentRangeStart','commentReference','footnoteReference','TOCHeading','TOC1','TOC2','TOC3','gridSpan','DocxParser.parse','DocxWriter.save']:
        require(ext,needle,f'DOC-D2 P1 OOXML contract missing: {needle}')
    for needle in ['d2Columns','d2ColumnGap','d2SectionBreak','d2SectionEnd','sectionStart','PaginationEngine.paginate']:
        require(sections,needle,f'DOC-D2 section tool contract missing: {needle}')
    for needle in ["'cols'",'nextPage','d2SectionEnd','d2SectionStart','DocxParser.parse','DocxWriter.save']:
        require(sect_ext,needle,f'DOC-D2 section OOXML contract missing: {needle}')
    for needle in ['columns:1','columnGapPx:36']:
        require(spec,needle,f'DOC-D2 page spec contract missing: {needle}')
    for needle in ['columnCount','columnGap','columnFill']:
        require(surface,needle,f'DOC-D2 column rendering contract missing: {needle}')
    for needle in ['columnWidth','contentHeightPx*spec.columns']:
        require(pagination,needle,f'DOC-D2 column pagination contract missing: {needle}')
    for needle in ['MAX_BYTES','MAX_BLOCKS','MAX_DEPTH','windows-1252','fonttbl','colortbl','\\u','hardPageBreakBefore','RtfImporter']:
        require(rtf,needle,f'DOC-D2 RTF importer contract missing: {needle}')
    for needle in ["/\\.rtf$/i",'RtfImporter.parse','legacyOutputName','sourceBuffer:isDocx?buffer:null',"kind:isRtf?'rtf':'docx'",'Save copy creates DOCX']:
        require(opener,needle,f'DOC-D2 RTF open/save contract missing: {needle}')
    for needle in ['engine/d2-docx-extension.js','engine/d2-sections-extension.js','io/rtf-importer.js','ui/d2-tools.js','ui/d2-sections.js','ui/d2-tools.css','D2Tools.create','D2Sections.create',"fileInput.accept='.docx,.rtf"]:
        require(app,needle,f'DOC-D2 P1 app-local loader missing: {needle}')
    siblings=['apps/pdf/','apps/spreadsheets/','apps/presentations/','apps/epub/','apps/txt/']
    combined='\n'.join([tools,sections,ext,sect_ext,rtf,opener])
    if any(x in combined for x in siblings):
        raise SystemExit('DOC-D2 contains a sibling-workspace dependency')
    print('DOC-D2 P1 + RTF static and syntax contract passed.')

if __name__=='__main__':
    main()
