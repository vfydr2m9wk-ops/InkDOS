#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]
CURRENT_RUN_ID = int(os.environ["GITHUB_RUN_ID"])
CURRENT_SHA = os.environ["GITHUB_SHA"]

BASELINE_SHA = "3470607f440d34b361aff4a790acec442d84fb56"

# Permanent workflows that remain part of InkDOS after post-2.5.2 consolidation.
WORKFLOW_CI = 365567636
WORKFLOW_TAURI = 356691180
WORKFLOW_RELEASE = 356719870
WORKFLOW_PAGES = 327068594
ACTIVE_WORKFLOWS = {WORKFLOW_CI, WORKFLOW_TAURI, WORKFLOW_RELEASE, WORKFLOW_PAGES}

# Removed/superseded workflow IDs. Their useful conclusions are recorded in
# docs/QA_BASELINE_2.5.2.md before the historical runs are pruned.
RETIRED_WORKFLOWS = {
    361184835,  # Verify InkDOS 2.4.3 Integration
    365288439,  # Presentations mobile WebKit hotfix
    365724535,  # 2.5.2 stateful control audit
    365702991,  # 2.5.2 online render matrix
    361014087,  # old one-shot run purge
    364409880,  # RUN38 bootstrap v1
    364412086,  # RUN38 bootstrap v2
    364412956,  # RUN38 bootstrap v3
    364413452,  # RUN38 bootstrap v4
}

# Exact release/baseline evidence worth retaining in active workflow history.
PRESERVE_RUN_IDS = {
    35990375379,  # successful InkDOS 2.5.2 release
    35989889746,  # Tauri validation at the v2.5.2 tagged candidate
    35989888928,  # Pages deployment at the v2.5.2 tagged candidate
}


class ApiError(RuntimeError):
    pass


def request(method: str, path: str, payload=None, *, tolerate=( )):
    url = API + path
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "inkdos-post-release-cleanup",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read()
            if not body:
                return None
            return json.loads(body.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        if exc.code in tolerate:
            return {"_http_status": exc.code, "_body": body}
        raise ApiError(f"{method} {path}: HTTP {exc.code}: {body[:600]}") from exc


def paginate(path: str):
    page = 1
    items = []
    sep = "&" if "?" in path else "?"
    while True:
        payload = request("GET", f"{path}{sep}per_page=100&page={page}")
        if isinstance(payload, dict):
            batch = payload.get("workflow_runs") or payload.get("deployments") or []
        else:
            batch = payload or []
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def cleanup_runs():
    runs = paginate(f"/repos/{REPO}/actions/runs?")
    latest_success = {}
    for run in runs:
        wid = int(run["workflow_id"])
        if wid in ACTIVE_WORKFLOWS and run.get("conclusion") == "success":
            current = latest_success.get(wid)
            if current is None or int(run["id"]) > int(current["id"]):
                latest_success[wid] = run

    keep_latest = {int(run["id"]) for run in latest_success.values()}
    delete_ids = []
    kept = []

    for run in runs:
        rid = int(run["id"])
        wid = int(run["workflow_id"])
        status = run.get("status")
        conclusion = run.get("conclusion")
        sha = run.get("head_sha")

        reason = None
        if rid == CURRENT_RUN_ID:
            reason = "current cleanup run"
        elif status != "completed":
            reason = "not completed"
        elif sha == CURRENT_SHA:
            reason = "current cleanup commit"
        elif rid in PRESERVE_RUN_IDS:
            reason = "explicit baseline/release evidence"
        elif rid in keep_latest:
            reason = "latest successful active-workflow run"
        elif wid == WORKFLOW_RELEASE and conclusion == "success":
            reason = "successful historical release"
        elif wid in RETIRED_WORKFLOWS:
            delete_ids.append(rid)
        elif wid in ACTIVE_WORKFLOWS:
            delete_ids.append(rid)
        else:
            # Unknown completed workflow history is legacy by default after the
            # permanent workflow set has been consolidated.
            delete_ids.append(rid)

        if reason:
            kept.append((rid, wid, reason, run.get("name"), conclusion))

    print(f"Actions runs discovered: {len(runs)}")
    print(f"Actions runs to delete: {len(delete_ids)}")
    print(f"Actions runs to keep: {len(kept)}")
    for rid, wid, reason, name, conclusion in sorted(kept):
        print(f"KEEP run={rid} workflow={wid} conclusion={conclusion} reason={reason} name={name}")

    failures = []
    for idx, rid in enumerate(delete_ids, 1):
        result = request(
            "DELETE",
            f"/repos/{REPO}/actions/runs/{rid}",
            tolerate=(404, 409),
        )
        if isinstance(result, dict) and result.get("_http_status") not in (None, 404):
            failures.append((rid, result))
        if idx % 25 == 0:
            print(f"Deleted {idx}/{len(delete_ids)} Actions runs")

    if failures:
        print("Actions cleanup warnings:", json.dumps(failures[:10], indent=2))
    return len(delete_ids), failures


def wait_for_current_deployment(max_wait_seconds=120):
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        deployments = paginate(f"/repos/{REPO}/deployments?")
        if any(d.get("sha") == CURRENT_SHA for d in deployments):
            return deployments
        time.sleep(5)
    return paginate(f"/repos/{REPO}/deployments?")


def cleanup_deployments():
    deployments = wait_for_current_deployment()
    latest_by_environment = {}
    for deployment in deployments:
        env = deployment.get("environment") or "(default)"
        current = latest_by_environment.get(env)
        if current is None or int(deployment["id"]) > int(current["id"]):
            latest_by_environment[env] = deployment

    keep_ids = {int(d["id"]) for d in latest_by_environment.values()}
    for deployment in deployments:
        if deployment.get("sha") in {CURRENT_SHA, BASELINE_SHA}:
            keep_ids.add(int(deployment["id"]))

    candidates = [d for d in deployments if int(d["id"]) not in keep_ids]
    print(f"Deployments discovered: {len(deployments)}")
    print(f"Deployments to keep: {len(keep_ids)}")
    print(f"Deployments to prune: {len(candidates)}")

    deleted = 0
    warnings = []
    for deployment in candidates:
        did = int(deployment["id"])
        env = deployment.get("environment") or "github-pages"
        status_payload = {
            "state": "inactive",
            "description": "Pruned during InkDOS post-2.5.2 repository cleanup",
            "environment": env,
        }
        status_result = request(
            "POST",
            f"/repos/{REPO}/deployments/{did}/statuses",
            status_payload,
            tolerate=(404, 409, 422),
        )
        if isinstance(status_result, dict) and status_result.get("_http_status") in (409, 422):
            warnings.append((did, "inactive-status", status_result["_http_status"]))

        delete_result = request(
            "DELETE",
            f"/repos/{REPO}/deployments/{did}",
            tolerate=(404, 409, 422),
        )
        if isinstance(delete_result, dict) and delete_result.get("_http_status") in (409, 422):
            warnings.append((did, "delete", delete_result["_http_status"]))
        else:
            deleted += 1

    print(f"Deployments deleted/absent: {deleted}")
    if warnings:
        print("Deployment cleanup warnings:", json.dumps(warnings[:20], indent=2))
    return deleted, warnings


def main():
    print("InkDOS post-2.5.2 Actions/deployments cleanup")
    print(f"repository={REPO}")
    print(f"current_run={CURRENT_RUN_ID}")
    print(f"current_sha={CURRENT_SHA}")
    print(f"stable_baseline_sha={BASELINE_SHA}")

    run_deleted, run_warnings = cleanup_runs()
    deployment_deleted, deployment_warnings = cleanup_deployments()

    print(json.dumps({
        "actionsRunsDeleted": run_deleted,
        "actionsWarnings": len(run_warnings),
        "deploymentsDeleted": deployment_deleted,
        "deploymentWarnings": len(deployment_warnings),
    }, indent=2))

    # Warnings are reported but do not invalidate the repository if GitHub
    # refuses deletion of a protected/in-use deployment.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
