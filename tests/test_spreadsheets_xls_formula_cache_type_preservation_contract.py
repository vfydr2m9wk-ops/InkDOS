#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"apps/spreadsheets/io/xls-biff8-engine.js").read_text()
checks={
 "boolean cached formula type": "return{value:!!r[2],type:'b',special:true}",
 "error cached formula type": "return{value:'#ERROR!',type:'e',special:true}",
 "numeric cached formula type": "return{value:f64(v,0),type:'n',special:false}",
 "parser uses decoded cached type": "t:cached.type",
 "boolean display is logical": "cached.type==='b'?(cached.value?'TRUE':'FALSE')",
}
missing=[name for name,needle in checks.items() if needle not in src]
if missing: raise SystemExit("Missing BIFF8 formula cache type-preservation contract: "+", ".join(missing))
print("Spreadsheets BIFF8 formula cached-result type preservation contract: OK")
