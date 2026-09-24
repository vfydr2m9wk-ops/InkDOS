#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JS = Path(os.environ.get("INKDOS_UI_DENSITY_JS", ROOT / "shared" / "ui-density.js"))


def main() -> None:
    probe = r'''
const fs=require('fs');
const vm=require('vm');
const source=fs.readFileSync(process.argv[1],'utf8');
const listeners={};
const root={
  innerWidth:1360,
  location:{pathname:'/apps/documents/index.html'},
  localStorage:{getItem(){return null},setItem(){}},
  matchMedia(){return {matches:true}},
  addEventListener(type,listener){(listeners[type]??=[]).push(listener)},
  CustomEvent:function(type,init){this.type=type;this.detail=init?.detail},
};
root.globalThis=root;
root.document={
  documentElement:{
    clientWidth:1360,
    attrs:{},
    setAttribute(name,value){this.attrs[name]=value},
  },
  readyState:'complete',
  currentScript:null,
  getElementById(){return null},
  querySelector(){return null},
  querySelectorAll(){return []},
  dispatchEvent(){},
};
vm.runInContext(source,vm.createContext(root),{filename:process.argv[1]});
const snapshot=()=>({
  preference:root.InkDOSUiDensity.preference,
  effective:root.InkDOSUiDensity.effective,
  attr:root.document.documentElement.attrs['data-ui-density'],
});
const before=snapshot();
root.innerWidth=720;
root.document.documentElement.clientWidth=720;
for(const listener of listeners.resize||[])listener({type:'resize'});
const after=snapshot();
process.stdout.write(JSON.stringify({before,after}));
'''
    completed = subprocess.run(
        ["node", "-e", probe, str(JS)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    actual = json.loads(completed.stdout)
    expected = {
        "before": {"preference": "auto", "effective": "desktop", "attr": "desktop"},
        "after": {"preference": "auto", "effective": "mobile", "attr": "mobile"},
    }
    if actual != expected:
        raise AssertionError(f"Auto density did not follow viewport resize: {actual!r}")
    print("Adaptive interface auto-density resize contract: OK")


if __name__ == "__main__":
    main()
