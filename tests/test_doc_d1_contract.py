#!/usr/bin/env python3
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'apps'/'documents'

def require(text,needle,message):
    if needle not in text:
        raise SystemExit(message)

def main():
    files=[APP/'app.js',APP/'ui'/'d1-tools.js',APP/'engine'/'d1-docx-extension.js']
    for path in files:
        subprocess.run(['node','--check',str(path)],cwd=ROOT,check=True)
    tools=(APP/'ui'/'d1-tools.js').read_text(encoding='utf-8')
    ext=(APP/'engine'/'d1-docx-extension.js').read_text(encoding='utf-8')
    spec=(APP/'engine'/'page-spec.js').read_text(encoding='utf-8')
    app=(APP/'app.js').read_text(encoding='utf-8')
    for needle in ['foreColor','hiliteColor','strikeThrough','subscript','superscript','d1ReplaceNext','d1ReplaceAll','d1PageSize','d1Orientation','d1HeaderText','d1FooterText','d1PageNumber','d1PageBreak','Print / Export PDF']:
        require(tools,needle,f'DOC-D1 tool contract missing: {needle}')
    for needle in ['<w:strike/>','w:shd w:val=','w:vertAlign w:val=','pageBreakBefore','pgSz','pgMar','header-inkdos-d1.xml','footer-inkdos-d1.xml',' PAGE ','DocxParser.parse','DocxWriter.save']:
        require(ext,needle,f'DOC-D1 OOXML contract missing: {needle}')
    for needle in ["orientation:'portrait'","pageNumber:false"]:
        require(spec,needle,f'DOC-D1 page spec contract missing: {needle}')
    for needle in ['engine/d1-docx-extension.js','ui/d1-tools.js','ui/d1-tools.css']:
        require(app,needle,f'DOC-D1 app-local loader missing: {needle}')
    if 'apps/pdf/' in tools or 'apps/spreadsheets/' in tools or 'apps/presentations/' in tools or 'apps/epub/' in tools or 'apps/txt/' in tools:
        raise SystemExit('DOC-D1 tools contain a sibling-workspace dependency')
    print('DOC-D1 static and syntax contract passed.')

if __name__=='__main__':
    main()
