#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_ROOTS = ('modules', 'core', 'legacy')
ALLOWED_SHARED_FILES = {'ui-density.js', 'ui-density.css'}


def main():
    bad = [name for name in FORBIDDEN_ROOTS if (ROOT / name).exists()]

    shared = ROOT / 'shared'
    if shared.exists():
        unexpected = sorted(
            path.relative_to(shared).as_posix()
            for path in shared.rglob('*')
            if path.is_file() and path.relative_to(shared).as_posix() not in ALLOWED_SHARED_FILES
        )
        if unexpected:
            bad.extend(f'shared/{name}' for name in unexpected)

    retired_pdfjs = ROOT / 'shared' / 'vendor' / 'pdfjs'
    if retired_pdfjs.exists() and 'shared/vendor/pdfjs' not in bad:
        bad.append('shared/vendor/pdfjs')

    if bad:
        raise SystemExit('Legacy/cross-suite runtime roots present: ' + ', '.join(bad))
    print('No retired 1.x suite runtime roots are present; approved shared density assets are allowed.')


if __name__ == '__main__':
    main()
