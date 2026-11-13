"""Manifest validation and build-job task generation for genie-build-waves.

Used by setup_build_waves_job (validate, generate the task graph) and by
wave_gate_check (archived / runnable wave helpers). Pure Python, no Spark or SDK
imports, so the tests can import it directly.

Archived waves (`"archived": true`) are earlier builds kept in the manifest as
history. They are validated (ids, duplicate session ids, runtime target references)
but generate no job tasks, and their sessions count as already done for `depends_on`.

Continuation passes (`"continuation_passes"`, top level or per wave, default 1, 0 turns them off, max 3). A
session that stops at the Genie Code step limit still ends its for_each iteration SUCCESS,
and a repair cannot re-run a SUCCESS iteration. After the sessions, each pass k runs
w<w>_find_incomplete[k] (notebook: sessions with no final status) -> w<w>_has_incomplete[k]
(If/else) -> w<w>_continue[k] (for_each over the incomplete sessions, runner with
continuation=k). See docs/plans/2026-11-03_continuation-pass.md.

Branch sync (git and hybrid workflows, `workflow.sync_branch`, default true). Each wave starts
with w<w>_sync (notebook: pull the build branch into the Git folder, fast-forward, as the job's
run_as) -> w<w>_synced (If/else on its `synced` value) -> w<w>_sessions. A fix pushed to the
branch between runs (by a person or an external monitor) reaches the sessions when the run is
repaired from w<w>_sync. A failed sync excludes the wave; build_verdict fails the run.
"""

import json
import os
import re

from app_probes import validate_probe, validate_probe_auth

VALID_MODES = {"edit", "execute", "configure", "converge"}
VALID_TARGET_TYPES = {"app", "job", "pipeline", "dashboard", "genie_space", "table"}
DEFAULT_TIMEOUT_MIN = {"edit": 60, "execute": 60, "configure": 60, "converge": 180}
DEFAULT_CONTINUATION_PASSES = 1
MAX_CONTINUATION_PASSES = 3
FIND_INCOMPLETE_TIMEOUT_MIN = 10
SYNC_TIMEOUT_MIN = 10
SYNC_WORKFLOW_MODES = {"git", "hybrid"}
MAX_JOB_TASKS = 1000  # Lakeflow Jobs limit per job

# genie_task.parameters of the runner / integrator automations. The setup notebook puts a
# {{param}} placeholder for each one in the automation prompt; a parameter missing here never
# reaches the agent (tests check every generated parameter is listed).
RUNNER_PARAMS = ["session_id", "wave", "run_id", "branch", "build_root", "manifest_path", "continuation"]
INTEGRATOR_PARAMS = ["wave", "run_id", "branch", "build_root", "manifest_path"]

# Task keys allow letters, digits, '_' and '-' (max 100 chars). Wave ids become the
# task prefix w<wave_id>, e.g. wave "4-1" -> w4-1_sessions.
_WAVE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,60}$")
_PLAIN_IDENT_RE = re.compile(r"^[A-Za-z0-9_]+$")


def ref_ident(key: str) -> str:
    """A task key as an identifier inside a dynamic value reference ({{tasks.<key>...}}).

    References accept only letters, digits and '_'; other keys (e.g. w4-1_gate) must be
    escaped with backticks, otherwise jobs/reset rejects the reference as unknown.
    """
    return key if _PLAIN_IDENT_RE.match(key) else f"`{key}`"


# --- Archived / runnable waves -------------------------------------------------

def is_archived(wave: dict) -> bool:
    return wave.get("archived") is True


def runnable_waves(m: dict) -> list[dict]:
    """Waves that get job tasks, in manifest order."""
    return [wv for wv in m.get("waves") or [] if not is_archived(wv)]


def archived_session_ids(m: dict) -> set[str]:
    """Sessions in archived waves: done in an earlier build, treat as satisfied dependencies."""
    return {s.get("session_id") for wv in m.get("waves") or [] if is_archived(wv)
            for s in wv.get("sessions") or []}


def first_runnable_wave_id(m: dict):
    rw = runnable_waves(m)
    return rw[0]["wave_id"] if rw else None


def last_runnable_wave_id(m: dict):
    rw = runnable_waves(m)
    return rw[-1]["wave_id"] if rw else None


def unmet_dependencies(m: dict, session: dict) -> list[str]:
    """depends_on entries that must still be produced in this build (archived sessions are satisfied)."""
    done = archived_session_ids(m)
    return [d for d in session.get("depends_on") or [] if d not in done]


def _valid_passes(v) -> bool:
    return not isinstance(v, bool) and isinstance(v, int) and 0 <= v <= MAX_CONTINUATION_PASSES


def continuation_passes(m: dict, wave_cfg: dict | None = None) -> int:
    """Continuation passes for a wave: the wave's "continuation_passes", else the manifest's, else 1.

    validate_manifest rejects bad values; here an invalid value falls back to the next level.
    """
    if wave_cfg is not None and _valid_passes(wave_cfg.get("continuation_passes")):
        return wave_cfg["continuation_passes"]
    v = m.get("continuation_passes", DEFAULT_CONTINUATION_PASSES)
    return v if _valid_passes(v) else DEFAULT_CONTINUATION_PASSES


def passes_in_run(prefix: str, task_keys) -> int:
    """Continuation passes the job actually has for wave prefix w<wave_id> (from its task keys).

    The gate uses this instead of the live manifest, so a manifest edited after setup does not
    change how the run's iterations are read.
    """
    keys = set(task_keys or [])
    k = 0
    while k < MAX_CONTINUATION_PASSES and continuation_keys(prefix, k + 1)["continue"] in keys:
        k += 1
    return k


def sync_enabled(m: dict) -> bool:
    """Branch sync tasks run in git and hybrid workflows unless workflow.sync_branch is false."""
    wf = m.get("workflow") or {}
    return wf.get("mode", "git") in SYNC_WORKFLOW_MODES and wf.get("sync_branch", True) is not False


def sync_keys(prefix: str) -> dict:
    """Task keys of the branch sync for wave prefix w<wave_id>: the notebook and its If/else."""
    return {"sync": f"{prefix}_sync", "synced": f"{prefix}_synced"}


def job_task_count(m: dict) -> int:
    """Tasks generate_wave_tasks makes per runnable wave: 4, + 2 with branch sync, + 3 per
    continuation pass; + build_verdict."""
    waves = runnable_waves(m)
    per_sync = 2 if sync_enabled(m) else 0
    return sum(4 + per_sync + 3 * continuation_passes(m, wv) for wv in waves) + (1 if waves else 0)


def continuation_keys(prefix: str, k: int) -> dict:
    """Task keys for continuation pass k (1-based) of wave prefix w<wave_id>.

    Pass 1 has no suffix (w4-1_find_incomplete, w4-1_continue); later passes add the number
    (w4-1_find_incomplete2). 'inner' is the for_each nested task key.
    """
    sfx = "" if k == 1 else str(k)
    return {
        "find": f"{prefix}_find_incomplete{sfx}",
        "has": f"{prefix}_has_incomplete{sfx}",
        "continue": f"{prefix}_continue{sfx}",
        "inner": f"{prefix}_continue{sfx}_session",
    }


def manifest_summary(m: dict) -> str:
    waves = m.get("waves") or []
    n_arch = sum(1 for wv in waves if is_archived(wv))
    n_sessions = sum(len(wv.get("sessions") or []) for wv in waves)
    return (f"Manifest OK: {len(waves)} waves ({n_arch} archived, {len(waves) - n_arch} runnable), "
            f"{n_sessions} sessions, {len(m.get('runtime_targets') or {})} runtime targets, "
            f"continuation passes: {_passes_label(m)}, {job_task_count(m)} job tasks")


def _passes_label(m: dict) -> str:
    """'1 per wave', or 'default 2 (wave 3: 0)' when waves override the top-level value."""
    default = continuation_passes(m)
    overrides = [f"wave {wv.get('wave_id')}: {continuation_passes(m, wv)}" for wv in runnable_waves(m)
                 if continuation_passes(m, wv) != default]
    return f"default {default} ({', '.join(overrides)})" if overrides else f"{default} per wave"


# --- Validation ----------------------------------------------------------------

def _validate_targets(m: dict, targets: dict, errors: list, warnings: list) -> None:
    if m.get("probe_auth") is not None:
        errors += [f"probe_auth: {e}" for e in validate_probe_auth(m["probe_auth"])]

    for tname, t in targets.items():
        if t.get("type") not in VALID_TARGET_TYPES:
            errors.append(f"runtime_targets.{tname}: type must be one of {sorted(VALID_TARGET_TYPES)}")
        if not t.get("name") and not t.get("id"):
            errors.append(f"runtime_targets.{tname}: name (or id for job/pipeline/dashboard/genie_space) is required")
        if t.get("type") == "genie_space":
            if not t.get("id"):
                # Titles are not unique; the gate fails unless the name matches exactly one space.
                warnings.append(f"runtime_targets.{tname}: genie_space without id; the title must match exactly one space")
            if "check_example_sql" in t and not isinstance(t["check_example_sql"], bool):
                errors.append(f"runtime_targets.{tname}: check_example_sql must be true or false")
            if (t.get("stability") or {}).get("soak_minutes"):
                warnings.append(f"runtime_targets.{tname}: genie_space has no soak; soak_minutes is ignored")
            pq = t.get("probe_questions")
            if pq is not None and (not isinstance(pq, list) or not pq
                                   or not all(isinstance(q, str) and q.strip() for q in pq)):
                errors.append(f"runtime_targets.{tname}: probe_questions must be a non-empty list of strings")
            if t.get("probe_mode", "warn") not in ("warn", "fail"):
                errors.append(f"runtime_targets.{tname}: probe_mode must be warn or fail")
            pts = t.get("probe_timeout_seconds")
            if pts is not None and (not isinstance(pts, int) or isinstance(pts, bool) or pts <= 0):
                errors.append(f"runtime_targets.{tname}: probe_timeout_seconds must be a positive integer")
            sf = t.get("source_file")
            if sf is not None and (not isinstance(sf, str) or not sf.strip() or os.path.isabs(sf)):
                errors.append(f"runtime_targets.{tname}: source_file must be a path relative to bundle_root")
            if (t.get("require_fresh_deployment", True) is not False
                    and not t.get("source_file") and not t.get("resource_key")):
                warnings.append(f"runtime_targets.{tname}: genie_space without source_file or resource_key; "
                                f"a no-op deploy fails freshness (content cannot be compared)")
        elif "source_file" in t:
            errors.append(f"runtime_targets.{tname}: source_file is only supported on genie_space targets")
        elif any(k in t for k in ("probe_questions", "probe_mode")):
            errors.append(f"runtime_targets.{tname}: probe_questions / probe_mode are only supported on genie_space targets")
        if t.get("type") == "table":
            if not (isinstance(t.get("name"), str) and len(t["name"].split(".")) == 3 and all(t["name"].split("."))):
                errors.append(f"runtime_targets.{tname}: table name must be catalog.schema.table")
            rc = t.get("required_columns")
            if rc is not None and (not isinstance(rc, list) or not all(isinstance(c, str) and c for c in rc)):
                errors.append(f"runtime_targets.{tname}: required_columns must be a list of column names")
            mr = t.get("min_rows")
            if mr is not None and (not isinstance(mr, int) or isinstance(mr, bool) or mr < 0):
                errors.append(f"runtime_targets.{tname}: min_rows must be a non-negative integer")
            if (t.get("stability") or {}).get("soak_minutes"):
                warnings.append(f"runtime_targets.{tname}: table has no soak; soak_minutes is ignored")
        elif any(k in t for k in ("required_columns", "min_rows")):
            errors.append(f"runtime_targets.{tname}: required_columns / min_rows are only supported on table targets")
        if t.get("type") == "app" and not t.get("name"):
            errors.append(f"runtime_targets.{tname}: apps need name")
        probes = t.get("probes")
        if probes is not None:
            if t.get("type") != "app":
                errors.append(f"runtime_targets.{tname}: probes are only supported on app targets")
            elif not isinstance(probes, list) or not probes:
                errors.append(f"runtime_targets.{tname}: probes must be a non-empty list")
            else:
                errors += [f"runtime_targets.{tname}: {e}" for p in probes for e in validate_probe(p)]
        if t.get("probe_auth") is not None:
            errors += [f"runtime_targets.{tname}: {e}" for e in validate_probe_auth(t["probe_auth"])]
        if probes and t.get("type") == "app" and not (t.get("probe_auth") or m.get("probe_auth")):
            # Apps accept only OAuth tokens; the job's own credential is redirected to sign-in.
            errors.append(f"runtime_targets.{tname}: probes need probe_auth (target or top-level): Apps accept "
                          f"only OAuth tokens, and the job's own credential is redirected to sign-in")
        tel, stab = t.get("telemetry") or {}, t.get("stability") or {}
        for fld in ("min_traces", "max_trace_errors"):
            if stab.get(fld) is None:
                continue
            if t.get("type") != "app":
                errors.append(f"runtime_targets.{tname}: {fld} is only supported on app targets")
            if not (tel.get("traces_table") or tel.get("mlflow_experiment_id")):
                errors.append(f"runtime_targets.{tname}: stability.{fld} needs telemetry.traces_table "
                              f"(OTel spans) or telemetry.mlflow_experiment_id (MLflow 3 traces)")
        for fld in ("max_failed_records", "max_dropped_records"):
            v = stab.get(fld)
            if v is None:
                continue
            if t.get("type") != "pipeline":
                errors.append(f"runtime_targets.{tname}: stability.{fld} is only supported on pipeline targets")
            elif not isinstance(v, int) or isinstance(v, bool) or v < 0:
                errors.append(f"runtime_targets.{tname}: stability.{fld} must be a non-negative integer")
        if stab.get("min_traces") is not None and not probes:
            # An idle app emits no request spans; without probe traffic a trace floor fails healthy apps.
            warnings.append(f"runtime_targets.{tname}: min_traces without probes counts only organic traffic")


def validate_manifest(m: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors stop the setup job; warnings are printed.

    Archived waves keep the structural checks (wave ids, duplicate session ids, modes,
    runtime target references) but skip the planning rules that only matter for a wave
    that will run: rule 7 (single-writer deploys) and the owned_paths warning.
    """
    errors, warnings = [], []
    wf_mode = (m.get("workflow") or {}).get("mode", "git")
    targets = m.get("runtime_targets") or {}
    _validate_targets(m, targets, errors, warnings)

    cp = m.get("continuation_passes")
    if cp is not None and not _valid_passes(cp):
        errors.append(f"continuation_passes must be an integer from 0 to {MAX_CONTINUATION_PASSES} (got {cp!r})")
    for wv in m.get("waves") or []:
        wcp = wv.get("continuation_passes")
        if wcp is not None and not _valid_passes(wcp):
            errors.append(f"wave {wv.get('wave_id')}: continuation_passes must be an integer from 0 to "
                          f"{MAX_CONTINUATION_PASSES} (got {wcp!r})")
    wf = m.get("workflow") or {}
    if "sync_branch" in wf and not isinstance(wf["sync_branch"], bool):
        errors.append(f"workflow.sync_branch must be true or false (got {wf['sync_branch']!r})")
    elif wf.get("sync_branch") is True and wf_mode not in SYNC_WORKFLOW_MODES:
        warnings.append(f"workflow.sync_branch is ignored in {wf_mode!r} mode (no Git branch to sync)")
    n_tasks = job_task_count(m)
    if n_tasks > MAX_JOB_TASKS:
        errors.append(f"the build job would have {n_tasks} tasks; Lakeflow Jobs allows {MAX_JOB_TASKS}. "
                      f"Archive finished waves, lower continuation_passes or set workflow.sync_branch to false")

    waves = m.get("waves") or []
    if not waves:
        errors.append("manifest has no waves")
    elif not runnable_waves(m):
        errors.append("every wave is archived; nothing to run (add a wave without \"archived\": true)")

    wave_ids, session_ids = set(), set()
    session_wave_pos = {}  # session_id -> index of its wave
    for pos, wv in enumerate(waves):
        for s in wv.get("sessions") or []:
            session_wave_pos.setdefault(s.get("session_id"), pos)

    for pos, wv in enumerate(waves):
        wid = wv.get("wave_id")
        if wid in wave_ids:
            errors.append(f"duplicate wave_id {wid!r}")
        wave_ids.add(wid)
        if wid is None or isinstance(wid, bool) or not _WAVE_ID_RE.match(str(wid)):
            errors.append(f"wave {wid!r}: wave_id must be 1-60 letters, digits, '_' or '-' (it becomes the task prefix w<wave_id>)")
        if "archived" in wv and not isinstance(wv["archived"], bool):
            errors.append(f"wave {wid}: archived must be true or false (got {wv['archived']!r})")
        if "build" in wv and (isinstance(wv["build"], bool) or not isinstance(wv["build"], (str, int))):
            errors.append(f"wave {wid}: build is an informational label and must be a string or integer (got {wv['build']!r})")
        archived = is_archived(wv)

        sessions = wv.get("sessions") or []
        if not sessions:
            errors.append(f"wave {wid}: no sessions")
        gate_targets = set(wv.get("runtime_gate") or [])
        for g in gate_targets - set(targets):
            errors.append(f"wave {wid}: runtime_gate target {g!r} not in runtime_targets")
        for vb in wv.get("validate_bundles") or []:
            if not isinstance(vb, dict) or not vb.get("root") or not vb.get("target"):
                errors.append(f"wave {wid}: validate_bundles entries need root and target (got {vb!r})")
        rc = wv.get("required_checks")
        if rc is not None:
            if not isinstance(rc, list) or not all(isinstance(c, str) and c.strip() for c in rc):
                errors.append(f"wave {wid}: required_checks must be a list of check names")
            elif len(set(rc)) != len(rc):
                errors.append(f"wave {wid}: required_checks has duplicate names")

        deployers = []
        for s in sessions:
            sid = s.get("session_id")
            if sid in session_ids:
                errors.append(f"duplicate session_id {sid!r}")
            session_ids.add(sid)
            mode = s.get("mode", "edit")
            if mode not in VALID_MODES:
                errors.append(f"session {sid}: mode {mode!r} not in {sorted(VALID_MODES)}")
            if (not archived and mode in ("edit", "converge") and wf_mode in ("git", "hybrid")
                    and not s.get("owned_paths")):
                (errors if mode == "converge" else warnings).append(f"session {sid}: {mode} session has no owned_paths")
            if mode == "converge":
                rts = s.get("runtime_targets") or []
                if not rts:
                    errors.append(f"session {sid}: converge sessions need runtime_targets")
                for r in rts:
                    if r not in targets:
                        errors.append(f"session {sid}: runtime target {r!r} not in runtime_targets")
                    elif r not in gate_targets:
                        errors.append(f"wave {wid}: converge target {r!r} must be listed in runtime_gate")
            if mode == "converge" or s.get("allow_deploy"):
                deployers.append(sid)
            if not archived:
                for d in s.get("depends_on") or []:
                    if d not in session_wave_pos:
                        warnings.append(f"session {sid}: depends_on {d!r} is not a session in the manifest")
                    elif session_wave_pos[d] >= pos:
                        warnings.append(f"session {sid}: depends_on {d!r} is not in an earlier wave")

        if archived:
            continue  # rule 7 only matters for waves that run
        # Rule 7: deploys are single-writer
        if deployers and len(sessions) != 1:
            errors.append(
                f"wave {wid}: deploying sessions {deployers} must be alone in their wave "
                f"(found {len(sessions)} sessions)"
            )
        if deployers and wv.get("concurrency", 1) != 1:
            warnings.append(f"wave {wid}: concurrency forced to 1 (deploying wave)")

    return errors, warnings


# --- Task graph ----------------------------------------------------------------

def genie_task_retries(m: dict) -> dict:
    """Task-level retries for Genie Code tasks (manifest "task_retries" overrides).

    Agent start-up fails transiently (INTERNAL_ERROR: start_agent_run); a retry is cheaper
    than a repair or a fresh run. Timeouts are not retried: a timed-out converge loop
    should surface, not restart.
    """
    cfg = m.get("task_retries") or {}
    return {
        "max_retries": int(cfg.get("max_retries", 2)),
        "min_retry_interval_millis": int(cfg.get("min_retry_interval_seconds", 60)) * 1000,
        "retry_on_timeout": False,
    }


def make_genie_task(task_key: str, config_id: str, params: dict, depends_on: list[str] | None = None,
                    run_if: str | None = None, timeout_minutes: int | None = None,
                    retries: dict | None = None) -> dict:
    """Build a genie_task dict for the jobs/reset payload.

    Uses 'parameters' (not 'context') — only 'parameters' supports {{input.*}}
    and {{job.*}} template variable resolution at runtime.
    """
    task = {
        "task_key": task_key,
        "genie_task": {
            "configuration_id": config_id,
            "parameters": {k: str(v) for k, v in params.items()},
        },
    }
    if retries and retries.get("max_retries", 0) > 0:
        task.update(retries)
    if depends_on:
        task["depends_on"] = [{"task_key": dk} for dk in depends_on]
    if run_if:
        task["run_if"] = run_if
    if timeout_minutes:
        task["timeout_seconds"] = int(timeout_minutes) * 60
    return task


def make_notebook_task(task_key: str, notebook_path: str, params: dict, depends_on: list[str] | None = None,
                       run_if: str | None = None, timeout_minutes: int | None = None) -> dict:
    """Build a notebook_task dict (for the gate check)."""
    task = {
        "task_key": task_key,
        "notebook_task": {
            "notebook_path": notebook_path,
            "base_parameters": {k: str(v) for k, v in params.items()},
        },
    }
    if depends_on:
        task["depends_on"] = [{"task_key": dk} for dk in depends_on]
    if run_if:
        task["run_if"] = run_if
    if timeout_minutes:
        task["timeout_seconds"] = int(timeout_minutes) * 60
    return task


def session_timeout_minutes(wave_cfg: dict) -> int:
    """for_each iterations share one task definition, so use the longest session timeout in the wave."""
    return max(
        int(s.get("timeout_minutes") or wave_cfg.get("timeout_minutes") or DEFAULT_TIMEOUT_MIN.get(s.get("mode", "edit"), 60))
        for s in wave_cfg["sessions"]
    )


def gate_timeout_minutes(m: dict, wave_cfg: dict) -> int:
    """Gate notebook: static checks are quick; runtime gates add their soak windows (+ job/pipeline waits)."""
    targets = m.get("runtime_targets") or {}
    extra = 0
    for n in wave_cfg.get("runtime_gate") or []:
        t = targets.get(n, {})
        stab = t.get("stability") or {}
        if t.get("type") in ("dashboard", "genie_space", "table"):
            extra += 10  # dataset / table / example SQL / row count checks; no soak
        else:
            extra += int(stab.get("soak_minutes", 10))
        if t.get("probe_questions"):
            # each question: timeout + one retry
            extra += -(-2 * int(t.get("probe_timeout_seconds", 120)) * len(t["probe_questions"]) // 60)
        if t.get("probes"):
            extra += 2 * len(t["probes"])  # timeout + one retry per probe
        if stab.get("min_traces") is not None:
            extra += int(stab.get("traces_wait_minutes", 5))  # span ingestion lag after the soak
    return 20 + extra


VERDICT_TASK_KEY = "build_verdict"


def verdict_notebook_path(gate_notebook_path: str) -> str:
    """build_verdict sits next to the gate notebook, with the same extension."""
    ext = os.path.splitext(gate_notebook_path)[1]
    return os.path.join(os.path.dirname(gate_notebook_path), f"build_verdict{ext}")


def find_incomplete_notebook_path(gate_notebook_path: str) -> str:
    """find_incomplete_sessions sits next to the gate notebook, with the same extension."""
    ext = os.path.splitext(gate_notebook_path)[1]
    return os.path.join(os.path.dirname(gate_notebook_path), f"find_incomplete_sessions{ext}")


def sync_notebook_path(gate_notebook_path: str) -> str:
    """sync_branch sits next to the gate notebook, with the same extension."""
    ext = os.path.splitext(gate_notebook_path)[1]
    return os.path.join(os.path.dirname(gate_notebook_path), f"sync_branch{ext}")


def make_verdict_task(gate_keys: list[str], notebook_path: str) -> dict:
    """Final task: fails the run when any wave gate (or branch sync) failed.

    A failed gate does not raise (the next wave's ALL_DONE integrator and gate would run on
    UPSTREAM_FAILED). This task depends on every gate, and on every w<w>_sync task when branch
    sync is on, with run_if ALL_DONE; Excluded tasks count as done, so it runs after the
    cascade stops. A failed sync excludes its own wave's gate, so without the sync dependency
    a sync failure in the first wave would leave this task Excluded too.
    """
    return make_notebook_task(
        task_key=VERDICT_TASK_KEY,
        notebook_path=notebook_path,
        params={
            "run_id": "{{job.run_id}}",
            "build_root": "{{job.parameters.build_root}}",
            "manifest_path": "{{job.parameters.manifest_path}}",
        },
        depends_on=gate_keys,
        run_if="ALL_DONE",
        timeout_minutes=15,
    )


def generate_wave_tasks(m: dict, configuration_ids: dict, gate_notebook_path: str,
                        retries: dict | None = None, verdict_path: str | None = None,
                        find_incomplete_path: str | None = None, sync_path: str | None = None) -> list[dict]:
    """Generate the build job's task graph from the manifest's runnable waves.

    Archived waves generate nothing, so the first runnable wave has no upstream
    dependency. Session-level depends_on never becomes a task dependency: wave order
    enforces it, and sessions in archived waves are already done. A final build_verdict
    task depends on every wave gate (see make_verdict_task).

    Continuation passes sit between the sessions and the integrator. A task whose
    dependencies are all Excluded is itself Excluded, so pass k+1's find task depends on
    pass k's find task (never Excluded) as well as its continue task, and the integrator
    depends on the last pass's find and continue tasks (run_if ALL_DONE). When nothing is
    incomplete, every continue task is Excluded and the integrator still runs.
    
    With branch sync (sync_enabled), each wave starts with w<w>_sync (notebook, never raises,
    sets `synced`) -> w<w>_synced (If/else) -> w<w>_sessions (outcome true). The sync task
    takes the previous wave's gate_check dependency.
    """
    retries = genie_task_retries(m) if retries is None else retries
    find_path = find_incomplete_path or find_incomplete_notebook_path(gate_notebook_path)
    sync_nb = sync_path or sync_notebook_path(gate_notebook_path)
    sync = sync_enabled(m)
    tasks = []
    sync_task_keys = []
    prev_gate_key = None

    for wave_cfg in runnable_waves(m):
        wid = wave_cfg["wave_id"]
        prefix = f"w{wid}"
        sessions = wave_cfg["sessions"]
        passes = continuation_passes(m, wave_cfg)
        deploying = any(s.get("mode") == "converge" or s.get("allow_deploy") for s in sessions)
        # Rule 7: deploys are single-writer (validate_manifest already enforces one session)
        concurrency = 1 if deploying else wave_cfg.get("concurrency", len(sessions))

        # Common params injected into every Genie Code task
        common = {
            "run_id": "{{job.run_id}}",
            "branch": "{{job.parameters.branch}}",
            "build_root": "{{job.parameters.build_root}}",
            "manifest_path": "{{job.parameters.manifest_path}}",
        }

        # Dependency on a condition_task (If/else) requires an outcome.
        # "true" = only run when the previous gate passed (or this wave's sync succeeded).
        upstream = [{"task_key": prev_gate_key, "outcome": "true"}] if prev_gate_key else None

        # --- Branch sync (notebook + If/else) ---
        if sync:
            skeys = sync_keys(prefix)
            sync_task = make_notebook_task(
                task_key=skeys["sync"],
                notebook_path=sync_nb,
                params={"wave": wid, **common},
                timeout_minutes=SYNC_TIMEOUT_MIN,
            )
            if upstream:
                sync_task["depends_on"] = upstream
            tasks.append(sync_task)
            tasks.append({
                "task_key": skeys["synced"],
                "condition_task": {
                    "op": "EQUAL_TO",
                    "left": "{{" + f"tasks.{ref_ident(skeys['sync'])}.values.synced" + "}}",
                    "right": "true",
                },
                "depends_on": [{"task_key": skeys["sync"]}],
            })
            sync_task_keys.append(skeys["sync"])
            upstream = [{"task_key": skeys["synced"], "outcome": "true"}]

        # --- Sessions (for_each) ---
        # Include title in inputs so iterations are identifiable in the UI.
        inputs = json.dumps([
            {"session_id": s["session_id"], "title": s.get("title", s["session_id"])}
            for s in sessions
        ])
        # continuation "0" on the first run: every RUNNER_PARAMS placeholder must get a value.
        session_params = {**common, "wave": wid, "session_id": "{{input.session_id}}", "continuation": "0"}

        inner_task = make_genie_task(
            task_key=f"{prefix}_session",
            config_id=configuration_ids["runner"],
            params=session_params,
            timeout_minutes=session_timeout_minutes(wave_cfg),
            retries=retries,
        )
        inner_task["description"] = "{{input.session_id}}: {{input.title}}"

        sessions_task = {
            "task_key": f"{prefix}_sessions",
            "description": f"Wave {wid}: {', '.join(s.get('title', s['session_id']) for s in sessions)}",
            "for_each_task": {
                "inputs": inputs,
                "concurrency": concurrency,
                "task": inner_task,
            },
        }
        if upstream:
            sessions_task["depends_on"] = upstream
        tasks.append(sessions_task)

        # --- Continuation passes (sessions that stopped before a final status) ---
        integrate_deps = [f"{prefix}_sessions"]
        for k in range(1, passes + 1):
            keys = continuation_keys(prefix, k)
            tasks.append(
                make_notebook_task(
                    task_key=keys["find"],
                    notebook_path=find_path,
                    params={
                        "wave": wid,
                        "continuation": k,
                        "run_id": "{{job.run_id}}",
                        "build_root": "{{job.parameters.build_root}}",
                        "manifest_path": "{{job.parameters.manifest_path}}",
                    },
                    depends_on=integrate_deps,
                    run_if="ALL_DONE",
                    timeout_minutes=FIND_INCOMPLETE_TIMEOUT_MIN,
                )
            )
            tasks.append({
                "task_key": keys["has"],
                "condition_task": {
                    "op": "EQUAL_TO",
                    "left": "{{" + f"tasks.{ref_ident(keys['find'])}.values.has_incomplete" + "}}",
                    "right": "true",
                },
                "depends_on": [{"task_key": keys["find"]}],
            })
            cont_inner = make_genie_task(
                task_key=keys["inner"],
                config_id=configuration_ids["runner"],
                params={**session_params, "continuation": k},
                timeout_minutes=session_timeout_minutes(wave_cfg),
                retries=retries,
            )
            cont_inner["description"] = f"{{{{input.session_id}}}}: {{{{input.title}}}} (continuation {k})"
            tasks.append({
                "task_key": keys["continue"],
                "description": f"Wave {wid} continuation pass {k}: re-run sessions with no final status",
                "for_each_task": {
                    "inputs": "{{" + f"tasks.{ref_ident(keys['find'])}.values.incomplete" + "}}",
                    "concurrency": concurrency,
                    "task": cont_inner,
                },
                "depends_on": [{"task_key": keys["has"], "outcome": "true"}],
            })
            integrate_deps = [keys["find"], keys["continue"]]

        # --- Integrator ---
        tasks.append(
            make_genie_task(
                task_key=f"{prefix}_integrate",
                config_id=configuration_ids["integrator"],
                params={**common, "wave": wid},
                depends_on=integrate_deps,
                run_if="ALL_DONE",
                timeout_minutes=60,
                retries=retries,
            )
        )

        # --- Gate (deterministic notebook) ---
        gate_params = {
            "wave": wid,
            "run_id": "{{job.run_id}}",
            "build_root": "{{job.parameters.build_root}}",
            "manifest_path": "{{job.parameters.manifest_path}}",
        }
        tasks.append(
            make_notebook_task(
                task_key=f"{prefix}_gate",
                notebook_path=gate_notebook_path,
                params=gate_params,
                depends_on=[f"{prefix}_integrate"],
                run_if="ALL_DONE",
                timeout_minutes=gate_timeout_minutes(m, wave_cfg),
            )
        )

        # --- Gate check (If/else condition task) ---
        # Reads the gate notebook's taskValue. If false, all downstream tasks
        # are Excluded (zero-compute cascade stop via the exclusion cascade rule).
        tasks.append({
            "task_key": f"{prefix}_gate_check",
            "condition_task": {
                "op": "EQUAL_TO",
                "left": "{{" + f"tasks.{ref_ident(prefix + '_gate')}.values.gate_passed" + "}}",
                "right": "true",
            },
            "depends_on": [{"task_key": f"{prefix}_gate"}],
        })

        prev_gate_key = f"{prefix}_gate_check"

    gate_keys = [t["task_key"] for t in tasks if t["task_key"].endswith("_gate") and "notebook_task" in t]
    if gate_keys:
        tasks.append(make_verdict_task(gate_keys + sync_task_keys,
                                       verdict_path or verdict_notebook_path(gate_notebook_path)))
    return tasks
