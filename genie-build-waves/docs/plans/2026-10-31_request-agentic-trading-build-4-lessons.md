# Request: framework lessons from Agentic Trading build 4 (for the designer to review)

**Status:** open, for review (not scheduled) · **From:** Agentic Trading build 4 (run `800187417582767`, partial run
`396653921760382`, sessions 50-71) and its owner sessions · **Date:** 2026-10-31 · **Size:** several independent changes;
pick and order them · **Source in the consumer repo:** `agenticTrading/docs/requests/R16_build_waves_lessons.md`
(details and evidence), `docs/requests/R10_build4_session_requests.md`

Agentic Trading build 5 starts on the **current** framework (owner decision 2026-10-31) and works around each item
below in its manifest and plans. Nothing here blocks it. Code references are to `main` at `67f9811`.

## 1. Freshness is measured from the run start, so fresh `only` runs fail

`src/notebooks/wave_gate_check.ipynb` compares deployments, job runs, pipeline updates and table commits with
`run_start` (`check_app` ~line 410, `check_job` ~545, `check_pipeline` ~573, `check_table` ~691). A fresh run started
with `only` (README "Fresh runs") for a market-hours wave at 10:43 ET failed every `require_fresh_deployment` target
although the data was minutes old, because the deploys happened in the earlier run. Repairing the original run passed.

Requested: measure freshness against the **wave** start (first `w<wave>_sessions` task start in this run), or allow a
per-target `fresh_since` (`run_start` | `wave_start` | ISO timestamp). Document the repair-the-original rule in the README
until then.

## 2. Gates that depend on outside conditions need preconditions and a tracked waiver

Three build 4 gate lines could not be met for reasons outside the code (no open position, so no monitoring rows; an
`ai_decide` span only when an entry is allowed; a health-check job that had never succeeded). Each was waived by
hand-editing `.build-status/<run>/<id>.json` (not in git) plus a note in `waves.json`.

Requested:
* A `waivers` block in the manifest (`wave`, `gate_line` or target, `waived_by`, `reason`, `request_id`, `expires`) that
  the gate applies and reports as `waived` (not `pass`) in the gate file and the build verdict.
* Planner guidance: write the precondition into the gate line and a fallback evidence path in the plan; never gate on a
  job with no known-good run.

## 3. Owner-interactive steps

Unattended Genie Code tasks are refused for `apps create` / some `apps update` calls (`Invalid delegation claim`),
`bundle run` of grant jobs, and account-group changes. Each cost a repair cycle in build 4 (sessions 66, 68).

Requested: an optional session field such as `owner_steps: [{when: before|after, commands: [...], verify: ...}]`
that setup renders into the plan header and the integrator checks (evidence present) before it fails the session.
At minimum, a planner section listing the known-refused operations.

## 4. Sessions cannot edit dashboard objects

A `.lvdash.json` that is a DASHBOARD workspace object fails with `editAsset` (file), and a Lakeview API write
rewrites the whole file. Requested: planner guidance (dashboard edits are owner steps or a dedicated session with an
approved API path) and an integrator note when a request targets a dashboard object.

## 5. Request routing and one request schema

The runner skill (`genie-build-session-runner/SKILL.md` ~line 170) shows `{path, change, why}`; the integrator skill
(~line 137) shows `{from, path, change}`; build 4 sessions also wrote `{to, path, ask}`, `{to, what}` and `{to, text}`.
Requests addressed to a later session reach it only if a person edits its plan.

Requested:
* One schema in both skills: `{from, to, path, change, why, priority}`.
* An integrator step that lists open requests per target session in the wave summary and warns (or fails, by manifest
  option) when a request names a later session whose plan or `context_notes` does not mention it.
* Requests against files sessions may not edit (for example `PROJECT_MEMORY.md`) listed separately for the owner.

## 6. Non-standard session status values

Hand-resumed or long sessions wrote `"done"` and `"completed"` (sessions 53, 59); the integrator accepts only `pass`,
so each needed a manual edit and a repair. Requested: the runner skill states the allowed values explicitly, and the
integrator either maps `done` / `completed` to `pass` with a warning or fails with a message that names the fix.

## 7. Blocked sessions end SUCCESS

A session that writes `blocked` still ends its `for_each` iteration SUCCESS, so repairing `w<wave>_sessions` re-runs
nothing (already noted from Semantic Ground Truth, 2026-10-26). Requested: the runner fails the iteration when its
final status is not `pass`, or the README repair table covers this case.

## 8. Default error patterns and the redaction placeholder

Consumer patterns such as `api_token=[A-Za-z0-9]{8,}` match `api_token=REDACTED`. Requested: a planner note (and the
examples) using a negative lookahead, e.g. `api_token=(?!REDACTED)[A-Za-z0-9]{8,}`; check `DEFAULT_IGNORE_PATTERNS`
for the same issue.

## 9. Tooling versions

The integrator ran Databricks CLI v1.22.1, which rejects `workspace.sync_mode` (needs v1.23.0, which deprecates
`presets.source_linked_deployment`), and the guardrail blocks downloading a newer CLI. Serverless `npm` / `npx` are
broken symlinks; the working route is in the consumer's `docs/runbooks/node_toolchain_genie_code.md`. Requested: a
pinned, guardrail-approved CLI and Node toolchain step (or capability-probe check) in setup / smoke.

## Done when

The designer has marked each item adopt / defer / drop in this file, with a plan or branch for the adopted ones.

## Not in scope

Agentic Trading app code; the consumer's build 5 manifest (it uses workarounds for 1-9).
