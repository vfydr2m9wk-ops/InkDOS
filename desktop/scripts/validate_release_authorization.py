#!/usr/bin/env python3
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_FIELDS = {
    "version", "windowsDeviceUpgradeValidated", "windowsDeviceUpgradeWaived",
    "explicitUserAuthorization", "evidence", "evidenceSha256", "waiverReason"
}
EVIDENCE_FIELDS = {
    "platform", "fromVersion", "toVersion", "observedBeforeVersion", "observedAfterVersion", "webview2", "upgradeResult",
    "testedAtUtc", "artifactName", "artifactSha256", "windowsVersion", "windowsArchitecture",
    "webview2Version", "signatureVerified", "signerSubject", "signerThumbprint",
    "inAppUpdaterResult", "userFilesIntegrityResult", "regressionScenariosResult",
    "displayScalingResult", "rebootLaunchResult", "updaterNoRepeatOfferResult", "touchPenResult"
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

def _load_json(path, label):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid {label}: {exc}")

def _read_inventory(assets):
    sums=assets/"SHA256SUMS"
    if not sums.is_file(): raise SystemExit("Release SHA256SUMS inventory is missing")
    inventory={}
    for line in sums.read_text(encoding="utf-8").splitlines():
        m=re.fullmatch(r"([0-9a-f]{64})  (.+)",line)
        if not m or m.group(2) in inventory: raise SystemExit("Malformed or duplicate release SHA256SUMS entry")
        inventory[m.group(2)]=m.group(1)
    return inventory

def _validate_evidence(ep, version, assets):
    e=_load_json(ep,"Windows upgrade evidence")
    if not isinstance(e,dict) or set(e)!=EVIDENCE_FIELDS: raise SystemExit("Invalid Windows upgrade evidence fields")
    if e["platform"]!="windows": raise SystemExit("Evidence platform must be windows")
    if e["fromVersion"]!="2.4.0" or e["toVersion"]!=version: raise SystemExit("Evidence upgrade version path mismatch")
    if e["observedBeforeVersion"]!=e["fromVersion"] or e["observedAfterVersion"]!=e["toVersion"]: raise SystemExit("Evidence does not bind observed pre/post upgrade versions")
    if e["webview2"] is not True: raise SystemExit("Evidence does not confirm WebView2 validation")
    if e["upgradeResult"]!="pass": raise SystemExit("Evidence does not record a passing upgrade")
    required_steps={
        "inAppUpdaterResult":"in-app updater", "userFilesIntegrityResult":"user-file integrity",
        "regressionScenariosResult":"Windows regression scenarios", "displayScalingResult":"display scaling",
        "rebootLaunchResult":"post-reboot launch", "updaterNoRepeatOfferResult":"updater no-repeat-offer",
    }
    for field,label in required_steps.items():
        if e[field]!="pass": raise SystemExit(f"Evidence does not record a passing {label} validation")
    if e["touchPenResult"] not in {"pass","not-applicable"}: raise SystemExit("Invalid touch/pen validation status")
    if e["signatureVerified"] is not True: raise SystemExit("Evidence does not confirm updater signature verification")
    if not isinstance(e["signerSubject"],str) or not e["signerSubject"].strip(): raise SystemExit("Evidence does not identify the Authenticode signer subject")
    if not isinstance(e["signerThumbprint"],str) or not re.fullmatch(r"[0-9a-f]{40,64}",e["signerThumbprint"]): raise SystemExit("Evidence does not contain a valid Authenticode signer thumbprint")
    if e["windowsArchitecture"] not in {"X64","Arm64","X86"}: raise SystemExit("Evidence does not record a supported Windows architecture")
    for field,label in (("windowsVersion","Windows version"),("webview2Version","WebView2 version")):
        if not isinstance(e[field],str) or not e[field].strip(): raise SystemExit(f"Evidence does not record {label}")
    if not isinstance(e["artifactName"],str) or not e["artifactName"].strip() or Path(e["artifactName"]).name!=e["artifactName"]: raise SystemExit("Invalid tested artifact name")
    if not e["artifactName"].lower().endswith(".exe"): raise SystemExit("Windows upgrade evidence must identify the tested EXE artifact")
    if not isinstance(e["artifactSha256"],str) or not SHA256_RE.fullmatch(e["artifactSha256"]): raise SystemExit("Invalid tested artifact SHA-256")
    artifact=assets/e["artifactName"]
    if not artifact.is_file(): raise SystemExit("Tested Windows artifact is missing from release assets")
    actual_artifact=hashlib.sha256(artifact.read_bytes()).hexdigest()
    if actual_artifact!=e["artifactSha256"]: raise SystemExit("Tested Windows artifact SHA-256 mismatch")
    inventory=_read_inventory(assets)
    if inventory.get(e["artifactName"])!=actual_artifact: raise SystemExit("Tested Windows artifact is not bound to the validated release SHA256SUMS inventory")
    try: stamp=datetime.fromisoformat(e["testedAtUtc"].replace("Z","+00:00"))
    except (AttributeError,ValueError): raise SystemExit("Invalid evidence test timestamp")
    if stamp.tzinfo is None or stamp.utcoffset()!=timezone.utc.utcoffset(stamp): raise SystemExit("Evidence timestamp must be UTC")
    if stamp > datetime.now(timezone.utc): raise SystemExit("Evidence timestamp cannot be in the future")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--version",required=True); p.add_argument("--state",default="config/release-authorization.json"); p.add_argument("--assets",default="release-final"); a=p.parse_args()
    f=Path(a.state)
    if not f.is_file(): raise SystemExit("Release authorization state is missing")
    d=_load_json(f,"release authorization state")
    if not isinstance(d,dict) or set(d)!=EXPECTED_FIELDS: raise SystemExit("Invalid authorization fields")
    if d["version"]!=a.version: raise SystemExit("Release authorization version mismatch")
    if d["explicitUserAuthorization"] is not True: raise SystemExit("Explicit user publication authorization is absent")
    validated=d["windowsDeviceUpgradeValidated"] is True
    waived=d["windowsDeviceUpgradeWaived"] is True
    if validated==waived: raise SystemExit("Exactly one of Windows validation or explicit waiver must be selected")
    assets=Path(a.assets)
    if not assets.is_dir(): raise SystemExit("Release asset directory is missing")
    if waived:
        if d["evidence"] or d["evidenceSha256"]: raise SystemExit("Waived Windows validation must not carry fabricated evidence")
        reason=d["waiverReason"]
        if not isinstance(reason,str) or not reason.strip(): raise SystemExit("Windows validation waiver reason is missing")
        print(f"InkDOS {a.version} publication authorization gate passed with an explicit Windows/device pre-publication waiver. Post-launch validation remains required.")
        return
    if d["waiverReason"]: raise SystemExit("Validated Windows evidence path must not also carry a waiver reason")
    evidence=d["evidence"]; digest=d["evidenceSha256"]
    if not isinstance(evidence,str) or not evidence.strip(): raise SystemExit("Release authorization evidence reference is empty")
    if not isinstance(digest,str) or not SHA256_RE.fullmatch(digest): raise SystemExit("Invalid evidence SHA-256")
    ep=Path(evidence)
    if ep.is_absolute() or ".." in ep.parts: raise SystemExit("Evidence path must be repository-relative")
    ep=(ROOT/ep).resolve()
    if ROOT.resolve() not in ep.parents or not ep.is_file(): raise SystemExit("Release authorization evidence file is missing")
    actual=hashlib.sha256(ep.read_bytes()).hexdigest()
    if actual!=digest: raise SystemExit("Release authorization evidence SHA-256 mismatch")
    _validate_evidence(ep,a.version,assets)
    print(f"InkDOS {a.version} publication authorization gate passed with verified Windows upgrade evidence.")
if __name__=="__main__": main()
