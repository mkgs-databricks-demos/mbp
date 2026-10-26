# Repair Failed Wave — Re-starting from a Specific Wave

> Paste this into Genie Code in your **project** folder (or the bundle repo) when a build
> run has a failed wave and you need to repair it. This prompt covers both the repair_run
> workflow and the fresh-run fallback when the job structure has changed.
> Replace the bracketed placeholders with your run's details.

---

## Prompt

The build run `[run_id]` on job `[job_id]` has a failed wave `[wave_number]`. I need to repair the run and re-execute from the failed wave onward.

### Step 1: Diagnose the failure

Before repairing, understand what went wrong:

1. Read the `w[wave_number]_gate` task output in the run.
2. Read `.build-status/[run_id]/wave_[wave_number]_gate.json` — this lists which checks failed and why.
3. If it's a convergence wave, also read `.build-status/[run_id]/wave_[wave_number]_runtime.json` for deployment IDs, states, and error samples.
4. Read the failing session's status file and summary in `docs/sessions/`.
5. Check for `requests` in the gate file — these list changes a session needed outside its owned paths. Apply them before repairing.
6. Passing sessions are already committed (in `git`/`hybrid` mode). Failing sessions' code is left uncommitted.
7. Fix the root cause (plan, manifest, or code) before attempting the repair.

Note: downstream waves show as **Excluded** (not failed). This is correct cascade behavior — they never ran and consumed no compute.

### Step 2: Repair the run

Once the cause is fixed, repair from the failed wave's tasks onward. The key rule: **always include `rerun_dependent_tasks=True`** so that `wN_gate_check` and every later wave re-evaluates.

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
w.jobs.repair_run(
    run_id=[run_id],
    rerun_tasks=["w[wave_number]_sessions", "w[wave_number]_integrate", "w[wave_number]_gate"],
    rerun_dependent_tasks=True,  # re-runs wN_gate_check and every later wave
)
```

CLI equivalent:

```bash
databricks jobs repair-run [run_id] --json '{"rerun_tasks": ["w[wave_number]_sessions", "w[wave_number]_integrate", "w[wave_number]_gate"], "rerun_dependent_tasks": true}'
```

If the run was already repaired once, also pass `latest_repair_id`:
```python
repair_history = w.jobs.get_run(run_id=[run_id], include_history=True).repair_history
# Use the latest repair_id from repair_history
```

In the UI: choose **Repair run** and select the failed wave's tasks **and** everything after them, including each `wN_gate_check`.

### Which tasks to rerun

| What failed | `rerun_tasks` |
|---|---|
| A session (code, plan, or manifest fixed) | `w[wave_number]_sessions`, `w[wave_number]_integrate`, `w[wave_number]_gate` |
| Only the integrator (sessions passed) | `w[wave_number]_integrate`, `w[wave_number]_gate` |
| Only the gate verdict (e.g. stray files, runtime soak) | `w[wave_number]_gate` |

Keep `rerun_dependent_tasks=True` in every case. Without it, nothing after the named tasks runs.

**Pass `job_parameters` on every repair.** A `repair_run` falls back to the job-level parameter defaults when `job_parameters` is omitted. The setup job writes these defaults from the manifest, but if the original run was started with custom parameters (e.g. a different branch), the repair would silently use the wrong values. Always pass the same `branch`, `build_root`, and `manifest_path` the original run used:

```python
w.jobs.repair_run(
    run_id=[run_id],
    rerun_tasks=[...],
    rerun_dependent_tasks=True,
    job_parameters={
        "branch": "[feature-branch]",
        "build_root": "[build_root]",
        "manifest_path": "[manifest_path]",
    },
)
```

### Step 3: Fresh run fallback

If the build job was redeployed and re-patched since the failed run, Jobs refuses to repair it ("job structure has changed"). Start a new run with `only` set to the failed wave's task keys and everything after it:

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# List all task keys from the failed wave onward
only_tasks = [
    "w[wave_number]_sessions", "w[wave_number]_integrate", "w[wave_number]_gate", "w[wave_number]_gate_check",
    # ... all tasks from later waves too
]

w.jobs.run_now(
    job_id=[job_id],
    only=only_tasks,
)
```

Earlier waves show as SKIPPED. Files left in the working tree by the earlier run (uncommitted summaries, code from failed sessions) are reported by the integrator as `carryover_files`, not strays, so they no longer fail the new run's first gate. Summary carryover is committed; code carryover is left for the session that owns it. The last wave fails on any carryover code nobody claimed, so a human decides what to do with it. When the failed session reruns, it keeps its earlier changes; the gate credits them as inherited (same session's status file in the earlier run, inside its `owned_paths`), so they do not need to appear in any attempt of the new run.

### Step 4: Transient agent errors

**Transient agent start-up errors** (`INTERNAL_ERROR: start_agent_run`) are retried automatically: Genie Code tasks get `max_retries` (default 2, one minute apart, override with manifest `task_retries`). If a task still fails after its retries, repair as above — don't start a fresh run.

### Step 5: Convergence wave failures

A convergence wave can commit (its session passed) and still fail on `runtime_gate` (e.g. the app crashed during the soak). The commit is kept as progress; repair re-runs the converge session, which starts from the committed code.

---

_This prompt is generic. Adapt the placeholders for your run ID, job ID, and wave number._

## Retarget after merge

After a feature branch is merged to main and deleted on the remote, the build job's `branch` parameter default still points at the deleted branch. The integrator will fail with `branch not found on remote` on the next run. To retarget:

1. Create a new feature branch from main.
2. Update `branch` in `waves.json` to the new branch name.
3. Re-deploy the bundle with `--var="build_branch=<new-branch>"`.
4. Re-run the setup job to patch the build job's parameter defaults.
5. Start a new build run.
