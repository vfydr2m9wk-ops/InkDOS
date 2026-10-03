#!/usr/bin/env python3
"""Regression: dependency-driven formula recalculation matches whole-workbook recalculation.

Random workbooks (values, text, booleans, refs, ranges, cross-sheet refs, SUM/AVERAGE/MIN/MAX/COUNT/PRODUCT/IF,
arithmetic, cycles, #REF!, sheet renames and additions) are recalculated after random edits by the current evaluator
and by the previous evaluator that recalculated every formula four times; every result must match. It also checks
that editing one input recalculates only the formulas that depend on it.
"""
from __future__ import annotations
import os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = r'''
// Regression: dependency-driven recalculation gives the same results as recalculating every formula.
// Random workbooks (values, text, booleans, refs, ranges, cross-sheet refs, SUM/AVERAGE/MIN/MAX/COUNT/PRODUCT/IF,
// arithmetic, cycles, #REF!) are recalculated after random edits by the current evaluator and by the previous
// full-recalculation evaluator (kept below as the reference), and every formula result must match.
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = process.env.INKDOS_ROOT;
const read = rel => fs.readFileSync(path.join(ROOT, rel), 'utf8');
function colName(n){let s='';while(n>=0){s=String.fromCharCode(n%26+65)+s;n=Math.floor(n/26)-1}return s}
function encodeRef(r,c){return colName(c)+(r+1)}
function decodeRef(ref){const m=/^([A-Z]+)(\d+)$/i.exec(ref||'A1');if(!m)return{r:0,c:0};let c=0;for(const ch of m[1].toUpperCase())c=c*26+ch.charCodeAt(0)-64;return{r:Number(m[2])-1,c:c-1}}
const REFERENCE_RECALC = "function recalculate(book){for(let pass=0;pass<4;pass++)for(const sheet of book.sheets)for(const[ref,cell]of sheet.cells){if(!cell?.f)continue;const v=evaluate(book,sheet,cell.f,new Set([sheet.name+'!'+ref]));if(v!==null&&v!==undefined){cell.calculatedRaw=v;cell.calculated=v;cell.display=String(v)}}}";
function load(evaluatorSource){
  const g = {}; g.globalThis = g; g.LocalXLSX = {encodeRef, decodeRef};
  vm.createContext(g); vm.runInContext(read('apps/spreadsheets/engine/formula/arithmetic.js'), g); vm.runInContext(evaluatorSource, g);
  return g.InkDOS2Spreadsheets.FormulaEvaluator;
}
const current = load(read('apps/spreadsheets/engine/formula/evaluator.js'));
// Reference: the same parser/evaluate with the previous whole-workbook recalculation.
let refSource = read('apps/spreadsheets/engine/formula/evaluator.js');
refSource = refSource.replace(/\/\/ Recalculation follows[\s\S]*?function recalculate\(book[^)]*\)\{[\s\S]*?\}finally\{ctx=null\}\}/, REFERENCE_RECALC);
if (!refSource.includes(REFERENCE_RECALC)) throw new Error('could not build the reference evaluator');
const reference = load(refSource);

let seed = 12345; const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
const pick = a => a[Math.floor(rnd() * a.length)];
const SHEETS = ['Data', 'Calc Sheet'], ROWS = 12, COLS = 5;
function refText(own){const r=Math.floor(rnd()*ROWS),c=Math.floor(rnd()*COLS),ref=encodeRef(r,c);const other=pick(SHEETS);if(rnd()<.2&&other!==own)return (other.includes(' ')?`'${other}'`:other)+'!'+ref;return rnd()<.1?'$'+colName(c)+'$'+(r+1):ref}
function rangeText(own){const r1=Math.floor(rnd()*ROWS),c1=Math.floor(rnd()*COLS),r2=Math.floor(rnd()*ROWS),c2=Math.floor(rnd()*COLS);const t=encodeRef(r1,c1)+':'+encodeRef(r2,c2);if(rnd()<.2){const other=pick(SHEETS);return (other.includes(' ')?`'${other}'`:other)+'!'+t}return t}
function formula(own){const k=rnd();if(k<.25)return pick(['SUM','AVERAGE','MIN','MAX','COUNT','PRODUCT'])+'('+rangeText(own)+(rnd()<.4?','+refText(own):'')+')';if(k<.4)return 'IF('+refText(own)+','+refText(own)+','+(rnd()<.5?refText(own):'"no"')+')';if(k<.75)return refText(own)+pick(['+','-','*','/'])+(rnd()<.5?refText(own):String(Math.floor(rnd()*9)+1));if(k<.85)return refText(own);if(k<.9)return 'Missing!A1+1';return '('+refText(own)+'+'+refText(own)+')*2'}
function randomCell(own){const k=rnd();if(k<.35)return{f:formula(own),v:0,t:'n'};if(k<.75)return{v:Math.floor(rnd()*100)-20,t:'n'};if(k<.85)return{v:pick(['a','text','']),t:'s'};if(k<.9)return{v:rnd()<.5,t:'b'};return{v:0,t:'n'}}
function makeBook(){return{sheets:SHEETS.map(name=>({name,cells:new Map()}))}}
function snapshot(book){const out=[];for(const s of book.sheets)for(const[ref,c]of s.cells)if(c.f)out.push(s.name+'!'+ref+'='+JSON.stringify([c.calculated,c.display]));return out.sort().join('\n')}
let checks = 0;
for (let trial = 0; trial < 300; trial++) {
  const a = makeBook(), b = makeBook();
  for (const [i, name] of SHEETS.entries()) for (let n = 0; n < 30; n++) { const ref = encodeRef(Math.floor(rnd()*ROWS), Math.floor(rnd()*COLS)), cell = randomCell(name); a.sheets[i].cells.set(ref, {...cell}); b.sheets[i].cells.set(ref, {...cell}); }
  current.recalculate(a); reference.recalculate(b);
  if (snapshot(a) !== snapshot(b)) throw new Error(`initial recalculation differs (trial ${trial})`);
  for (let step = 0; step < 25; step++) {
    const si = Math.floor(rnd()*SHEETS.length), ref = encodeRef(Math.floor(rnd()*ROWS), Math.floor(rnd()*COLS)), k = rnd();
    if (k < .03) { for (const book of [a, b]) { const sh = book.sheets[1]; sh.name = sh.name === 'Calc Sheet' ? 'Renamed' : 'Calc Sheet'; } }
    else if (k < .05) { for (const book of [a, b]) book.sheets.push({name: 'Extra' + step, cells: new Map([['A1', {v: step, t: 'n'}]])}); }
    else if (k < .15) { a.sheets[si].cells.delete(ref); b.sheets[si].cells.delete(ref); }
    else if (k < .25) { // replace the whole map (undo restores a snapshot this way)
      for (const book of [a, b]) book.sheets[si].cells = new Map([...book.sheets[si].cells].map(([r, c]) => [r, JSON.parse(JSON.stringify(c))]));
    } else if (k < .35 && a.sheets[si].cells.get(ref)?.f) { // edits that reset a formula's cached result in place
      for (const book of [a, b]) { const c = book.sheets[si].cells.get(ref); delete c.calculated; c.display = '=' + c.f; }
    } else { const cell = randomCell(SHEETS[si]); a.sheets[si].cells.set(ref, {...cell}); b.sheets[si].cells.set(ref, {...cell}); }
    current.recalculate(a); reference.recalculate(b); checks++;
    const sa = snapshot(a), sb = snapshot(b);
    if (sa !== sb) { const la = sa.split('\n'), lb = sb.split('\n'); const i = la.findIndex((x, j) => x !== lb[j]); throw new Error(`recalculation differs (trial ${trial}, step ${step}): ${la[i]} vs ${lb[i]}`); }
  }
}
{ // Scope: editing one input recalculates only the formulas that depend on it.
  const book = {sheets: [{name: 'S', cells: new Map()}]}, cells = book.sheets[0].cells;
  for (let r = 1; r <= 2000; r++) { cells.set('A' + r, {v: r, t: 'n'}); cells.set('B' + r, {f: 'A' + r + '*2', v: 0, t: 'n'}); }
  cells.set('C1', {f: 'SUM(B1:B10)', v: 0, t: 'n'});
  current.recalculate(book);
  let writes = 0;
  for (const cell of cells.values()) if (cell.f) { let value = cell.calculated; Object.defineProperty(cell, 'calculated', {configurable: true, enumerable: true, get: () => value, set: x => { writes++; value = x; }}); }
  cells.get('A5').v = 500; current.recalculate(book);
  if (cells.get('B5').calculated !== 1000 || cells.get('C1').calculated !== 2 * (55 - 5 + 500)) throw new Error('dependents not recalculated');
  if (writes > 5) throw new Error(`an edit recalculated ${writes} formulas; expected only the 2 that depend on it`);
}
console.log(`Spreadsheets dependency recalculation equivalence: OK (${checks} edits)`);
'''


def test_recalculation_equivalence():
    run = subprocess.run(["node", "-"], input=SCRIPT, capture_output=True, text=True, timeout=300, env={**os.environ, "INKDOS_ROOT": str(ROOT)})
    assert run.returncode == 0, run.stdout + run.stderr
    assert "equivalence: OK" in run.stdout, run.stdout


if __name__ == "__main__":
    test_recalculation_equivalence()
    print("Spreadsheets formula recalculation equivalence contract: OK")
