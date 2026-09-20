#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'docs/2.4.3-UPGRADE-VALIDATION.md'; VALIDATION=ROOT/'scripts/run_release_validation.py'; AUTH=ROOT/'config/release-authorization.json'
def main():
 plan=PLAN.read_text(encoding='utf-8'); validation=VALIDATION.read_text(encoding='utf-8')
 assert '## Repository-verifiable prerequisites' in plan
 assert '## Real Windows/device validation' in plan
 assert '## Publication gate' in plan
 assert plan.index('## Repository-verifiable prerequisites') < plan.index('## Real Windows/device validation') < plan.index('## Publication gate')
 for item in ('Windows version','WebView2 version','signature verification result','source 2.4.0 build','destination 2.4.3 commit/tag candidate','100%, 125%, and 150% display scaling','touch/pen fill behavior'):
  assert item in plan,f'missing native upgrade evidence requirement: {item}'
 publication=plan.split('## Publication gate',1)[1]
 assert 'explicitly waived by the user' in publication
 assert 'does **not** count as a Windows validation pass' in publication
 assert 'post-launch updater validation remains required' in publication
 assert 'explicit user-authorized waiver' in publication and 'no fabricated evidence' in publication
 assert 'explicit user publication authorization' in publication
 for test in ('tests/test_243_release_version_agnostic_contract.py','tests/test_243_updater_manifest_dry_run_contract.py','tests/test_243_release_authorization_contract.py'):
  assert test in validation,f'persistent release validation omits {test}'
 import json
 state=json.loads(AUTH.read_text(encoding='utf-8'))
 assert state['windowsDeviceUpgradeValidated'] is False
 assert state['windowsDeviceUpgradeWaived'] is True
 assert state['explicitUserAuthorization'] is True
 print('InkDOS 2.4.3 upgrade/release gate classification contract passed with explicit waiver path.')
if __name__=='__main__': main()
