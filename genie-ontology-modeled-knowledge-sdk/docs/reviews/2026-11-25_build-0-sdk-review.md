# Build-0 SDK Code Review

Date: 2026-11-25 | Scope: the code build-0 produced (waves 0-0 to 0-3: library, skills, templates, run kit, init tool) | Method: file reads only. **pytest was not run** for this review; test results come from the build's own wave gates. Run and job ids are in [docs/sessions/](../sessions/INDEX.md), not here.

Questions answered:
1. Does the code follow SDK best practices?
2. How does it reference genie-build-waves?
3. How easy would it be for a customer to deploy and use on their own?
4. What should improve next, including publishing the skills to the Unity Gateway Skills library?

## 1. SDK best practices

### Strengths

| Area | Evidence |
|---|---|
| Packaging layout | `pyproject.toml`: setuptools `src/` layout, `requires-python >=3.11`, package data for `schemas/*.json`, pytest config |
| Small, testable modules | `src/genie_ontology_sdk/`: `config`, `mv_yaml`, `manifest`, `geniespace`, `pages`, `benchmark`, `scaffold`. Pure Python, no Spark imports; Databricks access through an injected `WorkspaceClient` (`config.check_access`, `pages.RestPagesClient`) |
| Explicit public API | Every module has `__all__` and a docstring that states its contract (for example the `mv_yaml` rules MV001-MV007 and the `benchmark` scoring definition) |
| Validated input contract | `schemas/sdk_config.schema.json` (JSON Schema 2020-12) plus `config.validate_config` name-shape checks; `check_access` reports problems instead of raising |
| Safety in generated SQL | `mv_yaml` only substitutes parameter values that are plain or backtick-quoted identifiers (`_SAFE_VALUE_RE`) |
| Determinism | `geniespace` builds byte-identical `.geniespace.json` output (uuid5 ids, sorted keys); `manifest` sorts entries |
| Safe defaults for writes | `pages.upsert_pages` defaults to `dry_run=True` and never deletes; `scaffold_project` never overwrites without `force` and never touches `.databricks/` or `.rendered/` |
| CLIs | `python -m genie_ontology_sdk.mv_yaml validate`, `manifest build`, `geniespace render`, `scaffold` |
| Tests | One test file per module plus template, scaffold and run-kit tests (`tests/`, 10 files + `conftest.py` with a fake `WorkspaceClient`) |
| Workspace-neutral templates | Bundle templates carry no hosts or real catalogs; real values live in gitignored `variable-overrides.json` |

### Gaps

| # | Gap | Evidence | Impact |
|---|---|---|---|
| G1 | No release artifact | `version = "0.0.1"`, no wheel build or publish step, no `[project.scripts]` entry points, no CHANGELOG | Customers cannot pin a version; CLIs need `python -m` and a `PYTHONPATH` |
| G2 | Library reaches projects as copied files | `scaffold.VENDORED_MODULES` copies `mv_yaml.py`, `manifest.py`, `geniespace.py` into `ontology-metric-views/src/genie_ontology_sdk_vendored/` with no version stamp | Copies drift silently from the SDK; fixes do not reach existing projects |
| G3 | Dependency floor too low | `databricks-sdk>=0.40`, while `benchmark` uses the Genie conversation API and skill publishing needs a much newer SDK | Fails at run time on older pre-installed SDKs (unverified per method; the notebooks upgrade the SDK first) |
| G4 | No lint, type check or CI | No ruff/mypy config, no GitHub Actions workflow | Regressions only show up inside a build wave |
| G5 | Agent size limits disagree | `geniespace.plan_agents` default `max_per_agent=50`, but `validate_space` allows at most 30 data sources (`MAX_DATA_SOURCES`) | A domain with 31-50 metric views gets one agent that fails validation; the split threshold should be `min(max_per_agent, 30)` |
| G6 | Account-wide page matching | `pages.upsert_pages` without `domain_id` lists every page in the account and **updates** a page whose title matches | Can overwrite another team's page with the same title (build-0 session 13 found 8 such collisions) |
| G7 | Notebook bootstraps by path | `notebooks/init_ontology_project` inserts `<sdk>/src` into `sys.path`, found from the notebook path through an internal `dbutils` context API | Breaks if the notebook is moved or copied; an installed wheel removes the need |
| G8 | Example defaults look real | Init notebook widget defaults are TPC-H values with `target_catalog = main`; in a workspace without `main` the access check fails (its last interactive run ended with "Fix the access problems", likely this, not proven) | First-run failure for a customer who keeps defaults |
| G9 | Broad default grant | `ontology-metric-views` and `ontology-genie-agents` templates default `consumer_group` to `account users` (SELECT on the schema, CAN_RUN on agents) | Over-shares by default; should be required with no default |

## 2. How the SDK references genie-build-waves

Loosely: there is **no runtime import** of genie-build-waves anywhere in `src/`.

| Touchpoint | Where | Notes |
|---|---|---|
| The run kit is a genie-build-waves manifest | `templates/run/waves.json`, `templates/run/plans/*.md`, `templates/run/INDEX.md` | `scaffold_project` copies it into the customer project's `docs/plans/`; the customer deploys a genie-build-waves instance pointed at it |
| Manifest validation in tests | `tests/test_run_kit.py` | Finds genie-build-waves via `$GENIE_BUILD_WAVES_DIR` or a sibling `genie-build-waves/` folder, imports `waves_manifest.validate_manifest`; that test is skipped if it is absent |
| Deployment instructions | `templates/run/README.md` step 3, SDK `README.md` | Text links to `../genie-build-waves` and its README |
| Skills | `templates/run/README.md` step 3 | "publish or copy `skills/ontology-*` so that build sessions can load them"; genie-build-waves' manifest `skills` object only covers its own runner, integrator and monitor skills |
| Conventions | run plans, skills | Sessions never run Git; status files; gates; continuation passes; `authorizations` |

Assessment: the coupling is right for an SDK (pluggable orchestrator, testable without it). Its weak point is that the customer must assemble the two halves by hand: the run kit's correctness depends on genie-build-waves rules (approvals, branch, single deployer), and those rules are only checked by an optional test.

## 3. Customer deploy-and-use path

What a customer does today:

1. Get both folders: the SDK and genie-build-waves (same repo here; two separate concerns).
2. Run `notebooks/init_ontology_project` with their inputs; it validates, checks access and scaffolds a project into a Git folder on a feature branch.
3. Write two gitignored `variable-overrides.json` files with matching catalog, schema, warehouse and group values (the agents bundle needs the **dev-prefixed** metric view schema name that the metric-views bundle produces).
4. Make the `skills/ontology-*` skills loadable by build sessions (not automated).
5. Deploy a genie-build-waves instance from the **web terminal** (`scripts/deploy_instance.py`), run its setup job, optionally its smoke test.
6. Start the build and watch gates; repair failures (or wire an external monitor, which needs a service principal, grants, Git token and IP access list entries).
7. Review and merge the feature branch.

Prerequisites: Genie Code job tasks, the Unity Gateway skills preview, serverless, a Git credential for the job's run-as identity, CREATE SCHEMA on the target catalog, and admin help for Pages domains.

**Difficulty: high for a typical customer data engineer; feasible for an SA/FDE.** Evidence from build-0 (run on generic sample data by the SDK's author) — every one of these stopped the build until a person acted:

| Stop | Root cause | Customer-facing lesson |
|---|---|---|
| Registration job could not run | `allow_deploy` implies only `bundle.deploy`, not `jobs.run_now` | Approvals must be in the manifest |
| Monitor blocked by IP access list | Monitor egress IP not allowed | External-monitor networking is a prerequisite |
| Setup did not pull the branch | genie-build-waves setup reads the job's branch default before it patches the job; the manifest had no top-level `branch` | Always set `branch` in the manifest |
| UC Pages blocked | No Discover domain; domain creation is opt-in | Domain must exist (or be approved) before the Pages wave |
| Agent deployment blocked | The agents bundle's overrides named a schema that did not exist (template default `schema_name` is `ontology`, the overrides assumed `ontology_tpch`) | Two hand-written overrides files must agree; derive one from the other |

### Customer-path blockers in the run kit (not yet exercised)

Build-0 dogfooded the SDK through its own manifest, not through `templates/run/`. Reading the run kit shows the customer path would hit:

* **Skills not in the project.** `scaffold_project` copies no `skills/` folder, yet run sessions are told to use `skills/ontology-*`.
* **No top-level `branch` and no `authorization_policy`** in `templates/run/waves.json` (the setup branch bug).
* **No explicit `bundle.deploy` approval per bundle** for the deploying sessions (06, 09, 10); the implied approval names "the bundle at build_root", which is neither project bundle.
* **UC Pages without a domain.** Plan `07_uc_pages.md` runs the live upsert even when no domain exists, which with G6 can update other teams' pages.
* **Tuning gate is hard.** The run kit's wave 6 gate requires >= 70% accuracy, so a first run on a new domain likely fails and needs manual waiving.

## 4. Recommended improvements (prioritized)

1. **Publish the six SDK skills to the Unity Gateway Skills library.** Use the Unity Gateway publishing GitHub Action (`databricks/unity-gateway/actions/publish-skills`, GitHub OIDC, no stored secret) with a `skills.yaml` mapping from `genie-ontology-sdk/skills/<name>` to `<catalog>.<skills_schema>.<snake_case_name>`; a notebook or SDK alternative is the create skill -> Files API upload -> finalize flow genie-build-waves setup already uses. Grant consumers USE CATALOG, USE SCHEMA and READ VOLUME on the skills (publishing needs CREATE VOLUME). Benefits: one governed, versioned copy; usable from interactive Genie Code and Genie One (UC skills already appear in Genie Code's skill list) as a "lite" path without build waves; removes blocker "skills not in the project". To verify: that unattended Genie Code job tasks load UC skills (earlier genie-build-waves builds fell back to workspace `SKILL.md` files).
2. **Ship a wheel instead of vendored modules (G1, G2, G7).** Build `genie_ontology_sdk-<version>-py3-none-any.whl`, add `[project.scripts]` (`gos-validate`, `gos-render`, `gos-scaffold`), publish to a UC volume or package index, and install it in bundle job environments; keep vendoring only as an offline fallback with a version stamp.
3. **Fix the run kit** (section 3 list): top-level `branch`, `authorization_policy` or per-session `bundle.deploy` / `jobs.run_now` approvals naming each project bundle, a Pages `manual_prereqs` entry (domain exists) or a skip path, a soft tuning gate (record accuracy, backlog below 70%), and let `scaffold_project` wire skills (copy or UC reference).
4. **Fix the library defects:** G5 (agent split at `min(max_per_agent, 30)`), G6 (require `domain_id` for live upserts and match titles only inside the domain), G9 (no default `consumer_group`), and derive the agents bundle's `schema` from the metric-views bundle (one source of truth instead of two overrides files).
5. **Add CI (G4).** A GitHub Actions workflow: ruff, mypy (or pyright), pytest with genie-build-waves checked out so `test_run_kit` always runs, and `bundle validate --strict` on both templates. Follow the repo's `sdlc-best-practices` workflow pattern.
6. **One guided setup notebook.** Extend `init_ontology_project` to: start from empty widgets (G8), write both overrides files from the access-checked inputs, publish or reference the skills, and print the exact genie-build-waves deploy commands and vars file.
7. **Raise the dependency floor (G3)** to the first `databricks-sdk` release with the Genie conversation and skills APIs, and test against it.
8. **Reconcile overlapping skills.** `ontology-mv-synthesis` overlaps an existing metric-view generation skill and the platform `metric-views` skill; keep one authoritative synthesis skill and have the others reference it.
9. **Prove the customer path in build 1.** Scaffold a second sample domain with `init_ontology_project` and run it through `templates/run/` unchanged, so the run kit, not a hand-written manifest, is what gets dogfooded.

## Not verified in this review

* pytest results (not run; the wave gates ran it during the build).
* Whether Genie Code job tasks load UC skills.
* The exact cause of the init notebook's last failed access check (the `main` catalog default is the likely cause).
* The minimum `databricks-sdk` version the code needs.
