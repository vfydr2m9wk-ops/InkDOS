#!/usr/bin/env python3
"""Check the vendored third-party libraries (config/vendor-inventory.json) against OSV.dev.

Only package names and versions are sent; no InkDOS files or user data. Exit status 1 when an
advisory is found that is not listed, with its reason, under "accepted_advisories".
Run before each release; needs network access.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'config' / 'vendor-inventory.json'


def query(package: str, ecosystem: str, version: str) -> list[dict]:
    body = json.dumps({'package': {'name': package, 'ecosystem': ecosystem}, 'version': version}).encode()
    req = urllib.request.Request('https://api.osv.dev/v1/query', data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp).get('vulns', [])


def main() -> int:
    inventory = json.loads(INVENTORY.read_text(encoding='utf-8'))
    accepted = inventory.get('accepted_advisories', {})
    packages = sorted({(f['package'], f['ecosystem'], f['version']) for f in inventory['files']})
    open_items = 0
    for package, ecosystem, version in packages:
        vulns = query(package, ecosystem, version)
        if not vulns:
            print(f'ok      {package} {version}')
            continue
        for v in vulns:
            ids = [v['id'], *v.get('aliases', [])]
            reason = next((accepted[i] for i in ids if i in accepted), None)
            label = 'accepted' if reason else 'OPEN'
            open_items += 0 if reason else 1
            print(f'{label:8}{package} {version}: {", ".join(ids)} — {v.get("summary", "")}')
            if reason:
                print(f'        reason: {reason}')
    if open_items:
        print(f'{open_items} advisory(ies) need a decision: update the library or record the reason in accepted_advisories.')
        return 1
    print('No open advisories for vendored libraries.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
