# genie-build-waves

A reusable Declarative Automation Bundle that orchestrates parallel Genie Code sessions to do any kind of work inside Databricks. Decompose any large project — code builds, data pipelines, ML training, migrations, infrastructure setup — into dependency-ordered waves. Run sessions in parallel within each wave, and gate progression with deterministic quality checks.

## What you can build with this

* **DABs bundles and apps** — Author code in parallel sessions, commit per wave (`git` mode)
* **Data engineering pipelines** — Create tables, run notebooks, validate outputs (`workspace` mode)
* **ML model training** — Parallel EDA, feature engineering, and model training with champion selection
* **Platform migrations** — Move workloads from external platforms into Databricks
* **Infrastructure setup** — Create schemas, volumes, endpoints, grants across environments
* **Testing campaigns** — Run validation notebooks in parallel, gate on pass/fail
* **Documentation** — Generate docs, diagrams, or reports across a project

## How it works

```
Wave 0:  [01] -> integrate -> gate -> gate_check (If/else)
                                          |
                                        true
                                          |
Wave 1:  [02] [03] [04] -> integrate -> gate -> gate_check
                                                    |
                                                  true
                                                    |
Wave N:  [...] ----------> integrate -> gate -> gate_check -> done
```

Each wave follows a four-phase pattern:

1. **Sessions** (`for_each` at full wave concurrency) — Genie Code tasks that each complete one plan file. `edit` sessions write files within `owned_paths`; `execute` sessions run notebooks/SQL; `configure` sessions set up resources; `converge` sessions (follow-up builds) deploy, read telemetry, fix and redeploy.
2. **Integrator** (single Genie Code task, `run_if: ALL_DONE`) — Collects session status files, runs gate checks. In `git`/`hybrid` mode: checks for stray files and commits by explicit path (the *only* committer). In `workspace` mode: status collection and gates only.
3. **Gate notebook** (`run_if: ALL_DONE`) — Reads the integrator's gate JSON and every session's status file independently. Sets a `gate_passed` task value (`true`/`false`).
4. **Gate check** (If/else condition task) — Checks `gate_passed == "true"`. If false, all downstream wave tasks are **Excluded** — zero compute on cascade failure.

## Initial builds and follow-up builds

| Phase | Waves | Sessions | Gate | Pass means |
|---|---|---|---|---|
| **Initial build** | Wide, parallel | `edit` / `execute` / `configure`, disjoint ownership | Static (validate, files, tables) | The pieces exist |
| **Follow-up (convergence)** | Sequential, one session each | `converge`: deploy, read telemetry, fix, redeploy | Static + deterministic `runtime_gate` | It deploys, runs, stays up, logs are clean |

A follow-up appends waves to the same `waves.json`. Optionally start with a parallel `edit` wave for known, file-disjoint errors; then add one `converge` wave per deployable thing, in dependency order. Each `converge` session gets `runtime_targets` (how to deploy it, where its OTel logs land, what "stable" means) and loops up to `max_attempts`. The gate notebook then checks the target itself. For an app: deployment succeeded during this run, `RUNNING`, unchanged through a soak window, no error lines for that deployment, startup markers present; for custom agents and MCP servers, optional `probes` (HTTP or MCP `initialize`, authenticated as a service principal whose OAuth credentials sit in a secret scope, `probe_auth`) pass, and the probe traffic shows up as traces without errors (`min_traces`, `max_trace_errors`) in the app's OTel spans table in Unity Catalog and/or its MLflow 3 experiment. For a job or pipeline: its latest run or update since the build started succeeded; for a pipeline, optionally its expectation failures and dropped records stay within `max_failed_records` / `max_dropped_records`. For an AI/BI dashboard: published during this run, and every dataset query passes `EXPLAIN` (or runs with `LIMIT 1` when `execute_datasets` is set). For a Genie space: updated during this run, warehouse attached, every table and metric view resolves, column configs match the current columns, and every example SQL passes `EXPLAIN`; optional `probe_questions` must produce SQL that runs (recorded as warnings by default, `probe_mode: fail` to block). For a table (any wave, no converge session needed, e.g. `workspace` mode): it exists, has the `required_columns`, at least `min_rows` rows, and was written during this run. **A passing stable build is part of the pass criteria.**

Deploys are single-writer: the setup job rejects any wave where a deploying session (`converge` or `allow_deploy`) shares the wave with another session. See `examples/converge-waves.json`.

### Several builds in one manifest: archived waves

Keep earlier builds in `waves.json` as history instead of deleting them. Mark every wave of a finished build `"archived": true` and append the next build's waves. Name waves `<build>-<n>` (`"wave_id": "4-1"`, with an optional informational `"build": "4"`), so task keys read `w<build>-<n>_sessions`, `w4-1_integrate`, `w4-1_gate`, `w4-1_gate_check`.

* Setup generates **no** tasks for archived waves; the first runnable wave has no upstream dependency. It prints `Manifest OK: N waves (A archived, R runnable), S sessions, T runtime targets`.
* Archived waves are still validated (unique wave ids and session ids, modes, `runtime_gate` and converge targets that exist); the single-writer rule is skipped for them.
* `depends_on` entries that name archived sessions count as done. Runners, the integrator and the gate notebook never expect `.build-status` files for them.
* "First wave" (remote-branch check) and "last wave" (unclaimed carryover) mean the first and last **runnable** wave.

Manifests without `archived` behave exactly as before. See [docs/manifest-schema.md](docs/manifest-schema.md#archived-waves).

A manifest can span several bundles. List them in a wave's `validate_bundles` (`root` + `target` each) and the integrator runs `bundle validate --strict` on every one; the gate notebook fails the wave if any is missing or failing. Runtime targets carry their own `bundle_root` and `bundle_target`. See [docs/manifest-schema.md](docs/manifest-schema.md#multiple-bundles-in-one-manifest).

## Architecture

| Component | Path | Purpose |
|---|---|---|
| Session Runner skill | `src/skills/genie-build-session-runner/SKILL.md` | Prompt for one session: load manifest, read plan, implement within owned paths, validate, write status JSON |
| Wave Integrator skill | `src/skills/genie-build-wave-integrator/SKILL.md` | Prompt for per-wave integration: collect status, check strays, commit+push, write gate JSON |
| Build Planner skill | `src/skills/genie-build-planner/SKILL.md` | Planning guide you give Genie Code in your project folder: decompose into waves/sessions, write plans and `waves.json`. Not published to UC |
| Gate check notebook | `src/notebooks/wave_gate_check.ipynb` | Deterministic stop: reads gate + status files; for `runtime_gate` waves also checks app/job/pipeline/dashboard/Genie space state, soak stability, OTel error lines, app probes and traces, dashboard datasets, Genie space tables, example SQL and probe questions, pipeline expectation budgets, and `table` row counts, columns and freshness itself; checks `validate_bundles` results |
| App probe module | `src/notebooks/app_probes.py` | HTTP / MCP `initialize` probes against an app's own URL as the `probe_auth` service principal, plus MLflow 3 trace counts; shared by the gate and the smoke job |
| Manifest module | `src/notebooks/waves_manifest.py` | Manifest validation (including `archived` waves) and task-graph generation; shared by setup and the gate |
| Jobs API module | `src/notebooks/jobs_api.py` | Jobs API 2.2 calls (`jobs/get`, `runs/get` following `next_page_token`, `jobs/reset`, `run-now`); 2.1 rejects jobs with more than 100 tasks |
| Unit tests | `tests/` | Paged reads and reset of a job with more than 100 tasks (fake client), archived/runnable waves, backwards compatibility with `examples/` |
| Placeholder notebook | `src/notebooks/genie_task_placeholder.ipynb` | Stand-in for `genie_task` (bundle CLI has no schema); fails loud if run |
| Setup notebook | `src/notebooks/setup_build_waves_job.ipynb` | Validates the manifest, publishes the runner and integrator skills to UC, creates/reuses automations, generates the task graph (with per-task timeouts and retries) from the manifest, resets the build and smoke jobs |
| Build job YAML | `resources/build_waves.job.yml` | Shell job (one placeholder); setup notebook replaces with full wave graph |
| Setup job YAML | `resources/setup_build_waves.job.yml` | Runs the setup notebook. Run it after every deploy (deploy restores the placeholders); `run_smoke=true` also runs the smoke job |
| Smoke job YAML | `resources/build_waves_smoke.job.yml` | 2-item `for_each` nonce echo, a read-only `capability_probe` (CLI, apps/jobs read, SQL, telemetry) for converge sessions, and `app_probe_check` (`src/notebooks/app_probe_check.ipynb`), which proves from a job that the `probe_auth` service principal can call the apps, that their trace sources are readable, and that the job can read each Genie space's configuration (`CAN_EDIT`) |

## Getting started with Genie Code

Clone this repo into the same workspace where the project you want to build lives. The bundle and the project are separate Git folders — the bundle orchestrates the build, the project is what gets built.

```
/Workspace/Users/you@example.com/
  ├─ genie-build-waves/    ← this bundle (cloned once per workspace)
  └─ my-project/            ← the project being built
```

### Let Genie Code plan your build

Open Genie Code in your **project** folder and paste this prompt (replace the two paths):

> Read the build planner skill at `[/Workspace/Users/you@example.com/genie-build-waves]/src/skills/genie-build-planner/SKILL.md`, then read the files it references in that same `genie-build-waves/` directory (README, manifest schema, examples, and the two runtime skills). Once you understand the framework, analyze this project and help me decompose it into waves and sessions. The project is: **[describe what you're building]**. The genie-build-waves bundle is at `[/Workspace/Users/you@example.com/genie-build-waves]`.

Genie Code will:
1. Read the planner skill and all framework docs from the bundle repo
2. Analyze your project's files and structure
3. Propose a wave/session decomposition
4. Write the plan files, waves.json manifest, and plan index in your project
5. Deploy the bundle with `--var` flags (does not modify `databricks.yml` — the bundle stays generic)

### Deploy and run

If you've already written your plans and manifest and just need to deploy:

> Read `[/Workspace/Users/you@example.com/genie-build-waves]/README.md`. Deploy the bundle using `--var` flags — do **not** edit `databricks.yml` (keep it generic so multiple projects can share the same bundle). My project is at `[project workspace path]` on branch `[branch name]`. Use catalog `[catalog]` and schema `[schema]` for skills. [Create the schema automatically / I already have this schema].

**Important:** Always pass project-specific values as `--var` flags at deploy time. Never edit `databricks.yml` with project-specific values — the bundle is a shared tool, not a per-project config file.

### The planner skill

The full planning guide lives at `src/skills/genie-build-planner/SKILL.md` in the bundle repo. It covers:
* Project analysis and workflow mode selection
* Session decomposition rules (ownership, sizing, mode selection)
* Wave grouping and gate design
* Plan file format and conventions
* Manifest and bundle configuration

## Prompt examples

Copy-paste prompts for the three most common Genie Code sessions:

* **New project** — Kick off an initial build: [docs/prompts/new-project.md](docs/prompts/new-project.md)
* **Follow-up build** — After the initial build completes, append convergence waves that deploy, read telemetry, and iterate until stable: [docs/prompts/follow-up-build.md](docs/prompts/follow-up-build.md)
* **Repair a failed wave** — Re-start the build from a specific wave's sessions, integrator, or gate step: [docs/prompts/repair-failed-wave.md](docs/prompts/repair-failed-wave.md)

Each prompt has bracketed placeholders for paths, names, and IDs. Replace them with your project's values before pasting into Genie Code.

## Quick start (manual)

### 1. Prepare your project

In your target project folder (Git folder for `git`/`hybrid` mode, any workspace folder for `workspace` mode):

1. Write **session plans** as markdown files in `docs/plans/` with numbered tasks, scope, and acceptance criteria.
2. Write a **plan index** (`docs/plans/INDEX.md`) with the dependency graph and wave grouping.
3. Create a **`waves.json` manifest** — choose your workflow mode:
   * `git` (default): for code builds in a Git folder (see `examples/waves.json`)
   * `workspace`: for notebook/SQL/SDK work with no Git (see `examples/workspace-waves.json`)
   * `hybrid`: for projects that mix file editing with notebook execution
4. Create a `docs/sessions/` directory for session summaries.
5. For `git`/`hybrid` mode: add `.build-status/` to `.gitignore`.

### 2. Deploy with `--var` flags

Pass all project-specific values at deploy time. Do **not** edit `databricks.yml` — keep the bundle generic so it can be shared across projects.

```bash
databricks bundle deploy --target dev \
  --var="project_name=My App" \
  --var="instance_suffix=-my-app" \
  --var="build_root=/Workspace/Users/you@example.com/my-project" \
  --var="build_branch=feature-genie-build" \
  --var="manifest_path=/Workspace/Users/you@example.com/my-project/docs/plans/waves.json" \
  --var="skills_catalog=my_catalog" \
  --var="skills_schema=my_schema"
```

Optional variables (with defaults): `project_name` (`"Genie Build Waves"`, used in job names), `instance_suffix` (`""`), `create_skills_schema` (`"true"`), `runner_skill_id`, `integrator_skill_id`.

**One deployment per project.** `instance_suffix` is appended to the bundle root path (`.bundle/genie-build-waves<suffix>/<target>`), so each project gets its own deployment state and its own build, setup and smoke jobs. Use the same suffix every time you deploy or validate for a project. Without it, deploying for a second project replaces the first project's jobs.

### 3. Run setup to patch jobs

```bash
# Run setup to patch placeholders into real Genie Code tasks:
databricks bundle run setup_build_waves --target dev
```

### 4. Smoke test

Run setup with `run_smoke=true` to verify Genie Code tasks work inside `for_each`:

```bash
databricks bundle run setup_build_waves --target dev --params run_smoke=true
```

Pass = both iterations SUCCESS, each echoing its `session_id` and the nonce. Before a follow-up build, also read the `capability_probe` output: every check should be `ok` (and `deploy_permitted=yes`), otherwise `converge` sessions cannot work unattended. If the manifest's apps use `probes` or `min_traces`, or it has Genie spaces, `app_probe_check` must be `pass`; `skipped` means no app was running or no space exists yet, so re-run the smoke once they do. Probes always need `probe_auth`: Apps accept only OAuth tokens, so the job's own credential is redirected to sign-in.

### 5. Start the build

```bash
databricks bundle run build_waves --target dev
```

Or choose **Run now** on the build job in the Jobs UI. `branch` defaults to `build_branch`; override it with `--params branch=<branch>`. Each wave runs `wN_sessions` → `wN_integrate` → `wN_gate` → `wN_gate_check`, and the next wave starts only when `wN_gate_check` is true. Watch each `wN_gate` task.

## When a wave fails

1. Read the `wN_gate` output, `.build-status/<run_id>/wave_<N>_gate.json` and, for convergence waves, `wave_<N>_runtime.json` (deployment id, states, error samples, missing markers).
2. Read the failing session's status file and summary in `docs/sessions/`.
3. Passing sessions are already committed. Failing sessions' code is left uncommitted.
4. Fix the cause (plan, manifest, or code), then repair the run (below).
5. `requests` in the gate file list changes a session needed outside its owned paths. Apply them before repairing.

Note: downstream waves show as **Excluded** (not failed). This is the correct cascade behavior — they never ran and consumed no compute.

### Repairing a failed wave

Once `wN_gate_check` has evaluated to `false`, every later wave is Excluded. Re-running only `wN_gate` does **not** re-evaluate `wN_gate_check`, so the Excluded waves stay excluded and the run stays terminated. Always repair with dependents:

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
w.jobs.repair_run(
    run_id=<failed_run_id>,
    rerun_tasks=["wN_sessions", "wN_integrate", "wN_gate"],  # start of the failed wave
    rerun_dependent_tasks=True,  # re-runs wN_gate_check and every later wave
)
```

CLI equivalent: `databricks jobs repair-run <failed_run_id> --json '{"rerun_tasks": ["wN_sessions", "wN_integrate", "wN_gate"], "rerun_dependent_tasks": true}'`. If the run was already repaired once, also pass `latest_repair_id` (from `w.jobs.get_run(run_id, include_history=True).repair_history`). In the UI, choose **Repair run** and select the failed wave's tasks **and** everything after them, including each `wN_gate_check`.

Which tasks to name in `rerun_tasks`:

| What failed | `rerun_tasks` |
|---|---|
| A session (code, plan or manifest fixed) | `wN_sessions`, `wN_integrate`, `wN_gate` |
| Only the integrator (sessions passed) | `wN_integrate`, `wN_gate` |
| Only the gate verdict (e.g. stray files committed by hand, runtime soak) | `wN_gate` |

Keep `rerun_dependent_tasks=True` in every case. Without it, nothing after the named tasks runs.

**Pass `job_parameters` on every repair.** A `repair_run` falls back to the job-level parameter defaults when `job_parameters` is omitted. The setup job writes these defaults from the manifest, but if the original run was started with custom parameters (e.g. a different branch), the repair would silently use the wrong values. Always pass `branch`, `build_root`, and `manifest_path`.

**Transient agent start-up errors** (`INTERNAL_ERROR: start_agent_run`) are retried automatically: Genie Code tasks get `max_retries` (default 2, one minute apart, override with manifest `task_retries`). If a task still fails after its retries, repair as above; don't start a fresh run.

**Fresh runs.** If the build job was redeployed and re-patched since the failed run, Jobs refuses to repair it ("job structure has changed"). Start a new run with `only` set to the failed wave's task keys and everything after it (earlier waves show as skipped). Files left in the working tree by the earlier run (uncommitted summaries, code from failed sessions) are reported by the integrator as `carryover_files`, not strays, so they no longer fail the new run's first gate. Summary carryover is committed; code carryover is left for the session that owns it. The last wave fails on any carryover code nobody claimed, so a human decides what to do with it.

**Inherited files.** When the failed session itself reruns in the new run, it keeps its earlier changes and lists them in `files_changed`, even though none of this run's attempts touched them. The gate (`src/notebooks/session_status.py`) and the integrator credit such a file as **inherited** when the same session's status file from another run lists it and it is inside the session's `owned_paths` (and not its `exclude_paths`). For converge sessions, `files_changed` must equal the inherited files plus the union of the attempts' `files_changed`. Inherited files are committed with the session and recorded in the gate's `carryover_files` as `kind: "inherited"`.

**Why not repair?** A session that ends `blocked` or `fail` still finishes its `for_each` iteration as SUCCESS, so repairing from `<wave>_sessions` re-runs nothing. After fixing the cause, start a new run from that wave (above).

A convergence wave can commit (its session passed) and still fail on `runtime_gate` (e.g. the app crashed during the soak). The commit is kept as progress; repair re-runs the converge session, which starts from the committed code.

### Retarget after merge

After a feature branch is merged to main and deleted on the remote, the build job's `branch` parameter still points at the deleted branch. The integrator will fail with `branch not found on remote`. To retarget: create a new feature branch, update `branch` in `waves.json`, re-deploy with `--var build_branch=<new>`, re-run setup, and start a new run.

## Changing a build

* **Skill or prompt change**: Edit the `SKILL.md` in this repo, then re-run the setup job (it republishes the skills). On `dev`, deployments are source-linked, so setup reads `src/skills` straight from this repo. On other targets, setup reads the deployed copy, so run `bundle deploy` first.
* **Next build in the same manifest**: mark the finished build's waves `"archived": true`, append the new `<build>-<n>` waves, then re-run the setup job.
* **Wave or session change**: Edit `waves.json` in your project, then re-run the setup job. The setup notebook reads the manifest from `manifest_path` and regenerates the full task graph; no deploy is needed unless you change bundle variables.
* Never edit the build jobs in the UI; deploy and setup overwrite them.

## Workflow modes

| Mode | Sessions write to | Integrator commits | Use for |
|---|---|---|---|
| `git` (default) | Files in a Git folder | Yes, by explicit path | Code builds, app development |
| `workspace` | Notebooks, tables, dashboards, UC objects | No Git | Data engineering, ML, migrations, infra |
| `hybrid` | Mix of file edits and workspace operations | Commits file edits only | Projects combining code + execution |

Sessions also have **modes** (`edit`, `execute`, `configure`, `converge`) that control what they're allowed to do. See [docs/manifest-schema.md](docs/manifest-schema.md) for details.

## Key design decisions

* **Ownership boundaries prevent conflicts** — `owned_paths` (for file work) and `owned_assets` (for resource work) don't overlap within a wave.
* **Git guardrails are conditional** — Only active in `git`/`hybrid` mode. `workspace` mode has no Git requirements at all.
* **Sessions are Git read-only** — In `git`/`hybrid` mode, only the integrator commits, by explicit path, to a feature branch.
* **Placeholder workaround** — `genie_task` isn't in the bundle CLI schema; notebook placeholders get swapped via `jobs/reset`.
* **Dynamic task graph** — The setup notebook generates the wave task structure from the manifest, so different projects with different wave counts work without YAML changes. Jobs calls use API 2.2 and read every page, so graphs with more than 100 tasks work.
* **Repair-friendly** — `run_if: ALL_DONE` on integrator/gate means failures get reported. Repair re-runs from the failed wave (with dependents); passing earlier waves are not re-run.
* **Zero-compute cascade** — If/else gate checks use the Excluded propagation rule: when a gate fails, all downstream wave tasks are Excluded instantly (no wasted Genie Code compute).

## Guardrails

* In `git`/`hybrid` mode: sessions never run Git write commands; only the integrator commits.
* `main`/`master` are refused as branch targets.
* `edit` sessions touch only their `owned_paths`; `execute`/`configure` sessions touch only their `owned_assets`.
* Deploys only where `allow_deploy: true` or in `converge` sessions, only to their declared targets, and only one deploying session per wave.
* `converge` sessions must fix causes, not hide them; any suppression (test skip, compile exclude, `@ts-ignore`, swallowed errors) must be listed in the status file and is surfaced in the gate output.
* Never put the build-waves job in the bundle a `converge` session deploys — the deploy would reset the running build job.
* Notebook/SQL execution only where `allow_execute: true` (default for `execute`/`configure` sessions).
* `.build-status/` is never committed.

## Manifest reference

See [docs/manifest-schema.md](docs/manifest-schema.md) for the complete `waves.json` schema.
