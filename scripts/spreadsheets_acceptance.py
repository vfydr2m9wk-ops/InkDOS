#!/usr/bin/env python3
"""Acceptance criteria for Spreadsheets, sheet by sheet.

Level 1 - nothing is lost:
  open      the workbook opens
  sheets    same sheets, same names, same order
  values    every non-empty reference cell is present with the same value (numbers within a
            relative 1e-6, text exact after Unicode normalisation)
  formulas  every reference formula cell still carries a formula
  merges    the same merged ranges
Level 2 - it reads right:
  display   the text each cell shows matches the reference "as shown" text

The reference is computed independently of InkDOS: the package structure (sheets, formulas, merges)
with openpyxl - a .xls is first converted to .xlsx by LibreOffice - and the cell values, raw and as
shown, from LibreOffice CSV exports of every sheet. Inputs may be private documents: nothing is
written to the repository, the report goes to --out.

    python3 scripts/spreadsheets_acceptance.py book.xlsx old.xls --out /tmp/xls-acceptance
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from presentations_fidelity import ROOT, free_port, run  # noqa: E402

CRITERIA = ('open', 'sheets', 'values', 'formulas', 'merges', 'display')
CSV_FILTER = 'csv:Text - txt - csv (StarCalc):44,34,76,1,,1033,false,true,{shown},false,false,-1'
MAX_CELLS = 200_000


def col_name(c: int) -> str:
    s = ''
    while c:
        c, r = divmod(c - 1, 26)
        s = chr(65 + r) + s
    return s


def norm(s: str) -> str:
    return unicodedata.normalize('NFKC', str(s)).replace('\r\n', '\n').replace('\r', '\n').strip()


def soffice() -> str | None:
    return shutil.which('soffice') or shutil.which('libreoffice')


def reference(src: Path, work: Path) -> dict | None:
    """Sheets, formulas, merges (openpyxl) and raw/shown values per sheet (LibreOffice CSV)."""
    try:
        import openpyxl
    except ImportError:
        print('openpyxl is required (pip install openpyxl)', file=sys.stderr)
        return None
    office = soffice()
    if not office:
        return None
    pkg = src
    if src.suffix.lower() != '.xlsx':
        run([office, '--headless', '--convert-to', 'xlsx', '--outdir', str(work), str(src)], timeout=300)
        pkg = work / (src.stem + '.xlsx')
        if not pkg.exists():
            return None
    try:
        wb = openpyxl.load_workbook(pkg, read_only=False, data_only=False)
    except Exception:
        return None
    sheets = []
    for ws in wb.worksheets:
        formulas = sorted(f'{c.column_letter}{c.row}' for row in ws.iter_rows() for c in row
                          if (isinstance(c.value, str) and c.value.startswith('=') or getattr(c, 'data_type', '') == 'f')
                          and str(c.value).upper() not in ('=TRUE()', '=FALSE()'))  # LibreOffice writes boolean constants as formulas
        sheets.append({'name': ws.title, 'formulas': formulas, 'merges': sorted(str(r) for r in ws.merged_cells.ranges)})
    for shown, key in (('false', 'raw'), ('true', 'shown')):
        out = work / key
        out.mkdir(exist_ok=True)
        run([office, '--headless', '--convert-to', CSV_FILTER.format(shown=shown), '--outdir', str(out), str(src)], timeout=300)
        files = list(out.glob('*.csv'))
        for i, sh in enumerate(sheets):
            cand = [f for f in files if f.stem == f'{src.stem}-{sh["name"]}'] or ([files[0]] if len(sheets) == 1 and files else [])
            cells = {}
            if cand:
                with open(cand[0], newline='', encoding='utf-8', errors='replace') as fh:
                    for r, row in enumerate(csv.reader(fh), 1):
                        for c, v in enumerate(row, 1):
                            if v.strip() and len(cells) < MAX_CELLS:
                                cells[f'{col_name(c)}{r}'] = v
            sh[key] = cells
    return {'sheets': sheets}


# Workbook as the app holds it: sheet names, and per cell its value, formula flag and the text the grid shows.
PROBE = r"""() => { const b=globalThis.__inkdosSpreadsheetsS1.session.book, grid=globalThis.InkDOS2Spreadsheets?.GridDisplay;
  return b.sheets.map(s=>({name:s.name, merges:(s.merges||[]).map(m=>typeof m==='string'?m:(m.ref||m.range||JSON.stringify(m))),
    cells:Object.fromEntries([...(s.cells instanceof Map?s.cells.entries():Object.entries(s.cells||{}))].filter(([k,c])=>c&&((c.v!==''&&c.v!=null)||c.f)).slice(0,200000)
      .map(([k,c])=>[k,{v:c?.v??null,f:!!(c&&c.f),d:grid?grid.display(c):(c?.display??(c?.v==null?'':String(c.v)))}]))})) }"""


DATE_RE = re.compile(r'^(\d{1,4})[/.-](\d{1,2})[/.-](\d{1,4})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$')


def date_serials(text: str) -> set[float]:
    """Excel 1900-system serials a date text can mean (day/month order is locale-dependent, so both)."""
    import datetime
    m = DATE_RE.match(norm(text))
    if not m:
        return set()
    a, b, c = (int(x) for x in m.group(1, 2, 3))
    frac = (int(m.group(4) or 0) * 3600 + int(m.group(5) or 0) * 60 + int(m.group(6) or 0)) / 86400
    out = set()
    for y, mo, d in ((a, b, c), (c, a, b), (c, b, a)):
        if y < 100:
            y += 2000 if y < 30 else 1900
        try:
            out.add((datetime.date(y, mo, d) - datetime.date(1899, 12, 30)).days + frac)
        except ValueError:
            pass
    return out


def number_readings(text: str) -> set[tuple[float, int]]:
    """(value, decimals) readings of a shown number; ambiguous separators give both readings."""
    t = norm(text).replace('\u00a0', '').replace(' ', '')
    pct = t.endswith('%')
    t = re.sub(r'^[^\d+-]+', '', t.rstrip('%'))
    if not re.fullmatch(r'[+-]?[\d.,]*\d', t or 'x'):
        return set()
    out = set()
    for dec in ('.', ','):
        other = ',' if dec == '.' else '.'
        if t.count(dec) > 1:
            continue
        whole, _, frac = t.partition(dec)
        if re.search(r'\d' + re.escape(other) + r'(?!\d{3}(\D|$))', whole):
            continue  # thousands groups must have three digits
        try:
            v = float(whole.replace(other, '') + ('.' + frac if frac else ''))
        except ValueError:
            continue
        out.add((round(v / (100 if pct else 1), 9), len(frac)))
    return out


def same_display(want: str, got: str) -> bool:
    """Shown text, tolerant only of regional conventions: date order and decimal/thousands separators."""
    if norm(want) == norm(got):
        return True
    dw, dg = date_serials(want), date_serials(got)
    if dw and dg:
        return bool(dw & dg)
    nw, ng = number_readings(want), number_readings(got)
    return bool(nw & ng)


def same_value(ref: str, cell: dict) -> bool:
    v = cell.get('v')
    if v is None or v == '':
        return False
    ds = date_serials(ref)
    if ds and isinstance(v, (int, float)) and not isinstance(v, bool):
        return any(abs(d - v) < 1 / 86400 + 1e-9 or int(d) == int(v) for d in ds)
    try:
        r = ref.strip().replace(',', '')
        a, b = (float(r[:-1]) / 100 if r.endswith('%') else float(r)), float(v)
        return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))
    except (TypeError, ValueError):
        pass
    if isinstance(v, bool) or str(v).upper() in ('TRUE', 'FALSE'):
        return norm(ref).upper() == str(v).upper()
    return norm(ref) == norm(v) or norm(ref) == norm(cell.get('d', ''))


def check_book(page, src: Path, work: Path) -> dict:
    ref = reference(src, work)
    if not ref:
        return {'file': src.name, 'skipped': True, 'failed': {c: 0 for c in CRITERIA}, 'sheets': []}
    page.set_input_files('#fileInput', str(src))
    try:
        page.wait_for_function("()=>!!globalThis.__inkdosSpreadsheetsS1?.session?.book?.loaded", timeout=120000)
    except Exception:
        return {'file': src.name, 'failed': {'open': 1}, 'sheets': []}
    page.wait_for_timeout(500)
    got = page.evaluate(PROBE)
    failed = {c: 0 for c in CRITERIA}
    if [s['name'] for s in got] != [s['name'] for s in ref['sheets']]:
        failed['sheets'] = 1
    report = []
    by_name = {s['name']: s for s in got}
    for rs in ref['sheets']:
        gs = by_name.get(rs['name'])
        if not gs:
            continue
        cells = gs['cells']
        lost = [k for k, v in rs.get('raw', {}).items() if k not in cells or not same_value(v, cells[k])]
        no_formula = [k for k in rs['formulas'] if k not in cells or not cells[k]['f']]
        merges_ref, merges_got = set(rs['merges']), set(gs['merges'])
        display = [k for k, v in rs.get('shown', {}).items() if k in cells and not same_display(v, cells[k]['d'])]
        res = {'sheet': rs['name'], 'cells': len(rs.get('raw', {})), 'lost': lost[:30], 'lostCount': len(lost),
               'formulasLost': no_formula[:30], 'mergesMissing': sorted(merges_ref - merges_got)[:20],
               'display': [{'cell': k, 'want': rs['shown'][k], 'got': cells[k]['d']} for k in display[:30]], 'displayCount': len(display)}
        for c, bad in (('values', lost), ('formulas', no_formula), ('merges', merges_ref - merges_got), ('display', display)):
            if bad:
                failed[c] += 1
        report.append(res)
    return {'file': src.name, 'failed': failed, 'sheets': report}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+', type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--chromium', default='/opt/pw-browsers/chromium')
    args = ap.parse_args()
    from playwright.sync_api import sync_playwright
    args.out.mkdir(parents=True, exist_ok=True)
    port = free_port()
    server = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    report = []
    try:
        with sync_playwright() as pw:
            launch = {'headless': True}
            if Path(args.chromium).exists():
                launch['executable_path'] = args.chromium
            browser = pw.chromium.launch(**launch)
            for src in args.files:
                src = src.resolve()
                work = args.out / re.sub(r'[^\w.-]+', '_', src.name)
                work.mkdir(parents=True, exist_ok=True)
                ctx = browser.new_context(service_workers='block', viewport={'width': 1300, 'height': 900})
                page = ctx.new_page()
                errors: list[str] = []
                page.on('pageerror', lambda e: errors.append(str(e)[:200]))
                try:
                    page.goto(f'http://127.0.0.1:{port}/apps/spreadsheets/', wait_until='load')
                    page.wait_for_timeout(600)
                    r = check_book(page, src, work)
                except Exception as e:
                    r = {'file': src.name, 'failed': {'open': 1}, 'error': str(e)[:200], 'sheets': []}
                finally:
                    ctx.close()
                if errors:
                    r['errors'] = errors[:5]
                report.append(r)
                bad = 'skipped (reference cannot read it)' if r.get('skipped') else (', '.join(f'{c} {n}' for c, n in r['failed'].items() if n) or 'all criteria pass')
                print(f"{r['file']}: {bad}", flush=True)
            browser.close()
    finally:
        server.terminate()
    (args.out / 'spreadsheets-acceptance.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    return 1 if any(any(r['failed'].values()) for r in report) else 0


if __name__ == '__main__':
    sys.exit(main())
