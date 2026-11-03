# Omnigent + Databricks Sandbox for Build-Waves Monitoring

**Status:** Research note
**Date:** 2026-11-03
**Scope:** Whether Omnigent, hosted on a Databricks Sandbox in the same workspace, can monitor and optionally repair genie build wave jobs in the same way we considered using Devin.

## Short answer

Yes, in principle. Omnigent on Databricks can run agent sessions on a **Databricks Sandbox** host that stays up when the laptop is off, uses the user's Databricks workspace identity, and routes model access through Foundation Model APIs over Unity Gateway. Omnigent also supports **scheduled tasks** that start recurring agent sessions, including on managed sandbox hosts.

That makes Omnigent a plausible replacement for an external Devin monitor for the **monitor/report** role, and a plausible option for limited **repair orchestration** if the repairs are done by calling Databricks-native surfaces such as Jobs APIs, CLI commands, or workspace files.

However, Omnigent is still less attractive than the in-job continuation pass for the step-limit problem because it is still an **outside observer**: it monitors the job and reacts after the fact, while the continuation pass fixes the failure mode inside the job graph itself.

## Relevant platform facts

### Omnigent on Databricks

* Omnigent on Databricks is a managed Omnigent server integrated with Databricks identity, Foundation Model APIs, Unity Gateway, and MLflow Tracing.
* Sessions launched from the workspace are attributed to the user's Databricks identity; there is no separate Omnigent account inside the Databricks-hosted product.
* A session can run on either:
  * a **Databricks Sandbox** host provisioned by Databricks, or
  * a user-registered machine/VM host.

### Databricks Sandbox

* A sandbox is an isolated, serverless Linux machine intended for agent harnesses, background tasks, and untrusted code.
* The sandbox includes a persistent home directory for the lifetime of that sandbox.
* The Databricks CLI inside the sandbox is already authenticated to the workspace where the sandbox runs.
* Sandboxes have open outbound network access in the current beta design and do not integrate with serverless egress control.
* The compute profile is fixed: 4 vCPUs, 8 GB RAM, 100 GB persistent home storage.

### Omnigent scheduled tasks

* Omnigent scheduled tasks are saved prompts that fire agent sessions on a recurring schedule.
* A task can either start a **new session each time** or **continue in the same session** across firings.
* A task can target either a **connected host** or a **managed sandbox**.
* Tasks support a per-run cost cap and a permission mode. When an agent uses Omnigent's scheduled-task tools to create or update tasks, that agent call requires interactive approval; direct UI or REST API changes follow their normal authorization rules.

## What this enables for build waves

## Option A — report-only monitor

Use Omnigent as a read-only monitoring agent that runs on a schedule, inspects the latest build-waves job run, and writes a status report.

### How it would work

1. A scheduled Omnigent task fires every N minutes on a managed sandbox host.
2. The agent uses the Databricks CLI or SDK already available through workspace auth to inspect:
   * the build-waves job definition,
   * the latest run and task states,
   * exported artifacts under `build_root`, and
   * workspace files such as session summaries or status exports.
3. The agent classifies the state of each wave:
   * passed,
   * failed,
   * blocked,
   * incomplete / step-limit likely,
   * integrator failed,
   * gate failed.
4. The agent writes a report somewhere durable:
   * a workspace file under a status folder,
   * a UC volume file, or
   * a comment / issue in an external system if that connector is available.

### Fit

Good fit for:

* periodic health checks,
* long-running background monitoring,
* report generation with a conversational summary,
* optional escalation workflow.

### Limits

* It still discovers problems **after** the job run reaches that state.
* It depends on Omnigent preview + Sandbox preview being enabled in the workspace.
* Session visibility is user-scoped, so if a human creates the scheduled task, the runs and their conversational history belong to that user unless a more shared operating model exists.

## Option B — report plus controlled repair

Use Omnigent to monitor the build job and invoke a narrow, approved repair action when the diagnosis is straightforward.

### Candidate repair actions

* Start a repair run at a specific task key (for example the continuation-discovery task or the integrator task).
* Re-run a failed gate after checking that the failure was external and transient.
* Export and summarize failure context for a human instead of repairing when the outcome is blocked or ambiguous.

### Recommended boundaries

Allow automatic repair only for situations with a deterministic playbook:

* latest wave task failed due to infrastructure/transient issues,
* continuation-discovery indicates incomplete sessions and the continuation task exists,
* integrator failed after all sessions finished,
* a known export/reporting step failed without changing source state.

Require escalation for:

* blocked sessions,
* request/approval deadlocks,
* branch drift or merge conflicts,
* ambiguous runtime gate failures,
* any fix that edits manifest or code.

### Why Omnigent is better positioned than Devin here

* Same-workspace identity is simpler: the sandbox already has a Databricks-authenticated CLI and Omnigent uses Databricks identity instead of a second SaaS identity plane.
* No separate GitHub App is needed for read-only monitoring.
* Model traffic stays inside Databricks governance via Unity Gateway / Foundation Model APIs.

### Why Omnigent is still not the first fix

The step-limit issue is fundamentally a **job design** problem, not just a monitoring problem. The continuation pass repairs it at the source by giving the job one more in-job iteration over incomplete sessions. Omnigent can detect and respond to the symptom, but it does not remove the symptom.

## Identity and authorization model

The important design choice is **who owns the Omnigent scheduled task**.

### If a user owns it

Pros:

* quick to set up,
* uses that user's Databricks identity automatically,
* easy to inspect and debug.

Cons:

* all actions are attributable to a person,
* loss of access or role changes break the automation,
* operational ownership is weaker.

### Preferred long-term model

Use a dedicated operational identity once Omnigent supports a clean shared-service operating model for scheduled tasks in your environment.

Until that is clear, keep Omnigent in a **report-only** posture or a very narrow repair posture, because scheduled sessions are tied to session ownership and visibility rather than to a distinct external service principal pattern like the Devin design we documented.

## Proposed operating model for a proof of concept

### POC goal

Answer one question: can Omnigent reliably inspect build-waves job state from a sandbox and produce a useful report, without creating duplicate sessions or requiring a human to babysit the run?

### Minimal POC

1. Create one Omnigent scheduled task on a managed sandbox.
2. Frequency: every 30 minutes.
3. Scope: report only.
4. Inputs:
   * build job id,
   * workspace path to the build-waves root,
   * path to the exported status folder.
5. Outputs:
   * one markdown status file per run, or
   * one continuously updated summary file.
6. Acceptance checks:
   * can read the target job and latest run,
   * can read the exported status artifacts,
   * correctly distinguishes success vs incomplete vs blocked vs failed,
   * does not create duplicate monitoring conversations unexpectedly,
   * cost remains bounded by the scheduled-task budget.

### Follow-on POC

If report-only works, add one repair action:

* trigger a repair from the designated continuation-discovery task when the diagnosis is "incomplete sessions only".

Keep all other cases report-only.

## Comparison with the Devin monitor design

| Dimension | Omnigent + Databricks Sandbox | Devin monitor |
| --- | --- | --- |
| Identity to Databricks | Native Databricks identity | Separate external identity + Databricks OAuth/service principal |
| Host | Databricks Sandbox in the same workspace | Devin-managed session VM |
| Model governance | Through Databricks FMs + Unity Gateway | External model/runtime |
| Git push to repo | Needs whatever Databricks-side git credentials / repo access exist | Needs Devin GitHub App or other Git credentials |
| Best use here | Read-only monitor; narrow repair | Read-only monitor; narrow repair |
| Main weakness | Still external to the job's control flow | Still external to the job's control flow |

## Recommendation

1. Keep the **continuation pass** as the primary fix for step-limit / incomplete-session failures.
2. If we want an external agent monitor, prefer **Omnigent on a Databricks Sandbox** over Devin for the first proof of concept because identity, workspace access, and model governance are simpler.
3. Start with **report-only** monitoring.
4. Add at most **one** automatic repair path, tied to a deterministic continuation or integrator rerun.
5. Do not use Omnigent to edit manifests, code, or branch state autonomously in phase 1.

## Open questions to test in this workspace

* Can an Omnigent scheduled task reliably target the same sandbox/host for repeated monitoring runs, or is a fresh managed sandbox per run preferable?
* What is the cleanest durable output location for reports: workspace file, UC volume, or a jobs artifact folder?
* Can a scheduled task owned by one user serve as a stable team-operated monitor, or do we need a different ownership model?
* How well does Omnigent handle Jobs repair workflows from its current Databricks integration surface?
* If the workspace later enables serverless egress control, does that rule out Sandbox-hosted Omnigent for this role?
