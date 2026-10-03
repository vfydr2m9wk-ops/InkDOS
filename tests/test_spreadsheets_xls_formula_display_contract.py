#!/usr/bin/env python3
"""Excel 97-2003 import: 3-D references, array/choose/missing-argument tokens and the full function
table decode to formulas; cached error codes and number formats show as Excel shows them."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRIPT = r"""
const fs=require('fs');globalThis.window=globalThis;eval(fs.readFileSync('apps/spreadsheets/io/xls-biff8-engine.js','utf8'));
const T=globalThis.LocalXLS._test,eq=(a,b,m)=>{if(a!==b){console.error(m+': got '+JSON.stringify(a)+' want '+JSON.stringify(b));process.exit(1)}};
const u=a=>new Uint8Array(a),le=n=>[n&255,n>>8];
// ='910826'!H41  (ptgRef3d ixti=0, row 40, col 7 relative)
eq(T.decodeFormulaTokens(u([0x3A,...le(0),...le(40),...le(0xC007)]),0,0,['910826']),"'910826'!H41",'Ref3d');
// SUM('a b'!A1:B2)  (ptgArea3d + ptgAttr sum)
eq(T.decodeFormulaTokens(u([0x3B,...le(0),...le(0),...le(1),...le(0),...le(1),0x19,0x10,0,0]),0,0,["a b"]),"SUM('a b'!$A$1:$B$2)",'Area3d');
// NOW() is in the full function table (id 74); CHOOSE jump table is skipped
eq(T.decodeFormulaTokens(u([0x41,...le(74)]),0,0,[]),'NOW()','function table');
eq(T.decodeFormulaTokens(u([0x1E,...le(2),0x19,0x04,...le(1),...le(0),...le(0),0x1E,...le(5),0x1E,...le(6),0x42,3,...le(100)]),0,0,[]),'CHOOSE(2,5,6)','choose');
// cached #N/A
const f=new Uint8Array(22);f[6]=2;f[8]=42;f[12]=0xFF;f[13]=0xFF;eq(T.formulaCached(f).value,'#N/A','error code');
eq(T.formatNumber(2.71,{numberFormat:'0.000'}),'2.710','three decimals');
eq(T.formatNumber(2.6,{numberFormat:'0'}),'3','integer format');
const acc='_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)';
eq(T.formatNumber(0,{numberFormat:acc,numFmtId:44}).trim(),'-','accounting zero section');
eq(T.formatNumber(-100,{numberFormat:acc,numFmtId:44}).trim(),'(100.00)','accounting negative section');
eq(T.formatNumber(35431,{numberFormat:'mmm-yy',numFmtId:17}),'Jan-97','built-in month-year date');
eq(T.formatNumber(15.534780208110757,{numberFormat:'General'}),'15.5347802081108','General precision');
eq(T.formatNumber(37270,{numberFormat:'m"月"d"日"',numFmtId:176}),'1月14日','custom date pattern');
console.log('ok');
"""


def main() -> None:
    out = subprocess.run(['node', '-e', SCRIPT], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout.strip() == 'ok', out.stderr or out.stdout
    print('Spreadsheets XLS formula/display contract: OK')


if __name__ == '__main__':
    main()
