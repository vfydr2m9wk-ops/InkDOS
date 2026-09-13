#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'apps'/'presentations'

def require(text,needle,message):
    if needle not in text:
        raise SystemExit(message)

def main():
    files=[APP/'app.js',APP/'engine'/'presentation-session.js',APP/'view'/'slide-surface.js',APP/'ui'/'ppt-p1-tools.js',APP/'io'/'save-controller.js',APP/'io'/'ppt-p1-object-writer.js']
    for path in files:
        subprocess.run(['node','--check',str(path)],cwd=ROOT,check=True)
    app=(APP/'app.js').read_text(encoding='utf-8')
    session=(APP/'engine'/'presentation-session.js').read_text(encoding='utf-8')
    surface=(APP/'view'/'slide-surface.js').read_text(encoding='utf-8')
    tools=(APP/'ui'/'ppt-p1-tools.js').read_text(encoding='utf-8')
    save=(APP/'io'/'save-controller.js').read_text(encoding='utf-8')
    writer=(APP/'io'/'ppt-p1-object-writer.js').read_text(encoding='utf-8')
    sw=(ROOT/'service-worker.js').read_text(encoding='utf-8')
    for needle in ['addImage','addShape','applyLayout','twoContent','section','importedUnmapped']:
        require(session,needle,f'PPT-P1 object model contract missing: {needle}')
    for needle in ['ppt-p1-object-overlay','ppt-p1-handle','Move object','Resize object','Rotate object','commitFromBefore']:
        require(surface,needle,f'PPT-P1 geometry interaction missing: {needle}')
    for needle in ['pptP1ImageBtn','pptP1Shape','pptP1TextColor','pptP1Fill','pptP1Border','pptP1Bullets','pptP1Layout','image/png','image/jpeg']:
        require(tools,needle,f'PPT-P1 object toolbar contract missing: {needle}')
    for needle in ['function insertShape(value)','function applyLayout(value)','shape.onchange=()=>','insertShape(value)','layout.onchange=()=>','applyLayout(value)','function setDisabled(id,value)']:
        require(tools,needle,f'PPT-P1 feature/control isolation contract missing: {needle}')
    for needle in ['ppt-p1-structure-writer.js','ppt-p1-object-writer.js','PptP1ObjectWriter']:
        require(save,needle,f'PPT-P1 writer loader missing: {needle}')
    for needle in ['package-preserving-pptx-home-editing','generated-pptx-home-editing','makeShape','makePic','objectMappings','ppt/media/inkdos','buChar','solidFill','setGeometry']:
        require(writer,needle,f'PPT-P1 object writer contract missing: {needle}')
    for needle in ['ui/ppt-p1-tools.js','get p1Tools()']:
        require(app,needle,f'PPT-P1 app integration missing: {needle}')
    for needle in ['./apps/presentations/io/ppt-p1-structure-writer.js','./apps/presentations/io/ppt-p1-object-writer.js','./apps/presentations/ui/ppt-p1-tools.js']:
        require(sw,needle,f'PPT-P1 offline shell contract missing: {needle}')
    combined='\n'.join([app,session,surface,tools,save,writer])
    for sibling in ['apps/documents/','apps/pdf/','apps/spreadsheets/','apps/epub/','apps/txt/']:
        if sibling in combined:
            raise SystemExit('PPT-P1 object editing contains a sibling-workspace runtime dependency')
    print('PPT-P1 objects/geometry/styles/layouts static, syntax and offline-shell contract passed.')

if __name__=='__main__':main()