param(
  [Parameter(Mandatory=$true)][string]$Artifact,
  [Parameter(Mandatory=$true)][string]$FromVersion,
  [Parameter(Mandatory=$true)][string]$ToVersion,
  [Parameter(Mandatory=$true)][string]$Output,
  [Parameter(Mandatory=$true)][ValidateSet('pass','fail')][string]$UpgradeResult,
  [Parameter(Mandatory=$true)][string]$ObservedBeforeVersion,
  [Parameter(Mandatory=$true)][string]$ObservedAfterVersion,
  [Parameter(Mandatory=$true)][ValidateSet('pass','fail')][string]$InAppUpdaterResult,
  [Parameter(Mandatory=$true)][ValidateSet('pass','fail')][string]$UserFilesIntegrityResult,
  [Parameter(Mandatory=$true)][ValidateSet('pass','fail')][string]$RegressionScenariosResult,
  [Parameter(Mandatory=$true)][ValidateSet('pass','fail')][string]$DisplayScalingResult,
  [Parameter(Mandatory=$true)][ValidateSet('pass','fail')][string]$RebootLaunchResult,
  [Parameter(Mandatory=$true)][ValidateSet('pass','fail')][string]$UpdaterNoRepeatOfferResult,
  [Parameter(Mandatory=$true)][ValidateSet('pass','not-applicable')][string]$TouchPenResult
)
$ErrorActionPreference = 'Stop'
# Fail closed: a failed collection attempt must never leave an older evidence file behind.
if (Test-Path -LiteralPath $Output) { Remove-Item -LiteralPath $Output -Force }
if ($ObservedBeforeVersion -ne $FromVersion) { throw 'Observed pre-upgrade InkDOS version does not match FromVersion.' }
if ($ObservedAfterVersion -ne $ToVersion) { throw 'Observed post-upgrade InkDOS version does not match ToVersion.' }
$artifactPath = (Resolve-Path -LiteralPath $Artifact).Path
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $artifactPath).Hash.ToLowerInvariant()
$sig = Get-AuthenticodeSignature -LiteralPath $artifactPath
$signatureVerified = $sig.Status -eq [System.Management.Automation.SignatureStatus]::Valid
$signerCertificate = $sig.SignerCertificate
$signerSubject = if ($signerCertificate) { [string]$signerCertificate.Subject } else { '' }
$signerThumbprint = if ($signerCertificate) { ([string]$signerCertificate.Thumbprint).Replace(' ', '').ToLowerInvariant() } else { '' }
$windowsCurrentVersionKey = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
try {
  $windowsInfo = Get-ItemProperty -LiteralPath $windowsCurrentVersionKey -ErrorAction Stop
} catch {
  throw 'Windows version could not be determined from the CurrentVersion registry key.'
}
$windowsProductName = [string]$windowsInfo.ProductName
$windowsDisplayVersion = [string]$windowsInfo.DisplayVersion
$windowsCurrentBuild = [string]$windowsInfo.CurrentBuildNumber
$windowsUbr = [string]$windowsInfo.UBR
if (-not $windowsProductName.Trim() -or -not $windowsCurrentBuild.Trim() -or $windowsCurrentBuild -notmatch '^\d+$' -or ($windowsUbr -and $windowsUbr -notmatch '^\d+$')) {
  throw 'Windows CurrentVersion registry data is incomplete or invalid.'
}
$windowsVersion = $windowsProductName.Trim() + ' ' + $windowsDisplayVersion.Trim() + ' build ' + $windowsCurrentBuild.Trim()
$windowsArchitecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
if ($windowsArchitecture -notin @('X64','Arm64','X86')) { throw 'Windows architecture could not be classified.' }
if ($windowsUbr) { $windowsVersion += '.' + $windowsUbr.Trim() }
$webviewClient = '{F1E7E5F4-7F54-4A26-AE8A-C2B8F98C0A7B}'
$webviewKeys = @(
  "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\$webviewClient",
  "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\$webviewClient",
  "HKCU:\Software\Microsoft\EdgeUpdate\Clients\$webviewClient",
  "HKCU:\Software\WOW6432Node\Microsoft\EdgeUpdate\Clients\$webviewClient"
)
$webview2Version = $null
foreach ($webviewKey in $webviewKeys) {
  try {
    $candidate = [string](Get-ItemProperty -LiteralPath $webviewKey -Name pv -ErrorAction Stop).pv
    if ($candidate -match '^\d+\.\d+\.\d+\.\d+$') { $webview2Version = $candidate; break }
  } catch {}
}
if (-not $webview2Version) { throw 'Microsoft Edge WebView2 Runtime version could not be determined from supported registry locations.' }
$evidence = [ordered]@{
  platform='windows'; fromVersion=$FromVersion; toVersion=$ToVersion; webview2=$true
  observedBeforeVersion=$ObservedBeforeVersion; observedAfterVersion=$ObservedAfterVersion
  upgradeResult=$UpgradeResult; inAppUpdaterResult=$InAppUpdaterResult
  userFilesIntegrityResult=$UserFilesIntegrityResult; regressionScenariosResult=$RegressionScenariosResult
  displayScalingResult=$DisplayScalingResult; rebootLaunchResult=$RebootLaunchResult
  updaterNoRepeatOfferResult=$UpdaterNoRepeatOfferResult; touchPenResult=$TouchPenResult
  testedAtUtc=[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
  artifactName=[IO.Path]::GetFileName($artifactPath); artifactSha256=$hash
  windowsVersion=$windowsVersion; windowsArchitecture=$windowsArchitecture; webview2Version=[string]$webview2Version
  signatureVerified=$signatureVerified; signerSubject=$signerSubject; signerThumbprint=$signerThumbprint
}
if (-not $signatureVerified) { throw "Artifact Authenticode signature is not valid: $($sig.Status)" }
if (-not $signerSubject.Trim()) { throw 'Artifact Authenticode signer subject is missing.' }
if ($signerThumbprint -notmatch '^[0-9a-f]{40,64}$') { throw 'Artifact Authenticode signer thumbprint is invalid.' }
if ($UpgradeResult -ne 'pass') { throw 'Upgrade result is not pass.' }
foreach ($gate in @($InAppUpdaterResult, $UserFilesIntegrityResult, $RegressionScenariosResult, $DisplayScalingResult, $RebootLaunchResult, $UpdaterNoRepeatOfferResult)) {
  if ($gate -ne 'pass') { throw 'Required Windows upgrade validation step is not pass.' }
}
# Persist only fully validated evidence, and replace atomically within the destination directory.
$outputPath = [IO.Path]::GetFullPath($Output)
$outputDir = [IO.Path]::GetDirectoryName($outputPath)
if (-not [IO.Directory]::Exists($outputDir)) { throw 'Evidence output directory does not exist.' }
$tempOutput = Join-Path $outputDir ('.inkdos-upgrade-evidence-' + [Guid]::NewGuid().ToString('N') + '.tmp')
try {
  $evidence | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $tempOutput -Encoding UTF8
  Move-Item -LiteralPath $tempOutput -Destination $outputPath -Force
} finally {
  if (Test-Path -LiteralPath $tempOutput) { Remove-Item -LiteralPath $tempOutput -Force }
}
