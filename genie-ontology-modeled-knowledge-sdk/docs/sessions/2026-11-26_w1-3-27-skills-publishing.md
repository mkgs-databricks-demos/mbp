# Session 27 (wave 1-3): Publish SDK skills to the Unity Gateway skills library (R1)

Run `288268071022101`, task `w1-3_session`, branch `mg-genie-ontology-build-1-plan` (checked read-only; no Git writes). Mode `edit` with `allow_execute`; owner authorization `uc_skills.publish` on the six SDK skills in the SDK schema (target `dev`).

## Context checked

* P1-3: `ai_gateway.list_skills` on the SDK schema (`hls_fde_dev.dev_matthew_giglia_ontology_sdk`, from `bundle summary -t dev`) returned 0 skills, no feature-disabled error.
* Publish calls taken from `genie-build-waves/src/notebooks/setup_build_waves_job` (get/create skill, `files.upload` under `/Skills/...`, `finalize_skill`). Files API read-back verified on the runner skill (`list_directory_contents` + `download`; missing path raises `NotFound`).
* Problem: the serverless default `databricks-sdk` has no `ai_gateway` service. Fix: `%pip install --upgrade databricks-sdk` (0.171.0 has `create/get/list/update/delete/finalize_skill`); the notebook's install cell upgrades it.

## Changes

| File | Change |
|---|---|
| `ci/skills.yaml` | New. 6 folders -> `${SKILLS_CATALOG}.${SKILLS_SCHEMA}.<snake_case id>` |
| `ci/github/workflows/publish-genie-ontology-skills.yml` | New. Hygiene test job + publish job (`production` env, OIDC `id-token: write`, path filter, `workflow_dispatch` dry run). Action ref is a zero SHA with `TODO(owner): pin reviewed SHA` |
| `src/genie_ontology_modeled_knowledge_sdk/skills_publish.py` | New. `load_mapping`, `read_skill_files`, `front_matter`, `skill_limit_errors`, `check_schema` (never creates unless `create_schema=True`), `published_files`, `plan_publish`, `publish` (changed files only; no finalize when unchanged), `list_published`, CLI |
| `notebooks/publish_skills.ipynb` | New. Widgets `skills_catalog`, `skills_schema` (empty defaults), `sdk_version`, `dry_run`; installs SDK + wheel `<sdk_volume_path>/.internal/...whl`, restarts, checks schema, plans, publishes, lists |
| `schemas/sdk_config.schema.json`, `config.py` | Optional `skills: {catalog, schema, ids}` (ids snake_case); `SdkConfig.skills`, round-trips through `to_dict` |
| `scaffold.py` | `skills_memory_section`; when `cfg.skills` is set, appends `## SDK skills` to the project's `PROJECT_MEMORY.md` (`sdk_config.json` gets it via `to_dict`) |
| `tests/test_skills.py`, `tests/test_skills_publish.py` | New, 30 tests (limits, front matter, mapping, fake-client idempotency, dry run, stale files, schema check, config key, scaffold) |
| `docs/skills/README.md`, `docs/skills/publish_results.md` | New. Flow, grants (documented, not applied), spike + fallback; results with placeholders |

## Decisions

* Widgets come before the install cell in the notebook (deviation from the usual install-first order): the wheel path is derived from the skills catalog/schema, since the skills schema is the SDK schema.
* Stale published files are reported, not deleted. Grants are documented only.
* Live publish used the module directly (plan task 7); the notebook calls the same functions and was not run.

## Live publish (authorized)

Run 1: 6 skills created, 9 files uploaded, 6 finalized. Run 2: 0 changes (no uploads, no finalize). Listing: 6 ids (`ontology_agent_curation`, `ontology_context_extraction`, `ontology_deep_eda`, `ontology_domain_research`, `ontology_mv_synthesis`, `ontology_tuning`); each `bundle_name` = folder name, finalized, published file count = local count.

## R1 spike: can an unattended job task load a Unity Catalog skill?

* **Yes, if it was published before the task started.** This task loaded its runner skill `hls_fde_dev.dev_matthew_giglia_build_waves.genie_build_session_runner` from Unity Catalog via `readSkillFile`.
* **No, for skills published during the task:** `readSkillFile("skills/hls_fde_dev.dev_matthew_giglia_ontology_sdk.ontology_tuning/SKILL.md")` returned "Skill file not found" right after publishing. The skill list is fixed at task start.
* How later sessions (wave 1-4 on) can tell: the id `<catalog>.<schema>.ontology_*` is in their skill registry and `readSkillFile` on it succeeds; otherwise use the workspace-folder fallback (`<sdk>/skills/<folder>/SKILL.md`), documented in `docs/skills/README.md`. The ontology skills now exist, so sessions starting after this one should see them.

## Checks

| Check | Result |
|---|---|
| pytest (copy in `/tmp/gos-gate-1-3`) | pass: 450 passed |
| skills_published (2 runs, 2nd 0 changes, 6 ids) | pass |
| No real catalog/schema in `ci/`, `docs/skills/`, `src/`, `tests/`, notebook | pass |
| No grants or schema creation | pass |
| `bundle validate` | skipped: no bundle YAML touched |

## Requests

* Owner: move `ci/skills.yaml` -> `<repo root>/skills.yaml` and the workflow -> `.github/workflows/`; pin the action SHA and check its input names; set `DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, `SKILLS_CATALOG`, `SKILLS_SCHEMA`; apply consumer grants (`READ VOLUME` per skill) for non-owner users. Optionally add a `ci/README.md` row for the new staged files (that file is not in this session's paths).
* Session 28 (run kit): reference skills by Unity Catalog id with the workspace-folder fallback (R1 item 5); pass `skills` into `sdk_config.json`.
