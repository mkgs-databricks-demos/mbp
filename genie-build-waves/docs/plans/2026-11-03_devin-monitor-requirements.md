# Requirements: Devin as an external monitor for build-waves runs

Status: **draft 2026-11-03, not implemented.** Optional add-on. Nothing in the bundle depends on it; the [continuation pass](2026-11-03_continuation-pass.md) handles sessions that run out of steps inside the job, for every user.

## Role

Devin (Cognition) watches a build job from outside the workspace and does what only an outside observer can:

* report each wave's result and the reason for any failure;
* repair runs whose cause is transient or already fixed;
* escalate what needs a person.

It does **not** run sessions, edit project code, change the manifest, deploy the bundle, or resume Genie Code conversations. Genie Code job-task conversations can only be continued interactively after the task ends ([Genie Code task for jobs](https://docs.databricks.com/aws/en/jobs/tasks/genie-code/)); there is no API to post into them.

### Levels

| Level | Devin may | Databricks permission on the build job |
|---|---|---|
| 1. Report (start here) | Read run state, task outputs, gate and status files; send a summary | `CAN_VIEW` |
| 2. Repair | Level 1, plus `repair-run` / `run-now --only` for the cases in the decision table | `CAN_MANAGE_RUN` |

Never grant `CAN_MANAGE` or `IS_OWNER`: setup (`jobs/reset`), deploys and permission changes stay with the instance owner.

## Databricks side: identity and authentication

### Service principal

* Create a **dedicated** service principal per instance (or per team), for example `build-waves-monitor`. Do not reuse a deploy principal, a job `run_as` principal, or a personal token.
* Give it the **Workspace access** entitlement (needed for the Jobs and Workspace APIs). No other entitlements.
* Authenticate with **OAuth machine-to-machine** (client ID + OAuth secret): [Authorize service principal access with OAuth](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m/). The CLI and SDKs pick it up from `DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` ([unified authentication](https://docs.databricks.com/aws/en/dev-tools/auth/index/)) and exchange it for short-lived tokens.
* Do not use personal access tokens. If Devin later documents an OIDC token issuer for its sessions, prefer workload identity federation (no stored secret) over the OAuth secret.
* Set an expiry on the OAuth secret and record the rotation date with the instance's other secrets.

### Grants

| Object | Grant | Why |
|---|---|---|
| Build job | `CAN_VIEW` (level 1) or `CAN_MANAGE_RUN` (level 2) | `jobs get`, `get-run`, `get-run-output`; repairs |
| `build_root` folder | `CAN_READ` | `<status_dir>/<run_id>/*.json` (gate, gate result, runtime, session status files), `docs/sessions/` summaries, the manifest |
| Setup and smoke jobs | none (optionally `CAN_VIEW`) | Devin never runs setup |
| Unity Catalog | none | The gate notebook does the UC reads; Devin only reads its results |

Repairs and new runs execute as the job's own `run_as` identity, not as the service principal; the principal only needs permission to manage runs. Verify this once with a no-op repair before relying on level 2.

### Network

* If the workspace has IP access lists or private connectivity, allow Devin's egress. Devin does not publish fixed egress addresses in the docs reviewed; confirm with Cognition before enabling.
* The OAuth token endpoint is on the workspace host (`https://<workspace-host>/oidc/v1/token`), so one hostname covers both.

## Devin side

### Organization and repository

* A Devin organization with automations enabled. Only the repo holding the bundle docs and skills needs to be readable; **write access is not required**.
  * Public repo: Devin sessions can clone it without the GitHub App.
  * Private repo: install the Devin GitHub App with **Only select repositories** and grant it to the Devin organization ([Devin GitHub integration](https://docs.devin.ai/integrations/gh)). The app requests broad read/write permissions; scope it to this repo.

### Environment (blueprint)

* Databricks CLI, pinned to the version the bundle documents (`databricks --version`). Install the Python SDK only if the monitor skill needs it.
* Secrets: `DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`. Store them as **personal secrets on a Devin service user you manage** (or your own personal secrets while testing), not as organization secrets, which every session in the Devin organization can read. See [Secret Management in Devin](../../../unity-gateway/devin-mcp/docs/guide.md#secret-management-in-devin) for the scopes and what is still unverified.
* Ignore any Databricks credentials already present in the environment from other teams; the monitor must use its own principal. Have the first step print `databricks current-user me` and stop if the identity is not the monitor principal.

### Network policy

Automation sessions start with a restricted network policy. Add only `<workspace-host>` (plus the Git host if the repo is private). Do not set an unrestricted policy.

### Automation

| Setting | Value |
|---|---|
| Trigger | Preferred: the build job's notifications (`on_start`, `on_success`, `on_failure`) sent to a Devin incoming-webhook trigger. Fallback: a schedule (for example every 30 minutes) with a Preflight check script that exits without starting a session when the build job has no active or newly finished run. |
| Action | Start a session with the monitor skill and the job ID, or message one long-running session (`auto_create`) so context carries across a multi-day build. |
| Concurrency | 1 run at a time; queue depth small (events for the same run are redundant). |
| Limits | Per-session ACU limit; invocation rate limit. |
| Run as | The automation creator (or the managed service user), so sessions are attributed to the instance owner and receive that identity's personal secrets. Running as organization uses the system user, which has no personal secrets. Verify secret visibility before go-live. |
| Notifications | Email to the instance owner, or a Slack channel if the Devin organization has Slack connected. |
| Tags | A session tag per instance, to track cost. |

Open: Databricks webhook notification destinations send a fixed payload with optional basic auth; confirm the Devin webhook trigger accepts it (or needs a relay) before relying on it.

### Instructions

A tool-agnostic `genie-build-monitor` skill in this bundle (to be written), built from `docs/prompts/repair-failed-wave.md` and the README. Devin reads it from its clone of the repo; Genie Code users can use the same file. A Devin playbook can point at it instead of copying it.

## What the monitor reads and calls

| Need | Call |
|---|---|
| Find the instance's runs | `jobs list-runs --job-id <id>` |
| Run and task state, repair history | `jobs get-run <run_id> --include-history` |
| Gate and verdict messages | `jobs get-run-output <task_run_id>` for `w<w>_gate` and `build_verdict` |
| Gate details | `workspace export <build_root>/<status_dir>/<run_id>/wave_<w>_gate.json` (and `_gate_result.json`, `_runtime.json`) |
| Session details | `workspace export .../<run_id>/<session_id>.json`, `docs/sessions/*-<session_id>-*.md` |
| Repair (level 2) | `jobs repair-run <run_id>` with `rerun_tasks`, `rerun_dependent_tasks: true`, `latest_repair_id`, and the run's original `job_parameters` (`branch`, `build_root`, `manifest_path`) |

## Decision table

| Observation | Level 1 | Level 2 |
|---|---|---|
| Wave passed | Report | Report |
| Genie Code task failed after its retries (`INTERNAL_ERROR: start_agent_run`) | Report | Repair from `w<w>_sessions` |
| Session still incomplete after the continuation pass | Report session, conversation and `progress.next` | Same; do not repair (a person resumes it) |
| Integrator failed, sessions passed | Report | Repair from `w<w>_integrate` |
| Runtime gate failed on soak or probes only | Report | Report; repair from `w<w>_gate` only if the cause was external and is gone |
| Session `blocked`, or gate lists `requests` | Report and escalate | Same |
| Repair refused ("job structure has changed") | Report; the owner decides on a fresh `--only` run | Same |
| Branch missing on the remote | Report; see "Retarget after merge" | Same |
| Anything else | Report and escalate | Same |

Limit level 2 to one automatic repair per wave per run; after that, escalate.

## Acceptance checks

1. From a Devin session: `databricks current-user me` returns the monitor principal.
2. `jobs get <build_job_id>` succeeds; `jobs get` on a job not shared with the principal (or its groups) is denied.
3. Exporting a status file under `build_root` succeeds; exporting a folder not shared with the principal is denied.
4. Level 2 only: a repair of a finished smoke run succeeds and runs as the job's `run_as`.
5. A test notification (or one scheduled tick) produces one report and no duplicate sessions.

## Open questions

* Devin egress addresses for workspaces with IP access lists.
* Whether automation sessions run as creator, and child sessions, receive personal secrets (test with a dummy personal secret; report only whether it is set).
* Webhook payload compatibility (see Automation).
