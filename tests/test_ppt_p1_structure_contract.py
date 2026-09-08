#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'apps'/'presentations'

def require(text,needle,message):
    if needle not in text:
        raise SystemExit(message)

def main():
    files=[APP/'engine'/'presentation-session.js',APP/'ui'/'editing-controller.js',APP/'io'/'save-controller.js',APP/'io'/'ppt-p1-structure-writer.js']
    for path in files:
        subprocess.run(['node','--check',str(path)],cwd=ROOT,check=True)
    session=(APP/'engine'/'presentation-session.js').read_text(encoding='utf-8')
    editor=(APP/'ui'/'editing-controller.js').read_text(encoding='utf-8')
    save=(APP/'io'/'save-controller.js').read_text(encoding='utf-8')
    writer=(APP/'io'/'ppt-p1-structure-writer.js').read_text(encoding='utf-8')
    for needle in ['sourceBaselineSlides','duplicateSourcePart','moveCurrent(delta)','slideMappings','sourceSlideParts=this.slides.map']:
        require(session,needle,f'PPT-P1 session structure contract missing: {needle}')
    for needle in ["session.sourceKind!=='ppt'",'moveSlideUpBtn','moveSlideDownBtn','session.moveCurrent(delta)','session.addSlide()','session.duplicateCurrent()','session.deleteCurrent()']:
        require(editor,needle,f'PPT-P1 toolbar structure contract missing: {needle}')
    for needle in ['ensureP1Writer','ppt-p1-structure-writer.js','PptxPreservationWriter.build']:
        require(save,needle,f'PPT-P1 save integration missing: {needle}')
    for needle in ['package-preserving-pptx-structure','sourceBaselineSlides','presentation.xml.rels','sldIdLst','slideMappings','duplicateSourcePart','ensureOverride','generatedSlideXml']:
        require(writer,needle,f'PPT-P1 package writer contract missing: {needle}')
    combined='\n'.join([session,editor,save,writer])
    for sibling in ['apps/documents/','apps/pdf/','apps/spreadsheets/','apps/epub/','apps/txt/']:
        if sibling in combined:
            raise SystemExit('PPT-P1 contains a sibling-workspace runtime dependency')
    print('PPT-P1 imported slide structure static/syntax contract passed.')

if __name__=='__main__':main()
