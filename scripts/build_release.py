#!/usr/bin/env python3
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_PARTS = {'.git', 'dist', '__pycache__', '.DS_Store'}


def source_files(output_directory: Path):
    output_directory = output_directory.resolve()
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        resolved = path.resolve()
        try:
            resolved.relative_to(output_directory)
            continue
        except ValueError:
            pass
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDE_PARTS for part in relative.parts):
            continue
        yield path, relative.as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default='dist')
    args = parser.parse_args()
    version = json.loads((ROOT / 'VERSION.json').read_text())['version']
    output_directory = (ROOT / args.output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    archive = output_directory / f'InkDesk_v{version}.zip'
    checksum = archive.with_suffix(archive.suffix + '.sha256')
    archive.unlink(missing_ok=True)
    checksum.unlink(missing_ok=True)

    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path, relative in source_files(output_directory):
            info = zipfile.ZipInfo(relative, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            package.writestr(info, path.read_bytes())

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(digest + '  ' + archive.name + '\n')
    print(archive)
    print(digest)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
