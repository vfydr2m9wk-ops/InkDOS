#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK_MODEL = ROOT / 'apps' / 'epub' / 'engine' / 'book-model.js'


def main() -> None:
    probe = f"""
const fs=require('fs');
globalThis.InkDOS2Epub={{ContentProjector:{{}}}};
eval(fs.readFileSync({json.dumps(str(BOOK_MODEL))},'utf8'));
const resolve=globalThis.InkDOS2Epub.BookModel.resolve;
const result={{
  resource:resolve('EPUB/package.opf','../Text/chapter%201.xhtml?edition=2#sec%201'),
  queryOnly:resolve('EPUB/package.opf','?edition=2#metadata'),
  fragmentOnly:resolve('EPUB/Text/chapter 1.xhtml','#part%202'),
  external:resolve('EPUB/package.opf','https://example.invalid/book.xhtml?edition=2#part'),
}};
process.stdout.write(JSON.stringify(result));
"""
    proc = subprocess.run(
        ['node', '-e', probe],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stderr or proc.stdout)
    result = json.loads(proc.stdout)
    assert result['resource'] == {'path': 'Text/chapter 1.xhtml', 'fragment': 'sec 1'}, result
    assert result['queryOnly'] == {'path': 'EPUB/package.opf', 'fragment': 'metadata'}, result
    assert result['fragmentOnly'] == {'path': 'EPUB/Text/chapter 1.xhtml', 'fragment': 'part 2'}, result
    assert result['external'] == {
        'external': True,
        'href': 'https://example.invalid/book.xhtml?edition=2#part',
    }, result
    print('EPUB URL reference contract: OK')


if __name__ == '__main__':
    main()
