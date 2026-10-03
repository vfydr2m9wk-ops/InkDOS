#!/usr/bin/env python3
"""Legacy .doc: field instructions are hidden, footnotes, endnotes, text boxes and comments (stories
stored after the main text) are kept instead of dropped, and pictures are found in their BLIP store."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRIPT = r"""
const fs=require('fs');eval(fs.readFileSync('apps/documents/io/legacy-doc-reader.js','utf8'));
const T=globalThis.InkDOS2Documents.LegacyDocReader._test,assert=(c,m)=>{if(!c){console.error(m);process.exit(1)}};
// main text with a hyperlink field and a footnote reference; then footnote, endnote, text box, comment stories
const main='See \x13 HYPERLINK "http://x" \x14site\x15 here\x02.\r',ftn='\x02 Note body\r',edn='\x02 End body\r',atn='\x05 Comment body\r',txbx='Box body\r';
const text=main+ftn+atn+edn+txbx;
const d=T.fieldResultsOnly({text,pieces:[]});
assert(d.text.length===text.length,'field masking must keep CP offsets');
const fib={ccpText:main.length,stories:{ftn:ftn.length,hdd:0,mcr:0,atn:atn.length,edn:edn.length,txbx:txbx.length}};
const blocks=T.storyBlocks(d,fib,[],[]),all=blocks.map(b=>b.html).join('\n');
assert(!/HYPERLINK/.test(all),'field instruction leaked: '+all);
assert(/site/.test(all),'field result lost');
for(const w of['Note body','End body','Box body','Comment body'])assert(all.includes(w),w+' lost: '+all);
assert(/<sup>1<\/sup>/.test(blocks[0].html),'footnote reference is not numbered: '+blocks[0].html);
// FBSE (store entry, no name) holding a PNG BLIP: header 16-byte UID + tag byte, then the image bytes
const png=[0x89,0x50,0x4e,0x47,1,2,3],le32=n=>[n&255,(n>>8)&255,(n>>16)&255,n>>>24],blip=[0x00,0x6e,0x1e,0xf0,...le32(17+png.length),...new Array(17).fill(0),...png];
const fbse=[0x02,0x00,0x07,0xf0,...le32(36+blip.length),...new Array(36).fill(0),...blip],found=T.findBlip(new Uint8Array(fbse),0,fbse.length);
assert(found&&/^data:image\/png;base64,/.test(found.url),'PNG picture not found in its BLIP store entry');
console.log('ok');
"""


def main() -> None:
    out = subprocess.run(['node', '-e', SCRIPT], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout.strip() == 'ok', out.stderr or out.stdout
    print('Documents legacy DOC stories contract: OK')


if __name__ == '__main__':
    main()
