# Build-1 Requests

Status: **accepted by the owner (2026-11-25), not yet planned.** Source: [the build-0 SDK code review](../../reviews/2026-11-25_build-0-sdk-review.md) (gap ids G1-G9 below refer to it). The requests are listed in the owner's agreed **priority order**; the [sequencing table](#sequencing) gives the order they can be built in, because some depend on others.

When build-1 is planned, each request becomes one or more plan files under `docs/plans/build-1/` and sessions in a build-1 manifest. Merge this list with `docs/build-0-observations.md` (written at the end of build-0) before planning, so session-reported skill gaps and template fixes are not lost. Run and job ids for the evidence below are in `docs/sessions/`, not here.

| # | Request | Review gaps | Size |
|---|---|---|---|
| R1 | [Publish the SDK skills to the Unity Gateway Skills library](#r1-publish-the-sdk-skills-to-the-unity-gateway-skills-library) | customer-path blocker "skills not in the project" | M |
| R2 | [Ship a wheel instead of vendored modules](#r2-ship-a-wheel-instead-of-vendored-modules) | G1, G2, G7 | M |
| R3 | [Fix the run kit](#r3-fix-the-run-kit) | run-kit blockers | M |
| R4 | [Fix the library and template defects](#r4-fix-the-library-and-template-defects) | G5, G6, G9, overrides mismatch | M |
| R5 | [Add CI](#r5-add-ci) | G4 | S-M |
| R6 | [One guided setup notebook](#r6-one-guided-setup-notebook) | G8, customer path | M |
| R7 | [Raise the databricks-sdk floor](#r7-raise-the-databricks-sdk-floor) | G3 | S |
| R8 | [Reconcile overlapping skills](#r8-reconcile-overlapping-skills) | skill overlap | S |
| R9 | [Prove the customer path on a second domain](#r9-prove-the-customer-path-on-a-second-domain) | run kit never dogfooded | L |

---

## R1. Publish the SDK skills to the Unity Gateway Skills library

**Problem.** The six skills (`skills/ontology-deep-eda`, `ontology-domain-research`, `ontology-context-extraction`, `ontology-mv-synthesis`, `ontology-agent-curation`, `ontology-tuning`) exist only as folders in the SDK. `scaffold_project` does not copy them into a customer project, yet the run kit's sessions are told to use `skills/ontology-*`. They are not versioned, governed or discoverable, and interactive users (Genie Code, Genie One) cannot use them without a build.

**Evidence.** `scaffold.py` copies only the two bundle templates, the run kit, three vendored modules, `sdk_config.json` and empty docs folders. `templates/run/waves.json` session scopes say "using skills/ontology-...". `templates/run/README.md` step 3 leaves skill loading to the customer.

**Change.**
1. **Mapping file.** Add a `skills.yaml` mapping (repository root, since the repository holds several projects) from each `genie-ontology-modeled-knowledge-sdk/skills/<folder>` to a Unity Catalog skill `<catalog>.<skills_schema>.<skill_id>`. The mapping lets ids follow the Unity Catalog snake_case convention while `SKILL.md` keeps its `name`.
2. **GitHub publishing.** Add a workflow that runs the Unity Gateway publishing action (`databricks/unity-gateway/actions/publish-skills`) on merge to the publishing branch, with `workflow_dispatch` dry runs. Pin the action to a reviewed commit SHA, use a `production` GitHub environment and GitHub OIDC workload identity federation on a publishing service principal (no stored secret), and filter paths to `genie-ontology-modeled-knowledge-sdk/skills/**`, `skills.yaml` and the workflow file.
3. **Workspace publishing (no GitHub).** Add `notebooks/publish_skills`: for each skill folder, create the skill if missing, upload every file through the Files API under `/Skills/<catalog>/<schema>/<skill>/`, then finalize (the same create -> upload -> finalize flow genie-build-waves setup uses). Idempotent: an existing skill is updated, not duplicated. Requires the schema to exist; the notebook checks and reports instead of creating it unless told to.
4. **Grants.** Document and, in the notebook, optionally apply: publisher needs USE CATALOG, USE SCHEMA and CREATE VOLUME on the skills schema (plus READ VOLUME and WRITE VOLUME to update existing skills); consumers need USE CATALOG, USE SCHEMA and READ VOLUME (least privilege: READ VOLUME on each skill rather than the schema).
5. **Consumers.** Run kit plans and the session scope text reference skills by Unity Catalog id with the workspace folder as fallback; `scaffold_project` records the skills location (catalog, schema, ids) in the project's `PROJECT_MEMORY.md` and `sdk_config.json` (new optional `skills` key in the schema).
6. **Skill hygiene test.** A test checks each skill folder against the platform limits (text files only, at most three folder levels and 50 files or folders) and that `SKILL.md` front matter has `name` and `description`.

**Files.** `skills.yaml` (new), `.github/workflows/publish-genie-ontology-skills.yml` (new), `notebooks/publish_skills` (new), `schemas/sdk_config.schema.json`, `config.py`, `scaffold.py`, `templates/run/waves.json`, `templates/run/plans/*.md`, `templates/run/README.md`, `tests/test_skills.py` (new), README.

**Acceptance criteria.**
- [ ] The workflow's dry run validates all six skills; a real run publishes them, and listing skills in the target schema returns six ids.
- [ ] Running `notebooks/publish_skills` twice changes nothing the second time.
- [ ] A consumer with only the documented grants can load a skill in interactive Genie Code.
- [ ] Spike, recorded in the session summary: an unattended Genie Code job task loads a Unity Catalog skill. If it cannot, the workspace-folder fallback is documented and still works.
- [ ] `tests/test_skills.py` passes for all six skills.

**Dependencies.** Workspace previews for Unity Gateway skills in Genie (and the account-level Enhanced Unity AI Gateway preview); an existing skills schema; a publishing service principal with OIDC federation. Feeds R3 and R6.

**Open questions.** Which catalog and schema per environment; whether ids are snake_case (`ontology_mv_synthesis`) or keep the folder names; whether genie-build-waves' own skills move to the same publishing workflow.

---

## R2. Ship a wheel instead of vendored modules

**Problem.** The SDK has no release artifact (G1). The library reaches projects as byte-for-byte copies in `ontology-metric-views/src/genie_ontology_modeled_knowledge_sdk_vendored/` with no version stamp (G2), so fixes never reach existing projects and copies drift silently. The init notebook imports the SDK by inserting `<sdk>/src` into `sys.path`, found through an internal `dbutils` context API (G7).

**Change.**
1. **Versioning.** Move to `0.1.0` with a single version source (`importlib.metadata` in `__init__.py`, setuptools reads it once) and a `CHANGELOG.md`; semantic versioning, and the `sdk_config` schema version bumps on breaking input changes.
2. **Entry points.** Add `[project.scripts]` for the existing CLIs, for example `gos-check-config`, `gos-validate-mv`, `gos-build-manifest`, `gos-render-agents`, `gos-scaffold`. Keep `python -m` working.
3. **Build and publish.** Build a pure-Python wheel; publish it to a Unity Catalog volume (`/Volumes/<catalog>/<schema>/<volume>/genie_ontology_modeled_knowledge_sdk-<version>-py3-none-any.whl`) and optionally an internal package index.
4. **Bundles use the wheel.** The metric-views bundle template's job environment lists the wheel as a dependency through a bundle variable (`sdk_wheel`), so registration notebooks import `genie_ontology_modeled_knowledge_sdk` instead of the vendored package; gate text and skills drop the `PYTHONPATH=...vendored` forms.
5. **Scaffold.** No vendored folder by default; `--vendor` (and `vendor=True`) keeps an offline fallback that writes a `VENDORED_VERSION` file, and a test fails when a vendored copy differs from the SDK at that version.
6. **Init notebook.** Installs the wheel (`%pip install <wheel path or version>`) instead of editing `sys.path`.

**Files.** `pyproject.toml`, `src/genie_ontology_modeled_knowledge_sdk/__init__.py`, `CHANGELOG.md` (new), `scaffold.py`, `templates/ontology-metric-views/` (job YAML, notebooks, README), `templates/run/waves.json` gate text, skills that cite the vendored path, `notebooks/init_ontology_project`, tests.

**Acceptance criteria.**
- [ ] CI (R5) builds the wheel as an artifact; `pip install` of it on serverless gives working `gos-*` commands.
- [ ] The metric-views template job registers a fixture metric view using only the installed wheel.
- [ ] `scaffold_project` without `vendor` writes no `genie_ontology_modeled_knowledge_sdk_vendored/`; with `vendor` the drift test passes.
- [ ] No `sys.path` manipulation remains in shipped notebooks.

**Dependencies.** R5 (build in CI), R7 (dependency floor), a volume for wheels.

---

## R3. Fix the run kit

**Problem.** Build-0 dogfooded the SDK through its own manifest, not `templates/run/`. Reading the run kit shows a customer run would hit the same stops build-0 hit, plus new ones.

**Evidence.** `templates/run/waves.json` has no top-level `branch` and no `authorization_policy`; its approvals are only `jobs.run_now` for sessions 06 and 10 and `workspace.write` for 07, with no explicit `bundle.deploy` naming either project bundle for the deploying sessions 06, 09 and 10. Plan `07_uc_pages.md` runs the live upsert when no domain exists. The wave 6 gate requires at least 70% accuracy.

**Change.**
1. **Branch.** New run-kit token `{{branch}}` rendered by `scaffold_project` into a top-level `"branch"` (setup otherwise empties the build job's branch default and the first wave's sync fails).
2. **Approvals.** For each deploying session, explicit `authorizations` that name the exact bundle and target: 06 `bundle.deploy` + `jobs.run_now` (metric-views bundle, registration job); 09 `bundle.deploy` (agents bundle); 10 `bundle.deploy` for both bundles + `jobs.run_now`. Add an `authorization_policy` that lets an external monitor grant only `jobs.run_now` and `bundle.deploy` on `owned_assets`, and give each deploying session `owned_assets` text matching its approvals.
3. **UC Pages prerequisite.** Add a `manual_prereqs` entry before the Pages wave: a Discover domain for the project exists (owner provides its id in `sdk_config.json`, new optional `pages_domain_id`) or the owner approves creating one. Without it the session runs the dry run only, writes the results, and ends `pass` with "publishing deferred" so the build continues.
   * **Development domain (owner decision, 2026-11-25).** The development metastore is at its domain limit, so build 1 develops and dogfoods Pages in an existing domain the owner controls, chosen in [the dev Pages domain session summary](../../sessions/2026-11-25_build-1-dev-pages-domain.md). Its id goes only in a gitignored or session-summary location, never in committed SDK files. Pages are written as `DRAFT` only, and every created page id is recorded in the project's `docs/pages/pages_registration.md`, so the pages can be removed later.
4. **Soft tuning gate.** The wave 6 gate requires the benchmark results to exist with a final run after the build started, and records accuracy; below 70% becomes a tuning backlog entry, not a failed build (build-0's decision).
5. **Skills.** Session scopes and plans load skills by the ids from R1 (fallback: workspace folder).
6. **Agents schema.** The agents session reads the resolved metric view schema produced by R4 instead of a hand-written value.
7. **Tests.** Extend `tests/test_run_kit.py`: top-level `branch` present; every `allow_deploy` session has a `bundle.deploy` approval naming a bundle under `build_root`; registration sessions have `jobs.run_now`; the Pages wave has its `manual_prereqs`; genie-build-waves `validate_authorizations` returns 0 errors (not only `validate_manifest`).

**Files.** `templates/run/waves.json`, `templates/run/plans/06_*.md`, `07_uc_pages.md`, `09_*.md`, `10_tuning.md`, `templates/run/INDEX.md`, `templates/run/README.md`, `scaffold.py` (`RUN_TOKENS`), `schemas/sdk_config.schema.json`, `tests/test_run_kit.py`.

**Acceptance criteria.**
- [ ] Rendered run kit: `validate_manifest` and `validate_authorizations` 0 errors, 0 warnings.
- [ ] The new `test_run_kit.py` assertions pass and fail on a deliberately broken copy.
- [ ] R9 runs the kit with no hand edits to generated plans or the manifest.

**Dependencies.** R1 (skill ids), R4 (resolved schema). Framework note: the genie-build-waves setup should read the branch from the manifest before syncing (tracked separately in genie-build-waves).

---

## R4. Fix the library and template defects

**Problem and change, one item each.**

1. **Agent size limits disagree (G5).** `geniespace.plan_agents` splits at `max_per_agent` (default 50) but `validate_space` allows at most 30 data sources (`MAX_DATA_SOURCES`), so a domain with 31-50 metric views gets one agent that fails validation. Split at `min(max_per_agent, MAX_DATA_SOURCES)`; `config.validate_config` warns when `max_metric_views_per_agent` exceeds 30; update the L200-G rule text and the agent-curation skill.
2. **Account-wide page matching (G6).** `pages.upsert_pages` without `domain_id` lists every page in the account and updates any page whose title matches, which can overwrite another team's page. Live upserts require `domain_id` (missing -> every term is an `error` result, nothing written); matching is scoped to the domain; account-wide listing is used only in dry runs to report title collisions. Also strip markdown links before truncating the 160-character description.
3. **Broad default grant (G9).** Both templates default `consumer_group` to `account users`. Remove the default so the owner must name a group; document it in both READMEs and the overrides examples.
4. **Two overrides files that must agree.** The agents bundle needs the metric views' full dev-prefixed schema name, written by hand; build-0 stopped when it named a schema that did not exist (the metric-views template's `schema_name` default is `ontology`, the overrides assumed the project's own name). Make one source of truth: the metric-views registration job writes the resolved catalog and schema to a small JSON (for example `docs/registration/resolved_target.json`), and `geniespace render` accepts it with `--params`; the guided notebook (R6) writes both overrides files from the same inputs; `scaffold_project` renders `schema_name` from `sdk_config.target_schema` instead of the generic default.

**Files.** `geniespace.py`, `config.py`, `pages.py`, `templates/ontology-metric-views/databricks.yml` + README + registration notebook, `templates/ontology-genie-agents/databricks.yml` + README, `scaffold.py`, `skills/ontology-agent-curation/SKILL.md`, tests.

**Acceptance criteria.**
- [ ] Tests: 29, 30, 31 and 50 metric views produce agents that all pass `validate_space`.
- [ ] Tests with a fake pages client: a same-title page in another domain is never updated; a live upsert without `domain_id` writes nothing.
- [ ] `bundle validate --strict` fails with a clear message when `consumer_group` is missing.
- [ ] Rendering agents from the registration job's resolved-target JSON gives identifiers that exist after registration (checked in R9).

**Dependencies.** None; R3 and R6 consume item 4.

---

## R5. Add CI

**Problem.** No lint, type check or CI (G4); regressions show up only inside a build wave, and `test_run_kit`'s genie-build-waves check is skipped wherever genie-build-waves is not next to the SDK.

**Change.**
1. Add `ruff` (lint + format) and `mypy` configuration to `pyproject.toml`; fix or annotate existing findings.
2. Add a GitHub Actions workflow for pull requests touching `genie-ontology-modeled-knowledge-sdk/**`: lint, type check, pytest with `GENIE_BUILD_WAVES_DIR` pointing at the repository's genie-build-waves folder (so the manifest test always runs), wheel build (R2) uploaded as an artifact.
3. A job that runs `databricks bundle validate --strict` on both templates with placeholder overrides, authenticated to a dev workspace through GitHub OIDC (no stored secret).
4. Follow the repository's existing SDLC workflow conventions (required checks, branch protection on `main`, feature branches only).

**Files.** `pyproject.toml`, `.github/workflows/genie-ontology-modeled-knowledge-sdk-ci.yml` (new), small code fixes from lint and type findings.

**Acceptance criteria.**
- [ ] The workflow passes on a clean branch and fails on a seeded lint error, type error and test failure.
- [ ] The genie-build-waves manifest test runs (not skipped) in CI.
- [ ] Both templates pass `bundle validate --strict` in CI.

**Dependencies.** A dev workspace service principal with OIDC federation for the validate job.

---

## R6. One guided setup notebook

**Problem.** A customer assembles the SDK, two overrides files, skills and a genie-build-waves instance by hand (about seven manual steps). The init notebook's defaults are real-looking example values (`target_catalog = main`), so a customer who keeps them fails the access check on the first run (G8).

**Change.** Extend `notebooks/init_ontology_project` (or add `setup_ontology_project`) to:
1. Start with empty widgets; an "example" dropdown loads the TPC-H values from `examples/tpch/sdk_config.json` instead of hard-coding them.
2. Check prerequisites and report each as pass or action needed: target catalog access and CREATE SCHEMA, the warehouse exists and the user can use it, the target folder is a Git folder on a feature branch (not `main`), the skills schema and skills exist (R1), and the Pages domain if one is set (R3).
3. After scaffolding, write both gitignored `variable-overrides.json` files from the same validated inputs (R4 item 4).
4. Publish or reference the skills (R1).
5. Write the genie-build-waves instance vars file (outside the repository) and print the exact deploy, setup and run steps.
6. End with a checklist of what is done and what the owner must still do.

**Files.** `notebooks/init_ontology_project` (or a new notebook), `examples/tpch/sdk_config.json`, `scaffold.py` (helpers to write overrides), `docs/usage.md`, README.

**Acceptance criteria.**
- [ ] With empty defaults the notebook does nothing until required inputs are set.
- [ ] On a fresh project it writes both overrides files with matching catalog and schema and they pass `bundle validate --strict`.
- [ ] Re-running changes nothing (idempotent) and never overwrites edited overrides without `force`.
- [ ] The printed steps deploy a working genie-build-waves instance (checked in R9).

**Dependencies.** R1, R2, R3, R4.

---

## R7. Raise the databricks-sdk floor

**Problem.** `pyproject.toml` requires `databricks-sdk>=0.40`, while the code calls the Genie conversation API (`benchmark`) and the skills publishing flow needs a much newer SDK (G3). Older pre-installed SDKs fail at run time.

**Change.** Find the first `databricks-sdk` release with every API the SDK calls (`genie.start_conversation_and_wait`, `genie.get_message_attachment_query_result`, the skills create/finalize API used by R1, `files`); set the floor to it and an upper bound below the next major version. Notebooks install the same range. CI (R5) tests both the floor and the latest release.

**Files.** `pyproject.toml`, notebooks' install cells, CI matrix, README.

**Acceptance criteria.**
- [ ] CI passes on the floor version and the latest version.
- [ ] A test imports every SDK service the code uses.

**Dependencies.** R5.

---

## R8. Reconcile overlapping skills

**Problem.** `ontology-mv-synthesis` overlaps the platform `metric-views` skill and an existing workspace metric-view generation skill; an agent may load several with conflicting rules. The same risk applies to `ontology-*` skills that wrap platform skills (for example Discover pages).

**Change.**
1. Inventory each SDK skill against platform and published skills with similar triggers.
2. Keep one authoritative source per rule: SDK skills hold only SDK-specific rules (tokens, manifest, `# verified:` joins, subdomain comments, MV-first tuning) and reference the platform skill for syntax; remove restated platform rules.
3. Make descriptions trigger only for Genie Ontology Modeled Knowledge SDK work (name the SDK stage and the run project files), so they do not compete with general metric view requests.
4. Add `skills/README.md`: each skill, its stage, the platform skills it relies on, and precedence when both load.

**Files.** `skills/*/SKILL.md`, `skills/README.md` (new).

**Acceptance criteria.**
- [ ] No SKILL.md restates platform metric view syntax rules.
- [ ] `skills/README.md` lists every skill with its dependencies and precedence.
- [ ] A manual check: a general "create a metric view" request in Genie Code does not load an `ontology-*` skill.

**Dependencies.** Coordinate with R1 so the published versions are the reconciled ones.

---

## R9. Prove the customer path on a second domain

**Problem.** The run kit and init notebook have never been used the way a customer would use them; build-0 ran a hand-written manifest over the SDK's own folder.

**Change.**
1. Choose a second sample dataset available in any workspace (for example another `samples` schema) and a separate Git folder that mimics a customer project.
2. Follow only the published instructions (`docs/usage.md`, the guided notebook from R6): scaffold, write overrides, use the published skills (R1) and wheel (R2), deploy a separate genie-build-waves instance pointed at the project, run setup, run the build.
3. Do not edit generated plans or the manifest; only tokens rendered by the scaffold may differ from the templates.
4. Log every manual intervention (who, why, which step) and turn each into a fix or a documented prerequisite.

**Files.** A run report under `docs/` (generic findings) plus session summaries with ids under `docs/sessions/`; fixes land in the files of the request they belong to.

**Acceptance criteria.**
- [ ] All waves pass, or stop only on documented owner prerequisites (for example the Pages domain).
- [ ] Zero hand edits to generated plans or the manifest.
- [ ] The intervention log is empty or every entry has a merged fix or a documented prerequisite.

**Dependencies.** R1-R7 (R8 recommended).

---

## Sequencing

Priority order is the owner's ranking; build order follows dependencies. Requests in the same step can run as parallel sessions only if their owned files are disjoint; where they overlap the table says so.

| Step | Requests | Why here |
|---|---|---|
| 1 | R5 + R7 | CI and the dependency floor are needed to build and test everything else; both change `pyproject.toml` and the CI workflow, so one session does both |
| 2 | R4 | Library and template fixes first: R2 and R4 both change `scaffold.py` and the metric-views template, so they run in sequence |
| 3 | R2, R8 | Wheel and packaging (R2) in parallel with skill reconciliation (R8). R8 owns `skills/`, so R8 also makes R2's skill wording change (installed package instead of the vendored path) |
| 4 | R1 | Publish the reconciled skills |
| 5 | R3, R6 | Run kit and guided notebook consume R1, R2 and R4; R3 owns `templates/run/`, R6 owns the notebook and `docs/usage.md` (both touch `scaffold.py`: give it to R3, R6 adds helpers in a new module) |
| 6 | R9 | End-to-end customer-path proof |

## Related items tracked elsewhere

* genie-build-waves setup reads the build job's branch default before patching the job (framework fix, genie-build-waves backlog; R3 item 1 avoids it for SDK runs).
* Remove the temporary IP access list entry added for the external monitor after build-0 (operations, see the build-waves deploy session summary).
* Tuning results below 70% accuracy from build-0 (if any) go into the tuning backlog under R3 item 4.
* Session-reported skill gaps and template fixes: `docs/build-0-observations.md` (written at the end of build-0).
