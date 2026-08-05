#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse
import os
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXT = {'.html', '.css', '.js', '.json', '.md', '.cff', '.webmanifest', '.txt', '.py', '.yml', '.yaml', '.xml'}
IGNORED_PARTS = {'.git', 'dist', '__pycache__', '.DS_Store'}
DEFAULT_FORBIDDEN = [
    '/mnt/data', '/tmp/inkdesk', '/home/oai', 'file:///Users/', 'C:\\Users\\',
    'Local Office Suite', 'External Display Browser'
]
EMAIL_BYTES = re.compile(rb'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
EMAIL_TEXT = re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
ABS_PATH = re.compile(rb'''(?i)(?:/home/[^\s"']+|/mnt/data/[^\s"']+|[A-Z]:\\Users\\[^\s"']+)''')


def files():
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in IGNORED_PARTS for part in rel.parts):
            continue
        yield path, rel.as_posix()


def term_encodings(term: str):
    variants = {term.encode('utf-8', 'ignore').lower(), term.encode('utf-16le', 'ignore').lower()}
    try:
        variants.add(term.encode('latin-1').lower())
    except UnicodeEncodeError:
        pass
    return [value for value in variants if value]


def scan_payload(data: bytes, label: str, forbidden: list[str], errors: list[str]) -> None:
    low = data.lower()
    for term in forbidden:
        if any(encoded in low for encoded in term_encodings(term)):
            errors.append(f'{label}: forbidden term present')
    for match in EMAIL_BYTES.findall(data):
        email = match.decode('utf-8', 'replace')
        if not email.endswith('@users.noreply.github.com'):
            errors.append(f'{label}: email address present: {email}')
    # UTF-16LE strings are common in legacy CFB/XLS metadata.
    utf16 = data.decode('utf-16le', 'ignore')
    for email in EMAIL_TEXT.findall(utf16):
        if not email.endswith('@users.noreply.github.com'):
            errors.append(f'{label}: UTF-16 email address present: {email}')


def scan_zip(path: Path, rel: str, forbidden: list[str], errors: list[str]) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                if info.file_size > 25 * 1024 * 1024:
                    errors.append(f'{rel}:{info.filename}: oversized audit entry')
                    continue
                scan_payload(archive.read(info), f'{rel}:{info.filename}', forbidden, errors)
    except Exception as exc:
        errors.append(f'{rel}: ZIP metadata/content unreadable: {exc}')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--forbidden', action='append', default=[])
    args = parser.parse_args()
    forbidden = DEFAULT_FORBIDDEN + args.forbidden + [x for x in os.environ.get('INKDESK_AUDIT_EXTRA_TERMS', '').split('|') if x]
    errors: list[str] = []

    for path, rel in files():
        data = path.read_bytes()
        if rel != 'scripts/audit_source.py':
            scan_payload(data, rel, forbidden, errors)
            if any(term.lower() in rel.lower() for term in forbidden):
                errors.append(f'{rel}: forbidden term in filename/path')

        if path.suffix.lower() in TEXT_EXT and rel != 'scripts/audit_source.py':
            if ABS_PATH.search(data):
                errors.append(f'{rel}: absolute local path present')

        if path.suffix.lower() in {'.docx', '.xlsx', '.pptx'}:
            scan_zip(path, rel, forbidden, errors)
            try:
                with zipfile.ZipFile(path) as archive:
                    for name in ('docProps/core.xml', 'docProps/custom.xml', 'docProps/app.xml'):
                        if name not in archive.namelist():
                            continue
                        text = archive.read(name).decode('utf-8', 'replace')
                        for tag in ('creator', 'lastModifiedBy'):
                            values = re.findall(rf'<[^>]*{tag}[^>]*>(.*?)</', text, re.I | re.S)
                            for value in values:
                                value = re.sub('<.*?>', '', value).strip()
                                if value and value != 'InkDesk QA':
                                    errors.append(f'{rel}:{name}: unexpected {tag}={value!r}')
            except Exception as exc:
                errors.append(f'{rel}: OOXML metadata unreadable: {exc}')

        if path.suffix.lower() == '.pdf':
            try:
                from pypdf import PdfReader
                metadata = PdfReader(str(path)).metadata or {}
                for key, value in metadata.items():
                    if key in {'/Author', '/Creator', '/Producer'} and str(value) not in {'', 'InkDesk QA'}:
                        errors.append(f'{rel}: unexpected PDF {key}={value!r}')
            except Exception as exc:
                errors.append(f'{rel}: PDF metadata unreadable: {exc}')

        if path.suffix.lower() == '.png':
            try:
                from PIL import Image
                with Image.open(path) as image:
                    unsafe = set(image.info) - {'dpi', 'transparency', 'srgb', 'gamma'}
                    if unsafe:
                        errors.append(f'{rel}: PNG ancillary metadata keys: {sorted(unsafe)}')
            except Exception as exc:
                errors.append(f'{rel}: PNG unreadable: {exc}')

    if errors:
        print('\n'.join('ERROR: ' + message for message in sorted(set(errors))))
        return 1
    print('OK: privacy and metadata audit passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
