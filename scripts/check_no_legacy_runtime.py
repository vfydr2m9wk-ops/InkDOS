#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN=('shared','modules','core','legacy','shared/vendor/pdfjs')
def main():
    bad=[x for x in FORBIDDEN if (ROOT/x).exists()]
    if bad: raise SystemExit('Legacy/cross-suite runtime roots present: '+', '.join(bad))
    print('No retired 1.x suite runtime roots are present.')
if __name__=='__main__': main()
