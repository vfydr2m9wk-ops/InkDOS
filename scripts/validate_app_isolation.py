#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import re
import shutil
import tempfile

ROOT=Path(__file__).resolve().parents[1]
ACTIVE=('documents','spreadsheets','presentations','txt','epub','pdf')
TEXT_SUFFIXES={'.html','.css','.js','.json','.webmanifest'}
HOME_FRAME={
    'documents':'runtime/frame/frame-menu.js',
    'spreadsheets':'runtime/frame/frame-menu.js',
    'presentations':'runtime/frame/frame-menu.js',
    'txt':'runtime/frame/app-frame.js',
    'epub':'runtime/frame/frame-menu.js',
    'pdf':'runtime/frame/frame-menu.js',
}
EPUB_LAYOUT={
    'engine/annotations.js','engine/book-model.js','engine/content-projector.js',
    'io/epub-writer.js','io/file-delivery.js','io/package-reader.js',
    'state/annotation-store.js','state/appearance.js','state/reading-state.js',
    'view/reader-viewport.js','view/reader.css','view/renderer.js',
    'ui/reader-controls.css','ui/reader-controls.js','ui/start-state.css',
    'session/book-session.js','runtime/frame/frame-menu.js','runtime/frame/app-frame.css',
    'runtime/tokens/base.css','app.js','index.html','assets/epub.svg'
}
EPUB_RETIRED_ROOT_FILES={
    'annotation-store.js','annotations.js','book-model.js','content-projector.js',
    'epub-writer.js','package-reader.js','renderer.js'
}

class RefParser(HTMLParser):
    def __init__(self):
        super().__init__();self.refs=[]
    def handle_starttag(self,tag,attrs):
        data=dict(attrs);is_home=tag=='a' and data.get('aria-label')=='Home'
        for key in ('src','href'):
            value=data.get(key)
            if value:self.refs.append((tag,key,value,is_home))

def local_path(value):
    if not value or value.startswith(('#','data:','blob:','javascript:','mailto:','tel:','//')):return None
    parsed=urlsplit(value)
    if parsed.scheme:return None
    return unquote(parsed.path)

def ensure_within(base,target):
    try:target.relative_to(base);return True
    except ValueError:return False

def validate_isolated_copy(app,errors):
    source=ROOT/'apps'/app
    with tempfile.TemporaryDirectory(prefix=f'inkdos-{app}-') as td:
        isolated=Path(td)/app;shutil.copytree(source,isolated)
        index=isolated/'index.html'
        parser=RefParser();parser.feed(index.read_text(encoding='utf-8'))
        for tag,key,value,is_home in parser.refs:
            path=local_path(value)
            if path is None:continue
            if is_home:
                if path!='../../index.html':errors.append(f'{app}: unexpected Home target {value}')
                continue
            resolved=(isolated/path).resolve()
            if not ensure_within(isolated.resolve(),resolved):
                errors.append(f'{app}: {tag} {key} escapes app root: {value}')
            elif not resolved.exists():
                errors.append(f'{app}: missing isolated resource: {value}')

def validate_cross_app_references(app,errors):
    root=ROOT/'apps'/app
    other=[name for name in ACTIVE if name!=app]
    patterns=[re.compile(rf'(?<![A-Za-z0-9_-])apps/{re.escape(name)}/') for name in other]
    patterns += [re.compile(rf'(?:\.\./)+{re.escape(name)}/') for name in other]
    forbidden_roots=('shared/','modules/','core/')
    for path in root.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:continue
        text=path.read_text(encoding='utf-8',errors='ignore')
        rel=path.relative_to(ROOT).as_posix()
        for pattern in patterns:
            if pattern.search(text):errors.append(f'{app}: cross-app source reference in {rel}: {pattern.pattern}')
        for marker in forbidden_roots:
            if re.search(rf'(?:\.\./)+{re.escape(marker)}',text):errors.append(f'{app}: shared runtime reference in {rel}: {marker}')

def validate_optional_home(app,errors):
    index=(ROOT/'apps'/app/'index.html').read_text(encoding='utf-8')
    if 'aria-label="Home"' not in index or 'href="../../index.html"' not in index:
        errors.append(f'{app}: optional Home anchor missing')
    frame_path=ROOT/'apps'/app/HOME_FRAME[app]
    if not frame_path.is_file():
        errors.append(f'{app}: app-local frame module missing: {HOME_FRAME[app]}');return
    frame=frame_path.read_text(encoding='utf-8')
    for marker in ('configureOptionalHome','URLSearchParams',"get('suite')==='1'","removeAttribute('href')"):
        if marker not in frame:errors.append(f'{app}: optional Home gate missing marker {marker}')

def validate_home_launcher(errors):
    home=(ROOT/'index.html').read_text(encoding='utf-8')
    for app in ACTIVE:
        expected=f'./apps/{app}/index.html?v=2.0.12&amp;suite=1'
        if expected not in home:errors.append(f'Home: suite opt-in route missing for {app}')

def validate_service_worker_shell(errors):
    sw=(ROOT/'service-worker.js').read_text(encoding='utf-8')
    refs=re.findall(r'["\'](\./[^"\']+)["\']',sw)
    for ref in refs:
        path=urlsplit(ref).path
        candidate=(ROOT/path[2:]).resolve()
        if not ensure_within(ROOT.resolve(),candidate):
            errors.append(f'Service worker shell escapes repository: {ref}')
        elif not candidate.exists():
            errors.append(f'Service worker shell references missing file: {ref}')

def validate_epub_layout(errors):
    root=ROOT/'apps'/'epub'
    for rel in EPUB_LAYOUT:
        if not (root/rel).is_file():errors.append(f'epub: expected modular file missing: {rel}')
    for rel in EPUB_RETIRED_ROOT_FILES:
        if (root/rel).exists():errors.append(f'epub: retired flat root file still present: {rel}')
    index=(root/'index.html').read_text(encoding='utf-8')
    for rel in ('io/package-reader.js','engine/content-projector.js','engine/book-model.js','state/annotation-store.js','engine/annotations.js','io/epub-writer.js','view/renderer.js','ui/start-state.css'):
        if rel not in index:errors.append(f'epub: modular index reference missing: {rel}')

def validate_source_lock_policy(errors):
    lock=json.loads((ROOT/'SOURCE_LOCK.json').read_text(encoding='utf-8'))
    if lock.get('release')!='2.0.12':errors.append('SOURCE_LOCK: release must be 2.0.12')
    policy=lock.get('integrationPolicy','')
    for marker in ('suite=1','physically independent','EPUB','isolated'):
        if marker not in policy:errors.append(f'SOURCE_LOCK: 2.0.12 integration policy missing {marker}')
    for app in ACTIVE:
        allowed='\n'.join(lock.get('apps',{}).get(app,{}).get('allowedIntegrationChanges',[]))
        if '2.0.12' not in allowed or 'Home' not in allowed:
            errors.append(f'SOURCE_LOCK: optional Home change not recorded for {app}')
    epub='\n'.join(lock.get('apps',{}).get('epub',{}).get('allowedIntegrationChanges',[]))
    for marker in ('structural refactor','io/','engine/','state/','view/'):
        if marker not in epub:errors.append(f'SOURCE_LOCK: EPUB refactor record missing {marker}')

def main():
    errors=[]
    validate_home_launcher(errors)
    validate_service_worker_shell(errors)
    validate_epub_layout(errors)
    validate_source_lock_policy(errors)
    for app in ACTIVE:
        validate_optional_home(app,errors)
        validate_isolated_copy(app,errors)
        validate_cross_app_references(app,errors)
    if errors:raise SystemExit('\n'.join(errors))
    print('Standalone app isolation, optional Home, offline shell, EPUB modular layout and source-lock policy passed.')

if __name__=='__main__':main()
