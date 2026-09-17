#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def dump(name,value): (ROOT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
    v=json.loads((ROOT/'VERSION.json').read_text(encoding='utf-8'))
    components=v['components']
    dump('BUILD_INFO.json',{'schemaVersion':1,'product':'InkDOS','version':v['version'],'buildDate':v['date'],'channel':v['releaseChannel'],'modules':list(components),'plannedModules':list(v.get('plannedComponents',{})),'architecture':'launcher-plus-independent-apps','requiresPreviousRuntime':False})
    dump('SOURCE_MANIFEST.json',{'schemaVersion':1,'product':'InkDOS','version':v['version'],'generatedAt':v['date'],'entryPoint':'index.html','repository':v['repository'],'sourceLock':'SOURCE_LOCK.json','updateWorkflow':'.github/workflows/apply-inkdos-update.yml'})
    dump('RELEASE_MANIFEST.json',{'schemaVersion':2,'project':'InkDOS','version':v['version'],'releaseName':v['releaseName'],'releaseDate':v['date'],'releaseType':'Core Release','entryPoints':{k:x['path'] for k,x in components.items()},'supportedFormats':[x['format'] for x in components.values()],'planned':v.get('plannedComponents',{}),'repository':v['repository'],'homepage':v['demo'],'buildRequired':False,'automaticRemoteRuntimeDependencies':False})
    print(f"Release metadata synchronized for InkDOS {v['version']}.")
if __name__=='__main__': main()
