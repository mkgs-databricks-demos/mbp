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

## Files

`src/notebooks/monitor_grants.py`, `src/notebooks/setup_build_waves_job.ipynb`, `databricks.yml`, `resources/setup_build_waves.job.yml`, `README.md`, `docs/plans/2026-11-03_devin-monitor-requirements.md`, `src/skills/genie-build-monitor/SKILL.md`, `tests/test_monitor_grants.py`, `docs/sessions/INDEX.md`.
