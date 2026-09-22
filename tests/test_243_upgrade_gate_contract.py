#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'docs' / '2.4.3-UPGRADE-VALIDATION.md'
VALIDATION = ROOT / 'scripts' / 'run_release_validation.py'


def main():
    plan = PLAN.read_text(encoding='utf-8')
    validation = VALIDATION.read_text(encoding='utf-8')

    # Repository-verifiable checks and native/device evidence are distinct gates.
    assert '## Repository-verifiable prerequisites' in plan
    assert '## Real Windows/device validation' in plan
    assert '## Publication gate' in plan
    assert plan.index('## Repository-verifiable prerequisites') < plan.index('## Real Windows/device validation') < plan.index('## Publication gate')

    native_evidence = [
        'Windows version', 'WebView2 version', 'signature verification result',
        'source 2.4.0 build', 'destination 2.4.3 commit/tag candidate',
        '100%, 125%, and 150% display scaling', 'touch/pen fill behavior',
    ]
    for item in native_evidence:
        assert item in plan, f'missing native upgrade evidence requirement: {item}'

    # Publication remains blocked until the real device upgrade test completes.
    publication = plan.split('## Publication gate', 1)[1]
    assert 'real Windows/device upgrade test are complete' in publication
    assert 'explicit user authorization' in publication

    # Dry-run updater and version-agnostic contracts are mandatory in the persistent gate.
    for test in (
        'tests/test_243_release_version_agnostic_contract.py',
        'tests/test_243_updater_manifest_dry_run_contract.py',
    ):
        assert test in validation, f'persistent release validation omits {test}'

    print('InkDOS 2.4.3 upgrade/release gate classification contract passed.')


if __name__ == '__main__':
    main()
