#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'release.yml'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    text = WORKFLOW.read_text(encoding='utf-8')
    publish = text.index('  publish:')
    section = text[publish:]

    bundle = section.index('Validate final release bundle coherence')
    transaction = section.index('Publish verified release transactionally')
    first_gh = section.index('gh release ')
    promote = section.index('gh release edit "$RELEASE_TAG"')
    remote_inventory = section.index('REMOTE_ASSETS')
    exact_inventory = section.index('REMOTE_SORTED')

    require(bundle < transaction < first_gh,
            'publication can start before final-bundle verification')
    require(remote_inventory < exact_inventory < promote,
            'public promotion can occur before exact remote inventory verification')
    require("comm -3 /tmp/local-assets.txt /tmp/remote-assets.txt" in section,
            'transaction does not reject missing or stale remote draft assets')
    require('Refusing to promote draft with non-exact asset inventory' in section,
            'transaction lacks fail-closed exact-inventory guard')
    require('--draft=false' in section and promote < section.index('--draft=false', promote),
            'release is not explicitly promoted only at the final step')
    print('InkDOS 2.4.3 publication transaction contract passed.')


if __name__ == '__main__':
    main()
