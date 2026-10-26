"""Instance ownership checks: stop one genie-build-waves instance from taking over another's jobs.

Every instance (`instance_suffix`) has its own remote state under
`.bundle/genie-build-waves<suffix>/<target>/state/`, but the CLI also keeps a local
state cache that is not keyed by the suffix. Deploying instance B can reuse instance
A's cached state, bind to A's job IDs, rename them and reset them to the placeholder
(docs/plans/2026-10-26_instance-state-isolation.md). These checks catch that before
`bundle deploy` (scripts/deploy_instance.py) and again before setup patches the jobs
(setup_build_waves_job.ipynb).

Signals, in order of strength:

* `deployment.metadata_file_path` on a job: the bundle root that last deployed it. It
  must be under this instance's `workspace.root_path`. Setup's jobs/reset drops this
  field from the build and smoke jobs, so it is usually only present on the setup job.
* Remote state: when the instance has no remote `resources.json`, `bundle summary`
  must show no job IDs (they can only come from another instance's cache). When it
  has one, the summary IDs must match it.
* The build job's `manifest_path` parameter default and the manifest of its latest run
  must match this instance's manifest (a different project's jobs fail this).

Pure functions only (no SDK), so tests can pass plain dicts.
"""

GUARD_PREFIX = "INSTANCE_GUARD_FAILED"


def _norm(path) -> str:
    """Compare workspace paths with or without the /Workspace prefix and trailing slash."""
    p = str(path or "").strip().rstrip("/")
    if p.startswith("/Workspace/"):
        p = p[len("/Workspace"):]
    return p


def under_root(path, root_path) -> bool:
    """True when `path` is `root_path` or inside it."""
    p, r = _norm(path), _norm(root_path)
    return bool(r) and (p == r or p.startswith(r + "/"))


def summary_job_ids(summary: dict) -> dict:
    """{resource_key: job_id} from `bundle summary -o json` (jobs without an id are skipped)."""
    jobs = ((summary or {}).get("resources") or {}).get("jobs") or {}
    return {k: str(v["id"]) for k, v in jobs.items() if isinstance(v, dict) and v.get("id")}


def state_job_ids(resources_state) -> dict | None:
    """{resource_key: job_id} from a remote `state/resources.json` (direct engine); None = no state."""
    if resources_state is None:
        return None
    out = {}
    for key, entry in ((resources_state or {}).get("state") or {}).items():
        if key.startswith("resources.jobs.") and isinstance(entry, dict) and entry.get("__id__"):
            out[key[len("resources.jobs."):]] = str(entry["__id__"])
    return out


def state_problems(summary_ids: dict, remote_ids, root_path) -> list[str]:
    """Summary job IDs that this instance's remote state does not account for."""
    if remote_ids is None:
        if summary_ids:
            ids = ", ".join(f"{k}={v}" for k, v in sorted(summary_ids.items()))
            return [f"no remote state under {root_path}, but bundle summary shows job IDs ({ids}); "
                    "they come from a local state cache of another instance"]
        return []
    problems = []
    for key, jid in sorted(summary_ids.items()):
        want = remote_ids.get(key)
        if want is None:
            problems.append(f"{key}: bundle summary shows job {jid}, but the remote state under {root_path} has no {key}")
        elif want != jid:
            problems.append(f"{key}: bundle summary shows job {jid}, but the remote state under {root_path} has job {want}")
    return problems


def job_parameter_default(job: dict, name: str):
    for p in ((job or {}).get("settings") or {}).get("parameters") or []:
        if p.get("name") == name:
            return p.get("default")
    return None


def job_problems(key: str, job_id, job, root_path=None, manifest_path=None, project_name=None) -> list[str]:
    """Ownership problems for one job (`job` is a jobs/get response; None = not found).

    A job that no longer exists is not an ownership problem (deploy recreates it).
    `project_name` checks the job name ("[dev user] <project_name>: ...").
    """
    if not job:
        return []
    settings = job.get("settings") or {}
    name = settings.get("name", "")
    problems = []
    if project_name and f"{project_name}: " not in name:
        problems.append(f"{key}: job {job_id} is named {name!r}, expected the project name {project_name!r}")
    meta = (settings.get("deployment") or {}).get("metadata_file_path")
    if meta and root_path and not under_root(meta, root_path):
        problems.append(f"{key}: job {job_id} ({name!r}) was deployed from {meta}, not from this instance ({root_path})")
    if manifest_path:
        current = job_parameter_default(job, "manifest_path")
        if current and _norm(current) != _norm(manifest_path):
            problems.append(f"{key}: job {job_id} ({name!r}) has manifest_path default {current}, "
                            f"this instance uses {manifest_path}")
    return problems


def run_manifest(run: dict):
    """manifest_path a run used (its value, else the default recorded on the run)."""
    for p in (run or {}).get("job_parameters") or []:
        if p.get("name") == "manifest_path":
            return p.get("value") or p.get("default")
    return None


def history_problems(job_id, runs: list, manifest_path) -> list[str]:
    """The build job's latest run must have used this manifest (runs: newest first).

    Only the latest run counts: a project may legitimately move its manifest over time.
    """
    if not manifest_path:
        return []
    for run in runs or []:
        used = run_manifest(run)
        if used:
            if _norm(used) != _norm(manifest_path):
                return [f"build job {job_id}: latest run {run.get('run_id')} used manifest {used}, "
                        f"this instance uses {manifest_path}"]
            return []
    return []


BUILD_KEY = "build_waves"


def deploy_problems(summary: dict, remote_state, jobs: dict, build_runs: list, manifest_path=None) -> list[str]:
    """Pre-deploy check for one instance.

    summary: `bundle summary -o json`; remote_state: the instance's remote resources.json
    (None = absent); jobs: {resource_key: jobs/get response or None} for the summary IDs;
    build_runs: the build job's runs, newest first; manifest_path: the instance's manifest.
    """
    root = ((summary or {}).get("workspace") or {}).get("root_path")
    ids = summary_job_ids(summary)
    problems = state_problems(ids, state_job_ids(remote_state), root)
    for key, jid in sorted(ids.items()):
        problems += job_problems(key, jid, (jobs or {}).get(key), root,
                                 manifest_path if key == BUILD_KEY else None)
    if BUILD_KEY in ids:
        problems += history_problems(ids[BUILD_KEY], build_runs, manifest_path)
    return problems


def setup_problems(jobs: dict, build_runs: list, manifest_path, root_path=None, project_name=None) -> list[str]:
    """Setup-time check: jobs is {resource_key: (job_id, jobs/get response or None)}.

    root_path / project_name are optional so setup jobs deployed before they were passed
    still run the manifest and run-history checks.
    """
    problems = []
    for key, (jid, job) in sorted((jobs or {}).items()):
        if not jid:
            continue
        if job is None:
            problems.append(f"{key}: job {jid} not found")
            continue
        problems += job_problems(key, jid, job, root_path,
                                 manifest_path if key == BUILD_KEY else None, project_name)
    build_id = ((jobs or {}).get(BUILD_KEY) or (None, None))[0]
    if build_id:
        problems += history_problems(build_id, build_runs, manifest_path)
    return problems


def guard_message(problems: list[str], force: bool = False) -> str:
    """One message for logs and exceptions; empty when there are no problems."""
    if not problems:
        return ""
    head = f"{GUARD_PREFIX}: {len(problems)} problem(s)" + (" (force=true: continuing)" if force else "")
    lines = [head] + [f"  - {p}" for p in problems]
    if not force:
        lines.append("These jobs may belong to another instance. Check `bundle summary` and the remote state, "
                     "move the local state cache aside, or pass force=true if this change is intended.")
    return "\n".join(lines)
