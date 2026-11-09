# 2026-11-09: Monitor principal grants for the UC monitor skill

## Problem

Setup publishes `genie_build_monitor` to UC, but an external monitor (Devin today, possibly another agent later) cannot read it without grants. The owner asked for a generic bundle variable and the minimum necessary privileges.

## Research (Databricks docs: AI Gateway "Govern skills" and "Skills API and SDK reference")

* Skills use the volume privileges. Reading a skill (metadata + download) needs `READ VOLUME` on the skill plus `USE CATALOG` and `USE SCHEMA` on its parents. `CREATE VOLUME` / `WRITE VOLUME` are for authors only.
* `READ VOLUME` can be granted on the skill itself (`securable_type="skill"`, `w.grants.update` / `databricks grants update skill <fqn>` / `PATCH /api/2.1/unity-catalog/permissions/skill/<fqn>`). A schema-level grant would expose every skill and volume in the schema.
* Only the skill owner or a `MANAGE` holder can grant on it; setup's `run_as` publishes the skill, so it owns it.
* Read-only checks on fevm-hls-fde: `get_effective` works for `catalog`, `schema` and `skill`; the monitor SPN (`mkgs-devin`, `72bab3e9-...`) held only `READ_METADATA` (via `account users`, from the metastore) on all three, so all three grants are needed; the owner holds `ALL_PRIVILEGES` + `MANAGE` on `hls_fde_dev` and owns `dev_matthew_giglia_build_waves`, so a dev setup run can grant them.
* OAuth scopes needed to read a UC Skill with a scoped secret are not documented in the pages read; probably `ai-gateway` and `files`. Marked unverified in README and the requirements doc.

## Changes

* `src/notebooks/monitor_grants.py` (new): `monitor_grant_plan` (catalog `USE_CATALOG`, schema `USE_SCHEMA`, skill `READ_VOLUME`), `held_privileges` (from `get_effective`, groups and inherited included), `missing_grants` (`ALL_PRIVILEGES` counts), `principal_problem`, `grant_command` (CLI fallback).
* `setup_build_waves_job.ipynb`: `monitor_principal` widget, validated in the Parameters cell (placeholder or whitespace -> error; set without `monitor_skill_id` -> error); new cell "Grant monitor read access" after publishing: skips grants already held, grants the rest, never raises, prints the owner CLI command on failure; `monitor_grants` in the summary output; intro markdown updated.
* `databricks.yml`: variable `monitor_principal` (default `""`), commented example under the dev target. `setup_build_waves.job.yml` passes it.
* README: "External monitor (optional)" section (manual SPN / secret / job and folder grants, what setup grants and why, revocation, Genie Code prompt), variables line, file table row. Requirements doc: grants table row. Monitor skill: grant note.
* `tests/test_monitor_grants.py`: 5 tests.

## Decisions

* Generic name `monitor_principal` (any agent; SPN application ID recommended, user or group accepted).
* Only the monitor skill is shared; runner and integrator skills stay private.
* Job (`CAN_VIEW` / `CAN_MANAGE_RUN`) and `build_root` (`CAN_READ`) grants stay manual: deploy and setup do not manage permissions, and level choice is the owner's.
* Grants are additive; no automatic revoke when the variable changes.

## Verification

* 172 tests pass. Setup cells parse. `bundle validate --strict` OK with and without `--var monitor_principal=...`; the value reaches the setup task's `base_parameters`.
* The plan / held / missing logic ran against the real Grants API (read-only, runner skill as a stand-in): monitor SPN missing all 3, owner missing none; `Privilege(...)` resolves all three names.
* Not run: the grant writes themselves (first run: the test instance's setup with `monitor_principal` in its vars file).

## Follow-up: build job grant in the bundle

Owner asked to include the job grant so it needs no second step and survives redeploys; chose the bundle YAML over a setup PATCH.

Research (CLI v1.23.0, direct engine, scratch bundle `permtest` deployed to the owner's dev `.bundle` folder; jobs `permtest-a` 510820400312418 with a permissions block, `permtest-b` 290452284207787 without):

* `permissions: [{service_principal_name: ${var.monitor_principal}, level: ...}]` with an empty variable: the CLI drops the entry; `validate --strict` OK. The CLI adds the deployer as `IS_OWNER` whenever a job has a permissions block.
* The direct engine plans `resources.jobs.<name>.permissions` as one resource holding the full list.
* Deploy with the principal set -> job ACL `CAN_MANAGE_RUN` + owner. Redeploy with it empty -> the SPN grant was removed. The bundle owns the ACL.
* Not verified: whether a grant added in the UI survives a deploy (my permissions PATCH was blocked; the owner did not add one). Docs say "expected to be removed".
* Docs (bundles "Set permissions"): job levels `CAN_MANAGE`, `CAN_MANAGE_RUN`, `CAN_VIEW`, `IS_OWNER`; resource-level permissions combine with target and top-level ones.

Changes: `build_waves.job.yml` permissions block (`monitor_principal` at `monitor_job_level`); variable `monitor_job_level` (default `CAN_VIEW`); `monitor_grants.monitor_var_problems` + check in `scripts/deploy_instance.py` (only `CAN_VIEW` / `CAN_MANAGE_RUN`, SPN application ID, no user names; exit 2); README (what deploy grants, ACL ownership, `build_root` grant still manual, prompt), requirements doc build job row, `databricks.yml` comments; 1 more test (173 pass). `bundle validate --strict` OK with and without the variables; the build job shows the expected permissions, setup and smoke jobs none.

Scratch jobs `permtest-a` / `permtest-b` are still deployed (bundle at `/tmp/permtest`, remote root `/Workspace/Users/matthew.giglia@databricks.com/.bundle/permtest/dev`), kept for the UI-grant check; delete them afterwards.

## Files

`src/notebooks/monitor_grants.py`, `src/notebooks/setup_build_waves_job.ipynb`, `resources/build_waves.job.yml`, `scripts/deploy_instance.py`, `databricks.yml`, `resources/setup_build_waves.job.yml`, `README.md`, `docs/plans/2026-11-03_devin-monitor-requirements.md`, `src/skills/genie-build-monitor/SKILL.md`, `tests/test_monitor_grants.py`, `docs/sessions/INDEX.md`.
