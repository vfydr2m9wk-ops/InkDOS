#!/usr/bin/env python3
import contextlib,hashlib,importlib.util,io,json,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]; S=R/'desktop/scripts/validate_release_authorization.py'
_spec=importlib.util.spec_from_file_location('inkdos_validate_release_authorization',S); V=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(V)
class Result:
 def __init__(self,returncode,stdout='',stderr=''): self.returncode=returncode; self.stdout=stdout; self.stderr=stderr
def invoke_validator(root,state,assets):
 old_root,old_argv=V.ROOT,sys.argv; out,err=io.StringIO(),io.StringIO(); V.ROOT=root; sys.argv=[str(S),'--version','2.4.3','--state',str(state),'--assets',str(assets)]
 try:
  with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err): V.main()
  rc=0
 except SystemExit as exc:
  rc=exc.code if isinstance(exc.code,int) else 1
  if exc.code and not isinstance(exc.code,int): err.write(str(exc.code))
 finally: V.ROOT=old_root; sys.argv=old_argv
 return Result(rc,out.getvalue(),err.getvalue())
BASE_EVIDENCE={'platform':'windows','fromVersion':'2.4.0','toVersion':'2.4.3','observedBeforeVersion':'2.4.0','observedAfterVersion':'2.4.3','webview2':True,'upgradeResult':'pass','testedAtUtc':'2026-09-19T20:00:00Z','artifactName':'InkDOS_2.4.3_x64-setup.exe','artifactSha256':'','windowsVersion':'Windows 11 24H2','windowsArchitecture':'X64','webview2Version':'140.0.3485.81','signatureVerified':True,'signerSubject':'CN=InkDOS Release Test','signerThumbprint':'0123456789abcdef0123456789abcdef01234567','inAppUpdaterResult':'pass','userFilesIntegrityResult':'pass','regressionScenariosResult':'pass','displayScalingResult':'pass','rebootLaunchResult':'pass','updaterNoRepeatOfferResult':'pass','touchPenResult':'not-applicable'}
VALIDATED={'version':'2.4.3','windowsDeviceUpgradeValidated':True,'windowsDeviceUpgradeWaived':False,'explicitUserAuthorization':True,'evidence':'','evidenceSha256':'','waiverReason':''}
WAIVED={'version':'2.4.3','windowsDeviceUpgradeValidated':False,'windowsDeviceUpgradeWaived':True,'explicitUserAuthorization':True,'evidence':'','evidenceSha256':'','waiverReason':'Explicit pre-publication Windows/WebView2 waiver; validate after launch.'}
def run(d,evidence=None,inventory_mode='good'):
 with tempfile.TemporaryDirectory(prefix='inkdos-release-auth-contract-') as td:
  td=Path(td); synthetic_root=td/'repo'; synthetic_script=synthetic_root/'desktop/scripts/validate_release_authorization.py'; synthetic_script.parent.mkdir(parents=True); synthetic_script.write_bytes(S.read_bytes())
  assets=synthetic_root/'release-final'; assets.mkdir(); artifact=assets/'InkDOS_2.4.3_x64-setup.exe'; artifact.write_bytes(b'tested-windows-installer')
  digest=hashlib.sha256(artifact.read_bytes()).hexdigest(); (assets/'SHA256SUMS').write_text(f'{digest}  {artifact.name}\n',encoding='utf-8')
  d=dict(d)
  if d.get('windowsDeviceUpgradeValidated'):
   evdata=dict(evidence or BASE_EVIDENCE)
   if not evdata.get('artifactSha256'): evdata['artifactSha256']=digest
   if inventory_mode=='wrong': (assets/'SHA256SUMS').write_text(f"{'0'*64}  {artifact.name}\n",encoding='utf-8')
   elif inventory_mode=='missing': (assets/'SHA256SUMS').unlink()
   elif inventory_mode=='duplicate': (assets/'SHA256SUMS').write_text(f'{digest}  {artifact.name}\n{digest}  {artifact.name}\n',encoding='utf-8')
   ev=synthetic_root/'windows-upgrade-evidence.json'; ev.write_text(json.dumps(evdata,sort_keys=True),encoding='utf-8')
   d['evidence']=d.get('evidence') or ev.relative_to(synthetic_root).as_posix(); d['evidenceSha256']=d.get('evidenceSha256') or hashlib.sha256(ev.read_bytes()).hexdigest()
  p=td/'state.json'; p.write_text(json.dumps(d)); return invoke_validator(synthetic_root,p,assets)
def main():
 # Both supported authorization modes must be explicit and mutually exclusive.
 assert run(VALIDATED).returncode==0
 w=run(WAIVED); assert w.returncode==0 and 'waiver' in w.stdout.lower(),w.stdout
 for d in (
  dict(WAIVED,explicitUserAuthorization=False),
  dict(WAIVED,windowsDeviceUpgradeWaived=False),
  dict(WAIVED,windowsDeviceUpgradeValidated=True),
  dict(WAIVED,waiverReason=''),
  dict(WAIVED,evidence='fake.json'),
  dict(WAIVED,evidenceSha256='0'*64),
 ):
  assert run(d).returncode!=0,d
 # Verified-evidence mode remains fail-closed and binds exact artifact bytes/inventory.
 wrong_hash=dict(BASE_EVIDENCE,artifactSha256='b'*64); assert run(VALIDATED,wrong_hash).returncode!=0
 wrong_name=dict(BASE_EVIDENCE,artifactName='other.exe'); assert run(VALIDATED,wrong_name).returncode!=0
 for mode in ('wrong','missing','duplicate'): assert run(VALIDATED,inventory_mode=mode).returncode!=0,mode
 for k,v in (('explicitUserAuthorization',False),('evidenceSha256','0'*64),('evidence','../outside.json'),('waiverReason','not allowed with evidence')):
  d=dict(VALIDATED);d[k]=v;assert run(d).returncode!=0,(k,run(d).stderr)
 bad=[]
 for k,v in (('platform','linux'),('fromVersion','2.4.2'),('toVersion','2.4.4'),('observedBeforeVersion','2.3.0'),('observedAfterVersion','2.4.2'),('webview2',False),('upgradeResult','fail'),('signatureVerified',False),('signerSubject',''),('signerThumbprint','bad'),('windowsVersion',''),('windowsArchitecture','Unknown'),('webview2Version',''),('testedAtUtc','not-a-date'),('artifactName','../evil.exe'),('artifactSha256','bad'),('inAppUpdaterResult','fail'),('userFilesIntegrityResult','fail'),('regressionScenariosResult','fail'),('displayScalingResult','fail'),('rebootLaunchResult','fail'),('updaterNoRepeatOfferResult','fail'),('touchPenResult','fail')):
  e=dict(BASE_EVIDENCE);e[k]=v;bad.append((k,e))
 for k,e in bad: assert run(VALIDATED,e).returncode!=0,k
 extra=dict(BASE_EVIDENCE,notes='unstructured'); assert run(VALIDATED,extra).returncode!=0
 future=dict(BASE_EVIDENCE,testedAtUtc='2999-01-01T00:00:00Z'); assert run(VALIDATED,future).returncode!=0
 flow=(R/'.github/workflows/release.yml').read_text(); assert '--assets release-final' in flow; assert 'Validate explicit publication authorization' in flow and flow.index('Validate explicit publication authorization')<flow.index('Publish verified release transactionally')
 state=json.loads((R/'config/release-authorization.json').read_text()); assert not state['windowsDeviceUpgradeValidated'] and state['windowsDeviceUpgradeWaived'] and state['explicitUserAuthorization']; assert state['waiverReason'] and not state['evidence'] and not state['evidenceSha256']
 print('InkDOS 2.4.3 release authorization evidence/waiver contract passed.')
if __name__=='__main__': main()
