# Follow-up Build — Convergence Waves Planning Prompt

> Paste this into Genie Code in your **project** folder after the initial build has completed
> (or partially completed with failures). This prompt tells the planner to read the build
> output, identify what needs fixing, and append convergence waves that deploy, read
> telemetry, and iterate until stable.
> Replace the bracketed placeholders with your project's details.

---

## Prompt

We are continuing the `[project name]` build. The initial build (waves 0 through N) ran to completion — sessions passed their static gates — but the first real deploy failed (or the build stopped at a failed wave). We need a follow-up build that fixes the errors, applies any unfulfilled cross-session requests, deploys, reads telemetry, and iterates until stable.

### What changed since the initial build

The **genie-build-waves** framework (at `[/Workspace/Users/<you>/genie-build-waves]`) now supports:

- **`converge` session mode**: deploy, read deployment status and OTel logs, diagnose, fix within `owned_paths`, and redeploy in a bounded loop (up to `max_attempts`).
- **`runtime_targets`** in the manifest: declares each deployable thing (app, job, pipeline, dashboard, Genie space) with its bundle target, deploy commands, telemetry tables, error/ignore patterns, required startup markers, and stability criteria (soak minutes, max errors, min traces).
- **`runtime_gate`** on a wave: the gate notebook deterministically checks the named targets — deployment succeeded during this run, running, soak-stable, error lines clean, startup markers present, probes pass, traces show up without errors. A **passing stable build is part of the pass criteria**.
- **`instance_suffix`** variable: one genie-build-waves deployment per project.
- **`context_notes`** on a session: hand-over context from this interactive session.
- **Manifest validation**: the setup job rejects waves where a deploying session shares the wave with another session (single-writer rule). Converge waves are forced to concurrency 1.

Read these files from the genie-build-waves bundle to understand the updated schema:
1. `/Workspace/Users/<you>/genie-build-waves/README.md`
2. `/Workspace/Users/<you>/genie-build-waves/docs/manifest-schema.md`
3. `/Workspace/Users/<you>/genie-build-waves/examples/converge-waves.json`
4. `/Workspace/Users/<you>/genie-build-waves/src/skills/genie-build-planner/SKILL.md`

### Current state

- **Repo**: `[repo name]`, branch `[branch name]` (commit `[sha]`, [pushed/clean])
- **Build run ID**: `[run_id]` on job `[job_id]`
- **Build status**: [describe — e.g. "waves 0-4 passed, wave 5 gate failed", or "all waves passed but first deploy failed"]
- **Deployable targets**: [list what needs to deploy — e.g. app `my-app-dev`, job `my-job`, pipeline `my-pipeline`]
- **Telemetry tables**: [list OTel tables — e.g. `catalog.schema.app_otel_logs`, `catalog.schema.app_otel_spans`]
- **Known errors**: [list compile errors, runtime errors, or point to OTel log query results]
- **Unfulfilled requests**: [list cross-session requests from gate files, or state "none"]

### Step 1: Read the build output

Read these files from the project's `.build-status/` directory to understand what happened:

- `.build-status/[run_id]/wave_*_gate.json` — gate results per wave (pass/fail, checks, requests)
- `.build-status/[run_id]/wave_*_runtime.json` — runtime gate details (deployment IDs, states, error samples)
- `docs/sessions/` — session summaries from each passing session
- `docs/plans/waves.json` — the current manifest (waves 0 through N)

Identify:
1. Which waves passed and which failed.
2. Any unfulfilled cross-session `requests` from the gate files.
3. Any errors from deployment attempts or OTel log queries.
4. What needs to deploy and where its telemetry lands.

### Step 2: Write the follow-up manifest

Append new waves to the existing `docs/plans/waves.json`. Keep the existing waves' content unchanged — they already ran and their results are in `.build-status/` — but mark each of them `"archived": true` so setup generates no tasks for them (the job stays small, and the new waves start the run). Name the new waves `<build>-<n>` (e.g. `2-0`, `2-1`; task keys `w2-0_sessions`, ...). Their `depends_on` may name archived sessions; those count as done. Update:

- `branch`: current branch (if it changed since the initial build)
- Add `context_files` if not already present: `["PROJECT_MEMORY.md", "docs/plans/INDEX.md"]`
- Add `runtime_targets` for each deployable target:
  ```json
  "runtime_targets": {
    "[target_name]": {
      "type": "app",
      "name": "[app-name]",
      "resource_key": "[bundle_resource_key]",
      "bundle_root": "[/Workspace/Users/<you>/<project-folder>]",
      "bundle_target": "dev",
      "deploy_commands": [
        "bundle deploy --target dev",
        "bundle run [resource_key] --target dev"
      ],
      "telemetry": {
        "logs_table": "[catalog.schema.app_otel_logs]",
        "traces_table": "[catalog.schema.app_otel_spans]",
        "deployment_id_attribute": "app.deployment_id",
        "log_source_attribute": "app.log_source",
        "error_patterns": ["[regex patterns matching your errors]"],
        "ignore_patterns": ["[regex patterns for benign log lines]"],
        "required_markers": ["[strings that prove the app started]"]
      },
      "stability": { "soak_minutes": 10, "max_errors": 0, "min_traces": 1 }
    }
  }
  ```

### Step 3: Plan the new waves

#### Optional: Parallel fix wave (edit sessions)

If the known errors fall into disjoint file groups, fix them in parallel `edit` sessions with non-overlapping `owned_paths`. Static gates only (bundle validate, no runtime_gate). This is a speed-up, not a substitute for convergence.

Group errors by file ownership — e.g.:
- Session A: errors in `server/services/*.ts`
- Session B: errors in `server/routes/*.ts`
- Session C: config/infra cleanup (`databricks.yml`, `app.yaml`, `.gitignore`, dead code deletion)

Each session's plan file should include a `## Known issues` section listing the specific errors and requests it handles, with their source (gate file, OTel query, deploy output).

#### Convergence waves (one per runtime target, in dependency order)

One `converge` session per wave, alone:
- `mode`: `converge`
- `runtime_targets`: `["[target_name]"]`
- `owned_paths`: broad — cover all code the session may need to fix
- `max_attempts`: [5-10, depending on expected fix iterations]
- `timeout_minutes`: [120-240]
- `depends_on`: all sessions from prior fix/converge waves it needs
- Wave has `runtime_gate`: `["[target_name]"]`
- Scope: deploy, read OTel logs for the new deployment ID, diagnose errors, fix within owned_paths, redeploy. Repeat until RUNNING with no error lines and required markers present.

Order converge waves by dependency: the app before the MCP service that needs the app's URL, the pipeline before the dashboard that queries its tables, etc.

### Step 4: Write plan files

Create `docs/plans/<session_id>_<title>.md` for each new session. Include:
- `## Known issues` — specific errors and requests, with their source
- `## Tasks` — numbered, specific tasks
- `## Context` — cross-session dependencies, prior session summaries
- `## Acceptance Criteria` — testable criteria including the runtime gate checks

When you write `context_notes` on a session in the manifest, include findings from this conversation that the runner should know but shouldn't have to re-derive.

### Step 5: Re-run setup and start the follow-up build

After committing the updated manifest and plans:

```bash
# Re-run setup to regenerate the task graph with the new waves
databricks bundle run setup_build_waves --target dev \
  --var="instance_suffix=-[project-slug]"

# Start the follow-up build
databricks bundle run build_waves --target dev \
  --var="instance_suffix=-[project-slug]"
```

### Constraints

- **Stay on the current branch** (or create a new feature branch if needed).
- **Do NOT deploy from this planning session.** The converge session handles deployment.
- The genie-build-waves bundle is deployed separately with `--var="instance_suffix=-[project-slug]"`.
- **No suppressions**: fix the actual errors. No `@ts-ignore`, no `tsconfig` `exclude`, no swallowed exceptions. Any suppression must be listed in the status file and is surfaced in the gate output.
- **Single-writer rule**: any wave with a `converge` session must have exactly that one session and concurrency 1.
- **Never put the build-waves job in the bundle a converge session deploys** — the deploy would reset the running build job.

### Deliverables

Before committing, show me:
1. The updated `waves.json` with old waves preserved and new waves appended
2. The plan files for each new session
3. The `runtime_targets` definitions
4. `bundle validate --strict --target dev` passing (for the project bundle, if applicable)

Then commit and push on the current branch.

---

_This prompt is generic. Adapt the placeholders for your project, build output, and workspace._
