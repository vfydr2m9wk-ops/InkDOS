#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'desktop/scripts/collect_windows_upgrade_evidence.ps1'
s=p.read_text(encoding='utf-8')
required=['Get-FileHash -Algorithm SHA256','Get-AuthenticodeSignature','SignatureStatus]::Valid','Windows NT\\CurrentVersion','ProductName','DisplayVersion','CurrentBuildNumber','UBR','RuntimeInformation]::OSArchitecture','windowsArchitecture=$windowsArchitecture','Microsoft\\EdgeUpdate\\Clients','[DateTime]::UtcNow','ConvertTo-Json',"platform='windows'",'artifactSha256=$hash','signatureVerified=$signatureVerified','SignerCertificate','signerSubject=$signerSubject','signerThumbprint=$signerThumbprint','ObservedBeforeVersion','ObservedAfterVersion','InAppUpdaterResult','UserFilesIntegrityResult','RegressionScenariosResult','DisplayScalingResult','RebootLaunchResult','UpdaterNoRepeatOfferResult','TouchPenResult','observedBeforeVersion=$ObservedBeforeVersion','observedAfterVersion=$ObservedAfterVersion']
for token in required: assert token in s, token
assert "throw 'Windows version could not be determined from the CurrentVersion registry key.'" in s
assert "throw 'Windows CurrentVersion registry data is incomplete or invalid.'" in s
assert '[System.Environment]::OSVersion.VersionString' not in s
assert "throw 'Microsoft Edge WebView2 Runtime version could not be determined from supported registry locations.'" in s
assert 'HKLM:\\SOFTWARE\\Microsoft\\EdgeUpdate\\Clients' in s
assert 'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients' in s
assert 'HKCU:\\Software\\Microsoft\\EdgeUpdate\\Clients' in s
assert 'HKCU:\\Software\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients' in s
assert "$candidate -match '^\\d+\\.\\d+\\.\\d+\\.\\d+$'" in s
assert 'if (-not $signatureVerified)' in s and "if ($UpgradeResult -ne 'pass')" in s
assert "if ($ObservedBeforeVersion -ne $FromVersion)" in s
assert "if ($ObservedAfterVersion -ne $ToVersion)" in s
assert "ValidateSet('pass','not-applicable')" in s
assert "Required Windows upgrade validation step is not pass." in s
# Failed or interrupted collection must not preserve stale authorization evidence.
assert 'if (Test-Path -LiteralPath $Output) { Remove-Item -LiteralPath $Output -Force }' in s
assert s.index('if (-not $signatureVerified)') < s.index('Set-Content -LiteralPath $tempOutput')
assert s.index("if ($UpgradeResult -ne 'pass')") < s.index('Set-Content -LiteralPath $tempOutput')
assert 'Move-Item -LiteralPath $tempOutput -Destination $outputPath -Force' in s
assert "'.inkdos-upgrade-evidence-'" in s and '[Guid]::NewGuid()' in s
v=(R/'desktop/scripts/validate_release_authorization.py').read_text(encoding='utf-8')
for field in ('windowsVersion','windowsArchitecture','webview2Version','signatureVerified','signerSubject','signerThumbprint','artifactSha256','observedBeforeVersion','observedAfterVersion'): assert field in v
assert 'Evidence does not bind observed pre/post upgrade versions' in v
assert 'Evidence does not identify the Authenticode signer subject' in v
assert 'Evidence does not contain a valid Authenticode signer thumbprint' in v
print('InkDOS 2.4.3 Windows upgrade evidence collector contract passed.')
