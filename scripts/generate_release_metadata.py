#!/usr/bin/env python3
"""Generate deterministic, non-identifying release manifests for InkDesk."""
from __future__ import annotations
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {'.git', 'dist', '__pycache__', '.DS_Store'}
SOURCE_MANIFEST = 'SOURCE_MANIFEST.json'
CHECKSUM_MANIFEST = 'RUNTIME_CHECKSUMS.sha256'
RELEASE_MANIFEST = 'RELEASE_MANIFEST.json'
SBOM = 'SBOM.spdx.json'
GENERATED = {SOURCE_MANIFEST, CHECKSUM_MANIFEST, RELEASE_MANIFEST, SBOM}


def distributable_files():
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        yield path, rel.as_posix()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + '\n')


def main() -> int:
    version_data = json.loads((ROOT / 'VERSION.json').read_text())
    version = version_data['version']
    released = version_data.get('date', '2026-08-05')

    sbom = {
        'spdxVersion': 'SPDX-2.3',
        'dataLicense': 'CC0-1.0',
        'SPDXID': 'SPDXRef-DOCUMENT',
        'name': f'InkDesk-{version}',
        'documentNamespace': f'https://github.com/vfydr2m9wk-ops/InkDesk/releases/tag/v{version}/sbom',
        'creationInfo': {
            'created': released + 'T00:00:00Z',
            'creators': ['Tool: InkDesk release metadata generator']
        },
        'packages': [
            {
                'name': 'InkDesk', 'SPDXID': 'SPDXRef-Package-InkDesk',
                'versionInfo': version, 'downloadLocation': 'NOASSERTION',
                'filesAnalyzed': False, 'licenseConcluded': 'MIT',
                'licenseDeclared': 'MIT', 'copyrightText': 'NOASSERTION'
            },
            {
                'name': 'JSZip', 'SPDXID': 'SPDXRef-Package-JSZip',
                'versionInfo': '3.10.1', 'downloadLocation': 'NOASSERTION',
                'filesAnalyzed': False, 'licenseConcluded': 'MIT',
                'licenseDeclared': 'MIT', 'copyrightText': 'NOASSERTION'
            },
            {
                'name': 'pako inflate bundle', 'SPDXID': 'SPDXRef-Package-Pako',
                'versionInfo': '1.0.11', 'downloadLocation': 'NOASSERTION',
                'filesAnalyzed': False, 'licenseConcluded': 'MIT',
                'licenseDeclared': 'MIT', 'copyrightText': 'NOASSERTION'
            },
            {
                'name': 'PDF.js', 'SPDXID': 'SPDXRef-Package-PDFJS',
                'versionInfo': '3.11.174', 'downloadLocation': 'NOASSERTION',
                'filesAnalyzed': False, 'licenseConcluded': 'Apache-2.0',
                'licenseDeclared': 'Apache-2.0', 'copyrightText': 'NOASSERTION'
            }
        ],
        'relationships': [
            {'spdxElementId': 'SPDXRef-DOCUMENT', 'relationshipType': 'DESCRIBES', 'relatedSpdxElement': 'SPDXRef-Package-InkDesk'},
            {'spdxElementId': 'SPDXRef-Package-InkDesk', 'relationshipType': 'DEPENDS_ON', 'relatedSpdxElement': 'SPDXRef-Package-JSZip'},
            {'spdxElementId': 'SPDXRef-Package-InkDesk', 'relationshipType': 'DEPENDS_ON', 'relatedSpdxElement': 'SPDXRef-Package-Pako'}
            ,{'spdxElementId': 'SPDXRef-Package-InkDesk', 'relationshipType': 'DEPENDS_ON', 'relatedSpdxElement': 'SPDXRef-Package-PDFJS'}
        ]
    }
    write_json(ROOT / SBOM, sbom)

    current = list(distributable_files())
    final_count = len(current)
    release_manifest = {
        'schemaVersion': 2,
        'name': 'InkDesk',
        'version': version,
        'channel': version_data.get('releaseChannel', 'beta'),
        'releaseName': version_data.get('releaseName', ''),
        'releaseDate': released,
        'archiveName': f'InkDesk_v{version}.zip',
        'repository': version_data.get('repository'),
        'workspaces': ['documents', 'spreadsheets', 'presentations', 'pdf'],
        'syntheticFixtures': [
            'tests/fixtures/inkdesk-letterhead-a4.docx',
            'tests/fixtures/inkdesk-letterhead-a4-bom.docx',
            'tests/fixtures/inkdesk-prescription-a4.xls',
            'tests/fixtures/inkdesk-prescription-a4.xlsx',
            'tests/fixtures/inkdesk-presentation-layout.pptx',
            'tests/fixtures/inkdesk-pdf-sample.pdf',
            'tests/fixtures/inkdesk-pdf-long-4000-pages.pdf'
        ],
        'privacy': {
            'privateReferenceFilesIncluded': False,
            'fixtureMetadataNormalized': True,
            'repositoryImagesMetadataStripped': True,
            'localBuildPathsIncluded': False
        },
        'validation': [
            'python3 scripts/check_no_legacy_runtime.py',
            'python3 scripts/validate_repository.py',
            'python3 scripts/audit_source.py',
            'python3 -m unittest discover -s tests -p test_*.py',
            'python3 scripts/run_browser_regressions.py'
        ],
        'distributableFileCount': final_count,
        'sourceManifest': SOURCE_MANIFEST,
        'checksumManifest': CHECKSUM_MANIFEST,
        'sbom': SBOM
    }
    write_json(ROOT / RELEASE_MANIFEST, release_manifest)

    source_entries = []
    for path, rel in distributable_files():
        if rel in {SOURCE_MANIFEST, CHECKSUM_MANIFEST}:
            continue
        source_entries.append({'path': rel, 'bytes': path.stat().st_size, 'sha256': sha256(path)})
    source_manifest = {
        'schemaVersion': 2,
        'name': 'InkDesk source manifest',
        'version': version,
        'generatedFrom': 'local release candidate',
        'exclusions': [SOURCE_MANIFEST, CHECKSUM_MANIFEST, 'dist/', '.git/', '__pycache__/'],
        'fileCount': len(source_entries),
        'files': source_entries
    }
    write_json(ROOT / SOURCE_MANIFEST, source_manifest)

    checksum_lines = []
    for path, rel in distributable_files():
        if rel == CHECKSUM_MANIFEST:
            continue
        checksum_lines.append(f'{sha256(path)}  {rel}')
    (ROOT / CHECKSUM_MANIFEST).write_text('\n'.join(checksum_lines) + '\n')

    # Update the final count now that all generated files exist.
    release_manifest['distributableFileCount'] = sum(1 for _ in distributable_files())
    write_json(ROOT / RELEASE_MANIFEST, release_manifest)

    # RELEASE_MANIFEST changed after the first hash pass; refresh both manifests.
    source_entries = []
    for path, rel in distributable_files():
        if rel in {SOURCE_MANIFEST, CHECKSUM_MANIFEST}:
            continue
        source_entries.append({'path': rel, 'bytes': path.stat().st_size, 'sha256': sha256(path)})
    source_manifest['fileCount'] = len(source_entries)
    source_manifest['files'] = source_entries
    write_json(ROOT / SOURCE_MANIFEST, source_manifest)
    checksum_lines = []
    for path, rel in distributable_files():
        if rel == CHECKSUM_MANIFEST:
            continue
        checksum_lines.append(f'{sha256(path)}  {rel}')
    (ROOT / CHECKSUM_MANIFEST).write_text('\n'.join(checksum_lines) + '\n')

    print(f'OK: generated release metadata for {version} ({release_manifest["distributableFileCount"]} distributable files).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
