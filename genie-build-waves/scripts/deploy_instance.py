#!/usr/bin/env python3
"""Deploy one genie-build-waves instance without taking over another instance's jobs.

The supported way to deploy an instance (README: "One deployment per project"):

    python scripts/deploy_instance.py --target dev --vars my-project.vars.json
    python scripts/deploy_instance.py --target dev --vars my-project.vars.json --check-only

`--vars` is a JSON object of bundle variables (project_name, instance_suffix, build_root,
build_branch, manifest_path, skills_catalog, skills_schema, ...). Keep it next to the
project's waves.json, not in this bundle.

Steps:
1. Move the local state cache `.databricks/bundle/<target>` aside (to `<target>.bak`,
   replacing an older backup), because it is shared by every instance deployed from this
   folder. `bundle summary` then rebuilds it from this instance's remote state.
2. `bundle summary -o json`, read the instance's remote `state/resources.json`, get every
   job the summary names, and run `instance_guard.deploy_problems`. Any problem stops
   here (exit 2) unless `--force`.
3. `bundle deploy`, then check that every job now records a `deployment.metadata_file_path`
   under this instance's root and that no job ID changed from the remote state.
4. Move the cache aside again, so a later plain `databricks bundle ...` for another
   instance does not start from this instance's state.

From Genie Code, run this through Python (`subprocess`) rather than the CLI tool: the CLI
tool keeps its own state cache, which step 1 cannot clear.
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys

BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BUNDLE_ROOT, "src", "notebooks"))

import instance_guard  # noqa: E402


def var_flags(variables: dict) -> list[str]:
    """--var flags for the CLI; values are passed as strings."""
    return [f"--var={k}={'' if v is None else v}" for k, v in sorted((variables or {}).items())]


def cache_dir(bundle_root: str, target: str) -> str:
    return os.path.join(bundle_root, ".databricks", "bundle", target)


def backup_path(path: str) -> str:
    return f"{path}.bak"


def move_cache_aside(bundle_root: str, target: str):
    """Rename the local state cache to `<target>.bak` (one backup, the previous one is
    replaced); returns the backup path, or None when there was no cache."""
    src = cache_dir(bundle_root, target)
    if not os.path.isdir(src):
        return None
    dst = backup_path(src)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.rename(src, dst)
    return dst


def post_deploy_problems(summary: dict, jobs: dict, remote_ids_before) -> list[str]:
    """After deploy: every job is owned by this root and no existing job ID changed."""
    root = summary["workspace"]["root_path"]
    ids = instance_guard.summary_job_ids(summary)
    problems = []
    for key, jid in sorted(ids.items()):
        meta = (((jobs.get(key) or {}).get("settings") or {}).get("deployment") or {}).get("metadata_file_path")
        if not meta or not instance_guard.under_root(meta, root):
            problems.append(f"{key}: job {jid} metadata_file_path is {meta!r}, expected under {root}")
        before = (remote_ids_before or {}).get(key)
        if before and before != jid:
            problems.append(f"{key}: job ID changed from {before} to {jid}")
    return problems


def _cli(args: list[str], capture=True) -> str:
    cmd = ["databricks"] + args
    print("$ " + " ".join(cmd))
    p = subprocess.run(cmd, cwd=BUNDLE_ROOT, capture_output=capture, text=True)
    if p.returncode != 0:
        raise SystemExit(f"command failed ({p.returncode}): {' '.join(cmd[:4])}\n{p.stderr or ''}{p.stdout or ''}")
    return p.stdout if capture else ""


def _remote_state(w, root_path):
    from databricks.sdk.errors import NotFound
    from databricks.sdk.service.workspace import ExportFormat
    try:
        r = w.workspace.export(f"{root_path}/state/resources.json", format=ExportFormat.AUTO)
    except NotFound:
        return None
    return json.loads(base64.b64decode(r.content))


def _jobs(w, ids: dict) -> dict:
    import jobs_api
    out = {}
    for key, jid in ids.items():
        try:
            out[key] = jobs_api.get_job(w.api_client, jid)
        except Exception as e:  # deleted job: not an ownership problem
            if "does not exist" in str(e) or "NOT_FOUND" in str(e) or "RESOURCE_DOES_NOT_EXIST" in str(e):
                out[key] = None
            else:
                raise
    return out


def _runs(w, job_id, limit=5) -> list:
    if not job_id:
        return []
    r = w.api_client.do("GET", "/api/2.2/jobs/runs/list", query={"job_id": str(job_id), "limit": str(limit)})
    return r.get("runs") or []


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--target", default="dev")
    ap.add_argument("--vars", required=True, help="JSON file of bundle variables")
    ap.add_argument("--check-only", action="store_true", help="run the checks, do not deploy")
    ap.add_argument("--force", action="store_true", help="deploy even when the checks find problems")
    ap.add_argument("--keep-cache", action="store_true", help="do not move the local state cache aside")
    a = ap.parse_args(argv)

    with open(a.vars) as f:
        variables = json.load(f)
    flags = ["--target", a.target] + var_flags(variables)

    if not a.keep_cache:
        moved = move_cache_aside(BUNDLE_ROOT, a.target)
        print(f"Local state cache moved to {moved}" if moved else "No local state cache to move")
    try:
        return _run(a, variables, flags)
    finally:
        if not a.keep_cache and move_cache_aside(BUNDLE_ROOT, a.target):
            print("Local state cache cleared again")


def _run(a, variables: dict, flags: list[str]) -> int:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()

    summary = json.loads(_cli(["bundle", "summary", "-o", "json"] + flags))
    root = summary["workspace"]["root_path"]
    ids = instance_guard.summary_job_ids(summary)
    remote = _remote_state(w, root)
    remote_ids = instance_guard.state_job_ids(remote)
    print(f"Instance root: {root}")
    print(f"Summary job IDs: {ids or 'none'}")
    print(f"Remote state job IDs: {remote_ids if remote_ids is not None else 'no remote state (first deploy)'}")

    jobs = _jobs(w, ids)
    problems = instance_guard.deploy_problems(
        summary, remote, jobs, _runs(w, ids.get(instance_guard.BUILD_KEY)), variables.get("manifest_path"))
    if problems:
        print(instance_guard.guard_message(problems, force=a.force))
        if not a.force:
            return 2
    else:
        print("Pre-deploy checks passed")
    if a.check_only:
        return 0

    _cli(["bundle", "deploy"] + flags, capture=False)

    after = json.loads(_cli(["bundle", "summary", "-o", "json"] + flags))
    after_ids = instance_guard.summary_job_ids(after)
    post = post_deploy_problems(after, _jobs(w, after_ids), remote_ids)
    print(f"Deployed job IDs: {after_ids}")
    if post:
        print(instance_guard.guard_message(post))
        return 3
    print("Post-deploy checks passed. Run the setup job next.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
